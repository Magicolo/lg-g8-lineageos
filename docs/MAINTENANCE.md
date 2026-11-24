# Maintain and contribute to the port

The project repository is the entry point for documentation, issues and pinned manifests. Direct code changes belong in the matching fork. Keep device-specific configuration separate from portable fixes so other maintainers can review or cherry-pick each independently.

## Change the ROM without losing the baseline

Start with the [full rebuild](REBUILD.md). Keep that baseline, the released ZIP, and a working test phone while developing the next version. Keep unpublished data and release keys in separate private storage.

| Work | Where to edit |
| --- | --- |
| Device packages, config, kernel fragment selection, G8 overlays | `device/lge/alphaplus`, the [alphaplus fork](https://github.com/Magicolo/android_device_lge_alphaplus). The full IMS build uses the branch pinned by `ims/local-manifest.xml`. |
| Audio, radio, SELinux, and configuration shared by LG SM8150 devices | `device/lge/sm8150-common`, the [common fork](https://github.com/Magicolo/android_device_lge_sm8150-common). The full IMS build uses the local manifest pin. |
| DTS, touch/NFC drivers, kernel config and backports | `kernel/lge/sm8150`, the [kernel fork](https://github.com/Magicolo/android_kernel_lge_sm8150). |
| Generic camera failure handling | `frameworks/av`, the [framework fork](https://github.com/Magicolo/android_frameworks_av). |
| IMS Java and native bridge, privileged permissions, and ABI shims | `vendor/lge/alphaplus-ims` and `frameworks/opt/net/ims/src/java/com/android/ims/LGImsFeature.java` in the Android checkout. The verified archive stages these files. The top-level `ims/` directory carries the reviewed source copies and integration notes. |
| Reproducible project pins, tools, CarrierConfig compatibility patch and documentation | This repository. The built revisions are in `manifest.xml` plus `ims/local-manifest.xml`. |

For a local edit, first stage the verified archive, then create a work branch in the project you are about to change. For example, run `git -C "$tree/device/lge/alphaplus" switch -c work/alpha-fix`. Edit the file and check `git diff` within that project. For a staged IMS source edit, make the change at the path in the **Android checkout**. Check the corresponding source copy in this repository before publishing. The proprietary archive supplies the exact matching binaries. [Change map](CHANGES.md) · [IMS boundaries](IMS.md)

To test local source changes while keeping the manifest baseline and the existing signing family, rerun the build using `--source-edits`. Use a new output directory for each candidate.

```bash
bash "$guide/tools/build-signed-alphaplus.sh" --source-edits \
  "$tree" "$inputs" "$keys" "$base/candidate-01" 8
```

The option permits edits to staged source text such as Java, C++, Soong definitions and XML. The archive digest, expected project heads and exact binary inputs still have to match. Tracked device, kernel and platform edits can also be tested before committing. To reproduce a committed source change, publish its commit on a candidate branch and update the matching manifest pin. If you intentionally replace a proprietary input, publish a separately versioned, verified input archive and update its digest in `tools/prepare-local-ims.py`. Save the source change and the steps that produce that input with its review.

## Update LineageOS, Android or the kernel

Use a candidate manifest branch and an independent checkout for an upstream refresh. Run the work in this order so a regression has a small set of suspects.

1. **Record the baseline.** From the last known-good checkout save `repo manifest -r -o "$base/current.xml"`, the signed OTA and its checksums, public key fingerprints, the effective kernel config and hardware results. Check the installed build with `adb shell getprop ro.build.version.incremental` and `adb shell getprop ro.build.version.security_patch`.
2. **Choose one update.** Start with a same-branch LineageOS security update or one compatible downstream kernel backport. For a platform refresh, compare the official upstream manifest as a unit, including AOSP tag assignments, toolchain and prebuilt pins. Keep the local device, kernel, framework and vendor overrides. Avoid building a mixture of unrelated Android tags when the platform revision changes. Use the default refs of the corresponding component only after confirming they match the intended LineageOS branch.
3. **Review what moved.** The audit helper below reports `MATCH`, `DIFFERS`, `NO_REF` and `UNAVAILABLE` for configured refs. The four fork refs are your pinned work branches, so also compare their upstream parents. LG device, common and kernel source come from `lge-qcom-dev`. The camera source comes from `LineageOS`. Check the desired branch explicitly. Use the original local commit as a starting point, fetch the parent branch, inspect the changes and carry the small project patches forward in separate commits. Resolve missing LFS objects or unreachable commits before proceeding.
4. **Advance the pins.** Commit and push the component candidates to their own repositories or to equivalent public forks. In the candidate guide, update each affected `revision` plus its fetch hint `upstream` in the appropriate XML. Keep the source-preview device pins in `manifest.xml` and the IMS-enabled device pins in `ims/local-manifest.xml`. The staging helper reads these files for the six IMS-sensitive checks. If the CarrierConfig patch conflicts, compare the package's new `versionCode` with the installed build. Adapt the compatibility patch while preserving an equal or higher version. Use the same component sources on the second build host.
5. **Sync, stage and build the candidate.** Use the commands in [Rebuild](REBUILD.md), substituting the candidate guide checkout and `repo init -b refs/heads/<candidate-branch>`. Point `-u` at your manifest fork if applicable. Copy its local manifest **before** syncing. Where practical, build the affected targets first, then complete the full signed OTA. Publish exact commit pins and a resolved manifest only when the build and review agree.

Run this audit from the current Android checkout. Compare the resulting TSV with official security, AOSP and Lineage release information. Detached source revisions and pinned AOSP tags can require manual review.

```bash
cd "$tree"
repo manifest -r -o "$base/current.xml"
python3 "$guide/tools/audit-upstream.py" --checkout "$tree" \
  --manifest "$base/current.xml" > "$base/upstream.tsv"
```

### What to check for each kind of update

| Change | Keep together and verify |
| --- | --- |
| **LineageOS monthly patch on Android 17** | Android SPL and branch pins, WebView LFS files, VINTF, telephony, recovery, OTA, APEX inventory, Google Apps persistence and same-key migration. A newer Android SPL does not change the LG vendor components. |
| **New Android version** | Official LineageOS/AOSP manifest and toolchain, device lunch target, SDK/build metadata checks, vendor VINTF, BPF loader, Java/Binder and native IMS ABI, SELinux policy and Android-version-specific ARM64 Google Apps. Update `tools/check-alphaplus-ota.py` and install instructions to the verified SDK, SPL and add-on hash. Establish a clean-booting build before offering an in-place update. |
| **Kernel patch** | Use the device's downstream kernel tree. Keep SM8150/LG drivers, ordered G8 fragments, boot/DTBO, encryption support, pinned BPF compatibility and VINTF. Review the effective config and run `m -j8 dtbimage dtboimage` before full packaging. Check actual mitigation status and networking on the phone. Upstream 4.14 fixes may require deliberate backports. A move to a different major kernel needs its own hardware port. |

Known baseline evidence and limits are in [Compatibility](COMPATIBILITY.md), [Changes](CHANGES.md), [Attempts](ATTEMPTS.md) and the [hardware test matrix](VALIDATION.md). Start with those before carrying forward a workaround.

## Qualify the candidate

1. Keep the same private keys for an in-place update and verify the OTA and platform certificate against the last installed release. If a new APEX requires a key, generate a disposable key directory from the candidate's unsigned target-files using `tools/signing-inputs.py --new-keys`. Copy only the complete `.pem`, `.pk8` and `.x509.pem` set for that new APEX into the maintained key directory, after confirming all three destination paths are absent. Preserve existing APK, APEX and AVB keys. Back up the newly added set.
2. Run the [offline verification](REBUILD.md#4-verify-before-installing-or-publishing). Verify that the candidate timestamp advances, the OTA is a full A/B package for `alphaplus_lao_com`, boot/DTBO/vbmeta match the payload, Android and recovery trust the expected signer, and partition sizes permit the intended add-on. Compare the APEX public keys of existing packages with the previous signed target-files. Test any branch changing the GApps package with the actual add-on and clean setup.
3. On a spare **LM-G820UM2 on 40b**, test a clean install and separately a same-key OTA with representative data and optional Google Apps. Check first boot, encryption and reboot, both call directions after boot and after idle, call audio, SMS/data, Wi-Fi, camera, torch, NFC, fingerprint and remaining [validation cases](VALIDATION.md). Record results and the exact hashes. Investigate a failed hardware test before offering the OTA.
4. Publish the reviewed source pins, docs, OTA and checksums together. Follow [the release checklist](RELEASES.md). Updater accepts suitable packages signed by the trusted family. Automatic updates require a maintained HTTPS feed plus new OTA builds. Generate the feed entry with [make-updater-index.py](../tools/make-updater-index.py) and deploy it only after the candidate passes. Review the project's release page for this fork's actual availability. [AOSP security bulletins](https://source.android.com/docs/security/bulletin) · [LineageOS Updater](https://github.com/LineageOS/android_packages_apps_Updater/tree/lineage-24.0)

## Debugging and reporting

Include exact model, firmware revision, Android incremental, current slot, reproducible steps, expected result, and observed result. Distinguish a real call or capture from service enumeration. For audio use the route and what the far-end listener heard. For camera record the PID before and after failure and only the relevant redacted stack and log lines. Keep subscriber IDs, phone numbers, account state, IMEI, raw radio logs, traces containing private media, signing material and private source URLs out of public reports.

Use the tools in this repository as test fixtures. Install the diagnostic app only for a test session and remove it after use. If a fix requires logs from SELinux, constrain any policy change to the minimum domain, endpoint and operations and test with enforcing enabled.

## Send fixes upstream

- The generic HIDL torch failure guard is the first candidate. Check whether the target branch already carries equivalent handling and attach a small regression case. Keep the device package patch independent.
- Device registration, hardware profiles and kernel configuration belong in the LG trees. A new variant needs matching firmware, hardware validation, and obvious entry points for maintainers.
- When submitting to LineageOS, use Gerrit and follow its contributor agreement and AI-assisted contribution rules. Use the required attribution trailer and have a human maintainer review, explain and support the implementation. Check the policy for fully tool-generated work.
- Official device support is a separate process. It requires meeting the device charter and a maintainer committed to ongoing support.

[Submitting patches](https://lineageos.github.io/lineage_wiki/how-to/submitting-patches/) · [AI contribution rules](https://github.com/LineageOS/charter/blob/main/ai-coding-assistants.md) · [Device support charter](https://github.com/LineageOS/charter/blob/main/device-support-requirements.md) · [Submitting a port](https://lineageos.github.io/lineage_wiki/submitting_device.html)
