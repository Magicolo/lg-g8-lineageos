# Investigation history and lessons

This record keeps the unsuccessful and incomplete paths alongside their useful evidence. It separates observations on the Canadian handset from inferences and results reported for other devices.

## Stock, firmware, and ROM selection

| Attempt | Result and what to carry forward |
| --- | --- |
| Test VoLTE on the original G8 and a second phone | The carrier test call and ordinary calls failed on the G8. The same physical SIM handled both on a supported Moto G 5G. This isolated the SIM and account from at least part of the failure. It did not establish a modem or firmware defect. |
| Refurbish to Canadian stock firmware and inspect mobile settings | Stock Android booted, but the test number did not ring and the expected VoLTE toggle was absent. A stock or rooted settings override alone did not establish IMS registration or working voice. Canada 40b became the firmware reference for the subsequent ROM. |
| Inspect the G8 boot partition with Qualcomm tooling | Several attempts stopped at USB port selection, Sahara startup or an incomplete transfer. Other attempts eventually read the expected boot partition. Treat a programmer handshake, GPT read and byte verification as different checks. No broad claim about QFIL, WSL or a specific driver follows from the earlier failures. |
| Use a nearby custom ROM or phone as the fix | The LG V60, Snapdragon 845 LG family and Palm ports supplied useful IMS and packaging ideas. Their stock libraries, modem configuration and image layouts are hardware-specific. The implementation kept the G8's 40b substrate. |
| Build the baseline in the Windows/WSL workflow | The early host workflow was abandoned in favor of a Linux machine with more storage and memory. The Linux build host's Android 17 Soong graph still exhausted memory once. Resuming with more swap and fewer compile jobs let the build proceed without changing product behavior. |

## LineageOS 21 IMS iterations

1. **Android carrier toggle only.** CarrierConfig could advertise VoLTE and bind the service. LTE attach and a ready service still produced no live IMS bearer, registration or voice. The useful signals were the actual subscription, requested bearer, native LTE state and network error.
2. **Partial carrier identification.** An informational resolver recognized parts of the carrier identity, while the actual policy still selected the generic handler. Matching the exact carrier tuple against the existing Canadian operator path corrected policy selection. It did not by itself prove that the native stack was ready.
3. **Timed bearer trial.** The first trigger did not prove the trial armed. A later bounded trial produced an LG-owned request, an IPv6 IMS network and two P-CSCF addresses. Android still reported unregistered. Repeating with Wi-Fi off yielded the same result. The trial established the bearer path and exposed the native state mismatch.
4. **VoPS fallback with a missing binder.** Handling a completely missing proxy was insufficient. The stock client could produce a wrapper whose network feature report was empty even though the modem reported LTE PS voice support. Expand the fallback only to a missing usable report on the actual subscription and keep a real OEM report authoritative.
5. **IPsec omitted.** MTU or APN guesses would not have restored authentication. Once the IMS bearer became normal, the native engine logged local IPsec socket/policy failures. Restoring the firmware-matched helpers with narrow permissions addressed that stage.
6. **Registration without usable voice.** Early media and alerting did not imply two-way audio. The ordinary-voice media precondition needed the scoped mask change. Decline and cancel also exposed a call cleanup problem. The handset echo and incoming SIP rejection each needed their own diagnosis. [Final implementation and tests](IMS.md#outgoing-first-call-setup-and-incoming-ringing)

## Android 17 bring-up and later experiments

| Attempt or symptom | Decision |
| --- | --- |
| Reuse the Android 14 kernel configuration path | It selected a defconfig absent from the new tree. Append the alpha fragment after the existing shared stack. [Kernel config change](CHANGES.md#3-select-the-working-kernel-fragment-stack) |
| Bring over every old IMS prebuilt unchanged | Stock and source-built lgdata 1.0 tried to install the same destination. Use the existing source-built 1.0 and matching stock 1.1 with ELF validation. Keep archival `Android.bp` snapshots out of Soong discovery. |
| Trust the pinned WebView commit without checking LFS | Compilation used an LFS pointer where an ARM APK was required. Materialize the pinned ARM and ARM64 blobs and verify both against their Git pointers. |
| Forward the old media object directly into Android 17 | Its caller allocates the older, smaller BufferItem. Use a separately constructed object for platform calls. A broad symbol rename also reordered indices referenced by Android's packed relocations and caused an IMS initialization crash. Preserve the indices and compare decoded relocations. |
| Install an early ZIP with generic target identity | Recovery rejected the target assertion mismatch. Preserve the Canadian identity and check the exact package before reboot. A generated ZIP can exist even after the full build failed. Use the verified staging output. |
| Write the carrier voice row from ordinary shell or assume an installed carrier XML updated it | The provider requires a privileged writer. A historical profile already showing 27 cannot prove first-install initialization. Make the scoped adjustment at the stock app's startup boundary and test a fresh profile on separate hardware. |
| Global carrier CarrierConfig override and temporary LG diagnostics | A carrier-wide override is too broad for the OEM adaptation. Keep the device, slot and SIM checks. Retire the test bearer receiver and native tracing from production. |
| Keep polling NFC state without checking its device node | The HAL was up, but the expected character device did not exist. Restore the PN553 driver and wake configuration on the matching hardware. Validate real tag and card behavior separately. |
| Treat post-crash camera enumeration as proof of flashlight health | The provider and camera service restarted and enumeration returned to normal. Torch transitions and stable PIDs found the fault and proved the paired Gralloc and transport fixes. |
| Remove the inherited CPU idle flag to improve battery | The post-boot script already attempts to clear it on msmnile. Plugged-in measurements did not show deeper little-core residency. Restored the inherited flag after the experiment. Use repeated unplugged tests before changing power policy. |
| Treat offline release signing as a tested upgrade | Offline signature and trust-store checks are useful. The production-key clean install, same-key update and rollback still need physical validation. |

[Change map](CHANGES.md) · [LG IMS engineering notes](IMS.md) · [Build and testing workflow](BUILD.md) · [Validation results](VALIDATION.md)
