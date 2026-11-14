#include <chrono>
#include <string>

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
    if (dm.GetDmDevicePathByName(name, &path)) {
        return 0;
    }
    android::fs_mgr::CreateLogicalPartitionParams params;
    params.block_device = "/dev/block/by-name/super";
    params.metadata_slot = slot == "_a" ? 0 : 1;
    params.partition_name = name;
    params.timeout_ms = std::chrono::seconds(10);
    if (!android::fs_mgr::CreateLogicalPartition(params, &path)) {
        LOG(ERROR) << "Cannot map " << name;
        return 1;
    }
    return 0;
}
