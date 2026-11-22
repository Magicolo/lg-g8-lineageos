# Recovery and install troubleshooting

Work through one symptom at a time. Keep the working stock or LineageOS rollback files available. The G8 is a physical A/B device. The slot you boot from and the slot being written have different roles. A data format is destructive and a slot fallback cannot recover the old data. [Android A/B update model](https://source.android.com/docs/core/ota/ab/ab_implement)

| What you see | What it means and what to check |
| --- | --- |
| `adb devices` is empty | Check the cable, direct USB port, current mode and Windows device driver. Android ADB, recovery sideload, LG Download Mode and Qualcomm 9008 are different USB modes. Platform-Tools cannot use a Qualcomm 9008 port as ADB. |
| ADB says `unauthorized` | Unlock Android and approve the host on the handset. A data wipe clears previously authorized USB keys. |
| Recovery is open but ADB won't sideload | Choose **Apply update → Apply from ADB**. Confirm the device's state changes to `sideload`. Use the intended single device. |
| Host transfer stops near 47% | Read the phone's recovery status. Wait while the package is still installing. Resume only after it reports success or displays the next expected menu. |
| ROM signature verification fails | Check the file hash, exact ROM, recovery version and the signing family. Recover with a verified matching recovery and OTA. A separately signed, verified optional add-on can have a different expected trust prompt. |
| Package names another device | Stop. The tested Canadian package asserts `alphaplus_lao_com`. Verify board identity, package build and recovery. The early generic override build was rejected because the asserted identity did not match. Forcing device checks can write incompatible images. |
| Recovery has **Factory reset** but no **Format data** on the main page | Select **Factory reset** to open its submenu. **Format data/factory reset** is inside that submenu. Confirm the backup before choosing it. |
| ROM success and a prompt to install additional packages | If adding a verified Android 17 ARM64 package, reboot to the new slot's recovery first and sideload there. If skipping add-ons, proceed to reboot system. |
| The phone repeatedly returns to the LG logo | Stop the cycle if you can return to the known-working recovery. Review boot, DTBO, vbmeta, slot, firmware and selected recovery as a matched set. An older slot might still boot, but user data and firmware can prevent fallback. Preserve readable backups before touching either slot. |
| Android shows the Lineage animation for several minutes | First boot can take time. A repeated return to the LG logo, consistently absent boot progress or a recovery error calls for diagnosis. Avoid reflashing multiple packages at once. |
| Android boots but VoLTE fails | Check the exact model and 40b firmware, then IMS service binding, bearer, registration and voice capability. A visible toggle, LTE indicator, or early-media test alone cannot confirm ordinary calls. Use the [IMS diagnosis guide](IMS.md). |
| Phone only enumerates as Qualcomm 9008 | Treat it as emergency service mode. Protect backups and follow a verified “return to stock” procedure specific to that unit. A failed read or missing GPT leaves write safety unproven. |

## Record the failure before recovery

Record the model, firmware, last working build and slot, exact filenames and hashes, recovery message and last successful step. If Android is available, read `ro.boot.slot_suffix` and `ro.build.version.incremental` through ADB. Logs from an encrypted profile can be limited before the first unlock. Share only the relevant redacted lines.

If restoring stock or an earlier major Android version, use the manufacturer images specific to the exact hardware and a complete rollback procedure. The first project restore used the matching Canadian stock firmware. A successful USB programmer read, a boot image restored in isolation, or a blank slot does not establish that a full downgrade is safe. Keep the bootloader unlocked while custom images are installed. Do not write another device's EFS or calibration partitions.

[Install guide](INSTALL.md) · [Upstream G8 installation and recovery reference](https://lineageos.github.io/lineage_wiki/devices/alphaplus/install/variant1/) · [G8 device and recovery entry](https://lineageos.github.io/lineage_wiki/devices/alphaplus/variant1/)
