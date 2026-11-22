# Change map and engineering rationale

All changes below are on the four public `g8-lineage-24.0-source-preview` branches. Each repository preserves its upstream history. The listed scope reflects the code selection and the hardware tested.

| Component | Pinned public tip | Scope |
| --- | --- | --- |
| [G8 device tree](https://github.com/Magicolo/android_device_lge_alphaplus/commit/af01108dcd97dd9a8f47284ff27a14200fcf4f6e) | `af01108dcd97` | 64-bit Gralloc1, kernel fragment selection and G8 call microphone property |
| [Shared SM8150 tree](https://github.com/Magicolo/android_device_lge_sm8150-common/commit/7c9c90a044cfc879ff37dc2d28684e1fb17990d3) | `7c9c90a044cf` | Shared audio default becomes overridable |
| [LG SM8150 kernel](https://github.com/Magicolo/android_kernel_lge_sm8150/commit/8817f5e6c9372e59e0c10a8dbe96517f64e927a8) | `8817f5e6c937` | ARM64 page-table isolation and LG PN553 |
| [Camera framework](https://github.com/Magicolo/android_frameworks_av/commit/d87bc7d158853a78da22047dd2648559a1d99f1b) | `d87bc7d15885` | HIDL transport-error handling for the torch API |

## 1. Flashlight package selection

The Qualcomm CamX/CHI code used by LG opens a legacy Gralloc1 hardware module while preparing torch buffers. On the tested G8, `ro.hardware=qcom` and there was no overriding Gralloc property. The 64-bit vendor process fell through to the software default module when the Qualcomm module was absent. Its buffer initialization failed and the camera provider died in cleanup.

The G8 product now requests `gralloc.qcom:64` in `device/lge/alphaplus/device.mk`. This reuses a source-built SM8150 module discovered through normal libhardware lookup. The Mapper 4 service and 32-bit package selection stay on the upstream paths. To port this change, first establish the legacy module lookup, ABI, architecture and vendor import requirements on the other device. Test torch transitions, capture and video after adding it. [Related SM8150 product](https://github.com/LineageOS/android_device_oneplus_sm8150-common/blob/lineage-24.0/common.mk)

## 2. Camera framework transport guard

On the same failure, the framework read a failed HIDL return as a successful HAL status and cameraserver aborted. `HidlProviderInfo.cpp` now checks for a null camera interface and checks the HIDL return's transport status before unwrapping it. A missing or dead interface returns `DEAD_OBJECT`. Another transport error returns `UNKNOWN_ERROR`. A successful transaction still maps the HAL status with the existing method.

This applies to any HIDL camera device on that torch path. Keep it independent from the hardware package change. Validate both the successful path and provider loss when submitting it upstream. AIDL providers use a different transport path.

## 3. Select the working kernel fragment stack

The alpha device previously selected a defconfig absent from the pinned kernel tree. The G8 `BoardConfig.mk` now appends `vendor/lge/lge-alpha.config` after the shared SM8150 performance defconfig and LG common fragment. The order lets the device retain shared build settings while enabling G8-specific hardware. Inspect the merged `.config` after any rebase, especially NFC, encryption filesystems, and security options.

The same device commit filters the inherited `kpti=off` argument. Its paired kernel commit enables `CONFIG_UNMAP_KERNEL_AT_EL0=y` in the alpha fragment. The driver and ARM64 CPU logic decide the runtime mitigation. The test handset reported `Vulnerable` before the change and `Mitigation: PTI` afterward. This is a mitigation-status result. It does not quantify exploitability or the performance and battery cost.

## 4. Select the LG PN553 NFC driver

Another alpha fragment commit enables `CONFIG_NFC`, `CONFIG_LGE_NFC`, `CONFIG_LGE_NFC_PN553` and `CONFIG_LGE_NFC_SET_IRQ_WAKEUP`. It deselects `CONFIG_NFC_NQ`. The matching G8 NXP HAL and device policy expect the LG driver's `/dev/pn547` device node even though the controller is PN553. Before carrying this patch to another variant, match the controller, DT wiring, IRQ and wake behavior, device node, and HAL/SELinux configuration. NFC state ON proves initialization. Tag reads and card emulation need separate tests.

## 5. Restore the calibrated call microphone route

The shared SM8150 tree now specifies `ro.vendor.audio.sdk.fluencetype?=nxp`. Android's optional property assignment preserves the existing NXP default for products that supply no override. The G8 tree explicitly selects `ro.vendor.audio.sdk.fluencetype=fluence` to activate its calibrated Qualcomm dual-microphone call path. This is a two-repository change. Keep both sides aligned so the G8 can override the property while sibling devices keep their default.

Far-end callers heard echo with the handset and the problem disappeared on a headset. A real call after the change passed the far-end check on the tested configuration. A generic audio recording does not cover the telephony DSP path. Test earpiece, loudspeaker, wired headset and Bluetooth HFP on a real two-way call before generalizing calibration or gain changes.

## Experiments reviewed and left out of the baseline

The inherited `lpm_levels.sleep_disabled=1` argument was removed in one G8 test build. The shared Qualcomm post-boot script already attempts to clear the parameter on msmnile. The plugged-in snapshots showed no improvement in deeper idle counts on the little cores. The final baseline restored the inherited behavior. Follow [the power test procedure](VALIDATION.md#power-and-wake) before changing it again.

The complete development ROM also carried a device-specific LG IMS package setup, carrier profile, restricted IPsec policy and an upgrade-only CarrierConfig version bump. [The IMS guide](IMS.md) records their purpose, scope and evidence.
