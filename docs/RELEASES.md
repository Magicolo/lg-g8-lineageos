# Release artifacts and OTA qualification

## Source preview and build outputs

The source-preview release carries device-tree and configuration outputs taken from the completed Canadian development build `1795369605`. It also includes the rebuilt diagnostic app. They are inspection and development inputs. There is no full recovery image or installable Android system in this release.

| Asset | Provenance and use |
| --- | --- |
| `alphaplus-1795369605-base-dtb.bin` | The base device-tree blob extracted from the verified build's `boot.img`. It matches the build's generated `dtb.img` byte for byte. |
| `alphaplus-1795369605-raw-dtbo.bin` | The raw 14-entry overlay table from the kernel build. It matches the embedded payload of the private `dtbo.img` before the AVB footer and partition padding. |
| `alphaplus-1795369605-kernel.config` | Effective configuration extracted from the booted build's kernel image. It matches all three build directories' effective kernel, DTB and DTBO configs byte for byte. |
| `compatibility-smoke.apk` | The development test fixture, rebuilt from the included source with its own disposable app certificate. It runs synthetic Android API checks and is separate from the OS. |
| `SHA256SUMS` | Validate the downloaded assets with `sha256sum -c SHA256SUMS`. |

The corresponding kernel source is [commit 8817f5e6c937](https://github.com/Magicolo/android_kernel_lge_sm8150/tree/8817f5e6c9372e59e0c10a8dbe96517f64e927a8). The alpha fragment in the build matched that commit exactly. The [pinned manifest](../manifest.xml) also records the device makefiles, Android build rules, and Android Clang toolchain (`r596125`, project revision `29182889399818f97baa65ea238c80e8117981eb`). The [build guide](BUILD.md) lists the device-tree targets. These outputs do not carry firmware or modem calibration files. The raw blobs are not padded or AVB-wrapped Android partition images. Use them for source-to-binary inspection and comparisons.

The local test OTA was verified with the public AOSP test certificate and contains the private LG IMS adaptations. A build fingerprint inherited from 40b can include `release-keys` even when the actual OTA certificate is a test key. Inspect the actual signer and payload. The earlier release-signing rehearsal passed offline verification and old-key rejection. The normalized private release-key build was subsequently installed on the spare through its original Lineage Recovery. The installed OTA trust store matched the verified certificate. [Signing results](SIGNING.md)

## What a complete install kit contains

For the exact signed candidate and the disposition of every asset group, see the [full ROM distribution audit](RELEASE-AUDIT.md).

A kit has one tested firmware and signing combination for the Canadian G8. It contains:

- A full Canadian A/B OTA ZIP, its device and build metadata, the signing certificate fingerprint, and SHA-256 sums.
- The matching Lineage Recovery boot image and any companion boot-chain images the validated stock-to-recovery procedure actually needs. Keep boot, the packaged DTBO and vbmeta paired from the same target-files. A normal sideload writes the OTA partitions and does not require separate raw flashing of those images.
- The matching public source manifest, kernel configuration, known limitations, and complete installation and rollback instructions. The user obtains the required LG stock firmware and any optional Google Apps from their documented publishers. These are separate from the ROM package.

The public source-preview assets cannot substitute for those files. Both the private test-key build and the private release-key build contain modified LG IMS components. Exact redistribution permission for the proprietary parts is unresolved. Offline re-signing alone cannot establish a safe stock-to-ROM install. See the [installation guide](INSTALL.md) and [troubleshooting](RECOVERY.md).

## Qualify a future installable release

See [the Trust signing guide](SIGNING.md) for release-key verification and the test-key migration requirements.

1. Freeze the exact source manifest, target assumptions, kernel inputs and asset list. Establish redistribution rights for any included LG or Qualcomm APK, firmware, table, library or adaptation. Document extraction from owner-supplied stock inputs where appropriate. Provide the exact corresponding kernel source and build configuration with any distributed kernel image.
2. Generate dedicated release keys and back them up securely. Keep private keys outside Git and its releases. Apply the release keys to APKs and any project-signed APEX containers and payloads, then sign the whole OTA and payload against the recovery and system trust chains. Preserve intentional, permitted presigned packages. Pin the public signing certificate fingerprint. Validate that the obsolete test key and a wrong release key are rejected.
3. On one exact device, require Canadian target identity, SDK 37, increasing timestamp, matching A/B layout, image capacities, VINTF and both signatures. Use the [offline OTA preflight](../tools/check-alphaplus-ota.py) with the matching target-files and a verified ARM64 GApps ZIP when evaluating space. It checks partition sizes and add-on capacity. The default Android verifier checks the whole-package and A/B payload signatures. Run VINTF independently. Keep Google Apps separate.
4. Verify clean installation and recovery. On the tested G8, Lineage Recovery runs from the appropriate A/B boot image. For a major clean install using verified images, back up data and account recovery first. Verify the required firmware, format data once when the migration requires it, apply the device-specific OTA and reboot to the new slot's recovery before installing any compatible add-on as directed. Recovery's final status is authoritative if host sideload progress stalls around 47%. Test only the model and image matching the intended release.
5. Verify upgrade and rollback on the actual release signing family. The old test-key Updater cannot normally validate a release-key OTA. Changing platform, APK and APEX identities can also affect app data and encryption keys. Use a clean install as the tested migration baseline until a specific migration path passes. Test incoming and outgoing voice, encryption, recovery, update state and add-on persistence on the new signing family.
6. For an Updater channel, use the `lineage.updater.uri` product setting with a direct HTTPS v2 metadata endpoint. Match release type and SDK and advance the build timestamp. The metadata client rejects redirects. Verify the URL, OTA bytes and signature before switching the index. The [index generator](../tools/make-updater-index.py) verifies the signed package before writing version metadata. Test a real same-key A/B update from the published index and record the resulting slot and build on a device.

[AOSP signing guide](https://source.android.com/docs/core/ota/sign_builds) · [LineageOS build signing](https://wiki.lineageos.org/signing_builds) · [Linux kernel licensing](https://docs.kernel.org/process/license-rules.html) · [LineageOS Updater](https://github.com/LineageOS/android_packages_apps_Updater/tree/lineage-24.0)
