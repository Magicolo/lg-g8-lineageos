#!/usr/bin/env bash
# Compile, normalize notices, sign and verify the Canadian G8 build.
set -eo pipefail
umask 077
if [[ $# != 5 ]]; then
    echo "Usage: $0 ANDROID_CHECKOUT IMS_INPUT_ARCHIVE KEY_DIRECTORY NEW_OUTPUT_DIRECTORY JOBS" >&2
    exit 2
fi
tools=$(cd "$(dirname "$0")" && pwd)
tree=$(realpath "$1")
inputs=$(realpath "$2")
keys=$(realpath "$3")
output=$(realpath -m "$4")
jobs=$5
[[ "$jobs" =~ ^[1-9][0-9]*$ && ! -e "$output" ]]
python3 "$tools/prepare-local-ims.py" "$tree" "$inputs" --upgrade-compat --verify-only
mkdir -m 700 -p "$(dirname "$output")"
scratch=$(mktemp -d "$(dirname "$output")/.g8-release-build.XXXXXX")
trap 'printf "Build inputs and logs retained in %s\n" "$scratch"' EXIT
cd "$tree"
export BUILD_USERNAME=builder BUILD_HOSTNAME=android-build
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
bash "$tools/sign-alphaplus-release.sh" "$unsigned" "$keys" "$scratch/signed"
python3 "$tools/check-target-notices.py" "$scratch/signed/signed-target-files.zip"
python3 "$tools/extract-alphaplus-images.py" "$scratch/signed/lineage_alphaplus-ota.zip" "$scratch/signed/signed-target-files.zip" "$scratch/signed"
mv -T "$scratch/signed" "$output"
