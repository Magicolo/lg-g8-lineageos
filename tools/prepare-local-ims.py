#!/usr/bin/env python3
"""Stage the verified IMS inputs in the pinned public checkout."""

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
from xml.etree import ElementTree


INPUT_SHA256 = "b8dc7e0e6097a66f0eba895c0d9e67c58953e66463e2d1ff6c76670a1b5e4094"
PIN_PATHS = (
    "device/lge/alphaplus", "device/lge/sm8150-common", "kernel/lge/sm8150",
    "frameworks/av", "packages/apps/CarrierConfig", "frameworks/opt/net/ims",
)
SOURCE_SUFFIXES = {".aidl", ".bp", ".cpp", ".java", ".properties", ".rc", ".xml"}
GUIDE = Path(__file__).resolve().parents[1]
TOP_LEVEL = ("device/lge/alphaplus/ims/", "vendor/lge/alphaplus-ims/")
PROFILE = "device/lge/alphaplus/ims/config/compat-profile.properties"
LG_IMS_FEATURE = "frameworks/opt/net/ims/src/java/com/android/ims/LGImsFeature.java"
PATCH = GUIDE / "ims/carrierconfig-upgrade-only.patch"


def git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)


def check_archive(archive):
    with archive.open("rb") as source:
        if hashlib.file_digest(source, "sha256").hexdigest() != INPUT_SHA256:
            raise ValueError("IMS input archive does not match the released checkpoint")


def effective_properties(data):
    return [line.strip() for line in data.splitlines()
            if line.strip() and not line.lstrip().startswith(b"#")]


def pins():
    projects = ElementTree.parse(GUIDE / "manifest.xml").getroot().findall("project")
    overlays = ElementTree.parse(GUIDE / "ims/local-manifest.xml").getroot().findall("extend-project")
    by_path = {project.get("path") or project.attrib["name"]: project.attrib["revision"]
               for project in projects + overlays}
    for project in PIN_PATHS:
        yield project, by_path[project]


def stage(tree, archive, upgrade, verify_only, source_edits):
    for project, revision in pins():
        result = git(tree / project, "rev-parse", "HEAD")
        if result.returncode or result.stdout.strip() != revision:
            raise ValueError(f"{project}: checkout must be at {revision}")
    patches = tree / "packages/apps/CarrierConfig"
    if upgrade and git(patches, "apply", "--reverse", "--check", PATCH).returncode:
        if git(patches, "apply", "--check", PATCH).returncode:
            raise ValueError("CarrierConfig migration patch does not apply cleanly")
        apply_upgrade = True
    else:
        apply_upgrade = False

    check_archive(archive)
    pending = []
    with tarfile.open(archive) as files:
        for member in files.getmembers():
            if member.isdir() or member.name.startswith("migration/"):
                continue
            name = member.name
            parts = PurePosixPath(name)
            if (not member.isfile() or parts.is_absolute() or ".." in parts.parts
                    or not (name == LG_IMS_FEATURE or name.startswith(TOP_LEVEL))):
                raise ValueError(f"Unexpected checkpoint member: {name}")
            destination = tree / name
            if not destination.resolve().is_relative_to(tree) or destination.is_symlink():
                raise ValueError(f"Refusing escaped or linked destination: {name}")
            data = files.extractfile(member).read()
            if destination.exists():
                if not destination.is_file():
                    raise ValueError(f"Expected a regular file: {name}")
                current = destination.read_bytes()
                if name == PROFILE and effective_properties(current) == effective_properties(data):
                    continue
                if current != data:
                    if source_edits and destination.suffix in SOURCE_SUFFIXES:
                        print(f"Using local source edit: {name}")
                        continue
                    raise ValueError(f"Existing file differs from checkpoint: {name}")
            else:
                pending.append((destination, data, member.mode & 0o777))
    if not verify_only:
        if apply_upgrade:
            git_result = git(patches, "apply", PATCH)
            if git_result.returncode:
                raise ValueError(git_result.stderr.strip())
        for destination, data, mode in pending:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as output:
                output.write(data)
            destination.chmod(mode)
    action = "were required" if verify_only else "were staged"
    print(f"{len(pending)} missing IMS files {action}. Existing files matched.")
    if verify_only and (pending or apply_upgrade):
        raise ValueError("The checkout is not fully prepared")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path, help="root of the pinned Android checkout")
    parser.add_argument("input_archive", type=Path, help="verified lg-ims-working-inputs.tar.gz")
    parser.add_argument("--upgrade-compat", action="store_true",
                        help="carry the versionCode used on the tested signed release")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--source-edits", action="store_true",
                        help="allow local edits to the staged text sources, preserving binary checks")
    args = parser.parse_args()
    stage(args.checkout.resolve(), args.input_archive, args.upgrade_compat, args.verify_only,
          args.source_edits)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, ElementTree.ParseError, tarfile.TarError) as error:
        sys.exit(f"IMS preparation stopped: {error}")
