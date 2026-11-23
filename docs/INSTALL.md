# Install LineageOS 24.0 on the Canadian LG G8

> [!IMPORTANT]
> The current public release contains development artifacts. It cannot install Android. Use this guide only when you have a complete install kit for the exact model, with its checksum list, verified signing certificate, and matching recovery. See [what a complete kit contains](RELEASES.md#what-a-complete-install-kit-contains).

This guide covers the Canadian **LG G8 ThinQ LM-G820UM2**, LG Android 12 **G820UM40b** firmware, and Android device ID **alphaplus_lao_com**. The official LineageOS wiki groups several G8 models under `alphaplus`. The tests here apply to the named Canadian variant. Check the original model in stock Settings or on the device identification label. A generic `LM-G820` ADB response alone is insufficient. Cross-flashed or unidentified hardware needs a separate assessment. [LineageOS G8 variant page](https://lineageos.github.io/lineage_wiki/devices/alphaplus/variant1/) · [Firmware and partition reference](COMPATIBILITY.md)

## Choose your starting point

| What your G8 has now | Start here | User data |
| --- | --- | --- |
| LG stock Android, locked bootloader | [A. Start from LG stock Android](#a-start-from-lg-stock-android) | Backup required. Bootloader preparation and a clean install may wipe internal storage. |
| LG stock Android, already unlocked | [A. Start from LG stock Android](#a-start-from-lg-stock-android) | Clean install wipes internal storage. |
| Official LineageOS, another unofficial fork, or a different signing key | [B. Start from another LineageOS build](#b-start-from-another-lineageos-build) | Use a clean install unless the kit explicitly documents a tested data-preserving migration for your starting build. |
| This exact LineageOS 24 fork, same signing key | [C. Install an update from the same signing family](#c-install-an-update-from-the-same-signing-family) | Back up first. See the signing-family results in the [release qualification](RELEASES.md). |

## Before touching partitions

1. **Back up away from the handset.** Verify the copy opens. Save account recovery methods and app-specific encrypted backups. Confirm your Google account and second factors work on another device. A factory reset erases apps and internal shared storage, including Downloads. Remove portable SD media if you want it excluded and no step requires it.
2. **Identify the firmware and rollback kit.** The tested radio stack requires the Canadian 40b firmware. The ROM ZIP does not replace the entire LG firmware. Keep a verified path back to 40b and your prior recovery and system build. If the phone never booted the intended stock firmware, verify the radio and hardware from stock first. Never write another handset's EFS, modem calibration or personal partitions.
3. **Prepare USB.** Charge the phone, use a reliable data cable and a direct USB port, and download Android Platform-Tools. Enable Developer options and USB debugging on the working system, connect it, unlock it and accept the computer's debugging prompt. On Windows open PowerShell in the extracted `platform-tools` folder and substitute `.\adb.exe` for `adb` in all examples. [Google Platform-Tools](https://developer.android.com/tools/releases/platform-tools)
4. **Verify the download.** Check the exact asset names and signed certificate fingerprint for the build. Keep the files together. On Linux, in the download directory, run `sha256sum -c SHA256SUMS`. On macOS use `shasum -a 256 -c SHA256SUMS`. In Windows run the following for each kit file and compare the resulting digest with its corresponding line. A checksum match verifies the bytes. The release's trusted signature still controls installation.

   ```powershell
   Get-FileHash -Algorithm SHA256 -LiteralPath ".\lineage-alphaplus_lao_com.zip"
   ```

5. **Check the device tool output before entering recovery.** Proceed when the expected handset appears as `device`. If it shows `unauthorized`, unlock the phone and approve USB debugging. An empty line means the computer cannot see a data connection. The slot and verified boot properties are useful observations. Confirm unlock state with the model-specific procedure if the properties are missing or unclear.

   ```bash
   adb devices
   adb shell getprop ro.product.device
   adb shell getprop ro.boot.slot_suffix
   adb shell getprop ro.boot.flash.locked
   adb shell getprop ro.boot.verifiedbootstate
   ```

## A. Start from LG stock Android

1. **Establish the baseline.** Boot Canadian stock 40b and confirm the model, firmware, SIM, data, camera and USB behavior. Fix hardware and firmware mismatches before using a custom ROM. Remove Google accounts from the handset before the clean reset if appropriate, with the backup and access checks complete.
2. **Unlock before installing recovery.** The LineageOS G8 wiki states there is no official LG unlock method for this variant. It begins from an already unlocked phone. The project did not qualify a fresh unlock on a second stock handset. If yours is locked or the status is uncertain, stop here until you have a verified, exact-variant unlock and rollback route. The official generic Android fastboot procedure alone does not establish support for this G8. [G8 bootloader prerequisite](https://lineageos.github.io/lineage_wiki/devices/alphaplus/variant1/) · [Android Verified Boot states](https://source.android.com/docs/security/features/verifiedboot/device-state)
3. **Install the kit's matching recovery.** This model uses recovery in the boot image. The model-specific LineageOS wiki documents its `dd` installation from an environment that already has root and the appropriate partition links. Follow its recovery section only if your environment meets those prerequisites and the kit authorizes that exact recovery image. Ordinary stock ADB shell lacks permission to write those partitions. If the recovery route is unclear, leave the working system intact and verify it before proceeding. [G8 recovery installation](https://lineageos.github.io/lineage_wiki/devices/alphaplus/install/variant1/#installing-a-custom-recovery-using-dd)
4. **Verify both slots' firmware.** Follow the model-specific firmware copy section if setting up A/B firmware for the first time. That section supplies its own signed package and conditions. The tested upgrade began with 40b already prepared for both slots. Copying from the wrong or uncertain active slot can spread the wrong firmware. Leave the stock backups and bootloader state intact. [G8 firmware slot instructions](https://lineageos.github.io/lineage_wiki/devices/alphaplus/install/variant1/#ensuring-all-firmware-partitions-are-consistent)
5. When the recovery title and kit's certificate are confirmed, follow [the clean sideload steps](#clean-install-in-lineage-recovery).

## B. Start from another LineageOS build

1. Verify 40b firmware on both slots using your installation records. A modern Android version in Settings does not identify the installed LG firmware.
2. Check the kit's documented starting recovery and verify the ROM ZIP against the supplied, independently trusted release certificate and checksum. When available, run `check_ota_package_signature ota-release.x509.pem lineage-alphaplus_lao_com.zip` and compare the certificate fingerprint with the maintainer's independent record. The [offline verification tool](../tools/check-alphaplus-ota.py) also checks the payload. On the tested spare, the three newly signed boot-chain images staged alone on inactive A initially led to `OPID Mismatched`. The successful route used the complete OTA from the existing recovery. [Recovery notes](RECOVERY.md)
3. Reboot into the known working Lineage Recovery with `adb reboot recovery` and follow [the clean sideload steps](#clean-install-in-lineage-recovery). The verified Canadian setup came from official LineageOS 21.0 on 40b. That recovery asks for explicit confirmation because the ROM uses this project's different release key. Proceed only with the known, independently verified kit on this documented migration path. Stop if a different model, unexpected signer, invalid checksum, unknown recovery, or any other verification error appears. [Upstream G8 upgrade guide](https://lineageos.github.io/lineage_wiki/devices/alphaplus/upgrade/variant1/)

## Clean install in Lineage Recovery

![Illustrated Lineage Recovery main menu and factory reset submenu](images/recovery-reset.png)

*Illustration of the menu choices. The font, placement and navigation can differ on your recovery.*

1. Confirm the phone says **Lineage Recovery** and the kit matches it. Verify the external backup one last time. Select **Factory reset**, then **Format data/factory reset**, and confirm the wipe. Wait for recovery to explicitly report completion. Return to the main menu once. The physical stock LG factory-reset screen is a different screen.
2. Select **Apply update**, then **Apply from ADB**. On the host, `adb devices` should now show the device in `sideload` state.

   ![Illustrated Lineage Recovery Apply update and Apply from ADB menu choices](images/recovery-sideload.png)

3. From the folder containing the verified ROM ZIP, run the command below with the actual release filename. Leave the cable connected and wait for recovery to finish.

   ```bash
   adb devices
   adb sideload lineage-alphaplus_lao_com.zip
   ```

4. Read the **phone** before deciding that the install succeeded. A host progress bar that stops near 47% can be normal when recovery is still verifying or installing. Continue only when recovery reports success. A different-signer confirmation is expected only in the documented path B transition after independent verification. If recovery reports a device assertion, unexpected signature error or failed install, stop. Save the exact error and return to [troubleshooting](RECOVERY.md). [LineageOS sideload guidance](https://lineageos.github.io/lineage_wiki/devices/alphaplus/install/variant1/#installing-lineageos-from-recovery)
5. **If you want Google Apps**, use only the separately verified **Android 17 ARM64** add-on supported by the kit. Accept the ROM install prompt to reboot to recovery before add-ons, or use **Advanced → Reboot to recovery** if the kit directs you to do so. On the newly installed slot, choose **Apply update → Apply from ADB** again, then sideload the verified add-on ZIP. A separately signed add-on can show the known trust prompt. Compare its actual publisher and digest before continuing. Verify the add-on separately from the ROM. Path B documents the separate ROM signer-change case. Do not boot Android before completing this step. [Tested Android 17 ARM64 MindTheGapps release](https://github.com/MindTheGapps/17.0.0-arm64/releases/tag/MindTheGapps-17.0.0-arm64-20261022_132445)
6. Select **Reboot system now**. Once Android reaches setup, verify the new build ID, slot, Wi-Fi and mobile data. Before restoring apps, place and receive ordinary calls and listen for echo. Check encryption, SELinux and any separately installed Google Apps. [First-boot validation](VALIDATION.md)

## C. Install an update from the same signing family

1. Confirm the current and new releases use the same project OTA certificate, exact device and update branch. A different signing family belongs in [path B](#b-start-from-another-lineageos-build).
2. Copy the verified update ZIP to internal shared storage. Open **Settings → System → Updater** and select the local update option if provided by the build. Choose the ZIP and wait until Updater explicitly asks for a reboot. Leave the working slot and user data intact.
3. Reboot from Updater. Confirm the new incremental ID and expected slot. Recheck encryption, SELinux, both directions of calls, storage contents and the installed add-on state. See the [release qualification](RELEASES.md) for the signatures and Google Apps combinations tested.

[Recovery and troubleshooting](RECOVERY.md) · [Release requirements and kit contents](RELEASES.md) · [Tester matrix](VALIDATION.md)
