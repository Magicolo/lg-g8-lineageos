# LineageOS Trust signing warning

The G8 on development build `1795369605` reported `ro.build.tags=test-keys`. Its OTA trust store held the known AOSP test certificate. Trust checks the build tags. The real fix is to re-sign the build with a dedicated keyset. Android's signing tools change the tags as part of that process. A tag change alone leaves the original public signing keys in use. [Trust implementation](https://github.com/LineageOS/android_lineage-sdk/blob/a891029846705dc78f81452b68467fb7ded565e3/lineage/lib/main/java/org/lineageos/platform/internal/TrustInterfaceService.java#L324) · [AOSP signing instructions](https://source.android.com/docs/core/ota/sign_builds)

## Build and verify a release-key package

1. Use one dedicated keyset for this ROM's update channel. Keep a secure backup apart from the build tree. Use the LineageOS instructions and AOSP tools to sign the exact target-files, including the Android APK and project-signed APEX key mappings. Publish only the public OTA certificate.
2. Generate the OTA from the signed target-files. Use boot/recovery, packaged DTBO and vbmeta from that same archive. Verify the complete OTA and payload signatures, image hashes, build tags and both recovery and Android OTA trust. Verify representative APKs, including the matching platform signatures of `framework-res.apk` and LG IMS when present.
3. Add `--require-release-keys` to the normal `tools/check-alphaplus-ota.py` command and pass the expected public certificate via `--ota-certificate`. This checks the release tags and the two trust stores before the existing OTA verifier runs. Verify APKs, APEX, and VINTF separately. A new release must have a newer build timestamp and use the same signing family.
4. Keep the [distribution audit](RELEASE-AUDIT.md) with the build. Signing changes which packages Android and recovery trust. It does not grant rights to the components in the package.

[LineageOS signing guide](https://lineageos.github.io/lineage_wiki/signing_builds.html) · [OTA qualification](RELEASES.md)

## Move a G8 from test keys to release keys

The current installation trusts the AOSP test certificate. Same-key local OTA does not apply to this change. Package certificates, shared UIDs, APEX updates and encrypted userdata need a separate migration test. The running build has `ro.debuggable=0`. The upstream rooted migration script and temporary migration builds have yet to be validated for this G8 and its additional key mappings.

The path prepared for this device is a clean install. Verify a current backup, a working recovery that trusts the new OTA, and a rollback route before erasing userdata. Follow the [existing-Lineage installation path](INSTALL.md#b-start-from-another-lineageos-build). After setup and reboot, check `adb shell getprop ro.build.tags` for `release-keys` and check Trust for private signing keys. This alert is separate from the unlocked bootloader state and hardware-backed attestation. Run the [device validation matrix](VALIDATION.md) before restoring personal apps.
