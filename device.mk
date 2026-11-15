# Copyright (C) 2022 The TWRP Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

DEVICE_PATH := device/xiaomi/plato
PRODUCT_SHIPPING_API_LEVEL := 32
PRODUCT_TARGET_VNDK_VERSION := 31

AB_OTA_UPDATER := true
PRODUCT_USE_DYNAMIC_PARTITIONS := true
AB_OTA_PARTITIONS += system system_ext product vendor vendor_dlkm odm odm_dlkm \
    boot vendor_boot vbmeta vbmeta_system vbmeta_vendor dtbo
PRODUCT_PACKAGES += update_engine_sideload update_verifier

PRODUCT_PACKAGES += android.hardware.boot@1.2-mtkimpl.recovery
TARGET_RECOVERY_DEVICE_MODULES += android.hardware.boot@1.2-mtkimpl.recovery
PRODUCT_SOONG_NAMESPACES += $(DEVICE_PATH)

PRODUCT_PACKAGES += toolbox
TARGET_RECOVERY_DEVICE_MODULES += toolbox
TW_RECOVERY_ADDITIONAL_RELINK_BINARY_FILES += $(TARGET_OUT_EXECUTABLES)/toolbox

$(call inherit-product, $(DEVICE_PATH)/crypto/crypto.mk)
