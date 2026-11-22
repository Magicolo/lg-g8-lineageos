#!/usr/bin/env python3
"""Prepare a LineageOS 24 v2 update index from a verified full A/B OTA."""

import argparse
from datetime import date
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zipfile import BadZipFile, ZIP_STORED, ZipFile


METADATA = "META-INF/com/android/metadata"


def read_metadata(archive):
    with ZipFile(archive) as package:
        for name in (METADATA, "metadata.pb", "payload.bin", "payload_properties.txt"):
            path = "META-INF/com/android/" + name if name == "metadata.pb" else name
            if package.namelist().count(path) != 1:
                raise ValueError(f"Expected one {path}")
        if package.getinfo("payload.bin").compress_type != ZIP_STORED:
            raise ValueError("A/B payload must be stored uncompressed")
        values = {}
        for line in package.read(METADATA).decode("utf-8").splitlines():
            key, separator, value = line.partition("=")
            if not separator or key in values:
                raise ValueError(f"Invalid or duplicate OTA metadata key: {key}")
            values[key] = value.strip()
    return values


def security_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"Invalid security patch level: {value!r}")
    return date.fromisoformat(value)


def make_index(args):
    props = read_metadata(args.ota)
    if props.get("ota-type") != "AB" or props.get("pre-build") or props.get("pre-build-incremental"):
        raise ValueError("Expected a full A/B OTA with no source build restriction")
    if any(key in props for key in ("ota-downgrade", "spl-downgrade", "ota-wipe")):
        raise ValueError("Wipe and downgrade packages are unsuitable for this channel")
    if props["pre-device"] != args.device:
        raise ValueError(f"OTA target {props['pre-device']!r} does not match {args.device!r}")
    sdk = int(props["post-sdk-level"])
    if sdk != args.sdk:
        raise ValueError(f"OTA SDK {sdk} does not match {args.sdk}")
    timestamp = int(props["post-timestamp"])
    if timestamp <= args.after_timestamp:
        raise ValueError("OTA timestamp must advance beyond the channel baseline")
    patch = props["post-security-patch-level"]
    if security_date(patch) < args.min_security_patch:
        raise ValueError("OTA security patch level is below the channel baseline")
    url = urlsplit(args.url)
    if (url.scheme != "https" or not url.hostname or url.username or url.password
            or url.query or url.fragment or unquote(url.path.rsplit("/", 1)[-1]) != args.ota.name):
        raise ValueError("Use a direct HTTPS URL ending in the exact OTA filename")

    result = subprocess.run(
        [args.verifier, str(args.certificate), str(args.ota)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="", file=sys.stderr)
    with args.ota.open("rb") as stream:
        sha256 = hashlib.file_digest(stream, "sha256").hexdigest()

    # Require the full download and the client's whole-package signature check.
    return [{
        "datetime": timestamp,
        "files": [{
            "filename": args.ota.name,
            "os_patch_level": patch,
            "os_sdk_level": sdk,
            "sha256": sha256,
            "size": args.ota.stat().st_size,
            "url": args.url,
        }],
        "type": args.release_type,
        "version": args.version,
    }]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ota", type=Path, required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--device", required=True, help="Exact signed OTA pre-device value")
    parser.add_argument("--sdk", type=int, required=True)
    parser.add_argument("--version", required=True, help="Device's ro.lineage.build.version")
    parser.add_argument("--release-type", required=True, help="Device's ro.lineage.releasetype")
    parser.add_argument("--after-timestamp", type=int, required=True)
    parser.add_argument("--min-security-patch", type=security_date, required=True)
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--verifier", default="check_ota_package_signature")
    args = parser.parse_args()
    try:
        print(json.dumps(make_index(args), indent=2))
    except subprocess.CalledProcessError as exc:
        sys.exit(f"OTA signature verification failed:\n{exc.stdout or ''}")
    except (BadZipFile, OSError, ValueError, KeyError) as exc:
        sys.exit(f"Update index refused: {exc}")


if __name__ == "__main__":
    main()
