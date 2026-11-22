# Maintain and contribute to the port

The project repository is the entry point for documentation, issues and pinned manifests. Direct code changes belong in the matching fork. Keep device-specific configuration separate from portable fixes so other maintainers can review or cherry-pick each independently.

## Update dependencies

1. Record the current manifest and device evidence before updating. Use `repo manifest -r` in the working checkout and keep the last verified package and recovery images.
2. Compare both platform and device branches with their upstreams. The [audit helper](../tools/audit-upstream.py) compares revisions to the refs configured in the checkout. It reports `MATCH`, `DIFFERS`, `NO_REF` or `UNAVAILABLE`. For fork entries, separately compare the public parent `lineage-24.0` branch to the fork base. Manually inspect pinned references that have no comparable branch. Use `--all` to include toolchains.
3. Rebase only on a separate development branch. Check the actual diffs before taking updated manifest refs. Review monthly Android security bulletins, LineageOS platform changes, Chromium WebView and the LG kernel backports independently. A later platform Security Patch Level does not change the vintage of modem, camera or other vendor firmware. The tested build reported Android SPL 2026-11-01, LG vendor SPL 2022-12-01 and OpenELA-based kernel 4.14.357.
4. Preserve the scope of every change. Keep HIDL transport handling independent of Gralloc packaging. Keep the default/override audio pair aligned. Preserve the G8 fragment order and pair kernel and board-side KPTI changes. Test other devices before expanding an LG profile. Verify that older quirks still exist before carrying local workarounds across a platform upgrade.
5. Run the focused targets, build a new candidate, and apply the [validation matrix](VALIDATION.md). Update the manifest to the new exact commit IDs only after checking the build and maintaining a rollback route. Tag the manifest used for each public release.

Example source audit on a synced checkout.

```bash
repo manifest -r -o resolved-local.xml
python3 /path/to/lg-g8-lineageos/tools/audit-upstream.py \
    --checkout "$PWD" --manifest resolved-local.xml
```

[Android security bulletins](https://source.android.com/docs/security/bulletin) · [OpenELA kernel source](https://github.com/openela/kernel-lts) · [LineageOS Updater source](https://github.com/LineageOS/android_packages_apps_Updater/tree/lineage-24.0)

## Debugging and reporting

Include exact model, firmware revision, Android incremental, current slot, reproducible steps, expected result, and observed result. Distinguish a real call or capture from service enumeration. For audio use the route and what the far-end listener heard. For camera record the PID before and after failure and only the relevant redacted stack and log lines. Keep subscriber IDs, phone numbers, account state, IMEI, raw radio logs, traces containing private media, signing material and private source URLs out of public reports.

Use the tools in this repository as test fixtures. Install the diagnostic app only for a test session and remove it after use. If a fix requires logs from SELinux, constrain any policy change to the minimum domain, endpoint and operations and test with enforcing enabled.

## Send fixes upstream

- The generic HIDL torch failure guard is the first candidate. Check whether the target branch already carries equivalent handling and attach a small regression case. Keep the device package patch independent.
- Device registration, hardware profiles and kernel configuration belong in the LG trees. A new variant needs matching firmware, hardware validation, and obvious entry points for maintainers.
- When submitting to LineageOS, use Gerrit and follow its contributor agreement and AI-assisted contribution rules. Use the required attribution trailer and have a human maintainer review, explain and support the implementation. Check the policy for fully tool-generated work.
- Official device support is a separate process. It requires meeting the device charter and a maintainer committed to ongoing support.

[Submitting patches](https://lineageos.github.io/lineage_wiki/how-to/submitting-patches/) · [AI contribution rules](https://github.com/LineageOS/charter/blob/main/ai-coding-assistants.md) · [Device support charter](https://github.com/LineageOS/charter/blob/main/device-support-requirements.md) · [Submitting a port](https://lineageos.github.io/lineage_wiki/submitting_device.html)
