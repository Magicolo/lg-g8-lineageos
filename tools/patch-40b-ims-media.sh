#!/usr/bin/env bash
# Reproduce the Android 17 media ABI adaptation from the exact stock 40b library.
set -euo pipefail
if [[ $# != 2 || ! -f "$1" || -e "$2" || -L "$2" ]]; then
    echo "Usage: $0 STOCK_40B_LIBIMS_MMPF NEW_OUTPUT_FILE" >&2
    exit 2
fi
stock=$(realpath "$1")
blob=$(realpath -m "$2")
patchelf_first=${PATCHELF_0_17_2:-patchelf-0_17_2}
patchelf=${PATCHELF:-patchelf}
llvm_readelf=${LLVM_READELF:-llvm-readelf}
stock_sha=0b0a50d4e5cf140b084dbf4acb566e240dd50883448e49b353b1c28b276b18e2
prepared_sha=449806fb069654839c32fd5f5cb3f311fd0a157e74aea245695432d8a28dfd69
needed_sha=c5a5606261f4e032bc751620369cb5f38a46efb541091634c1a3ad3471cc69fe
final_sha=588ca47049ab44df484867699529231b9d0fef83320aa4b3337ee2c04e4a3dfd

printf '%s  %s\n' "$stock_sha" "$stock" | sha256sum -c -
work=$(mktemp -d "$(dirname "$blob")/.media-abi.XXXXXX")
trap 'rm -f -- "$work/prepared.so" "$work/rewritten.so" "$work/before.txt" "$work/after.txt"; rmdir -- "$work"' EXIT
cp -- "$stock" "$work/prepared.so"
"$patchelf_first" --add-needed libalphaplus_lgims_compat.so "$work/prepared.so"
printf '%s  %s\n' "$prepared_sha" "$work/prepared.so" | sha256sum -c -
cp -- "$work/prepared.so" "$work/rewritten.so"
"$patchelf" --add-needed libaudiobase.so "$work/rewritten.so"
printf '%s  %s\n' "$needed_sha" "$work/rewritten.so" | sha256sum -c -
"$llvm_readelf" --relocations "$work/prepared.so" > "$work/before.txt"
# Keep dynamic symbol indices fixed. Android packed relocations refer to them.
python3 - "$work/rewritten.so" "$work/before.txt" <<'PY'
from pathlib import Path
import struct
import sys

blob_path, relocations_path = map(Path, sys.argv[1:])
blob = bytearray(blob_path.read_bytes())
relocations = relocations_path.read_text()
symbol_table = 0xF0058
string_table = 0x120000
symbol_entry_size = 24
renames = {
    191: ('_ZN7android10BufferItemC1Ev', 'lg_ims_bi_construct'),
    192: ('_ZN7android10BufferItemD1Ev', 'lg_ims_bi_destroy'),
    210: ('_ZN7android18BufferItemConsumer13acquireBufferEPNS_10BufferItemElb',
          'lg_ims_bi_acquire'),
    211: ('_ZN7android18BufferItemConsumer13releaseBufferERKNS_10BufferItemERKNS_2spINS_5FenceEEE',
          'lg_ims_bi_release'),
}
for index, (old_name, new_name) in renames.items():
    symbol_offset = symbol_table + index * symbol_entry_size
    name_offset, _, _, section = struct.unpack_from('<IBBH', blob, symbol_offset)
    start = string_table + name_offset
    end = blob.index(0, start)
    if section != 0 or blob[start:end] != old_name.encode() or len(new_name) > end - start:
        raise SystemExit(f'Unexpected import at dynamic symbol index {index}')
    blob[start:end] = new_name.encode().ljust(end - start, b'\0')
    relocations = relocations.replace(old_name, new_name)
blob_path.write_bytes(blob)
relocations_path.write_text(relocations)
PY
"$llvm_readelf" --relocations "$work/rewritten.so" > "$work/after.txt"
cmp "$work/before.txt" "$work/after.txt"
"$llvm_readelf" --dynamic-table "$work/rewritten.so" | grep -F '[libaudiobase.so]'
printf '%s  %s\n' "$final_sha" "$work/rewritten.so" | sha256sum -c -
# The hard link fails if another process created the output in the meantime.
ln -T -- "$work/rewritten.so" "$blob"
