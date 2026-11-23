# LineageOS Trust signing warning

The G8 on development build `1795369605` reported `ro.build.tags=test-keys`. Its OTA trust store held the known AOSP test certificate. Trust checks the build tags. The real fix is to re-sign the build with a dedicated keyset. Android's signing tools change the tags as part of that process. A tag change alone leaves the original public signing keys in use. [Trust implementation](https://github.com/LineageOS/android_lineage-sdk/blob/a891029846705dc78f81452b68467fb7ded565e3/lineage/lib/main/java/org/lineageos/platform/internal/TrustInterfaceService.java#L324) · [AOSP signing instructions](https://source.android.com/docs/core/ota/sign_builds)

## Build and verify a release-key package

1. Use one dedicated keyset for this ROM's update channel. Keep a secure backup apart from the build tree. Use the LineageOS instructions and AOSP tools to sign the exact target-files, including the Android APK and project-signed APEX key mappings. Publish only the public OTA certificate.
2. Generate the OTA from the signed target-files. Use boot/recovery, packaged DTBO and vbmeta from that same archive. Verify the complete OTA and payload signatures, image hashes, build tags and both recovery and Android OTA trust. Verify representative APKs, including the matching platform signatures of `framework-res.apk` and LG IMS when present.
3. Add `--require-release-keys` to the normal `tools/check-alphaplus-ota.py` command. Pass the expected public OTA certificate via `--ota-certificate` and the expected public platform certificate via `--platform-certificate`. This checks release tags, both OTA trust stores, and representative APK signatures extracted from the final system image. The embedded checks use `debugfs` and `apksigner`. Verify the project-signed APEX keys and VINTF separately. A new release must have a newer build timestamp and use the same signing family.
4. Keep the [distribution audit](RELEASE-AUDIT.md) with the build. Signing changes which packages Android and recovery trust. It does not grant rights to the components in the package.

[LineageOS signing guide](https://lineageos.github.io/lineage_wiki/signing_builds.html) · [OTA qualification](RELEASES.md)

## Move a G8 from test keys to release keys

An existing test-key or official LineageOS installation trusts a different certificate. Local Updater expects the same signing family. Platform APKs, shared UIDs, APEX updates and encrypted userdata are also affected by a signing-family change. A data-preserving migration is unqualified for this device.

On a second Canadian G8 with 40b firmware, the existing Lineage Recovery 21.0 installed the independently verified full private-key Android 17 OTA. This used the clean install workflow. Recovery displayed the expected different-signer prompt for the already verified package. Android first booted in slot A after the separate GApps install. See [installing from another LineageOS build](INSTALL.md#b-start-from-another-lineageos-build) for prerequisites and stop points.

The device reported `release-keys`. Its Android OTA trust store contained precisely the expected certificate. The matched system image contained the expected private platform certificate on framework-res, Settings, LineageParts and LG IMS. With Trust onboarding complete and **Build signature** alerts enabled, a normal restart showed no public-keys alert. The unlocked bootloader remains a separate boot-integrity state. [Validation results](VALIDATION.md)
