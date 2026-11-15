#include <chrono>
#include <string>
#include <sys/mount.h>

#include <android-base/logging.h>
#include <android-base/properties.h>
#include <fs_mgr_dm_linear.h>
#include <libdm/dm.h>

int main() {
    const auto slot = android::base::GetProperty("ro.boot.slot_suffix", "");
    if (slot != "_a" && slot != "_b") {
        LOG(ERROR) << "Invalid boot slot";
        return 1;
    }
    const auto name = "vendor" + slot;
    std::string path;
    auto& dm = android::dm::DeviceMapper::Instance();
    if (!dm.GetDmDevicePathByName(name, &path)) {
        android::fs_mgr::CreateLogicalPartitionParams params;
        params.block_device = "/dev/block/by-name/super";
        params.metadata_slot = slot == "_a" ? 0 : 1;
        params.partition_name = name;
        params.timeout_ms = std::chrono::seconds(10);
        if (!android::fs_mgr::CreateLogicalPartition(params, &path)) {
            LOG(ERROR) << "Cannot map " << name;
            return 1;
        }
    }
    if (mount(path.c_str(), "/mnt/plato_vendor", "erofs", MS_RDONLY, nullptr) != 0 &&
        mount(path.c_str(), "/mnt/plato_vendor", "ext4", MS_RDONLY, "noload") != 0) {
        PLOG(ERROR) << "Cannot mount " << name;
    return 1;
        }
        return 0;
}
