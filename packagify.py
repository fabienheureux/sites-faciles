#!/usr/bin/env python3
import argparse
import logging
import pathlib
import re
import subprocess

import yaml

# Allowed text file extensions
TEXT_EXTENSIONS = {
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


def is_text_file(path: pathlib.Path) -> bool:
    """Check if the file extension suggests it's a text file."""
    return path.suffix in TEXT_EXTENSIONS


def apply_rule(file_path: pathlib.Path, search: str, replace: str, dry_run: bool) -> bool:
    """Apply a regex substitution to a file. Returns True if changed."""
    if not is_text_file(file_path):
        logging.debug(f"Skipping binary file {file_path}")
        return False

    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logging.error(f"❌ Failed to read {file_path}: {e}")
        return False

    new_text, count = re.subn(search, replace, text)
    if count > 0:
        logging.info(f"✏️ {file_path} — {count} replacements")
        if dry_run:
            logging.debug(f"DRY-RUN: would replace '{search}' → '{replace}'")
        else:
            file_path.write_text(new_text, encoding="utf-8")
            logging.debug(f"Updated {file_path}")
        return True
    else:
        logging.debug(f"No matches in {file_path} for '{search}'")
    return False


def setup_logger(verbose: int):
    """Configure logging verbosity."""
    level = logging.WARNING  # default
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        format="%(levelname)-8s %(message)s",
        level=level,
    )


def git_ls_files(pattern: str) -> list[str]:
    """Return tracked files matching a glob pattern."""
    result = subprocess.run(
        ["git", "ls-files", pattern],
        capture_output=True,
        text=True,
    )
    files = result.stdout.splitlines()
    logging.debug(f"Found {len(files)} files for pattern: {pattern}")
    return files


def load_rules(config_file="search-and-replace.yml"):
    logging.info(f"📖 Loading rules from {config_file}")
    with open(config_file) as f:
        return yaml.safe_load(f)


def expand_rules(config: dict) -> list[dict]:
    """Expand {app} placeholders into concrete rules."""
    apps = config.get("apps", [])
    rules = config.get("rules", [])

    expanded = []
    for rule in rules:
        if "{app}" in rule["search"] or "{app}" in rule["replace"]:
            for app in apps:
                expanded.append(
                    {
                        "search": rule["search"].replace("{app}", app),
                        "replace": rule["replace"].replace("{app}", app),
                        "scope": rule["scope"],
                    }
                )
        else:
            expanded.append(rule)

    logging.info(f"🔧 Expanded {len(rules)} rules into {len(expanded)} concrete rules")
    return expanded


def main():
    parser = argparse.ArgumentParser(description="Refactor a codebase with regex rules")
    parser.add_argument(
        "-c",
        "--config",
        default="../search-and-replace.yml",
        help="Path to config file",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show changes without modifying files")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity (-v, -vv for more)",
    )
    args = parser.parse_args()

    setup_logger(args.verbose)

    config = load_rules(args.config)
    scopes = config["scopes"]
    rules = expand_rules(config)

    total_changes = 0
    for rule in rules:
        search = rule["search"]
        replace = rule["replace"]
        scope_name = rule["scope"]

        if scope_name not in scopes:
            logging.warning(f"⚠️ Unknown scope '{scope_name}', skipping rule")
            continue

        file_glob = scopes[scope_name]
        files = git_ls_files(file_glob)

        if not files:
            logging.debug(f"No files for scope '{scope_name}' ({file_glob})")
            continue

        for file in files:
            if apply_rule(pathlib.Path(file), search, replace, args.dry_run):
                total_changes += 1

    logging.warning(f"🎬 Finished {'(dry-run)' if args.dry_run else ''}: {total_changes} file(s) changed")


if __name__ == "__main__":
    main()
