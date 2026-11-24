# LineageOS 24.0 for the LG G8 ThinQ

An unofficial Android 17 ROM for the Canadian **LG G8 ThinQ LM-G820UM2** with LG Android 12 **G820UM40b** firmware.

## Install or update

1. Open the [beginner installation guide](docs/INSTALL.md) and choose the route that matches your phone.
2. Get the ROM ZIP, its checksum list, and optional Google Apps from the [v1.1.0 release](https://github.com/Magicolo/lg-g8-lineageos/releases/tag/v1.1.0). The ROM is one ZIP.
3. If you run into a problem, see [recovery troubleshooting](docs/RECOVERY.md). The same release includes stock firmware and tools for recovery or rebuilding.

The project includes camera, flashlight, microphone, NFC, and VoLTE fixes. Other hardware variants and firmware versions need their own validation.

<details>
<summary>Developer documentation</summary>

The [IMS engineering notes](docs/IMS.md) cover the device integration and its dependencies. The tagged manifest pins the LineageOS, AOSP, and LG sources and selects the four project forks.

| Start here | What it contains |
| --- | --- |
| [Recover or rebuild a signed kit](docs/REBUILD.md) | Clean-checkout commands, local inputs, signing and image recovery |
| [Build the source preview](docs/BUILD.md) | Standard `repo` commands, inputs, exact target, kernel targets and common build failures |
| [Check device and firmware compatibility](docs/COMPATIBILITY.md) | Exact 40b stock input, userspace provenance, BPF, A/B limits and Google Apps |
| [Understand the changes](docs/CHANGES.md) | Each public commit, root cause, implementation, and limits on reuse |
| [Read the investigation history](docs/ATTEMPTS.md) | Failed approaches, evidence that ruled them out, and decisions that followed |
| [Port LG IMS and VoLTE](docs/IMS.md) | Carrier selection, Android 17 ABI bridges, first-call fixes, and test requirements |
| [Test the device](docs/VALIDATION.md) | Hardware and radio test matrix, evidence from the development build, pending checks, and power testing |
| [Maintain the port](docs/MAINTENANCE.md) | Updating the pinned source, rebasing changes, submitting patches and preparing releases |
| [Understand release artifacts](docs/RELEASES.md) | What the binaries contain, how they were checked, and what a public OTA requires |
| [Fix the Trust signing warning](docs/SIGNING.md) | Verify release keys and migrate an installed test-key build |
| [Read the full ROM distribution audit](docs/RELEASE-AUDIT.md) | Signed candidate, license and notice evidence, and remaining release gates |

</details>

Original material in this repository is licensed under the [Apache License 2.0](LICENSE). See [NOTICE](NOTICE) for scope. Upstream components and redistributed artifacts retain their own licenses. [LineageOS upstream](https://github.com/LineageOS/android/tree/lineage-24.0) · [LG community device tree](https://github.com/lge-qcom-dev/android_device_lge_alphaplus)

*Developed in collaboration with GPT 6.2 Sol.*
