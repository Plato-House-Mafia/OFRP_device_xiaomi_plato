#!/system/bin/sh
modules=/lib/modules
if [ ! -r "$modules/modules.load.recovery" ] || [ ! -r "$modules/modules.dep" ]; then
    echo "xaga: ESK recovery module list/dependencies missing" > /dev/kmsg
    exit 1
fi
/system/bin/toolbox modprobe -d "$modules" --all="$modules/modules.load.recovery" || exit 1
setprop twrp.modules.loaded true
