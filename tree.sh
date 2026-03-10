#!/usr/bin/env bash
SCRIPT_DIR="$(dirname "$(realpath "$0")")"

for arg in "$@"; do
    if [[ "$arg" == "--prototypes" ]]; then
        exec python3 "$SCRIPT_DIR/ptree.py" "$@"
    fi
done

exec tree "$@"
