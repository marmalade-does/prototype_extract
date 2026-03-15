#!/usr/bin/env python3
"""
ptree - tree with function prototypes
"""

import argparse
import sys
import re
import os
from pathlib import Path
from typing import List, Optional

# ANSI color codes
BLUE = "\033[34m"
GREEN = "\033[32m"
CYAN = "\033[36m"
GRAY = "\033[90m"
RESET = "\033[0m"

# Check if output is a terminal
USE_COLOR = sys.stdout.isatty() and os.environ.get("TERM") != "dumb"


def colorize(text: str, color: str) -> str:
    """Apply color to text if terminal supports it."""
    if USE_COLOR:
        return f"{color}{text}{RESET}"
    return text


def extract_prototypes(file_path: Path) -> List[str]:
    """Extract function prototypes from a file."""
    suffix = file_path.suffix.lower()

    if suffix == ".py":
        return extract_python_prototypes(file_path)
    elif suffix in (".c", ".cpp"):
        return extract_c_prototypes(file_path)
    else:
        return []


def extract_python_prototypes(file_path: Path) -> List[str]:
    """Extract Python function signatures."""
    prototypes = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return []

    i = 0
    while i < len(lines):
        line = lines[i]
        # Match function definition
        if re.match(r"^\s*(?:async\s+)?def\s+\w+\s*\(", line):
            # Collect signature across multiple lines
            signature = line.rstrip()
            paren_depth = signature.count("(") - signature.count(")")

            line_count = 1
            while paren_depth > 0 and i + line_count < len(lines) and line_count <= 20:
                next_line = lines[i + line_count].rstrip()
                signature += " " + next_line.strip()
                paren_depth += next_line.count("(") - next_line.count(")")
                line_count += 1

            # Clean up and strip leading whitespace
            signature = signature.strip()
            prototypes.append(signature)
            i += line_count
        else:
            i += 1

    return prototypes


def extract_c_prototypes(file_path: Path) -> List[str]:
    """Extract C/C++ function signatures."""
    prototypes = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return []

    in_multiline_comment = False
    i = 0

    while i < len(lines):
        line = lines[i]
        original_line = line

        # Handle multiline comments
        if "/*" in line:
            in_multiline_comment = True
        if "*/" in line:
            in_multiline_comment = False
            i += 1
            continue

        if in_multiline_comment:
            i += 1
            continue

        # Skip lines starting with preprocessor, comments, or continuation of multiline
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
            i += 1
            continue

        # Try to match function signature start
        if re.search(r"[a-zA-Z_][\w\s\*:~<>]*?\s+[\w:~]+\s*\(", line):
            signature = line.rstrip()
            paren_depth = signature.count("(") - signature.count(")")

            line_count = 1
            while paren_depth > 0 and i + line_count < len(lines) and line_count <= 20:
                next_line = lines[i + line_count].rstrip()
                # Stop if we hit a preprocessor or comment
                if next_line.lstrip().startswith("#") or next_line.lstrip().startswith("//"):
                    break
                signature += " " + next_line.strip()
                paren_depth += next_line.count("(") - next_line.count(")")
                line_count += 1

            # Clean up: strip trailing { or ;
            signature = signature.rstrip()
            signature = re.sub(r"[{;]\s*$", "", signature).strip()

            prototypes.append(signature)
            i += line_count
        else:
            i += 1

    return prototypes


def print_tree(
    path: Path,
    prefix: str = "",
    is_last: bool = True,
    show_prototypes: bool = False,
    max_depth: Optional[int] = None,
    current_depth: int = 0,
):
    """Recursively print directory tree with optional prototypes."""
    # Check if we've reached max depth
    if max_depth is not None and current_depth >= max_depth:
        return

    # Determine connectors
    connector = "└── " if is_last else "├── "
    continuation = "    " if is_last else "│   "

    # Print current entry
    name = colorize(path.name, BLUE) if path.is_dir() else colorize(path.name, CYAN if path.suffix.lower() in (".py", ".c", ".cpp") else RESET)
    print(f"{prefix}{connector}{name}")

    # If it's a directory, recurse
    if path.is_dir():
        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
        except PermissionError:
            print(f"{prefix}{continuation}[permission denied]")
            return

        for i, entry in enumerate(entries):
            is_last_entry = i == len(entries) - 1
            next_prefix = prefix + continuation

            if entry.is_dir():
                # Recurse into directory (only if we haven't reached max depth)
                if max_depth is None or current_depth + 1 < max_depth:
                    print_tree(entry, next_prefix, is_last_entry, show_prototypes, max_depth, current_depth + 1)
                else:
                    # Print directory name but don't recurse
                    dir_connector = "└── " if is_last_entry else "├── "
                    dir_name = colorize(entry.name, BLUE)
                    print(f"{next_prefix}{dir_connector}{dir_name}")
            else:
                # Print file (just the name, not recursing)
                file_connector = "└── " if is_last_entry else "├── "
                is_source = entry.suffix.lower() in (".py", ".c", ".cpp")
                file_name = colorize(entry.name, CYAN if is_source else RESET)
                print(f"{next_prefix}{file_connector}{file_name}")

                # If file has supported extension and --prototypes, show prototypes
                if show_prototypes and is_source:
                    prototypes = extract_prototypes(entry)
                    file_continuation = "    " if is_last_entry else "│   "
                    for proto in prototypes:
                        proto_line = f"{next_prefix}{file_continuation}\t{colorize(proto, GRAY)}"
                        print(proto_line)


def main():
    parser = argparse.ArgumentParser(description="Tree with function prototypes")
    parser.add_argument(
        "path", nargs="?", default=".", help="Path to directory or file"
    )
    parser.add_argument(
        "--prototypes",
        action="store_true",
        help="Show function prototypes for .py, .c, .cpp files",
    )
    parser.add_argument(
        "-L", "--level",
        type=int,
        default=None,
        help="Limit recursion depth to specified level",
    )

    args = parser.parse_args()
    path = Path(args.path)

    # Handle file input
    if path.is_file():
        if args.prototypes:
            # Check if file type is supported
            if path.suffix.lower() not in (".py", ".c", ".cpp"):
                supported = ".py, .c, .cpp"
                print(
                    f"ptree: unsupported file type '{path.suffix}' — supported: {supported}",
                    file=sys.stderr,
                )
                sys.exit(1)
            # Print filename
            print(path.name)
            # Print prototypes indented with tab
            prototypes = extract_prototypes(path)
            for proto in prototypes:
                print(f"\t{proto}")
        else:
            # Just print filename
            print(path.name)
        return

    if not path.exists():
        print(f"ptree: {path}: No such file or directory", file=sys.stderr)
        sys.exit(1)

    # Handle directory input
    print(colorize(f"{path.name}/", BLUE))
    try:
        entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
    except PermissionError:
        print("[permission denied]")
        return

    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        if entry.is_dir():
            print_tree(entry, "", is_last, args.prototypes, args.level, 1)
        else:
            # Handle files at root level
            connector = "└── " if is_last else "├── "
            is_source = entry.suffix.lower() in (".py", ".c", ".cpp")
            file_name = colorize(entry.name, CYAN if is_source else RESET)
            print(f"{connector}{file_name}")

            # If file has supported extension and --prototypes, show prototypes
            if args.prototypes and is_source:
                prototypes = extract_prototypes(entry)
                continuation = "    " if is_last else "│   "
                for proto in prototypes:
                    print(f"{continuation}\t{colorize(proto, GRAY)}")


if __name__ == "__main__":
    main()
