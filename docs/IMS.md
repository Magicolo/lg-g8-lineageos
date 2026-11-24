# LG IMS and VoLTE engineering notes

The full development build uses the Canadian 40b LG IMS stack through LineageOS 24. The public manifest omits the proprietary stack and its adaptations. This document records the changes, why each was needed, and how to evaluate the same architecture on another device using its own permitted firmware inputs.

## Firmware and carrier scope

The reference implementation was first proven on LineageOS 21 and carried into Android 17 in small steps. Keep the modem firmware, native LG IMS and VSS HALs, board audio calibration and IPsec userspace from one matching firmware family. Carry over only a shim with a matching ABI. Pin extracted input digests, compiled outputs and the exact device. Changing the Android version or a GL, camera, audio or telephony interface can invalidate a previously working binary adaptation.

The tested build identifies as `alphaplus_lao_com`. The carrier profile matches logical slot `0`, Android carrier ID `2417`, PLMN `302500` and GID1 `55`. The matching LG provisioning identifiers are `VTR/CA/FZZ`. Production selection has two parts.

1. The device declares VoLTE capability. A vendor CarrierConfig tuple selects `com.lge.ims` as MmTel and admits VoLTE only for the exact device and SIM tuple. Keep the global carrier carrier asset independent of the LG package.
2. Read the legacy compatibility parameters from a read-only product file at `/product/etc/lg-ims/compat-profile.properties`. Match device and slot before the subscription identifiers. Match hex GID1 case-insensitively. Treat an explicitly empty GID1 as absent or empty. An invalid or missing profile leaves the operator override, VoPS refresh and voice-row update inactive.

The profile specifies an explicit VoPS refresh opt-in and may specify a pair of ordinary-voice masks. Require both mask values together, permit clearing existing bits only, validate numeric inputs, and recheck the active subscription immediately before a write. Preserve the hook entry point names expected by the old APK while keeping variant data outside the shared Java code. A test matrix should contain exact match, mismatch of each field, missing or malformed profile, unsafe mask pairs and a synthetic second variant. Real hardware coverage is separate.

## Android 17 Java and native boundaries

| Boundary | Development implementation and check |
| --- | --- |
| LG IMS service and permissions | Use the stock LG service and matched native libraries with the necessary privileged permission and classloader allowlists. The Java bridge provides narrow legacy APIs including the expected `com.android.ims.LGImsFeature` contract. Check package signing and the Binder or JNI contracts. Keep all proprietary inputs and signature requirements explicit. |
| lgdata HIDL | Android 17 already builds `vendor.lge.hardware.lgdata@1.0`. The Android 14 port also installed an OEM prebuilt under another build module name, producing duplicate Ninja outputs. Keep one provider of the 1.0 SONAME and use it with the firmware-matched 1.1 library. The focused ELF check verified all 59 imports from the tested 1.1 stack against the replacement 1.0 exports. |
| Active subscription and bearer | Adapt the LG calls to the active subscription's ISIM and normal LTE packet state. Handle a missing OEM phone binder or a legacy query without a usable network feature. Retain the IPv6 carrier IMS APN, carrier P-CSCF discovery and IMS-AKA. Use the firmware's IPsec client and starter in dedicated SELinux domains with targeted XFRM and IPC access. Verify the actual bearer and IMS registration. A property saying VoLTE is enabled is insufficient. |
| Modem media and audio | Allow the LG radio client to reach the VSS media HAL and keep that HAL's IPC router operations scoped to its domain. Test with SELinux enforcing. Use the G8 Fluence route for call audio. Confirm the PCM microphone path and two-way call audio separately. |
| Android 17 audio and graphics ABI | The LG IMS media library needs `AudioSystem::setParameters` from `libaudiobase.so`. Android 17 also changes the graphics buffer callback signatures and grows `BufferItem`. Adapt only the affected IMS imports. Use a separately constructed Android 17 object so platform code never writes past the old caller's storage. Preserve constructor/destructor, acquire and release semantics. |
| Relocation integrity | A general ELF symbol rename reordered the dynamic symbol table while an Android packed relocation retained its previous index. A native mutex constructor then wrote through a pointer into executable storage and IMS repeatedly crashed. The corrected approach adds the audio library dependency and preserves existing symbol indices, including Android packed relocations. Compare decoded relocations before and after. The only intended changes are the four redirected constructor, destructor, acquire and release imports. Keep Android's ELF checks enabled. |

Leave archival module definitions outside the scanned Soong tree or under filenames other than `Android.bp`. Soong treats a second snapshot of a module definition as a duplicate even if it sits in a diagnostic directory.

## Outgoing first-call setup and incoming ringing

1. **Unregistered after boot.** First establish that the LG native libraries load, the IMS process stops crashing and Android sees the intended MmTel service. On the first Android 17 port the visible LTE state was normal while IMS JNI initialization failed. The relocation correction moved the build from repeated native crashes to working MmTel registration.
2. **Outgoing alerting without audio.** The ordinary carrier voice row initially had bitmask 31 and the LG stack attempted a media precondition reservation. Clear that one bit by changing the existing row from 31 to 27. Run the startup adjustment after the stock operator profile update and before the native stack takes its initial snapshot. Require the LG application's existing permission, the exact subscription and the single expected ordinary-voice row. If the provider has already reached 27, leave it alone. A test SIM that already has 27 cannot prove fresh initialization. Preserve the existing mask for another carrier or voice profile.
3. **Incoming call never rings.** The earlier LineageOS 21 trace showed an incoming SIP INVITE rejected with 488 despite LTE voice support from the modem. The legacy native stack needed its VoPS state refreshed after IMS registered and after call state returned to idle. Refresh through its existing event path only for the matching profile, when the original LG phone service is absent and the modem has positively reported LTE PS voice support for the registered slot. Preserve idle, detach and subscription-change behavior. A global always-true VoPS value would discard the modem's state.
4. **Dialer blocked after a declined or cancelled attempt.** The Android 14 implementation needed to clean up an already-progressed outgoing call when an early callback had cleared `mPendingMO`. Android 17 uses the platform's call cleanup path and does not carry the older framework workaround. Exercise decline and local cancel during alerting, then place a second ordinary call.
5. **Far-end echo.** The tested device moves from the generic input to its calibrated dual-microphone Fluence route. See [the public audio changes](CHANGES.md#5-restore-the-calibrated-call-microphone-route). A headset can hide an acoustics regression that is still present on the built-in earpiece or speaker.

The private upgrade kept CarrierConfig's version code at 3 for compatibility with already installed experimental builds. The public clean-start slice leaves that upstream. A later OTA should explicitly test package version and signature compatibility. The final private build also removed a temporary bearer receiver and native parcel-tracing hooks. Verification of the compiled APK and compatibility JAR checked their absence and the retention of the startup, carrier and LTE VoPS paths. Temporary diagnostics stay in fixtures outside the system image.

## Porting checklist

1. Scope the model, firmware, device identity, stock IMS subscription behavior and carrier first. Extract only firmware you can use and check hashes, SONAMEs, ABI layouts and dependencies.
2. Bring up service binding and assert SELinux remains enforcing before enabling the profile-specific behavior. Audit the active subscription at each carrier and voice-profile decision. Use a negative SIM or slot test.
3. Test fresh and preserved IMS profiles separately. Verify first outgoing, first incoming after boot and after idle, decline, hangup, retry and two-way audio. Include SMS, MMS and data handoff. The carrier diagnostic number is early media and may fail to enter Telecom ACTIVE. An ordinary call and carrier voicemail exercise different paths.
4. Test Wi-Fi calling, ePDG and emergency routing only with appropriate carrier provisioning and authorized facilities. Maintain a separate result for each capability. A second phone or hardware variant requires its own data and tests.

[Related LG V60 IMS port](https://github.com/greatluke/lgv60-ims-volte-vowifi-lineageos) · [LineageOS device support requirements](https://github.com/LineageOS/charter/blob/main/device-support-requirements.md)

## Final source and integration

The [IMS source folder](../ims/README.md) contains the reviewed Java and native compatibility code, build templates and opt-in device manifest. The ordinary public manifest remains the default.
