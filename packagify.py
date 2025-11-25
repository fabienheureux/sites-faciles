#!/usr/bin/env -S uv run python
"""
packagify.py
A tool for syncing and refactoring the sites-faciles codebase.

Commands:
  sync    - Clone a specific version and apply refactoring rules
  refactor - Apply refactoring rules to the current directory
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


def git_restore_files(pattern: str, source: str = "fork/main") -> None:
    """Restore files from a git source."""
    logging.info("🔄 Restoring %s from %s", pattern, source)
    cmd = ["git", "restore", f"--source={source}", pattern]

    try:
        run_command(cmd, check=False)
    except Exception as exc:
        logging.warning("Could not restore %s: %s", pattern, exc)


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
    """Expand {app} placeholders into concrete rules and validate minimal schema."""
    apps: list[str] = config.get("apps", [])
    raw_rules: list[dict[str, Any]] = config.get("rules", []) or []

    expanded: list[dict[str, Any]] = []
    for rule in raw_rules:
        search: str | None = rule.get("search")
        replace: str | None = rule.get("replace")

        if not search or replace is None:
            logging.warning("Skipping invalid rule (missing search/replace): %s", rule)
            continue

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
            expanded.append(rule)

    logging.info("🔧 Expanded %d rules into %d concrete rules", len(raw_rules), len(expanded))
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


def rename_template_dirs(apps: list[str], dry_run: bool = False) -> None:
    """Move {app}/templates/{app} → {app}/templates/sites_faciles_{app}."""
    for app in apps:
        src = Path(app) / "templates" / app
        dst = Path(app) / "templates" / f"sites_faciles_{app}"

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


def run_refactor(config_path: Path, dry_run: bool, jobs: int | None) -> None:
    """Run the refactoring process on the current directory."""
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

    # Build file-to-rules mapping to avoid redundant processing
    file_to_rules: dict[Path, list[dict[str, Any]]] = {}

    for rule in expanded_rules:
        files = get_files_for_rule(rule, scopes)

        for f in files:
            path = Path(f)
            if not is_text_file(path, text_exts):
                continue

            if path not in file_to_rules:
                file_to_rules[path] = []
            file_to_rules[path].append(rule)

    logging.info("📊 Found %d files to process", len(file_to_rules))

    # Process files with multithreading
    total_files_changed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
        futures: dict[concurrent.futures.Future[bool], Path] = {}

        for path, rules in file_to_rules.items():
            for rule in rules:
                future = executor.submit(apply_rule_to_file, path, rule, dry_run)
                futures[future] = path

        for future in concurrent.futures.as_completed(futures):
            path = futures[future]
            try:
                if future.result():
                    total_files_changed += 1
            except Exception as exc:
                logging.error("Worker failed for %s: %s", path, exc)

    logging.warning(
        "🎬 Finished replacements %s: scanned %d files, %d file(s) changed",
        "(dry-run)" if dry_run else "",
        len(file_to_rules),
        total_files_changed,
    )

    # Rename template directories
    apps: list[str] = config.get("apps", [])
    if apps:
        rename_template_dirs(apps, dry_run)


# -- Sync Command -------------------------------------------------------------


def run_sync(
    tag: str,
    config_path: Path,
    dry_run: bool,
    jobs: int | None,
    repo_url: str = "git@github.com:numerique-gouv/sites-faciles.git",
) -> None:
    """Sync sites-faciles from upstream and apply refactoring."""
    temp_dir = Path("sites_faciles_temp")
    target_dir = Path("sites_faciles")

    # Clean up temp directory if it exists
    if temp_dir.exists():
        logging.info("🧹 Removing existing temp directory")
        shutil.rmtree(temp_dir)

    # Clone repository
    git_clone(repo_url, tag, temp_dir)

    # Change to temp directory and run refactor
    original_dir = Path.cwd()
    try:
        os.chdir(temp_dir)
        logging.info("🔧 Running refactoring...")

        # Adjust config path to be relative to temp dir
        config_path_adjusted = Path("..") / config_path
        run_refactor(config_path_adjusted, dry_run, jobs)

    finally:
        os.chdir(original_dir)

    if dry_run:
        logging.warning("🎬 DRY-RUN: Would replace %s with %s", target_dir, temp_dir)
        return

    # Replace target directory
    logging.info("📦 Replacing %s with synced version", target_dir)
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.move(str(temp_dir), str(target_dir))

    # Cleanup unwanted directories
    for path in [".git", ".github", "pyproject.toml"]:
        full_path = target_dir / path
        if full_path.exists():
            logging.debug("Removing %s", full_path)
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink()

    # Restore specific files from fork
    git_restore_files("**/apps.py")
    git_restore_files("**/__init__.py")

    logging.warning("✅ Sync completed successfully!")


# -- Main ---------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync and refactor the sites-faciles codebase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Sync command
    sync_parser = subparsers.add_parser(
        "sync",
        help="Clone a specific version and apply refactoring",
    )
    sync_parser.add_argument(
        "tag",
        help="Git tag or branch to sync (e.g., v2.1.0)",
    )
    sync_parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("search-and-replace.yml"),
        help="Path to YAML config (default: search-and-replace.yml)",
    )
    sync_parser.add_argument(
        "--repo",
        default="git@github.com:numerique-gouv/sites-faciles.git",
        help="Repository URL to clone from",
    )
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without modifying files",
    )
    sync_parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv)",
    )
    sync_parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=None,
        help="Number of worker threads (default: CPU count)",
    )

    # Refactor command
    refactor_parser = subparsers.add_parser(
        "refactor",
        help="Apply refactoring rules to current directory",
    )
    refactor_parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("search-and-replace.yml"),
        help="Path to YAML config (default: search-and-replace.yml)",
    )
    refactor_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without modifying files",
    )
    refactor_parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv)",
    )
    refactor_parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=None,
        help="Number of worker threads (default: CPU count)",
    )

    args = parser.parse_args()

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        sys.exit(1)

    setup_logger(args.verbose)

    if args.command == "sync":
        run_sync(
            tag=args.tag,
            config_path=args.config,
            dry_run=args.dry_run,
            jobs=args.jobs,
            repo_url=args.repo,
        )
    elif args.command == "refactor":
        run_refactor(
            config_path=args.config,
            dry_run=args.dry_run,
            jobs=args.jobs,
        )


if __name__ == "__main__":
    main()
