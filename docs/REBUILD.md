# Rebuild the full LG G8 ROM from scratch

The [v1.1.0 release][release] contains the install files and the exact IMS input archive. The v1.1.0 Git tag pins the Android source. The current guide contains the rebuild and signing tools. You can recreate that source baseline with a new build timestamp, install the existing signed OTA, or develop the next build. The release's SHA-256 identifies the original binary. A rebuild has its own hashes.

## What you need

- An x86-64 Linux machine and a case-sensitive filesystem. The development machine ran Ubuntu 26.04 with about 61 GiB RAM and 39 GiB swap. A Soong phase reached about 52 GiB resident memory. Plan for at least 400 GB free, and preferably 500 GB to leave room for signing, test artifacts and Git storage. Use an SSD. A second checkout requires additional space. [AOSP host requirements](https://source.android.com/docs/setup/start/requirements)
- Internet access to GitHub and the AOSP Git servers. The [pinned manifest](../manifest.xml) fetches the four component forks and the rest of the Android source from their original hosts. It also pins both LG vendor repositories. The release archive supplies the extra LG IMS inputs.
- For a clean install on a development handset, generate your own keys below. To update a phone already running this project's signed ROM **with its apps and data**, restore the original private APK, APEX and AVB keyset from the maintainer's private escrow outside the checkout. A public certificate verifies the OTA. Only the original private keyset can sign a same-family update. [Signing and recovery](SIGNING.md)
- To install prebuilt files or return a phone to stock, use [Install](INSTALL.md) and [Stock preparation](STOCK.md). A build machine is optional for either operation.

## 1. Install host tools

On Ubuntu, open Bash and run the following. Use the [AOSP Repo launcher instructions](https://source.android.com/docs/setup/start/requirements#install-repo) if the `repo` package is unavailable or the launcher version is below 2.4. Android's prebuilt JDK and toolchain come from the pinned checkout. The verification scripts need Python 3.11 or newer.

```bash
sudo apt-get update
sudo apt-get install repo git git-lfs gnupg flex bison build-essential zip curl \
  zlib1g-dev libc6-dev-i386 x11proto-core-dev libx11-dev lib32z1-dev \
  libgl1-mesa-dev libxml2-utils xsltproc unzip fontconfig rsync python3 \
  libncurses-dev lz4 bc openssl e2fsprogs android-sdk-libsparse-utils
git lfs install --skip-repo
repo version
python3 --version
```

If Repo asks for Git author details, use a Git identity you are comfortable exposing in public commits. On WSL, put source and output in the Linux filesystem and give the VM adequate RAM and swap. Windows can perform the phone installation separately.

## 2. Fetch and verify the baseline

Run in Bash. Choose a new parent directory on a disk with enough free space. Keep your guide and downloads outside the Android tree. These commands fix the release tag. Later updates use [the candidate workflow](MAINTENANCE.md).

```bash
set -e
base="$HOME/g8-development"
guide="$base/guide"
tree="$base/android"
kit="$base/assets"
mkdir -p "$base" "$tree" "$kit"
git clone https://github.com/Magicolo/lg-g8-lineageos.git "$guide"

# Check that the current scripts target the sources shipped in v1.1.0.
git -C "$guide" diff --exit-code v1.1.0 HEAD -- manifest.xml ims/local-manifest.xml
release=https://github.com/Magicolo/lg-g8-lineageos/releases/download/v1.1.0
curl --fail --location --retry 3 \
  --output "$kit/lg-ims-working-inputs.tar.gz" "$release/lg-ims-working-inputs.tar.gz"
(cd "$kit" && sha256sum -c - <<'SUM'
b8dc7e0e6097a66f0eba895c0d9e67c58953e66463e2d1ff6c76670a1b5e4094  lg-ims-working-inputs.tar.gz
SUM
)

cd "$tree"
repo init -u https://github.com/Magicolo/lg-g8-lineageos.git \
  -b refs/tags/v1.1.0 -m manifest.xml --git-lfs --no-clone-bundle --partial-clone
mkdir -p .repo/local_manifests
cp "$guide/ims/local-manifest.xml" .repo/local_manifests/
repo sync -c -j8 --no-tags --fail-fast
repo manifest -r -o "$base/resolved.xml"

for arch in arm arm64; do
  webview="external/chromium-webview/prebuilt/$arch"
  git -C "$webview" lfs pull --include webview.apk
  git -C "$webview" lfs fsck --objects
  unzip -tq "$webview/webview.apk"
done

inputs="$kit/lg-ims-working-inputs.tar.gz"
python3 "$guide/tools/prepare-local-ims.py" "$tree" "$inputs" --upgrade-compat
python3 "$guide/tools/prepare-local-ims.py" "$tree" "$inputs" --upgrade-compat --verify-only
```

If the manifest comparison fails because the repository has moved to a newer release, use the preserved [v1.1.0 guide and tools](https://github.com/Magicolo/lg-g8-lineageos/tree/6e65fe467dffd04eda7dab67f0cc5a7a65c2fff9). Run `git -C "$guide" switch --detach 6e65fe467dffd04eda7dab67f0cc5a7a65c2fff9` in the cloned guide checkout, then resume from the manifest comparison. The Android source remains pinned by the v1.1.0 tag. Download all assets from that tag's release.

If the network failed, run the same `repo sync` command again inside `$tree` and keep the fetched objects. A failed LFS pull, a pointer in place of an APK, a missing pinned revision, or a failed IMS check needs to be fixed before compiling. See [Build troubleshooting](BUILD.md). The local manifest is required for the full build. The plain manifest is a preview without the local IMS integration.

The IMS input check verifies the whole archive and the six relevant checkout revisions. It installs only the expected files, reuses matching tracked files, and applies the CarrierConfig upgrade patch. Keep the APK and the versioned Java and native bindings together. [IMS layout and ABI](IMS.md)

## 3. Build a signed OTA

Use **one** of the commands below. Fresh keys are for a separate signing family and a clean install. An existing keyset is for a compatible OTA. Put keys in a mode-0700 directory on a private Linux filesystem, outside the checkout. Run a new-key build once and back up the key directory. If signing stops after key generation succeeds, omit `--new-keys` when resuming to reuse those keys.

```bash
# First build for a separate installation or distribution channel.
mkdir -m 700 -p "$HOME/.local/share/lg-g8"
keys="$HOME/.local/share/lg-g8/keys"
bash "$guide/tools/build-signed-alphaplus.sh" --new-keys \
  "$tree" "$inputs" "$keys" "$base/signed-output" 8

# Or build an update for the original signing family.
keys=/absolute/path/to/restored-private-keys
bash "$guide/tools/build-signed-alphaplus.sh" \
  "$tree" "$inputs" "$keys" "$base/signed-output" 8
```

The script compiles `lineage_alphaplus-cp2a-userdebug`, checks VINTF and notices, signs target-files, verifies both OTA signatures, and exports the boot-chain images after matching them to the OTA payload. Android build output is in `$tree/out`. Publication files appear in `$base/signed-output` after success. A failed build retains its scratch data and prints the path. Fix the error and rerun the command while keeping incremental output. For a new OTA the build timestamp and patch level must satisfy the installed build's upgrade rules. [Android OTA signing](https://source.android.com/docs/core/ota/sign_builds)

The first signing run creates the common Android APK keys, a vbmeta key, and a container/payload key pair for every non-presigned APEX in the target. Keep the same key directory for updates. The signing step checks for missing keys, including keys for newly introduced APEXes. [Maintaining the signing family](MAINTENANCE.md#qualify-the-candidate)

## 4. Verify before installing or publishing

Run this preflight even if you plan to use the ROM without Google apps. It checks the optional add-on against the image layout. Verify the room for the add-on again when its build or the platform changes.

```bash
gapps="$kit/MindTheGapps-17.0.0-arm64-20261022_132445.zip"
curl --fail --location --retry 3 --output "$gapps" "$release/$(basename "$gapps")"
output="$base/signed-output"
(cd "$output" && sha256sum -c SHA256SUMS)
export PATH="$tree/out/host/linux-x86/bin:$tree/prebuilts/jdk/jdk21/linux-x86/bin:$PATH"
python3 "$guide/tools/check-alphaplus-ota.py" \
  --ota "$output/lineage_alphaplus-ota.zip" \
  --target-files "$output/signed-target-files.zip" \
  --gapps "$gapps" \
  --ota-certificate "$output/ota-release.x509.pem" \
  --platform-certificate "$output/platform-release.x509.pem" \
  --require-release-keys --scratch-dir "$base"
```

Deploy to a spare first with the [validation matrix](VALIDATION.md). Keep its previous signed package and rollback paths until calls, upgrades and hardware pass. A new keyset requires a verified clean transition through recovery.

## Restore or inspect the existing release

For installation, use the exact hashes and the public OTA verifier in [Install](INSTALL.md). For developer archives or stock KDZ, download each numbered part from [the same release][release], plus `split-files.json` and `Join-ReleaseParts.ps1`. Follow [the asset reconstruction procedure](RELEASES.md). To re-export matching boot, DTBO and vbmeta, run `tools/extract-alphaplus-images.py OTA.zip signed-target-files.zip OUTPUT_DIRECTORY` with an empty output directory.

Repository verification has exercised the manifest and selected source sync, the exact IMS setup and the release artifacts. The release compiled in the development checkout. See [validation status](VALIDATION.md) for the tests still owed on a clean environment and a factory-locked handset.

[release]: https://github.com/Magicolo/lg-g8-lineageos/releases/tag/v1.1.0
