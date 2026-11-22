#!/usr/bin/env python3
"""Compare pinned Android source revisions against their configured upstream refs."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree


AREAS = (
    "android", "build/make", "build/release", "art", "bionic", "system/core",
    "system/sepolicy", "frameworks/base", "frameworks/av", "frameworks/native",
    "frameworks/opt/telephony", "frameworks/opt/net/ims", "packages/apps/CarrierConfig",
    "packages/apps/Settings", "packages/apps/Updater", "packages/services/Telephony",
    "packages/modules/", "external/chromium-webview/", "bootable/recovery",
    "system/update_engine", "external/avb", "vendor/lineage", "device/lge/",
    "kernel/lge/", "vendor/lge/", "hardware/lge", "device/lineage/sepolicy",
)


def upstream(checkout, project, default_remote):
    path = project.get("path") or project.attrib["name"]
    pinned = project.attrib["revision"]
    ref = project.get("upstream") or project.get("dest-branch")
    if not ref:
        return path, pinned, "-", "-", "NO_REF"
    if not ref.startswith("refs/"):
        ref = "refs/heads/" + ref
    remote = project.get("remote", default_remote)
    try:
        repository = checkout / path
        if repository == checkout or checkout not in repository.resolve().parents:
            raise ValueError("Manifest path escapes checkout")
        url = subprocess.check_output(
            ["git", "-C", str(repository), "remote", "get-url", remote],
            text=True, stderr=subprocess.DEVNULL, timeout=10,
        ).strip()
        if urlsplit(url).scheme != "https":
            raise ValueError("No public HTTPS upstream")
        result = subprocess.check_output(
            ["git", "ls-remote", "--exit-code", "--", url, ref, ref + "^{}"],
            text=True, stderr=subprocess.DEVNULL, timeout=25,
        )
        refs = {name: sha for sha, name in (line.split() for line in result.splitlines())}
        head = refs.get(ref + "^{}") or refs[ref]
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        return path, pinned, ref, "-", "UNAVAILABLE"
    return path, pinned, ref, head, "MATCH" if head == pinned else "DIFFERS"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True, help="Resolved repo manifest -r")
    parser.add_argument("--all", action="store_true", help="Compare all projects, including tooling")
    args = parser.parse_args()

    root = ElementTree.parse(args.manifest).getroot()
    default_remote = root.find("default").attrib["remote"]
    projects = []
    for project in root.findall("project"):
        path = project.get("path") or project.attrib["name"]
        if args.all or any(path == area or area.endswith("/") and path.startswith(area) for area in AREAS):
            projects.append(project)
    if not projects:
        parser.error("No matching manifest projects")
    checkout = args.checkout.resolve()
    print("project\tpinned\treference\tupstream\tstatus")
    with ThreadPoolExecutor(max_workers=8) as pool:
        states = pool.map(lambda project: upstream(checkout, project, default_remote), projects)
        remaining = []
        for state in states:
            print("\t".join(state))
            remaining.append(state[-1])
    return 2 if any(state in {"NO_REF", "UNAVAILABLE"} for state in remaining) else 0


if __name__ == "__main__":
    sys.exit(main())
