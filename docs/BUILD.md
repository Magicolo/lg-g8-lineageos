# Build the LG G8 source preview

The project manifest pins 1,246 Git projects and four component forks. Use a dedicated Linux workspace on a case-sensitive filesystem. The target is ARM64, Android 17 SDK 37, LineageOS 24.0. The tested development handset is the Canadian LM-G820UM2 on LG 40b. Its internal build target is `alphaplus`. The Canadian recovery target used by the full development OTA was `alphaplus_lao_com`.

## 1. Sync the pinned source

Install Git, Git LFS, Android's `repo` launcher and the standard LineageOS build dependencies. Budget several hundred GiB for the checkout, object store and build output. Keep build output distinct from the source working trees. One Android 17 Soong graph pass exceeded 52 GiB of resident memory on the development host before swap was added. Lowering Ninja's job count can help later compilation but cannot cap every Soong process.

Run the following in a new directory. To initialize from a release snapshot, use the full tag ref, for example `-b refs/tags/v0.1.2-source-preview`. A bare tag name is interpreted as a branch by `repo init`.

```bash
repo init -u https://github.com/Magicolo/lg-g8-lineageos.git \
    -b main -m manifest.xml --git-lfs --no-clone-bundle
repo sync -c -j8 --no-tags
repo manifest -r -o resolved-local.xml
```

All four fork entries pin the reviewed commit and specify its public branch as the fetch hint. A fresh `repo init` from the public tag and `repo manifest` resolved all 1,246 projects, including the four published fork revisions. A complete fresh sync and end-to-end build of this public slice remain to be verified. Keep existing development checkouts separate while testing a clean build. [Android repo launcher](https://source.android.com/docs/setup/download) · [Manifest reference](https://gerrit.googlesource.com/git-repo/+/HEAD/docs/manifest-format.md)

## 2. Check the source and firmware inputs

- Confirm the checkout matches `manifest.xml`. The expected four component revisions are listed in [the change map](CHANGES.md).
- The manifest references existing LG community device support and vendor projects. The compiled DTB and DTBO use the kernel source. A system build also needs the device's vendor blobs and the exact matching radio and boot firmware on the handset. Keep any independently obtained vendor inputs hash-pinned and verify redistribution terms before mirroring them.
- The public preview omits the working LG IMS integration and its binary inputs. Read [the IMS guide](IMS.md) before attempting to reproduce the complete call-capable development build.
- Check that Git LFS materialized both ARM and ARM64 Chromium WebView APKs under `external/chromium-webview/prebuilt/`. If either starts with the Git LFS pointer header, fetch the LFS objects at the manifest revision. Verify each file's size and SHA-256 against its pointer object before retrying. A valid Git commit alone does not establish that a prebuilt exists.
- The preview retains the selected platform's BPF compatibility changes and the matching SM8150 kernel backports. Keep them together when changing either side. A newer Android generic kernel does not automatically match the LG boot image, vendor HALs or firmware.

## 3. Compile and retain build identity

```bash
source build/envsetup.sh
lunch lineage_alphaplus-cp2a-userdebug
m -j8 dtbimage dtboimage
# For an intentional full development build with the matching inputs
m -j8 bacon check_ota_package_signature
```

Device trees are written under `out/target/product/alphaplus` by default. The kernel, base DTB and DTBO have independent build output directories under `obj`. The raw DTBO table is under `obj/DTBO_OBJ/arch/arm64/boot/dtbo.img`. The packaged `dtbo.img` includes additional Android Verified Boot partition data. See [artifact provenance](RELEASES.md) for the files kept from the completed development build.

Record the manifest, the toolchain revision, the product target, build timestamp, build variant, patch levels and the effective kernel configuration from `obj/KERNEL_OBJ/.config`. For an OTA also preserve matching boot, DTBO and vbmeta outputs, the target-files archive, public signing certificate fingerprint and SHA-256. Keep signing keys and unpublished firmware outside source control.

## Diagnose common failures

| Symptom | Check first |
| --- | --- |
| Soong is killed without a compile error | Check system memory and kernel OOM logs. Free memory or add suitable swap, then resume incrementally. Repeatedly clearing valid outputs wastes space and time. |
| WebView manifest or uses-library check fails | Verify the real Git LFS APK and inspect it with `aapt2` at the pinned revision. |
| Kernel config target does not exist | The old alpha defconfig is absent on this kernel branch. The board appends the alpha fragment to the shared fragment list. Inspect the actual merged config. |
| Ninja reports duplicate lgdata 1.0 destinations | A private IMS integration has selected two providers of the same SONAME. See [IMS packaging](IMS.md#android-17-java-and-native-boundaries). |
| OTA target or geometry does not match | Verify the exact device identity, firmware, A/B layout and image capacities. Check the generated OTA metadata and VINTF before any installation. |
