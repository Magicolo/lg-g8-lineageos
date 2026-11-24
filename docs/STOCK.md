# Prepare or restore Canadian LG stock firmware

This procedure covers the Canadian **LG G8 ThinQ LM-G820UM2** only. It uses Windows and the Canadian **G820UM40b** stock Android 12 package. A normal install from a working Lineage Recovery on that firmware can go directly to [Install](INSTALL.md). LGUP Refurbish erases apps and internal storage. Verify backups, account recovery and the model before choosing it.

## Find the starting point

| Phone state | Route |
| --- | --- |
| Stock 40b, bootloader confirmed unlocked, root working | Check [recovery preparation](#prepare-recovery-from-unlocked-stock). |
| Stock requires a 40b restore | Use [LG Download Mode and LGUP](#restore-40b-with-lgup). Check the bootloader and root afterward. |
| Factory-locked, or unlock state unknown | Stop before any custom image writes. The upstream guide starts from a rooted handset and provides no unlock procedure for this model. The project has no validated unlock from factory-locked Canadian 40b. |
| OPID Mismatched, boot loop, or only Qualcomm 9008 | Use [recovery troubleshooting](RECOVERY.md). Migration assumes a verified rollback for the exact handset. |

## Restore 40b with LGUP

1. Download `LG-G8-Windows-tools.zip`, the **three** 40b KDZ parts, `split-files.json`, `Join-ReleaseParts.ps1` and `SHA256SUMS` from the [release](https://github.com/Magicolo/lg-g8-lineageos/releases/tag/v1.1.0). Verify the Windows tools ZIP and the join script against `SHA256SUMS` before extracting it.
2. Place the join script, JSON and KDZ parts together. Open PowerShell in that folder and run the two commands below. The expected 40b KDZ is **4,830,976,937 bytes** and its SHA-256 is `73a4cce272d409b2b80822d849d38d670b397fca86320f0426bd672d0d682efb`. The join script verifies the parts and output. Keep only the recombined `.kdz` selected in LGUP.
3. Install `LGMobileDriver_WHQL_Ver_4.5.0.exe` from the extracted tools. Expand `LGUP_Lab_Frame_1.16.0.3_and_Common.zip` and install `LGUP_Lab_Frame_Ver_1_16_0_3.msi`. The tested installed layout had `LGUP.exe` in `C:\Program Files (x86)\LG Electronics\LGUP` and the supplied `LGUP_Common.dll` (version 2.1.0.23) in its `model\common` subfolder. Close LGUP before putting the Common DLL there. Use the exact included files.
4. Charge the phone, power it off and disconnect USB. Hold **Volume Up** while plugging a data cable directly into the PC. Confirm the handset visibly displays **Download Mode** and LGUP detects the connected G8. If Windows only shows a Qualcomm 9008 device, or LGUP reports a different model or rejects the KDZ, stop there.
5. In LGUP, browse for the verified `G820UM40b_00_OPEN_CA_OP_1129.kdz` under the file path. Select **Refurbish** for the tested full-stock restore. Check the file, device and wipe permission before pressing **Start**. Leave the cable connected while LGUP writes and the phone reboots. Recheck the software version in **Settings → About phone** and test USB, SIM, calls, mobile data and camera in stock.
6. Enable USB debugging if moving on to recovery. Complete the bootloader and root checks below. Returning to stock establishes the firmware and is independent of the bootloader unlock and Lineage recovery steps.

```powershell
.\Join-ReleaseParts.ps1 -File G820UM40b_00_OPEN_CA_OP_1129.kdz
Get-FileHash -Algorithm SHA256 .\G820UM40b_00_OPEN_CA_OP_1129.kdz
```

## Prepare recovery from unlocked stock

With USB debugging enabled and exactly one connected Android device, open a terminal in the released `platform-tools` and run these read-only checks. On Windows use `.\adb.exe` in place of `adb`.

```bash
adb devices
adb shell getprop ro.boot.flash.locked
adb shell getprop ro.boot.vbmeta.device_state
adb shell getprop ro.boot.verifiedbootstate
adb shell getprop ro.boot.slot_suffix
adb shell su -c id
```

A reported lock value of `1` or state `locked` blocks the custom recovery route. Where the bootloader provides these values, `0` and `unlocked` are consistent with an unlocked phone. A blank or conflicting report needs separate confirmation. A successful root command prints `uid=0`. An OEM unlocking toggle alone gives no proof of an unlocked bootloader.

Use the [upstream G8 rooted recovery instructions](https://lineageos.github.io/lineage_wiki/devices/alphaplus/install/variant1/#installing-a-custom-recovery-using-dd) to identify the recovery for the exact model and firmware. Preserve same-device boot-chain originals off the phone before touching slots. The project tested the transition **from working LineageOS 21 Recovery on 40b** by sideloading a complete OTA. A trial that installed the new release's raw boot-chain images ahead of the OTA produced **OPID Mismatched** on one G8. Keep the supplied raw images as matching recovery references. A confirmed 40b phone with existing Lineage Recovery can proceed directly by sideload.

Follow the upstream [A/B firmware consistency guidance](https://lineageos.github.io/lineage_wiki/devices/alphaplus/install/variant1/#ensuring-all-firmware-partitions-are-consistent) if the inactive slot may be stale. Its copy-partitions procedure takes the **active slot** as its source. Confirm that source is the known-good matching firmware, and obtain the exact helper from the upstream page. The helper is an upstream dependency of that route.

Once the recovery and both slots are prepared, use [the clean install and Google Apps steps](INSTALL.md#clean-install-in-lineage-recovery). The project still needs a complete rehearsal from root and recovery preparation on stock through the first Android boot. That rehearsal needs a spare and a proven handset-specific rollback path.
