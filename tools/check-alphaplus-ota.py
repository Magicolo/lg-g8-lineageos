#!/usr/bin/env python3
"""Check the Canadian G8 Android 17 OTA and estimate MindTheGapps fit offline."""

import argparse
from contextlib import nullcontext
import hashlib
from io import BytesIO
from pathlib import Path, PurePosixPath
import re
import shutil
import ssl
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import zipfile


DEVICE = "alphaplus_lao_com"
MIN_SECURITY_PATCH = "2026-11-01"
PARTITION_BYTES = {
    "boot": 100663296,
    "dtbo": 25165824,
    "product": 2147483648,
    "system": 4022337536,
    "vendor": 1782579200,
}
EXPECTED_AB = set(PARTITION_BYTES) | {"vbmeta"}
HEADER_MAGIC = {"boot": b"ANDROID!", "dtbo": bytes.fromhex("d7b7ab1e"), "vbmeta": b"AVB0"}
SPARSE_MAGIC = 0xED26FF3A
GAPPS_SHA256 = "a6844eeb2613541558237e467b20feb01f8b45b2ebab0109834140ea59b6ca4d"
INSTALLER_MARGIN = 10240 * 1024
AOSP_TEST_OTA_SHA256 = "a40da80a59d170caa950cf15c18c454d47a39b26989d8b640ecd745ba71bf5dc"



class DirectoryTarget:
    """Expose the same image and metadata reads on the target-files directory."""

    def __init__(self, root):
        self.root = root

    def open(self, entry):
        return (self.root / entry).open("rb")

    def read(self, entry):
        return (self.root / entry).read_bytes()

    def getinfo(self, entry):
        return SimpleNamespace(file_size=(self.root / entry).stat().st_size)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def properties(archive, entry):
    return dict(
        line.split("=", 1)
        for line in archive.read(entry).decode("utf-8").splitlines()
        if "=" in line and not line.startswith("#")
    )


def system_build_properties(target):
    try:
        return properties(target, "SYSTEM/etc/build.prop")
    except (KeyError, FileNotFoundError):
        return properties(target, "SYSTEM/build.prop")


def check_release_keys(target, build_props, certificate):
    tags = build_props.get("ro.build.tags", "")
    require("release-keys" in tags and "test-keys" not in tags,
            f"Expected release-key build tags, found {tags!r}")
    expected = ssl.PEM_cert_to_DER_cert(certificate.read_text(encoding="ascii"))
    require(hashlib.sha256(expected).hexdigest() != AOSP_TEST_OTA_SHA256,
            "The supplied OTA certificate is the public AOSP test certificate")
    for location in ("SYSTEM/etc/security/otacerts.zip",
                     "BOOT/RAMDISK/system/etc/security/otacerts.zip"):
        with zipfile.ZipFile(BytesIO(target.read(location))) as store:
            trusted = {
                ssl.PEM_cert_to_DER_cert(store.read(name).decode("ascii"))
                for name in store.namelist() if not name.endswith("/")
            }
        require(expected in trusted, f"Release OTA certificate missing from {location}")
        require(all(hashlib.sha256(cert).hexdigest() != AOSP_TEST_OTA_SHA256 for cert in trusted),
                f"Public AOSP test certificate remains trusted in {location}")
    print("Release-key tags and Android/recovery OTA trust verified")


def check_metadata(ota, target, build_props):
    ota_props = properties(ota, "META-INF/com/android/metadata")
    require(ota_props.get("ota-type") == "AB", "Expected a physical A/B OTA")
    require(ota_props.get("post-sdk-level") == "37", "Expected Android 17 SDK 37")
    require(
        DEVICE in re.split(r"[|;]", ota_props.get("pre-device", "")),
        f"OTA metadata does not name {DEVICE}",
    )
    require(not ota_props.get("pre-build"), "Expected a full OTA without a source build requirement")
    security_patch = ota_props.get("post-security-patch-level", "")
    require(
        re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", security_patch)
        and security_patch >= MIN_SECURITY_PATCH,
        f"Unexpected framework security patch level: {security_patch!r}",
    )
    product = set(target.read("META/ab_partitions.txt").decode("utf-8").split())
    require(product == EXPECTED_AB, f"Unexpected target-file A/B layout: {sorted(product)}")
    fingerprint = build_props.get("ro.build.fingerprint") or build_props.get("ro.system.build.fingerprint")
    require(
        fingerprint and fingerprint in re.split(r"[|;]", ota_props.get("post-build", "")),
        f"OTA and target-files fingerprints differ: {fingerprint!r}",
    )
    incremental = build_props.get("ro.build.version.incremental")
    require(
        incremental and incremental == ota_props.get("post-build-incremental"),
        f"OTA and target-files incrementals differ: {incremental!r}",
    )
    timestamp = build_props.get("ro.build.date.utc")
    require(
        timestamp and timestamp == ota_props.get("post-timestamp"),
        f"OTA and target-files timestamps differ: {timestamp!r}",
    )
    require(
        security_patch == build_props.get("ro.build.version.security_patch"),
        "OTA and target-files framework security patch levels differ",
    )
    require(
        {"payload.bin", "payload_properties.txt"}.issubset(ota.namelist()),
        "Missing A/B OTA payload",
    )
    print(f"Target: {DEVICE}, SDK 37, framework security patch {security_patch}")
    print(f"Matching build fingerprint: {fingerprint}")


def check_image_headers(target):
    for part in sorted(EXPECTED_AB):
        entry = f"IMAGES/{part}.img"
        info = target.getinfo(entry)
        with target.open(entry) as image:
            header = image.read(28)
        require(len(header) == 28, f"{part} header is incomplete")
        if part in HEADER_MAGIC:
            require(header.startswith(HEADER_MAGIC[part]), f"Unexpected {part} image header")
        if struct.unpack_from("<I", header)[0] == SPARSE_MAGIC:
            block_size, blocks = struct.unpack_from("<II", header, 12)
            require(block_size > 0 and blocks > 0, f"Invalid {part} sparse size")
            expanded = block_size * blocks
        else:
            expanded = info.file_size
        if part in PARTITION_BYTES:
            require(expanded <= PARTITION_BYTES[part], f"{part} exceeds its physical partition")
            print(f"{part}: {expanded:,} of {PARTITION_BYTES[part]:,} bytes")
        else:
            print(f"{part}: valid header, {expanded:,} bytes")


def check_space(target, gapps, partition, scratch, simg2img):
    entry = f"IMAGES/{partition}.img"
    packed = scratch / f"{partition}.img"
    raw = scratch / f"{partition}.raw"
    try:
        with target.open(entry) as source, packed.open("wb") as out:
            shutil.copyfileobj(source, out, length=1024 * 1024)
        with packed.open("rb") as image:
            magic = image.read(4)
        if magic == struct.pack("<I", SPARSE_MAGIC):
            subprocess.run([simg2img, packed, raw], check=True)
            packed.unlink()
        else:
            packed.rename(raw)

        fs = subprocess.check_output(
            ["dumpe2fs", "-h", raw], env={"LC_ALL": "C", "PATH": "/usr/sbin:/usr/bin:/bin"},
            stderr=subprocess.DEVNULL, text=True,
        )
        fields = dict(line.split(":", 1) for line in fs.splitlines() if ":" in line)
        block_size = int(fields["Block size"])
        free_bytes = (int(fields["Free blocks"]) - int(fields["Reserved block count"])) * block_size
        free_inodes = int(fields["Free inodes"])
        if partition == "product":
            files = [(p.filename.removeprefix("system/product/"), p.file_size)
                     for p in gapps.infolist()
                     if p.filename.startswith("system/product/") and not p.is_dir()]
        else:
            files = [(p.filename.removeprefix("system/"), p.file_size)
                     for p in gapps.infolist() if p.filename.startswith("system/")
                     and not p.filename.startswith("system/product/") and not p.is_dir()]
        require(files, f"No GApps files queued against {partition}")
        parents = {parent for name, _ in files for parent in PurePosixPath(name).parents}
        needed_bytes = sum(((n + block_size - 1) // block_size) * block_size for _, n in files)
        needed_bytes += len(parents) * block_size + INSTALLER_MARGIN
        needed_inodes = len(files) + len(parents)
        print(f"{partition} ext4: {free_bytes:,} available bytes, "
              f"{needed_bytes:,} estimated required, {free_inodes:,} free inodes, "
              f"{needed_inodes:,} estimated required")
        return free_bytes >= needed_bytes and free_inodes >= needed_inodes
    finally:
        packed.unlink(missing_ok=True)
        raw.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ota", type=Path, required=True)
    parser.add_argument("--target-files", type=Path, required=True, help="target-files directory or ZIP")
    parser.add_argument("--gapps", type=Path, required=True, help="verified MindTheGapps 17 ARM64 ZIP")
    parser.add_argument("--ota-certificate", type=Path, required=True)
    parser.add_argument("--require-release-keys", action="store_true",
                        help="require release build tags and matching private-key OTA trust stores")
    parser.add_argument("--scratch-dir", type=Path, required=True, help="disk-backed existing directory")
    parser.add_argument("--simg2img", default="simg2img")
    parser.add_argument("--ota-verifier", default="check_ota_package_signature")
    args = parser.parse_args()
    require(digest(args.gapps) == GAPPS_SHA256, "MindTheGapps ZIP differs from the verified package")
    if args.target_files.is_dir():
        target_context = nullcontext(DirectoryTarget(args.target_files))
    else:
        target_context = zipfile.ZipFile(args.target_files)
    with zipfile.ZipFile(args.ota) as ota, target_context as target:
        build_props = system_build_properties(target)
        check_metadata(ota, target, build_props)
        if args.require_release_keys:
            check_release_keys(target, build_props, args.ota_certificate)
        check_image_headers(target)
        with zipfile.ZipFile(args.gapps) as gapps:
            require("system/product/apex/com.google.android.gmssystem.prodvic.apex" in gapps.namelist(),
                    "Expected Google Play Services APEX missing")
            with tempfile.TemporaryDirectory(prefix="alphaplus-preflight-", dir=args.scratch_dir) as temp:
                results = [check_space(target, gapps, partition, Path(temp), args.simg2img)
                           for partition in ("product", "system")]
    sys.stdout.flush()
    subprocess.run([args.ota_verifier, args.ota_certificate, args.ota], check=True)
    print(f"OTA SHA-256: {digest(args.ota)}")
    require(all(results), "MindTheGapps exceeds the conservative estimate. Inspect installer reclaim and actual mount layout.")
    print("Offline preflight passed. Verify recovery slot, image/AVB behavior, and GApps activation on-device.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, zipfile.BadZipFile, subprocess.CalledProcessError) as exc:
        sys.exit(f"Preflight stopped: {exc}")
