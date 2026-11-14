#!/bin/bash
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
[[ ${2:-} == --last-call ]] || exit 0
installer="$1/META-INF/com/google/android/update-binary"
patch --batch --forward --reject-file=- --no-backup-if-mismatch \
    "$installer" "$script_dir/vendor-boot.patch" || {
    rm -f "$installer"
    exit 1
}
