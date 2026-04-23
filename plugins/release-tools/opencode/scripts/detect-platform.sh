#!/usr/bin/env bash

set -euo pipefail

remote_url="$(git remote get-url origin 2>/dev/null || true)"

if [[ -z "$remote_url" ]]; then
    echo "error: no origin remote configured" >&2
    exit 1
fi

if [[ "$remote_url" =~ github\.com ]]; then
    echo "github"
elif [[ "$remote_url" =~ gitlab\. ]]; then
    echo "gitlab"
elif [[ "$remote_url" =~ gitea\. ]]; then
    echo "gitea"
elif command -v glab >/dev/null 2>&1 && glab repo view >/dev/null 2>&1; then
    echo "gitlab"
else
    echo "error: unknown platform for $remote_url" >&2
    exit 1
fi
