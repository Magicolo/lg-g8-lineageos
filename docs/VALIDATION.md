# Validation and known limitations

Use this matrix when touching the G8 hardware paths. Start with the exact device identifier, firmware, SIM, release commit and boot slot. The results below apply to the **Canadian LM-G820UM2 on 40b** and the **complete development build**, whose additional LG IMS integration is described separately. They are evidence for the individual changes in that environment. The public source slice has no end-to-end runtime qualification.

## Recorded build checkpoints

| Incremental | Technical result |
| --- | --- |
| Android 14 build 27 | Ordinary carrier incoming and outgoing calls worked. Far-end echo was absent in a real handset call. |
| `1795321585` | Android 17 relocation-corrected OTA booted, LG IMS stopped crashing, and MmTel registered with voice capability. Early-media testing still exposed a voice-profile precondition issue. |
| `1795324697` | carrier first-call build with startup profile change. The owner later confirmed ordinary incoming and outgoing calls and the echo result. The existing voice mask already read 27, so fresh-profile initialization remained open. |
| `1795362667` | KPTI build booted and reported `Mitigation: PTI`. Retained file-based encryption, enforcing SELinux, Google Apps and NFC initialization. |
| `1795365591` | The portable profile and compatibility JAR matched their expected outputs. carrier voicemail used IMS and returned to idle. The host parser passed exact-match, negative and malformed profile cases. |
| `1795367652` | The Camera2 torch toggled on and off with stable camera service and HAL PIDs. The smoke fixture passed synthetic media playback, WebView, microphone and picture-in-picture checks. |
| `1795369605` | Final development build booted and retained encryption, enforcing SELinux and NFC. The torch and outgoing IMS voicemail worked before the first credential unlock. The final pre-unlock check covered those two paths. The app-level flashlight and media evidence is from the preceding build with the same torch changes. |

## Repeatable acceptance matrix

| Area | Procedure and success condition | Open coverage |
| --- | --- | --- |
| Boot and OTA | Check exact target, signatures, A/B state, slot after reboot, encryption, SELinux, recovery and retained data. Test a clean install and an update of the same signing family. | Public clean build, production release-key install and hosted Updater. |
| IMS | Check exact carrier match, real modem VoPS, service binding, IMS registration and voice capability. Place and receive ordinary calls. Check first incoming after idle and retry after decline. | Fresh voice-profile initialization, extended idle, alternate carrier and real second model. |
| Audio | Use a real far-end listener for earpiece, speakerphone, wired headset and Bluetooth HFP. Verify neither intelligibility nor echo regresses. Ordinary 48 kHz recording is a separate check. | Continuous far-end and accessory coverage including Quad DAC and USB audio. |
| Camera and torch | Capture front and rear stills and YUV frames, exercise wide and ultra-wide lenses, record video with sound, toggle torch on/off, watch the provider and cameraserver PIDs, and validate HAL recovery. | Photo flash, controls from apps, additional video modes and a repeatable HIDL provider-failure test. |
| Media and apps | Play synthetic H.264/HEVC with AAC, exercise app picture-in-picture, offline WebView JavaScript and graphics. Install separately verified GApps where authorized and check the mounted system APEX. | HDR, DRM playback, long browsing sessions and Play-dependent features requiring certification. |
| Network and connectivity | Verify Wi-Fi to mobile fallback and back, SMS, MMS, Bluetooth pairing and resume, tethering and USB composition. USB RNDIS was enumerated on a host. | Routed tethering traffic, VPN forwarding, OTG and accessory-dependent resume. |
| NFC | Check `/dev/pn547`, NXP HAL startup, NFC ON, tag reading and resume. Test emulation separately. | Actual tag/reader transactions and card emulation. |
| Sensors and accessories | Verify fingerprint, screen proximity in calls, location fix outdoors, USB-C display, portable storage, Qi charging and Bluetooth audio. | Outdoor fix, repeated fingerprint and proximity tests, DP and Qi fixtures, FM where supported. |

Passive enumeration is useful for diagnostics. NFC ON does not demonstrate transactions. Indoor GNSS acquisition acquired satellite observations without a location fix. Likewise Google Play's presence does not imply Play Integrity, Wallet, OEM biometrics or streaming certification. Stock LG face/hand functions and services dependent on OEM trust are separate from the open device port.

## Run the smoke fixture

The [fixture source](../tools/smoke/) uses public Android APIs and synthetic video. It records outcomes, audio sample counts and GNSS satellite counts in logcat. It does not save microphone samples or locations. Unlock the handset, obtain local permission for any camera, microphone or location check and run in an isolated test session.

```bash
ANDROID_TREE=/path/to/android-build bash tools/smoke/build.sh
adb install -r tools/smoke/out/compatibility-smoke.apk
adb shell am start -S -n org.g8rom.smoke/.SmokeActivity --es test torch
adb logcat -d -s G8RomSmoke:I
adb uninstall org.g8rom.smoke
```

Substitute `web`, `mic`, `camera`, `gps`, `media` or `pip` for `torch`. Use `--es clip h264` or `--es clip hevc` with media. For camera use `--es lens rear` or `--es lens front`. If a requested runtime permission is denied, grant it on the device Settings page for that fixture before rerunning. Capture PIDs and relevant camera errors separately. Redact diagnostics before posting.

## Power and wake

The CPU-idle boot flag experiment was reverted after it failed to improve the observed plugged-in little-core residency. To justify revisiting it, use repeated unplugged baselines with the same signal, SIM, initial charge, screen behavior, app load and test interval. Let indexing settle, disable USB Stay Awake for the measurement, and collect time on battery, screen time, charge-counter delta, temperature and CPU idle residency. Six hours is a useful initial comparison window. Do not simulate an unplugged measurement by changing BatteryService state.

The [battery collector](../tools/Measure-G8Battery.ps1) accepts explicit ADB and a phase label. Compare results with a second run per build. Validate alarm wake, first incoming call after idle, notifications, Wi-Fi and Bluetooth resume and charging reconnect before accepting changes that affect wake behavior.
