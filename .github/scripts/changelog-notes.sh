#!/bin/sh
# Print the CHANGELOG.md section for version $1 (without its heading).
# Fails if there is no such section or it is empty.
set -eu
version=${1:?usage: $0 VERSION}
notes=$(awk -v v="$version" '
	/^## \[/ { if (found) exit; if (index($0, "## [" v "]") == 1) { found = 1; next } }
	found && /^\[[^]]+\]: / { exit }
	found { print }
' CHANGELOG.md)
if [ -z "$(printf '%s' "$notes" | tr -d '[:space:]')" ]; then
	echo "No CHANGELOG.md entry for $version" >&2
	exit 1
fi
printf '%s\n' "$notes"
