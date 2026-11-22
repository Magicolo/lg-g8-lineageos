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
    parser.add_argument(
        "--stage-normalized-to", type=Path,
        help="stage corrected notice files in a new directory without changing the input ZIP",
    )
    args = parser.parse_args()

    corrections = {}
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
                checked = notice.replace(b"\x0c", b"\n") if args.stage_normalized_to else notice
                try:
                    ET.fromstring(checked)
                except ET.ParseError as error:
                    controls = Counter(b for b in checked if b < 32 and b not in (9, 10, 13))
                    detail = ", ".join(
                        f"0x{byte:02x}={count}" for byte, count in sorted(controls.items())
                    )
                    print(f"FAIL {name}: {error}" + (f" ({detail})" if detail else ""))
                    failed = True
                    continue
                if checked != notice:
                    corrections[name] = checked
                    print(f"STAGE {name}: normalized {notice.count(bytes([12]))} form feeds")
                else:
                    print(f"OK   {name}")
            if corrections and not failed:
                args.stage_normalized_to.mkdir()
                for name, corrected in corrections.items():
                    output = args.stage_normalized_to / name
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_bytes(gzip.compress(corrected, mtime=0))
    except (OSError, BadZipFile) as error:
        parser.error(str(error))
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
