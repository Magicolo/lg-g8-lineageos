# Compatibility, firmware and recovery reference

This reference records the device and platform details needed to resume the Canadian G8 port. Use the [build guide](BUILD.md) to sync the source and the [validation matrix](VALIDATION.md) to check behavior on actual hardware.

## Identify the hardware and firmware

| Item | Working development baseline |
| --- | --- |
| Phone | Canadian LG G8 ThinQ LM-G820UM2, Snapdragon 855 / SM8150. Product target `alphaplus`, OTA assertion `alphaplus_lao_com`. |
| Firmware | Canadian LG Android 12 G820UM40b. The audited local KDZ was `G820UM40b_00_OPEN_CA_OP_1129.kdz`, 4,830,976,937 bytes, SHA-256 `73a4cce272d409b2b80822d849d38d670b397fca86320f0426bd672d0d682efb`. This is a hash of the inspected copy. Vendor authenticity is a separate check. |
| Android / kernel | LineageOS 24.0, Android 17 SDK 37, 4.14.357 OpenELA-based LG kernel and Clang `r596125`. The observed Android framework SPL was 2026-11-01 and vendor SPL 2022-12-01. |
| Vendor compatibility | Device manifest framework compatibility matrix level 7. Retain the working level and HAL instances until an exact vendor compatibility change requires otherwise. |
| Radio | The common product uses LG radio HIDL 1.4. Other LG source trees contain different AIDL wrappers and shared slot declarations. Check the installed service and the actual SIM slot before choosing an adapter. |
| Blob provenance | The public G8 extraction list names Korean G820NO40c as the default input for unpinned blobs. The shared SM8150 list names G8X G850UM40c. The private IMS adaptation references the Canadian 40b stack. This makes the userspace a mixed set even when the handset itself has Canadian firmware. |

The G8 wiki lists multiple variants under `alphaplus`. The build and radio findings here cover the Canadian model and the tested carrier profile. Do not substitute Qualcomm firehose programmers, regional bootloaders, boot images or calibration partitions based on the family or CPU name. Match the actual partition, revision and expected image hash. Returning to stock through LG Download Mode and handling a Qualcomm emergency port are separate operations. [LG Canada device specification](https://www.lg.com/ca_en/cell-phones/lmg820um2/) · [LineageOS device variant](https://lineageos.github.io/lineage_wiki/devices/alphaplus/variant1/) · [G8 blob list](https://github.com/lge-qcom-dev/android_device_lge_alphaplus/blob/69f8c9488b113be8a7ad3855109bf59dc51a6890/proprietary-files.txt) · [Common blob list](https://github.com/lge-qcom-dev/android_device_lge_sm8150-common/blob/eef771f98ec2fdaeb874fefd0a0459959b312dc8/proprietary-files.txt)

## Legacy kernel and modern Android boundaries

- **BPF and networking.** The inherited common product sets `ro.bpf.kver_override=5.10.239` for Android's BPF loader. The actual kernel is still 4.14.357 with downstream backports. Keep the property and the corresponding kernel capabilities paired. On a rebase, check `bpf.progs_loaded`, the loader and netd, pinned maps, relevant verifier errors and SELinux before investigating DHCP, UID traffic accounting, IPv6/464XLAT or tethering. A matching displayed kernel version cannot prove the required helpers and attach types. [LG common BPF selection](https://github.com/lge-qcom-dev/android_device_lge_sm8150-common/commit/bf6d84506c)
- **Vendor interface.** Use VINTF on the actual signed target-files. Check HAL service version, instance, location and library namespace. Keep policy enforcing. Resolve one symbol, declaration or denial at a time. Existing camera, XML and Widevine extraction fixups have specific library contracts. A successful compile does not prove all proprietary libraries' runtime paths.
- **Page size and architecture.** This kernel and the vendor stack use 4 KiB pages. The product retains the Android compatibility ABI required by this device. Converting the G8 to 16 KiB pages or a generic newer kernel is a separate hardware and ABI qualification effort. [Android page-size guidance](https://developer.android.com/guide/practices/page-sizes)
- **Features and trust.** Test ToF and secondary camera routes, Quad DAC, USB-C display, FM, proximity, NFC transactions, fingerprint and portable media independently of service enumeration. Stock LG Hand ID, depth face unlock, Air Motion and OEM effects have no confirmed Lineage equivalent. Android APIs do not supply hardware such as satellite, 5G or UWB. Play Integrity, Wallet and DRM playback depend on device and service trust even when Play Store, Google sign-in and NFC are working. [Play Integrity verdicts](https://developer.android.com/google/play/integrity/verdicts)

## A/B layout to verify before installing

Use the matching images from the same build. The measured target limits were:

| Partition | Bytes |
| --- | ---: |
| `boot` | 100,663,296 |
| `dtbo` | 25,165,824 |
| `product` | 2,147,483,648 |
| `system` | 4,022,337,536 |
| `vendor` | 1,782,579,200 |

The reference uses boot header version 2 and recovery-in-boot. The OTA writes `boot`, `dtbo`, `product`, `system`, `vbmeta` and `vendor`. The entire original LG firmware and its calibration partitions are outside the OTA. Verify the effective input size, target slot, boot image, AVB metadata and signed OTA target as a set. Changing a build variable cannot enlarge a physical partition. Slot fallback also cannot restore incompatible or erased userdata. [Android A/B update flow](https://source.android.com/docs/core/ota/ab/ab_implement)

## Google Apps and data migration

- The tested publisher package for the clean development migration was Android 17 ARM64 MindTheGapps `17.0.0-arm64-20261022_132445`, SHA-256 `a6844eeb2613541558237e467b20feb01f8b45b2ebab0109834140ea59b6ca4d`. Download the package from its publisher and verify it separately. It is an optional add-on. [Publisher release](https://github.com/MindTheGapps/17.0.0-arm64/releases/tag/MindTheGapps-17.0.0-arm64-20261022_132445)
- Its Google Play Services APEX contains an EROFS payload. Keep the matching EROFS, LZ4, loop and dm-verity support. Measure ext4 free blocks and inodes in both product and system before installing. Verify activation via `adb shell dumpsys apexservice`. A launcher icon alone does not establish that the APEX initialized.
- The tested clean migration formatted data and installed the add-on from the new slot's recovery before first Android boot. Later same-key local OTAs preserved the add-on in the tested development signing family. Separately validate account sync, permission prompts and certified services. Before restoring private app data, test incoming and outgoing calls, echo, SMS/MMS, Wi-Fi and mobile data. The [install guide](INSTALL.md) describes the general backup prerequisites.

[Change details](CHANGES.md) · [Failed paths and evidence](ATTEMPTS.md) · [Distribution audit](RELEASE-AUDIT.md)
