#!/system/bin/sh
set -e
[ -d /mnt/plato_vendor/thh/ta ] || exit 1
mkdir -p /vendor/thh
cp -a /mnt/plato_vendor/thh/ta /vendor/thh/
[ -s /vendor/thh/ta/08030000000000000000000000000000.ta ] || exit 1
setprop plato.crypto.ready 1
