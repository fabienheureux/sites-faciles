#!/usr/bin/env python3
"""
refactor.py
A safer, more maintainable find-and-replace tool for git-tracked text files.

Features:
 - YAML config with named scopes and app templating
 - per-rule path_glob override (git ls-files pattern)
 - literal vs regex replacements
 - configurable text extensions
 - logging levels (-v / -vv)
 - --dry-run mode
"""

import argparse
import logging
import pathlib
import re
import subprocess
import sys

import yaml

# -- Helpers ------------------------------------------------------------------


def setup_logger(verbose: int):
    """Configure logging verbosity."""
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        format="%(levelname)-8s %(message)s",
        level=level,
    )


def git_ls_files(pattern: str) -> list:
    """
    Return tracked files matching a git pathspec (pattern).
    If pattern is empty, return all tracked files.
    """
    cmd = ["git", "ls-files", pattern] if pattern else ["git", "ls-files"]
    logging.debug("Running: %s", " ".join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception as exc:
        logging.error("git ls-files failed: %s", exc)
        return []
    files = [s for s in result.stdout.splitlines() if s]
    logging.debug("git ls-files returned %d files for pattern '%s'", len(files), pattern)
    return files


def load_config(path: str = "search-and-replace.yml") -> dict:
    logging.info("📖 Loading rules from %s", path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except FileNotFoundError:
        logging.error("Config file not found: %s", path)
        sys.exit(2)
    except Exception as exc:
        logging.error("Failed to parse config: %s", exc)
        sys.exit(2)


def expand_rules(config: dict) -> list:
    """Expand {app} placeholders into concrete rules and validate minimal schema."""
    apps = config.get("apps", [])
    raw_rules = config.get("rules", []) or []

    expanded = []
    for rule in raw_rules:
        # ensure required keys
        search = rule.get("search")
        replace = rule.get("replace")
        if search is None or replace is None:
            logging.warning("Skipping invalid rule (missing search or replace): %s", rule)
            continue

        # if {app} present and apps provided, expand
        if "{app}" in (search + replace) and apps:
            for app in apps:
                r = dict(rule)  # shallow copy
                r["search"] = search.replace("{app}", app)
                r["replace"] = replace.replace("{app}", app)
                expanded.append(r)
        else:
            expanded.append(rule)

    logging.info("🔧 Expanded %d rules into %d concrete rules", len(raw_rules), len(expanded))
    return expanded


# -- File / Replacement logic -----------------------------------------------


def is_text_file(path: pathlib.Path, text_exts: set) -> bool:
    """Rudimentary check: treat file as text if suffix is in text_exts."""
    return path.suffix in text_exts


def apply_rule_to_file(path: pathlib.Path, rule: dict, dry_run: bool) -> bool:
    """Apply a single rule to a single file. Returns True if file changed (or would change in dry-run)."""
    search = rule["search"]
    replace = rule["replace"]
    literal = bool(rule.get("literal", False))

    # read file
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        logging.error("❌ Failed to read %s: %s", path, exc)
        return False

    if literal:
        count = text.count(search)
        if count <= 0:
            logging.debug("No literal matches for '%s' in %s", search, path)
            return False
        new_text = text.replace(search, replace)
    else:
        # treat 'search' as a regex pattern
        try:
            new_text, count = re.subn(search, replace, text)
        except re.error as exc:
            logging.error("Invalid regex pattern '%s' in rule: %s", search, exc)
            return False

        if count <= 0:
            logging.debug("No regex matches for /%s/ in %s", search, path)
            return False

    # Report and write (or dry-run)
    logging.info("✏️ %s — %d replacement(s) for rule '%s' → '%s'", path, count, search, replace)
    if dry_run:
        logging.debug("DRY-RUN: not writing changes to %s", path)
    else:
        try:
            path.write_text(new_text, encoding="utf-8")
            logging.debug("Wrote updated file %s", path)
        except Exception as exc:
            logging.error("Failed to write %s: %s", path, exc)
            return False

    return True


# -- Main -------------------------------------------------------------------


def main():
    p = argparse.ArgumentParser(description="Refactor a codebase with YAML rules")
    p.add_argument(
        "-c",
        "--config",
        default="../search-and-replace.yml",
        help="Path to YAML config",
    )
    p.add_argument("--dry-run", action="store_true", help="Show changes without modifying files")
    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv)",
    )
    args = p.parse_args()

    setup_logger(args.verbose)

    config = load_config(args.config)
    scopes = config.get("scopes", {})
    text_extensions_from_cfg = config.get("text_extensions", [])
    DEFAULT_TEXT_EXTENSIONS = {
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
    text_exts = set(text_extensions_from_cfg) if text_extensions_from_cfg else DEFAULT_TEXT_EXTENSIONS
    logging.debug("Text extensions: %s", sorted(text_exts))

    expanded_rules = expand_rules(config)

    total_files_changed = 0
    scanned_files = 0

    for rule in expanded_rules:
        # Choose list of files: path_glob (rule-specific) > scope > skip rule
        path_glob = rule.get("path_glob")
        if path_glob:
            files = git_ls_files(path_glob)
            logging.debug("Rule has path_glob '%s' → %d files", path_glob, len(files))
        else:
            scope_name = rule.get("scope")
            if not scope_name:
                logging.warning("Rule missing both 'path_glob' and 'scope'; skipping: %s", rule)
                continue
            file_glob = scopes.get(scope_name)
            if not file_glob:
                logging.warning("Unknown scope '%s' in rule; skipping: %s", scope_name, rule)
                continue
            files = git_ls_files(file_glob)
            logging.debug(
                "Using scope '%s' (glob '%s') → %d files",
                scope_name,
                file_glob,
                len(files),
            )

        if not files:
            logging.debug("No files found for rule: %s", rule)
            continue

        for f in files:
            scanned_files += 1
            path = pathlib.Path(f)
            if not is_text_file(path, text_exts):
                logging.debug("Skipping non-text file: %s", path)
                continue
            changed = apply_rule_to_file(path, rule, args.dry_run)
            if changed:
                total_files_changed += 1

    logging.warning(
        "🎬 Finished %s: scanned %d files, %d file(s) changed",
        "(dry-run)" if args.dry_run else "",
        scanned_files,
        total_files_changed,
    )


if __name__ == "__main__":
    main()
