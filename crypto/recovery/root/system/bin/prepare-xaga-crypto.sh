#!/system/bin/sh
set -e
[ -d /mnt/xaga_vendor/thh/ta ] || exit 1
mkdir -p /vendor/thh
cp -a /mnt/xaga_vendor/thh/ta /vendor/thh/
[ -s /vendor/thh/ta/08030000000000000000000000000000.ta ] || exit 1
setprop xaga.crypto.ready 1
