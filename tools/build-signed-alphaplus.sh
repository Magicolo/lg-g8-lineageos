#!/usr/bin/env bash
# Compile, normalize notices, sign and verify the Canadian G8 build.
set -eo pipefail
umask 077
new_keys=false
source_edits=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --new-keys) new_keys=true ;;
        --source-edits) source_edits=(--source-edits) ;;
        --) shift; break ;;
        -*) echo "Unrecognized option: $1" >&2; exit 2 ;;
        *) break ;;
    esac
    shift
done
if [[ $# != 5 ]]; then
    echo "Usage: $0 [--new-keys] [--source-edits] ANDROID_CHECKOUT IMS_INPUT_ARCHIVE KEY_DIRECTORY NEW_OUTPUT_DIRECTORY JOBS" >&2
    exit 2
fi
tools=$(cd "$(dirname "$0")" && pwd)
tree=$(realpath "$1")
inputs=$(realpath "$2")
keys=$(realpath -m "$3")
output=$(realpath -m "$4")
jobs=$5
if [[ ! "$jobs" =~ ^[1-9][0-9]*$ || -e "$output" ]]; then
    echo "Choose a positive job count and a new output directory." >&2
    exit 2
fi
if "$new_keys"; then
    if [[ -e "$keys" || ! -d "$(dirname "$keys")" ]]; then
        echo "Choose a new key directory with an existing parent." >&2
        exit 2
    fi
else
    if [[ ! -s "$keys/releasekey.pk8" || ! -s "$keys/releasekey.x509.pem" ]]; then
        echo "Supply the existing signing family or explicitly request --new-keys." >&2
        exit 2
    fi
fi
python3 "$tools/prepare-local-ims.py" "$tree" "$inputs" --upgrade-compat --verify-only "${source_edits[@]}"
mkdir -m 700 -p "$(dirname "$output")"
scratch=$(mktemp -d "$(dirname "$output")/.g8-release-build.XXXXXX")
trap 'printf "Build inputs and logs retained in %s\n" "$scratch"' EXIT
cd "$tree"
export BUILD_USERNAME=builder BUILD_HOSTNAME=android-build OUT_DIR=out
export BUILD_DATETIME="${BUILD_DATETIME:-$(date +%s)}"
[[ "$BUILD_DATETIME" =~ ^[0-9]+$ && "$BUILD_DATETIME" -gt 1795454921 ]]
export BUILD_NUMBER="$BUILD_DATETIME"
source build/envsetup.sh
lunch lineage_alphaplus-cp2a-userdebug
m -j"$jobs" target-files-package otatools check_ota_package_signature
product=out/target/product/alphaplus
target="$product/obj/PACKAGING/target_files_intermediates/lineage_alphaplus-target_files"
host="$PWD/out/host/linux-x86"
export PATH="$host/bin:$PATH"
unsigned="$scratch/unsigned-target-files.zip"
if [[ -s "$target.zip" ]]; then
    cp --reflink=auto "$target.zip" "$unsigned"
else
    soong_zip -d -o "$unsigned" -C "$target" -r "$target.zip.list" -sha256
fi
python3 "$tools/check-target-notices.py" "$unsigned" --stage-normalized-to "$scratch/notices"
if [[ -d "$scratch/notices" ]]; then
    (cd "$scratch/notices" && find . -type f -name NOTICE.xml.gz -print | LC_ALL=C sort | zip -q "$unsigned" -@)
fi
grep -Fx COMPATIBLE "$product/obj/PACKAGING/check_vintf_all_intermediates/check_vintf_compatible.log"
if "$new_keys"; then
    python3 "$tools/signing-inputs.py" "$unsigned" --new-keys "$keys"
fi
python3 "$tools/normalize-target-paths.py" "$unsigned" "$tree" "$keys" \
    --build-fingerprint "$product/build_fingerprint-lineage_alphaplus.txt"
bash "$tools/sign-alphaplus-release.sh" "$unsigned" "$keys" "$scratch/signed"
python3 "$tools/normalize-target-paths.py" "$scratch/signed/signed-target-files.zip" "$tree" "$keys"
install -m 644 "$keys/platform.x509.pem" "$scratch/signed/platform-release.x509.pem"
install -m 644 "$product/obj/KERNEL_OBJ/.config" "$scratch/signed/kernel.config"
(cd "$scratch/signed" && sha256sum lineage_alphaplus-ota.zip signed-target-files.zip \
    ota-release.x509.pem platform-release.x509.pem kernel.config > SHA256SUMS)
python3 "$tools/check-target-notices.py" "$scratch/signed/signed-target-files.zip"
python3 "$tools/extract-alphaplus-images.py" "$scratch/signed/lineage_alphaplus-ota.zip" "$scratch/signed/signed-target-files.zip" "$scratch/signed"
mv -T "$scratch/signed" "$output"
