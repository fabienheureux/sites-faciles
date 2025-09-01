#!/usr/bin/env python3
"""
refactor.py
A safer, more maintainable find-and-replace tool for git-tracked text files.
Supports multithreaded file processing for better performance.
Renames template directories after replacements.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

# -- Helpers ------------------------------------------------------------------


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


def git_ls_files(pattern: str | None = None) -> list[str]:
    """Return tracked files matching a git pathspec (pattern)."""
    cmd = ["git", "ls-files"] + ([pattern] if pattern else [])
    logging.debug("Running: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except Exception as exc:
        logging.error("git ls-files failed: %s", exc)
        return []

    return [s for s in result.stdout.splitlines() if s]


def load_config(path: Path = Path("search-and-replace.yml")) -> dict[str, Any]:
    logging.info("📖 Loading rules from %s", path)
    try:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except FileNotFoundError:
        logging.error("Config file not found: %s", path)
        sys.exit(2)
    except Exception as exc:
        logging.error("Failed to parse config: %s", exc)
        sys.exit(2)


def expand_rules(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand {app} placeholders into concrete rules and validate minimal schema."""
    apps: list[str] = config.get("apps", [])
    raw_rules: list[dict[str, Any]] = config.get("rules", []) or []

    expanded: list[dict[str, Any]] = []
    for rule in raw_rules:
        search: str | None = rule.get("search")
        replace: str | None = rule.get("replace")
        if not search or not replace:
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


# -- File / Replacement logic -----------------------------------------------


def is_text_file(path: Path, text_exts: set[str]) -> bool:
    """Check if file should be treated as text based on file extension."""
    return path.suffix in text_exts


def apply_rule_to_file(path: Path, rule: dict[str, Any], dry_run: bool) -> bool:
    """Apply a single rule to a single file. Returns True if file changed."""
    search: str = rule["search"]
    replace: str = rule["replace"]
    literal: bool = bool(rule.get("literal", False))

    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        logging.error("❌ Failed to read %s: %s", path, exc)
        return False

    if literal:
        count = text.count(search)
        if count <= 0:
            logging.debug("No literal matches for %r in %s", search, path)
            return False
        new_text = text.replace(search, replace)
    else:
        try:
            new_text, count = re.subn(search, replace, text)
        except re.error as exc:
            logging.error("Invalid regex pattern %r in rule: %s", search, exc)
            return False
        if count <= 0:
            logging.debug("No regex matches for /%s/ in %s", search, path)
            return False

    logging.info("✏️ %s — %d replacement(s) for %r → %r", path, count, search, replace)

    if dry_run:
        logging.debug("DRY-RUN: not writing changes to %s", path)
    else:
        try:
            path.write_text(new_text, encoding="utf-8")
        except Exception as exc:
            logging.error("Failed to write %s: %s", path, exc)
            return False

    return True


# -- Rename -------------------------------------------------------------------


def rename_template_dirs(apps: list[str], dry_run: bool = False) -> None:
    """Move {app}/templates/{app} → {app}/templates/sites_faciles_{app}."""
    for app in apps:
        src = Path(app) / "templates" / app
        dst = Path(app) / "templates" / f"sites_faciles_{app}"

        if not src.exists():
            logging.debug("⏭️ No template dir to move for app %r: %s", app, src)
            continue

        if dst.exists():
            logging.warning("⚠️ Destination already exists, skipping: %s", dst)
            continue

        if dry_run:
            logging.info("[DRY-RUN] Would move: %s → %s", src, dst)
        else:
            logging.info("📂 Moving: %s → %s", src, dst)
            shutil.move(str(src), str(dst))


# -- Main -------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Refactor a codebase with YAML rules")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("../search-and-replace.yml"),
        help="Path to YAML config",
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
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

    config = load_config(args.config)
    scopes: dict[str, str] = config.get("scopes", {})
    text_extensions_from_cfg: list[str] = config.get("text_extensions", [])

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

    expanded_rules = expand_rules(config)

    # -- Process files with multithreading --
    total_files_changed = 0
    scanned_files = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures: list[concurrent.futures.Future[bool]] = []

        for rule in expanded_rules:
            path_glob: str | None = rule.get("path_glob")
            if path_glob:
                files = git_ls_files(path_glob)
            else:
                scope_name: str | None = rule.get("scope")
                if not scope_name:
                    logging.warning("Rule missing both 'path_glob' and 'scope'; skipping: %s", rule)
                    continue
                file_glob = scopes.get(scope_name)
                if not file_glob:
                    logging.warning("Unknown scope %r in rule; skipping: %s", scope_name, rule)
                    continue
                files = git_ls_files(file_glob)

            for f in files:
                path = Path(f)
                if not is_text_file(path, text_exts):
                    continue
                scanned_files += 1
                futures.append(executor.submit(apply_rule_to_file, path, rule, args.dry_run or False))

        for future in concurrent.futures.as_completed(futures):
            try:
                if future.result():
                    total_files_changed += 1
            except Exception as exc:
                logging.error("Worker failed: %s", exc)

    logging.warning(
        "🎬 Finished replacements %s: scanned %d files, %d file(s) changed",
        "(dry-run)" if args.dry_run else "",
        scanned_files,
        total_files_changed,
    )

    # Always run rename step after replacements
    apps: list[str] = config.get("apps", [])
    if apps:
        rename_template_dirs(apps, args.dry_run or False)


if __name__ == "__main__":
    main()
