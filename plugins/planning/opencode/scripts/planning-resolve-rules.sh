#!/usr/bin/env bash

set -euo pipefail

filename="${1:-}"
if [[ -z "$filename" ]]; then
    exit 0
fi

if [[ -n "${2:-}" ]]; then
    data_dir="$2"
else
    data_dir="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
fi

project_file=".opencode/${filename}"
user_file="${data_dir%/}/${filename}"

if [[ -f "$project_file" && -s "$project_file" ]]; then
    cat "$project_file"
elif [[ -f "$user_file" && -s "$user_file" ]]; then
    cat "$user_file"
fi

exit 0
