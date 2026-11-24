# LineageOS 24.0 source release for the LG G8 ThinQ

An unofficial Android 17 port for the Canadian **LM-G820UM2** (`alphaplus`) with LG Android 12 **40b** firmware. The repository pins the LineageOS, AOSP and LG dependencies and selects four public forks for the reviewed changes. Other G8 variants, firmware versions and carriers need their own validation.

The public source covers the camera and flashlight, call microphone routing, kernel configuration, NFC driver selection and ARM64 page-table isolation. Our working VoLTE build also uses a separate LG IMS adaptation. The default manifest gives developers the open source baseline. The final release also contains reviewed IMS bridge source, integration templates and an opt-in device manifest. The [IMS engineering notes](docs/IMS.md) describe the implementation and its dependencies.

## Installation and recovery

Open [Start here](docs/START-HERE.md) for the illustrated overview. Use the [installation guide](docs/INSTALL.md) to pick the stock LG, existing LineageOS, or same-key update path. It includes illustrated recovery menus, download verification and stop points. See [recovery troubleshooting](docs/RECOVERY.md) for common failures. The public downloads are engineering artifacts. A complete, compatible install kit is required before flashing.

## Developer documentation

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

See [GitHub Releases](https://github.com/Magicolo/lg-g8-lineageos/releases) for development artifacts and checksums. Installing requires the complete Canadian kit described in the release guide. Open issues against this repository with the exact build, model, firmware, a minimal reproduction and redacted diagnostics.

Original material in this repository is licensed under the [Apache License 2.0](LICENSE). See [NOTICE](NOTICE) for scope. Upstream components and redistributed artifacts retain their own licenses. [LineageOS upstream](https://github.com/LineageOS/android/tree/lineage-24.0) · [LG community device tree](https://github.com/lge-qcom-dev/android_device_lge_alphaplus)

*Developed in collaboration with GPT 6.2 Sol.*
