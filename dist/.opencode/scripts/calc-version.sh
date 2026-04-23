#!/usr/bin/env bash

set -euo pipefail

release_type="${1:-}"

if [[ -z "$release_type" ]]; then
    echo "error: release type required (major, minor, hotfix)" >&2
    exit 1
fi

git fetch origin --tags >/dev/null 2>&1 || true

last_tag="$(git describe --tags --abbrev=0 --match 'v*' 2>/dev/null || true)"

if [[ -z "$last_tag" ]]; then
    case "$release_type" in
        major) echo "v1.0.0" ;;
        minor) echo "v0.1.0" ;;
        hotfix) echo "v0.0.1" ;;
        *)
            echo "error: invalid type: $release_type" >&2
            exit 1
            ;;
    esac
    exit 0
fi

version="${last_tag#v}"
base_version="${version%%-*}"
IFS='.' read -r major minor patch <<< "$base_version"

if ! [[ "$major" =~ ^[0-9]+$ && "$minor" =~ ^[0-9]+$ && "$patch" =~ ^[0-9]+$ ]]; then
    echo "error: cannot parse version from $last_tag" >&2
    exit 1
fi

case "$release_type" in
    major) echo "v$((major + 1)).0.0" ;;
    minor) echo "v${major}.$((minor + 1)).0" ;;
    hotfix) echo "v${major}.${minor}.$((patch + 1))" ;;
    *)
        echo "error: invalid type: $release_type" >&2
        exit 1
        ;;
esac
