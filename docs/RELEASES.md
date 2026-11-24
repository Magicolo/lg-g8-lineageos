# Release downloads and verification

The [v1.1.0 release](https://github.com/Magicolo/lg-g8-lineageos/releases/tag/v1.1.0) contains the complete kit for build **1795533156**. The [beginner guide](INSTALL.md) is the starting point for installing or updating. The exact variant is the Canadian **LM-G820UM2** (`alphaplus_lao_com`) with LG firmware **G820UM40b**. The ROM uses Android 17 SDK 37 and the **2026-11-01** framework security patch.

| Task | Files from v1.1.0 |
| --- | --- |
| Update from this fork's release-key build | ROM ZIP and `SHA256SUMS`. The full OTA is one ZIP. |
| Clean install from working Lineage Recovery | ROM ZIP and `SHA256SUMS`. Add Google Apps if wanted. For USB on Windows, use the `platform-tools` folder inside `LG-G8-Windows-tools.zip`. |
| Restore matching stock firmware | Three `.kdz.partNN` files, `split-files.json`, and the Windows tools. See [recovery troubleshooting](RECOVERY.md). |
| Recover the boot chain | Matched `boot.img`, `dtbo.img` and `vbmeta.img` as required by the recovery procedure. |
| Rebuild or inspect | IMS input archive, three `signed-target-files.zip.partNN` files, effective kernel configuration, testing APK and public signing certificates. The [rebuild guide](REBUILD.md) covers the pinned source and tooling. |

The release's whole-package and A/B payload signatures verified. The boot-chain image digests matched the signed payload. The rebuilt package uses the same signing family as the earlier device-tested build. See [validation](VALIDATION.md#v110-release-validation) and [signing](SIGNING.md).

## Verified private-key OTA on the spare

On November 23, 2026, the Canadian G8 on 40b accepted a local full OTA from release-key build `1795369605` to `1795454921` through Lineage Updater. The follow-up advanced the build timestamp with the same source revision set and project keys. Its SHA-256 was `07841df02e14788527b1cff978d1ec15c9fa531067f5d389d102f8c6f716582b`.

The donor booted slot A. Updater authenticated the staged package, wrote slot B, verified the target filesystems, and finished postinstall before offering a reboot. The new build booted and marked slot B successful. The test file in shared storage and ADB authorization survived. The Play Store, Play Services, the active Google Services APEX and its add-on script remained available with file encryption and SELinux enforcing.

Both images passed the embedded private platform certificate check. The 39 packaged APEX payload public keys matched across the builds, as did the sampled ART and runtime container certificates. The installed framework and LG IMS APK hashes matched the verified target-files. The Android OTA trust store was unchanged and Trust showed no public-keys warning. The test used a local file through the normal Updater. A hosted update feed and live carrier checks on the spare remain separate qualifications.

## What a complete install kit contains

The table above lists the installation and recovery files. For developer-only checks and the matching source, see [Rebuild](REBUILD.md).

## Reassemble a split download

Only the stock `G820UM40b_00_OPEN_CA_OP_1129.kdz` and developer `signed-target-files.zip` are split. The ROM downloads as one ZIP.

1. Download the three matching `.partNN` files and `split-files.json` from this release. Put them together in a folder with room for the complete file.
2. **On Windows**, also download `Join-ReleaseParts.ps1`. In PowerShell in that folder, run the appropriate line below. The helper checks each part and the completed file's SHA-256. If Windows blocks the downloaded helper, compare its hash with `SHA256SUMS` before unblocking that specific file.
3. **On macOS or Linux**, check the part hashes in `SHA256SUMS`. Concatenate the three parts in order into a new file and compare its SHA-256 with the value in `split-files.json`.

```powershell
.\Join-ReleaseParts.ps1 -File G820UM40b_00_OPEN_CA_OP_1129.kdz
.\Join-ReleaseParts.ps1 -File signed-target-files.zip
```

## Qualify a future installable release

Build against the pinned sources, verify images and signatures, then test a clean installation and a same-key OTA on the exact device. For preparation and checks, use [Rebuild](REBUILD.md) and [Validation](VALIDATION.md).

## Extract inspection files from the archived build

Use GitHub's source archive for the [v1.1.0 tag](https://github.com/Magicolo/lg-g8-lineageos/tree/v1.1.0). The signed target-files archive contains the exact base DTB at `BOOT/dtb`. Use `avbtool erase_footer` on a **copy** of `dtbo.img` to retrieve its raw overlay table.
