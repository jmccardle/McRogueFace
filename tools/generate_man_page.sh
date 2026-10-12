#!/bin/bash
# Convert markdown docs to man page format

pandoc docs/API_REFERENCE_DYNAMIC.md \
    -s -t man \
    --metadata title="MCRFPY" \
    --metadata section=3 \
    --metadata date="$(date +%Y-%m-%d)" \
    --metadata footer="McRogueFace $("$(dirname "$0")/version.sh")" \
    -o docs/mcrfpy.3

echo "Generated docs/mcrfpy.3"
