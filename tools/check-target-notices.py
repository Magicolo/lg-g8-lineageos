#!/usr/bin/env python3
"""Validate compressed partition NOTICE XML in an Android target-files ZIP."""

import argparse
from collections import Counter
import gzip
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target_files", type=Path, help="signed Android target-files ZIP")
    args = parser.parse_args()

    failed = False
    try:
        with ZipFile(args.target_files) as archive:
            for partition in ("SYSTEM", "VENDOR", "PRODUCT"):
                name = f"{partition}/etc/NOTICE.xml.gz"
                try:
                    notice = gzip.decompress(archive.read(name))
                except (KeyError, OSError, EOFError) as error:
                    print(f"FAIL {name}: {error}")
                    failed = True
                    continue
                try:
                    ET.fromstring(notice)
                except ET.ParseError as error:
                    controls = Counter(b for b in notice if b < 32 and b not in (9, 10, 13))
                    detail = ", ".join(f"0x{byte:02x}={count}" for byte, count in sorted(controls.items()))
                    print(f"FAIL {name}: {error}" + (f" ({detail})" if detail else ""))
                    failed = True
                else:
                    print(f"OK   {name}")
    except (OSError, BadZipFile) as error:
        parser.error(str(error))
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
