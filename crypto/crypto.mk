PRODUCT_PACKAGES += \
    android.hardware.gatekeeper@1.0-service \
    android.hardware.gatekeeper@1.0-impl
TARGET_RECOVERY_DEVICE_MODULES += \
    android.hardware.gatekeeper@1.0-service \
    android.hardware.gatekeeper@1.0-impl
TW_RECOVERY_ADDITIONAL_RELINK_BINARY_FILES += \
    $(TARGET_OUT_VENDOR_EXECUTABLES)/hw/android.hardware.gatekeeper@1.0-service
TW_RECOVERY_ADDITIONAL_RELINK_LIBRARY_FILES += \
    $(TARGET_OUT_VENDOR_SHARED_LIBRARIES)/hw/android.hardware.gatekeeper@1.0-impl.so
PRODUCT_PROPERTY_OVERRIDES += \
    ro.hardware.gatekeeper=beanpod \
    ro.vendor.mtk_tee_gp_support=1 \
    ro.vendor.mtk_microtrust_tee_support=1

PRODUCT_PACKAGES += xaga_map_vendor
TARGET_RECOVERY_DEVICE_MODULES += xaga_map_vendor
