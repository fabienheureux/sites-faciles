#!/usr/bin/env -S uv run python
"""
paquet_facile.py
A tool for syncing the sites-faciles codebase and applying transformations.

Clones a specific version from upstream and applies namespacing transformations.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

# -- Logging ------------------------------------------------------------------


def setup_logger(verbose: int) -> None:
    """Configure logging verbosity based on verbosity level."""
    match verbose:
        case 0:
            level = logging.WARNING
        case 1:
            level = logging.INFO
        case _:
            level = logging.DEBUG

    logging.basicConfig(
        format="%(levelname)-8s %(message)s",
        level=level,
    )


# -- Git Integration ----------------------------------------------------------


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    logging.debug("Running: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=check,
            cwd=cwd,
        )
        return result
    except subprocess.CalledProcessError as exc:
        logging.error("Command failed: %s", " ".join(cmd))
        logging.error("Error: %s", exc.stderr)
        raise


def git_ls_files(pattern: str | None = None) -> list[str]:
    """Return tracked files matching a git pathspec (pattern)."""
    cmd = ["git", "ls-files"] + ([pattern] if pattern else [])

    try:
        result = run_command(cmd, check=False)
        if result.returncode != 0:
            logging.error("git ls-files failed: %s", result.stderr)
            return []
    except Exception as exc:
        logging.error("git ls-files failed: %s", exc)
        return []

    return [s for s in result.stdout.splitlines() if s]


def git_clone(repo_url: str, tag: str, target_dir: Path) -> None:
    """Clone a git repository at a specific tag."""
    logging.info("📥 Cloning %s @ %s", repo_url, tag)

    cmd = [
        "git",
        "clone",
        "--quiet",
        "-c",
        "advice.detachedHead=false",
        "--branch",
        tag,
        "--depth",
        "1",
        repo_url,
        str(target_dir),
    ]

    run_command(cmd)
    logging.info("✅ Clone completed")


# -- Configuration Loading ----------------------------------------------------


def load_config(path: Path) -> dict[str, Any]:
    """Load and parse YAML configuration file."""
    logging.info("📖 Loading rules from %s", path)
    try:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except FileNotFoundError:
        logging.error("Config file not found: %s", path)
        sys.exit(2)
    except yaml.YAMLError as exc:
        logging.error("Failed to parse config: %s", exc)
        sys.exit(2)
    except Exception as exc:
        logging.error("Unexpected error loading config: %s", exc)
        sys.exit(2)


def expand_rules(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand {app}, {package_name}, and {package_name_upper} placeholders into concrete rules and validate minimal schema."""
    apps: list[str] = config.get("apps", [])
    package_name: str = config.get("package_name", "sites_faciles")
    package_name_upper: str = package_name.upper()
    raw_rules: list[dict[str, Any]] = config.get("rules", []) or []

    expanded: list[dict[str, Any]] = []
    for rule in raw_rules:
        search: str | None = rule.get("search")
        replace: str | None = rule.get("replace")

        if not search or replace is None:
            logging.warning("Skipping invalid rule (missing search/replace): %s", rule)
            continue

        # Replace {package_name} and {package_name_upper} placeholders first
        search = search.replace("{package_name}", package_name)
        replace = replace.replace("{package_name}", package_name)
        search = search.replace("{package_name_upper}", package_name_upper)
        replace = replace.replace("{package_name_upper}", package_name_upper)

        if "{app}" in (search + replace) and apps:
            for app in apps:
                expanded.append(
                    {
                        **rule,
                        "search": search.replace("{app}", app),
                        "replace": replace.replace("{app}", app),
                    }
                )
        else:
            expanded.append({**rule, "search": search, "replace": replace})

    logging.info(
        "🔧 Expanded %d rules into %d concrete rules", len(raw_rules), len(expanded)
    )
    return expanded


# -- File Classification ------------------------------------------------------


def is_text_file(path: Path, text_exts: set[str]) -> bool:
    """Check if file should be treated as text based on file extension."""
    return path.suffix in text_exts


def get_files_for_rule(rule: dict[str, Any], scopes: dict[str, str]) -> list[str]:
    """Get list of files that match a rule's scope or path_glob."""
    path_glob: str | None = rule.get("path_glob")

    if path_glob:
        return git_ls_files(path_glob)

    scope_name: str | None = rule.get("scope")
    if not scope_name:
        logging.warning("Rule missing both 'path_glob' and 'scope'; skipping: %s", rule)
        return []

    file_glob = scopes.get(scope_name)
    if not file_glob:
        logging.warning("Unknown scope %r in rule; skipping: %s", scope_name, rule)
        return []

    return git_ls_files(file_glob)


# -- File Processing ----------------------------------------------------------


def apply_rule_to_text(text: str, rule: dict[str, Any]) -> tuple[str, int]:
    """
    Apply a single rule to text content.
    Returns tuple of (modified_text, replacement_count).
    """
    search: str = rule["search"]
    replace: str = rule["replace"]
    literal: bool = bool(rule.get("literal", False))
    filter_pattern: str | None = rule.get("filter")

    if literal:
        count = text.count(search)
        if count <= 0:
            return text, 0
        return text.replace(search, replace), count

    # Regex mode
    try:
        if filter_pattern:
            # Apply replacement only within sections matching the filter
            matches = re.findall(filter_pattern, text, re.DOTALL)
            new_text = text
            total_count = 0

            for match in matches:
                replaced_text, count = re.subn(search, replace, match)
                new_text = new_text.replace(match, replaced_text, 1)
                total_count += count

            return new_text, total_count
        else:
            new_text, count = re.subn(search, replace, text)
            return new_text, count

    except re.error as exc:
        logging.error("Invalid regex pattern %r in rule: %s", search, exc)
        return text, 0


def apply_rule_to_file(path: Path, rule: dict[str, Any], dry_run: bool) -> bool:
    """
    Apply a single rule to a single file.
    Returns True if file would be/was changed.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        logging.error("❌ Failed to read %s: %s", path, exc)
        return False

    new_text, count = apply_rule_to_text(text, rule)

    if count <= 0:
        return False

    search = rule["search"]
    replace = rule["replace"]
    logging.info("✏️  %s — %d replacement(s) for %r → %r", path, count, search, replace)

    if dry_run:
        logging.debug("DRY-RUN: not writing changes to %s", path)
        return True

    try:
        path.write_text(new_text, encoding="utf-8")
    except Exception as exc:
        logging.error("Failed to write %s: %s", path, exc)
        return False

    return True


# -- Directory Operations -----------------------------------------------------


def rename_template_dirs(
    apps: list[str], package_name: str, dry_run: bool = False
) -> None:
    """Move {app}/templates/{app} → {app}/templates/{package_name}_{app}."""
    for app in apps:
        src = Path(app) / "templates" / app
        dst = Path(app) / "templates" / f"{package_name}_{app}"

        if not src.exists():
            logging.debug("⏭️  No template dir to move for app %r: %s", app, src)
            continue

        if dst.exists():
            logging.warning("⚠️  Destination already exists, skipping: %s", dst)
            continue

        if dry_run:
            logging.info("[DRY-RUN] Would move: %s → %s", src, dst)
        else:
            logging.info("📂 Moving: %s → %s", src, dst)
            try:
                shutil.move(str(src), str(dst))
            except Exception as exc:
                logging.error("❌ Failed to move %s → %s: %s", src, dst, exc)


# -- Refactoring Logic --------------------------------------------------------


def _apply_transformations(config_path: Path, dry_run: bool, jobs: int | None) -> None:
    """Apply transformation rules to the current directory."""
    # Load configuration
    config = load_config(config_path)
    scopes: dict[str, str] = config.get("scopes", {})
    text_extensions_from_cfg: list[str] = config.get("text_extensions", [])

    # Set up text file extensions
    DEFAULT_TEXT_EXTENSIONS: set[str] = {
        ".py",
        ".html",
        ".htm",
        ".txt",
        ".md",
        ".csv",
        ".json",
        ".yaml",
        ".yml",
        ".po",
        ".ini",
        ".cfg",
        ".rst",
        ".xml",
        ".js",
        ".ts",
        ".css",
        ".scss",
    }
    text_exts = set(text_extensions_from_cfg) or DEFAULT_TEXT_EXTENSIONS
    logging.debug("Text extensions: %s", sorted(text_exts))

    # Expand rules
    expanded_rules = expand_rules(config)

    # Process files: apply each rule to all matching files
    total_files_changed = 0
    scanned_files = 0
    all_files_processed = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
        futures: list[concurrent.futures.Future[bool]] = []

        for rule in expanded_rules:
            files = get_files_for_rule(rule, scopes)

            for f in files:
                path = Path(f)
                if not is_text_file(path, text_exts):
                    continue

                all_files_processed.add(path)
                future = executor.submit(apply_rule_to_file, path, rule, dry_run)
                futures.append(future)

        scanned_files = len(all_files_processed)

        for future in concurrent.futures.as_completed(futures):
            try:
                if future.result():
                    total_files_changed += 1
            except Exception as exc:
                logging.error("Worker failed: %s", exc)

    logging.warning(
        "🎬 Finished replacements %s: scanned %d files, %d file(s) changed",
        "(dry-run)" if dry_run else "",
        scanned_files,
        total_files_changed,
    )

    # Rename template directories
    apps: list[str] = config.get("apps", [])
    package_name: str = config.get("package_name", "sites_faciles")
    if apps:
        rename_template_dirs(apps, package_name, dry_run)


# -- Sync Command -------------------------------------------------------------


def _cleanup_package_dir(package_dir: Path) -> None:
    """Remove unwanted directories and build files from the package."""
    # Cleanup unwanted directories and files
    for path in [".git", ".github"]:
        full_path = package_dir / path
        if full_path.exists():
            logging.debug("Removing %s", full_path)
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink()

    # Remove upstream's build files (we'll create our own)
    for build_file in ["pyproject.toml", "setup.py", "setup.cfg"]:
        build_path = package_dir / build_file
        if build_path.exists():
            logging.debug("Removing upstream %s", build_file)
            build_path.unlink()


def _process_templates(
    package_dir: Path, package_root: Path, package_name: str, tag: str
) -> None:
    """Process all template files and create package structure."""
    # Transform placeholders for templates
    package_name_title = package_name.replace("_", " ").title()
    package_name_kebab = package_name.replace("_", "-")
    class_name = "".join(word.capitalize() for word in package_name.split("_"))

    # Extract version from tag (remove leading 'v' if present)
    version = tag.lstrip("v")

    # Create main apps.py from template
    apps_template = Path("templates") / "apps.template.py"
    if apps_template.exists():
        logging.info("📝 Creating main apps.py from template")
        template_content = apps_template.read_text(encoding="utf-8")

        apps_content = template_content.replace("{PackageName}", class_name)
        apps_content = apps_content.replace("{package_name}", package_name)
        apps_content = apps_content.replace(
            "{package_verbose_name}", package_name_title
        )

        apps_file = package_dir / "apps.py"
        apps_file.write_text(apps_content, encoding="utf-8")
    else:
        logging.warning("⚠️  Template file not found: %s", apps_template)

    # Create pyproject.toml from template
    pyproject_template = Path("templates") / "pyproject.template.toml"
    if pyproject_template.exists():
        logging.info("📝 Creating pyproject.toml from template")
        template_content = pyproject_template.read_text(encoding="utf-8")

        pyproject_content = template_content.replace("{package_name}", package_name)
        pyproject_content = pyproject_content.replace(
            "{package_name_kebab}", package_name_kebab
        )
        pyproject_content = pyproject_content.replace("{version}", version)

        pyproject_file = package_root / "pyproject.toml"
        pyproject_file.write_text(pyproject_content, encoding="utf-8")
    else:
        logging.warning("⚠️  Template file not found: %s", pyproject_template)

    # Create __init__.py from template
    init_template = Path("templates") / "__init__.template.py"
    if init_template.exists():
        logging.info("📝 Creating __init__.py from template")
        template_content = init_template.read_text(encoding="utf-8")

        init_content = template_content.replace("{PackageName}", class_name)
        init_content = init_content.replace("{package_name}", package_name)

        init_file = package_dir / "__init__.py"
        init_file.write_text(init_content, encoding="utf-8")
    else:
        logging.warning("⚠️  Template file not found: %s", init_template)

    # Create README.md in package root
    readme_template = Path("templates") / "README.template.md"
    if readme_template.exists():
        logging.info("📝 Creating README.md from template")
        template_content = readme_template.read_text(encoding="utf-8")

        readme_content = template_content.replace("{package_name}", package_name)
        readme_content = readme_content.replace(
            "{package_verbose_name}", package_name_title
        )

        readme_file = package_root / "README.md"
        readme_file.write_text(readme_content, encoding="utf-8")
    else:
        logging.warning("⚠️  Template file not found: %s", readme_template)

    # Create management command structure from templates
    management_template_dir = Path("templates") / "management"
    if management_template_dir.exists():
        logging.info("📝 Creating management commands from templates")

        # Create management/commands directory
        management_dir = package_dir / "management"
        commands_dir = management_dir / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)

        # Process __init__.py files
        for init_file in ["__init__.template.py", "commands/__init__.template.py"]:
            init_template = management_template_dir / init_file
            if init_template.exists():
                template_content = init_template.read_text(encoding="utf-8")
                init_content = template_content.replace("{package_name}", package_name)

                # Determine output path (remove .template. from filename)
                output_path = management_dir / init_file.replace(".template.", ".")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(init_content, encoding="utf-8")

        # Process management command templates
        commands_template_dir = management_template_dir / "commands"
        if commands_template_dir.exists():
            for template_file in commands_template_dir.glob("*.template.py"):
                template_content = template_file.read_text(encoding="utf-8")
                command_content = template_content.replace(
                    "{package_name}", package_name
                )

                # Write to commands directory (remove .template. from filename)
                output_file = commands_dir / template_file.name.replace(
                    ".template.", "."
                )
                output_file.write_text(command_content, encoding="utf-8")
                logging.debug("  Created command: %s", output_file.name)
    else:
        logging.debug("⏭️  No management command templates found")

    # Create content_manager structure from templates
    content_manager_template_dir = Path("templates") / "content_manager"
    if content_manager_template_dir.exists():
        logging.info("📝 Creating content_manager files from templates")

        content_manager_dir = package_dir / "content_manager"
        content_manager_dir.mkdir(parents=True, exist_ok=True)

        # Process apps.py template if it exists
        apps_template = content_manager_template_dir / "apps.template.py"
        if apps_template.exists():
            template_content = apps_template.read_text(encoding="utf-8")
            apps_content = template_content.replace("{package_name}", package_name)

            output_file = content_manager_dir / "apps.py"
            output_file.write_text(apps_content, encoding="utf-8")
            logging.debug("  Created apps.py")
    else:
        logging.debug("⏭️  No content_manager templates found")

    # Create utils structure from templates
    utils_template_dir = Path("templates") / "utils"
    if utils_template_dir.exists():
        logging.info("📝 Creating utils files from templates")

        utils_dir = package_dir / "utils"
        utils_dir.mkdir(parents=True, exist_ok=True)

        # Process all Python template files in utils
        for template_file in utils_template_dir.glob("*.template.py"):
            template_content = template_file.read_text(encoding="utf-8")
            utils_content = template_content.replace("{package_name}", package_name)
            utils_content = utils_content.replace(
                "{package_name_upper}", package_name.upper()
            )

            # Write to utils directory (remove .template. from filename)
            output_file = utils_dir / template_file.name.replace(".template.", ".")
            output_file.write_text(utils_content, encoding="utf-8")
            logging.debug("  Created utils file: %s", output_file.name)
    else:
        logging.debug("⏭️  No utils templates found")

    # Create content_manager/blocks/choosers.py from template
    choosers_template = (
        Path("templates") / "content_manager" / "blocks" / "choosers.template.py"
    )
    if choosers_template.exists():
        logging.info("📝 Creating choosers.py from template")

        blocks_dir = package_dir / "content_manager" / "blocks"
        blocks_dir.mkdir(parents=True, exist_ok=True)

        template_content = choosers_template.read_text(encoding="utf-8")
        choosers_content = template_content.replace("{package_name}", package_name)

        output_file = blocks_dir / "choosers.py"
        output_file.write_text(choosers_content, encoding="utf-8")
        logging.debug("  Created choosers.py")
    else:
        logging.debug("⏭️  No choosers template found")


def _create_and_push_git_branch(package_dir: Path, tag: str) -> None:
    """Create a git branch with transformations and push to remote."""
    git_dir = package_dir / ".git"
    if not git_dir.exists():
        logging.warning("⚠️  No .git directory found, skipping git operations")
        return

    branch_name = f"{tag}-paquet-facile"
    logging.info("🌿 Creating branch %s", branch_name)

    try:
        # Create new branch
        run_command(["git", "checkout", "-b", branch_name], cwd=package_dir)

        # Stage all changes
        run_command(["git", "add", "-A"], cwd=package_dir)

        # Commit transformations
        commit_msg = f"Apply paquet-facile transformations for {tag}"
        run_command(["git", "commit", "-m", commit_msg], cwd=package_dir)

        # Get remote URL from main repository
        result = run_command(["git", "remote", "get-url", "origin"], check=False)
        if result.returncode == 0:
            main_repo_remote = result.stdout.strip()
            logging.info(
                "📡 Adding remote 'paquet-facile' pointing to %s", main_repo_remote
            )

            # Add the main repo as a new remote
            run_command(
                ["git", "remote", "add", "paquet-facile", main_repo_remote],
                cwd=package_dir,
                check=False,
            )

            # Push the new branch to the remote
            logging.info("🚀 Pushing branch %s to paquet-facile remote", branch_name)
            push_result = run_command(
                ["git", "push", "-f", "paquet-facile", branch_name],
                cwd=package_dir,
                check=False,
            )

            if push_result.returncode == 0:
                logging.info("✅ Successfully pushed branch to remote")
            else:
                logging.warning("⚠️  Failed to push branch: %s", push_result.stderr)
        else:
            logging.warning("⚠️  Could not get main repository remote URL")

    except Exception as exc:
        logging.warning("⚠️  Failed to create/push branch: %s", exc)


def run_sync(
    tag: str,
    config_path: Path,
    dry_run: bool,
    jobs: int | None,
    repo_url: str = "git@github.com:numerique-gouv/sites-faciles.git",
) -> None:
    """Sync sites-faciles from upstream and apply refactoring."""
    # Load config to get package_name
    config = load_config(config_path)
    package_name: str = config.get("package_name", "sites_faciles")

    temp_dir = Path(f"{package_name}_temp")
    package_root = Path(package_name)
    package_dir = package_root / package_name

    # Clean up temp directory if it exists
    if temp_dir.exists():
        logging.info("🧹 Removing existing temp directory")
        shutil.rmtree(temp_dir)

    # Clone repository
    git_clone(repo_url, tag, temp_dir)

    # Change to temp directory and apply transformations
    original_dir = Path.cwd()
    try:
        os.chdir(temp_dir)
        logging.info("🔧 Applying transformations...")

        # Adjust config path to be relative to temp dir
        config_path_adjusted = Path("..") / config_path
        _apply_transformations(config_path_adjusted, dry_run, jobs)

    finally:
        os.chdir(original_dir)

    if dry_run:
        logging.warning("🎬 DRY-RUN: Would create nested structure in %s", package_root)
        return

    # Create package structure: package_name/package_name/
    logging.info("📦 Creating nested package structure")
    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True)

    # Move cloned content into nested directory
    shutil.move(str(temp_dir), str(package_dir))

    # Process all templates to create package files
    _process_templates(package_dir, package_root, package_name, tag)

    # Create git branch, commit changes, and push (must be done LAST)
    _create_and_push_git_branch(package_dir, tag)

    # Cleanup unwanted files and directories
    _cleanup_package_dir(package_dir)

    logging.warning("✅ Sync completed successfully!")


# -- Main ---------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync sites-faciles from upstream and apply transformations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "tag",
        help="Git tag or branch to sync (e.g., v2.1.0)",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("search-and-replace.yml"),
        help="Path to YAML config (default: search-and-replace.yml)",
    )
    parser.add_argument(
        "--repo",
        default="git@github.com:numerique-gouv/sites-faciles.git",
        help="Repository URL to clone from",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without modifying files",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv)",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=None,
        help="Number of worker threads (default: CPU count)",
    )

    args = parser.parse_args()

    setup_logger(args.verbose)

    run_sync(
        tag=args.tag,
        config_path=args.config,
        dry_run=args.dry_run,
        jobs=args.jobs,
        repo_url=args.repo,
    )


if __name__ == "__main__":
    main()
