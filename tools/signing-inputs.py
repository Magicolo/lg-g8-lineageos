#!/usr/bin/env python3
"""List signable APEXes or create a private signing family for an LG G8 build."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from zipfile import BadZipFile, ZipFile


APK_KEYS = ("releasekey", "platform", "shared", "media", "networkstack",
            "sdk_sandbox", "bluetooth", "nfc")


def signable_apexes(target_files):
    with ZipFile(target_files) as source:
        metadata = source.read("META/apexkeys.txt").decode().splitlines()
    seen = set()
    names = []
    for line in metadata:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = dict(field.split("=", 1) for field in shlex.split(line))
        name = fields["name"]
        if not re.fullmatch(r"[A-Za-z0-9_.]+\.apex", name) or name in seen:
            raise ValueError(f"Invalid or duplicate APEX name: {name}")
        seen.add(name)
        payload = fields["private_key"] == "PRESIGNED"
        container = fields["container_private_key"] == "PRESIGNED"
        if payload != container:
            raise ValueError(f"Unexpected mixed signing of {name}")
        if not payload:
            names.append(name)
    if not names:
        raise ValueError("No signable APEX packages in META/apexkeys.txt")
    return names


def openssl(*args, data=None):
    result = subprocess.run(["openssl", *args], input=data, capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace").strip())
    return result.stdout


def rsa(bits):
    return openssl("genpkey", "-algorithm", "RSA", "-pkeyopt", f"rsa_keygen_bits:{bits}")


def apk_key(directory, name):
    private = rsa(2048)
    (directory / f"{name}.pk8").write_bytes(
        openssl("pkcs8", "-topk8", "-nocrypt", "-outform", "DER", data=private))
    (directory / f"{name}.x509.pem").write_bytes(
        openssl("req", "-new", "-x509", "-sha256", "-days", "3650", "-key", "/dev/stdin",
                "-subj", f"/CN=LG G8 Android {name[:42]}/", data=private))


def apex_key(directory, name):
    apk_key(directory, name)
    (directory / f"{name}.pem").write_bytes(rsa(4096))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_files", type=Path)
    parser.add_argument("--new-keys", type=Path, help="new private directory on a Linux filesystem")
    args = parser.parse_args()
    names = signable_apexes(args.target_files)
    if args.new_keys is None:
        print("\n".join(names))
        return

    keys = args.new_keys
    os.umask(0o077)
    keys.mkdir(mode=0o700)
    try:
        apex = keys / "apex"
        apex.mkdir()
        for name in APK_KEYS:
            apk_key(keys, name)
        (keys / "vbmeta.pem").write_bytes(rsa(4096))
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda name: apex_key(apex, name), names))
    except (OSError, ValueError) as error:
        raise ValueError(f"Key generation did not finish. Treat {keys} as incomplete: {error}") from error
    print(f"Created a new signing family with {len(names)} APEX key pairs.")
    print(openssl("x509", "-in", str(keys / "releasekey.x509.pem"), "-noout",
                  "-fingerprint", "-sha256").decode().strip())


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, BadZipFile) as error:
        sys.exit(f"Signing input check stopped: {error}")
