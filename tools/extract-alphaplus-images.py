#!/usr/bin/env python3
"""Extract the boot-chain images that match a Canadian G8 signed A/B payload."""

import argparse
import hashlib
from pathlib import Path
import struct
import sys
from zipfile import ZipFile


IMAGE_NAMES = ("boot", "dtbo", "vbmeta")


def varint(data, offset):
    value = 0
    for shift in range(0, 70, 7):
        if offset == len(data):
            break
        byte = data[offset]
        offset += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, offset
    raise ValueError("Invalid payload protobuf integer")


def protobuf(data):
    offset = 0
    while offset < len(data):
        key, offset = varint(data, offset)
        wire = key & 7
        if wire == 0:
            value, offset = varint(data, offset)
        else:
            if wire == 2:
                length, offset = varint(data, offset)
            elif wire in (1, 5):
                length = {1: 8, 5: 4}[wire]
            else:
                raise ValueError("Unexpected payload protobuf field type")
            value = data[offset:offset + length]
            offset += length
            if len(value) != length:
                raise ValueError("Truncated payload protobuf")
        yield key >> 3, value


def partitions(ota):
    with ota.open("payload.bin") as payload:
        magic, version, length, _signature_length = struct.unpack(">4sQQI", payload.read(24))
        if magic != b"CrAU" or version != 2 or not 0 < length <= 10_000_000:
            raise ValueError("Expected Android v2 A/B payload")
        metadata = payload.read(length)
        if len(metadata) != length:
            raise ValueError("Truncated A/B metadata")
    result = {}
    for field, entry in protobuf(metadata):
        if field == 13:
            details = dict(protobuf(entry))
            name = details[1].decode("ascii")
            if name in IMAGE_NAMES:
                if name in result:
                    raise ValueError(f"Duplicate partition in payload: {name}")
                info = dict(protobuf(details[7]))
                result[name] = (info[1], info[2].hex())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ota", type=Path)
    parser.add_argument("signed_target_files", type=Path)
    parser.add_argument("output", type=Path, help="existing output directory")
    args = parser.parse_args()
    with ZipFile(args.ota) as ota, ZipFile(args.signed_target_files) as target:
        metadata = dict(line.split("=", 1) for line in
                        ota.read("META-INF/com/android/metadata").decode().splitlines() if "=" in line)
        if (metadata.get("pre-device") != "alphaplus_lao_com"
                or metadata.get("ota-type") != "AB" or metadata.get("pre-build")):
            raise ValueError("Expected full Canadian G8 OTA")
        expected = partitions(ota)
        images = {}
        for name in IMAGE_NAMES:
            entry = target.read(f"IMAGES/{name}.img")
            if (len(entry), hashlib.sha256(entry).hexdigest()) != expected.get(name):
                raise ValueError(f"Image does not match payload: {name}")
            images[args.output / f"{name}.img"] = entry
    if not args.output.is_dir() or any(path.exists() for path in images):
        raise ValueError("Choose an existing directory with no boot-chain image files")
    for path, data in images.items():
        with path.open("xb") as output:
            output.write(data)
        digest = hashlib.sha256(data).hexdigest()
        print(f"{digest}  {path.name}")
        sums = args.output / "SHA256SUMS"
        if sums.is_file():
            with sums.open("a") as checksum_list:
                checksum_list.write(f"{digest}  {path.name}\n")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, struct.error) as error:
        sys.exit(f"Image extraction stopped: {error}")
