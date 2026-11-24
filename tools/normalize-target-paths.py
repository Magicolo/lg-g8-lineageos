#!/usr/bin/env python3
"""Make machine-specific paths in signed target-files metadata portable."""

import argparse
from pathlib import Path
import subprocess
import tempfile
from zipfile import ZipFile


ENTRY = "META/misc_info.txt"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_files", type=Path)
    parser.add_argument("android_checkout", type=Path)
    parser.add_argument("key_directory", type=Path)
    args = parser.parse_args()
    archive = args.target_files.resolve(strict=True)
    prefixes = (
        (str(args.key_directory.resolve(strict=True)) + "/", "release-keys/"),
        (str(args.android_checkout.resolve(strict=True)) + "/", ""),
    )
    with ZipFile(archive) as target:
        if target.namelist().count(ENTRY) != 1:
            raise ValueError("Expected exactly one target-files metadata entry")
        original = target.read(ENTRY).decode("utf-8")
    updated = original
    for prefix, replacement in prefixes:
        updated = updated.replace(prefix, replacement)
    if updated == original:
        return
    with tempfile.TemporaryDirectory() as work:
        path = Path(work) / ENTRY
        path.parent.mkdir()
        path.write_text(updated)
        subprocess.run(["zip", "-q", str(archive), ENTRY], cwd=work, check=True)
    with ZipFile(archive) as target:
        if target.namelist().count(ENTRY) != 1 or target.read(ENTRY).decode("utf-8") != updated:
            raise ValueError("Modified metadata was not saved")
    print("Normalized signing input paths in the target-files metadata; image entries unchanged.")


if __name__ == "__main__":
    main()
