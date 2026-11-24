# Rebuild or recover a complete Canadian LG G8 kit

The GitHub tag pins the source projects and their revisions. The exact signed install kit and the separately held local IMS checkpoint let the maintainer continue after deleting the old build directories. Keep them on a drive outside either workspace. A new build uses a new timestamp; the preserved OTA is the byte-for-byte copy of build 1795454921.

## What to save before deleting a build tree

| Item | Needed for |
| --- | --- |
| Complete signed OTA, public certificate and SHA256SUMS | Install and verify the existing build. Existing Lineage Recovery can sideload the OTA without independently flashing raw images. |
| Matching boot, DTBO and vbmeta plus signed target-files | Recovery and image inspection. Use the OTA and target-files together. |
| Local `lg-ims-working-inputs.tar.gz` archive | Complete IMS build. The archive SHA-256 is `3cdbef87a780543c98ef7a38f84a1f86e7eb0b945b2db8c92982b1d45c9e1d1f`. It contains the exact locally prepared binary and legacy ABI pair. |
| Dedicated APK, APEX and AVB signing keys | A compatible update for phones already signed by this project. Keep them in separate private storage. Use fresh keys for a separate signing family. |
| Source tag and this guide | Recover all source projects from GitHub and the other pinned upstream servers. |

The public source and checksums document the integration. The complete APK adaptation uses separately obtained inputs, and the public repository does not provide a from-stock adapter for all of them. Keep the input archive if you need the tested VoLTE build.

## Build from a new Linux checkout

Use a case-sensitive Linux filesystem. The last build used Ubuntu 26.04 x86-64, about 61 GiB RAM and 39 GiB swap. Allow several hundred GiB for source and output plus extra space for target-files, signed images and temporary data. Install Git LFS, the Android `repo` launcher, Python 3.11 or later and the standard LineageOS build packages.

Replace the example paths with your own. The install kit is a separate directory from the Android checkout.

```bash
guide="$HOME/lg-g8-guide"
tree="$HOME/android-g8"
kit="/path/to/private-install-kit"
keys="/path/to/private-release-keys"

git clone --branch v1.0.1 https://github.com/Magicolo/lg-g8-lineageos.git "$guide"
mkdir -p "$tree"
cd "$tree"
repo init -u https://github.com/Magicolo/lg-g8-lineageos.git \
    -b refs/tags/v1.0.1 -m manifest.xml --git-lfs --no-clone-bundle
mkdir -p .repo/local_manifests
cp "$guide/ims/local-manifest.xml" .repo/local_manifests/
repo sync -c -j8 --no-tags
repo manifest -r -o resolved-local.xml
inputs="$kit/Private build inputs/source-snapshot/lg-ims-working-inputs.tar.gz"
python3 "$guide/tools/prepare-local-ims.py" "$tree" "$inputs" --upgrade-compat
bash "$guide/tools/build-signed-alphaplus.sh" "$tree" "$inputs" "$keys" "$HOME/g8-signed-output" 8
```

If WebView still contains an LFS pointer, see [build troubleshooting](BUILD.md). The source preparation checks the component revisions and input archive hash, and rejects unrelated edits to the input paths. The migration flag retains the CarrierConfig version used by the released signing family. The build script uses generic host identifiers and pins the Canadian SDK 37 target. It saves the signed OTA, target-files, public certificate, boot-chain images and checksums. Use the [preflight](SIGNING.md#build-and-verify-a-release-key-package) and [hardware matrix](VALIDATION.md) before deploying a rebuild.

The public Java bridge uses carrier-neutral method names. The local archive pairs the historical ABI symbols with the APK that calls them. Use the archive's complete pair for a matching rebuild. For a port, use the [IMS design](IMS.md) and match the bridge and APK together. Numeric profiles are configuration inputs.

## Check an existing install kit

From the kit directory on Linux run `sha256sum -c SHA256SUMS`. On Windows compare `Get-FileHash -Algorithm SHA256` with the matching line. Verify the OTA with the pinned public certificate and the AOSP `check_ota_package_signature` from your build tools. A successful check covers the whole ZIP and its A/B payload.

To re-export the exact boot-chain images into an empty directory, use the signed target-files archive that belongs with the OTA.

```bash
mkdir recovered-images
python3 "$guide/tools/extract-alphaplus-images.py" \
    /path/to/lineage-alphaplus_lao_com-1795454921.zip \
    /path/to/signed-target-files.zip recovered-images
```

Then follow [Start here](START-HERE.md), [installation](INSTALL.md) and [recovery](RECOVERY.md). Use the illustrated steps and stop if the phone reports a different model, an unexpected signer, or OPID Mismatched.

[Android signing tools](https://source.android.com/docs/core/ota/sign_builds)
