#
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

$(call inherit-product, $(SRC_TARGET_DIR)/product/base.mk)

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)

$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota/launch_with_vendor_ramdisk.mk)

$(call inherit-product, $(SRC_TARGET_DIR)/product/emulated_storage.mk)

$(call inherit-product, vendor/twrp/config/common.mk)

$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota/compression.mk)

$(call inherit-product, device/xiaomi/xaga/device.mk)

$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota.mk)

PRODUCT_DEVICE := xaga
PRODUCT_NAME := twrp_xaga
PRODUCT_BRAND := Xiaomi
PRODUCT_MODEL := POCO X4 GT
PRODUCT_MANUFACTURER := Xiaomi
PRODUCT_RELEASE_NAME := POCO X4 GT / Redmi Note 11T Pro

PRODUCT_PROPERTY_OVERRIDES += ro.twrp.vendor_boot=true
