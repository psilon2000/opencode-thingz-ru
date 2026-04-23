#!/usr/bin/env bash

set -euo pipefail

platform="${1:-}"

if [[ -z "$platform" ]]; then
    echo "error: platform required (github, gitlab, gitea)" >&2
    exit 1
fi

git fetch origin --tags >/dev/null 2>&1 || true

last_tag="$(git describe --tags --abbrev=0 --match 'v*' 2>/dev/null || true)"
tag_date=""
if [[ -n "$last_tag" ]]; then
    tag_date="$(git log -1 --format=%aI "$last_tag" 2>/dev/null || true)"
fi

features="$(mktemp)"
improvements="$(mktemp)"
fixes="$(mktemp)"
other="$(mktemp)"
trap 'rm -f "$features" "$improvements" "$fixes" "$other"' EXIT

categorize() {
    local desc="$1"
    local suffix="$2"
    local lower_desc clean_desc entry

    lower_desc="$(printf '%s' "$desc" | tr '[:upper:]' '[:lower:]')"
    clean_desc="$(printf '%s' "$desc" | sed -E 's/^(feat|fix|refactor|perf|chore|docs|style|build|ci|test)(\([^)]*\))?[[:space:]]*:[[:space:]]*//')"
    entry="- ${clean_desc} ${suffix}"

    if [[ "$lower_desc" =~ ^feat ]]; then
        printf '%s\n' "$entry" >> "$features"
    elif [[ "$lower_desc" =~ ^fix ]]; then
        printf '%s\n' "$entry" >> "$fixes"
    elif [[ "$lower_desc" =~ ^(refactor|perf|chore|docs|style|build|ci|test) ]]; then
        printf '%s\n' "$entry" >> "$improvements"
    else
        printf '%s\n' "$entry" >> "$other"
    fi
}

if [[ "$platform" == "github" ]] && command -v gh >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
    if [[ -n "$tag_date" ]]; then
        gh pr list --state merged --limit 50 --json number,title,mergedAt,author 2>/dev/null | \
            jq -r --arg date "$tag_date" '.[] | select(.mergedAt > $date) | "\(.title)\t#\(.number) @\(.author.login)"' | \
            while IFS=$'\t' read -r title suffix; do categorize "$title" "$suffix"; done
    else
        gh pr list --state merged --limit 20 --json number,title,author 2>/dev/null | \
            jq -r '.[] | "\(.title)\t#\(.number) @\(.author.login)"' | \
            while IFS=$'\t' read -r title suffix; do categorize "$title" "$suffix"; done
    fi
elif [[ "$platform" == "gitlab" ]] && command -v glab >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
    if [[ -n "$tag_date" ]]; then
        glab mr list --merged -F json 2>/dev/null | \
            jq -r --arg date "$tag_date" '.[] | select(.merged_at > $date) | "\(.title)\t!\(.iid) @\(.author.username)"' | \
            while IFS=$'\t' read -r title suffix; do categorize "$title" "$suffix"; done
    else
        glab mr list --merged -F json 2>/dev/null | \
            jq -r '.[] | "\(.title)\t!\(.iid) @\(.author.username)"' | \
            while IFS=$'\t' read -r title suffix; do categorize "$title" "$suffix"; done
    fi
elif [[ "$platform" == "gitea" ]] && command -v tea >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
    if [[ -n "$tag_date" ]]; then
        tea pr list --state merged --output json 2>/dev/null | \
            jq -r --arg date "$tag_date" '.[] | select(.merged > $date) | "\(.title)\t#\(.index) @\(.user.login)"' | \
            while IFS=$'\t' read -r title suffix; do categorize "$title" "$suffix"; done
    else
        tea pr list --state merged --output json 2>/dev/null | \
            jq -r '.[] | "\(.title)\t#\(.index) @\(.user.login)"' | \
            while IFS=$'\t' read -r title suffix; do categorize "$title" "$suffix"; done
    fi
fi

if [[ -n "$last_tag" ]]; then
    git log "${last_tag}..HEAD" --oneline --no-merges --pretty='%h%x09%s' | \
        while IFS=$'\t' read -r hash msg; do categorize "$msg" "$hash"; done
else
    git log --oneline --no-merges --pretty='%h%x09%s' -20 | \
        while IFS=$'\t' read -r hash msg; do categorize "$msg" "$hash"; done
fi

output=""
if [[ -s "$features" ]]; then
    output="**New Features**
$(cat "$features")"
fi
if [[ -s "$improvements" ]]; then
    [[ -n "$output" ]] && output="$output

"
    output="${output}**Improvements**
$(cat "$improvements")"
fi
if [[ -s "$fixes" ]]; then
    [[ -n "$output" ]] && output="$output

"
    output="${output}**Bug Fixes**
$(cat "$fixes")"
fi
if [[ -s "$other" ]]; then
    [[ -n "$output" ]] && output="$output

"
    output="${output}**Other**
$(cat "$other")"
fi

printf '%s\n' "$output"
