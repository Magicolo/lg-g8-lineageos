#!/usr/bin/env bash
# Sign an already verified G8 target-files ZIP with the project keyset.
set -euo pipefail
umask 077

if [[ $# != 3 ]]; then
    echo "Usage: $0 target-files.zip key-directory output-directory" >&2
    exit 2
fi
source_zip=$(realpath "$1")
keys=$(realpath "$2")
output=$(realpath -m "$3")
host="$PWD/out/host/linux-x86"
certs=build/make/target/product/security

[[ -f "$source_zip" && -d "$keys" && ! -e "$output" ]]
[[ $(stat -c %a "$keys") == 700 ]]
export PATH="$host/bin:$PWD/prebuilts/jdk/jdk21/linux-x86/bin:$PATH"

for name in releasekey platform shared media networkstack sdk_sandbox bluetooth nfc; do
    [[ -s "$keys/$name.pk8" && -s "$keys/$name.x509.pem" ]]
done
[[ -s "$keys/vbmeta.pem" ]]
for name in testkey platform shared media networkstack sdk_sandbox bluetooth nfc; do
    release_name=$name
    [[ $name != testkey ]] || release_name=releasekey
    if cmp -s "$keys/$release_name.x509.pem" "$certs/$name.x509.pem"; then
        echo "Refusing the public AOSP $name certificate" >&2
        exit 2
    fi
done

apex_names=$(python3 - "$source_zip" <<'PY'
import re
import shlex
import sys
from zipfile import ZipFile

with ZipFile(sys.argv[1]) as source:
    metadata = source.read("META/apexkeys.txt").decode().splitlines()
for line in metadata:
    fields = dict(field.split("=", 1) for field in shlex.split(line) if "=" in field)
    if not fields:
        continue
    name = fields["name"]
    if not re.fullmatch(r"[A-Za-z0-9_.]+\.apex", name):
        sys.exit(f"Unexpected APEX name: {name}")
    payload = fields["private_key"] == "PRESIGNED"
    container = fields["container_private_key"] == "PRESIGNED"
    if payload != container:
        sys.exit(f"Unexpected mixed signing of {name}")
    if not payload:
        print(name)
PY
)
[[ -n "$apex_names" ]]
args=(-d "$keys" -o -k "$certs/nfc=$keys/nfc"
      --avb_vbmeta_key "$keys/vbmeta.pem" --avb_vbmeta_algorithm SHA256_RSA4096)
while IFS= read -r name; do
    base="$keys/apex/$name"
    [[ -s "$base.pem" && -s "$base.pk8" && -s "$base.x509.pem" ]]
    args+=(--extra_apks "$name=$base" --extra_apex_payload_key "$name=$base.pem")
done <<< "$apex_names"

mkdir -m 700 -p "$(dirname "$output")"
scratch=$(mktemp -d "$(dirname "$output")/.sign-alphaplus.XXXXXX")
trap 'if [[ -d "$scratch" ]]; then echo "Signing work retained at $scratch" >&2; fi' EXIT
sign_target_files_apks --threads 4 "${args[@]}" "$source_zip" "$scratch/signed-target-files.zip"
ota_from_target_files -k "$keys/releasekey" "$scratch/signed-target-files.zip" "$scratch/lineage_alphaplus-ota.zip"
check_ota_package_signature "$keys/releasekey.x509.pem" "$scratch/lineage_alphaplus-ota.zip"
install -m 644 "$keys/releasekey.x509.pem" "$scratch/ota-release.x509.pem"
(cd "$scratch" && sha256sum lineage_alphaplus-ota.zip signed-target-files.zip ota-release.x509.pem > SHA256SUMS)
mv -T "$scratch" "$output"
