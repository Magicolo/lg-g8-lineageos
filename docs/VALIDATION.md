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
| `1795369605`, test keys | Final development build booted and retained encryption, enforcing SELinux and NFC. The torch and outgoing IMS voicemail worked before the first credential unlock. The final pre-unlock check covered those two paths. The app-level flashlight and media evidence is from the preceding build with the same torch changes. |

## Second handset with private release keys

The full private-key `1795369605` OTA installed through Lineage Recovery 21 on the second Canadian G8. Android 17 booted in slot A with file-based encryption, SELinux enforcing, Play Store and the separately installed Google Play Services APEX active. A normal restart passed the [Trust signing check](SIGNING.md#move-a-g8-from-test-keys-to-release-keys). The same-key update to `1795454921` passed the boot, signing, data persistence and Google Apps checks on slot B. [OTA evidence](RELEASES.md#verified-private-key-ota-on-the-spare)

| Check | Result on the spare |
| --- | --- |
| Camera and LED | Both app-accessible Camera2 IDs returned built-in metadata and valid YUV frames. Torch on and off passed. The camera service enumerated five devices. The extra physical paths and video at other modes need separate coverage. |
| Microphone and media | 96,000 microphone samples at 48 kHz with nonzero signal. Synthetic H.264 and HEVC playback, WebView JavaScript and canvas, and picture-in-picture passed. |
| Storage and USB | A 64 MiB synthetic write over USB, sync and on-device SHA-256 readback matched. The UFS device reported pre-EOL `0x01` and both firmware wear estimates as `0x04`. The inspected boot log had no matching storage I/O or fatal UFS messages. These health descriptors and the spot test do not scan the entire flash medium. [Linux UFS health descriptors](https://docs.kernel.org/6.7/admin-guide/abi-testing.html) |
| Wireless controllers | Wi-Fi reconnected and became a validated network. Bluetooth and NFC powered off and on. These checks do not exercise an accessory or tag. |
| Location and other sensors | The GNSS engine called back without an indoor location fix. Accelerometer, gyroscope, magnetic field, light, proximity and pressure each supplied real sensor events. A fingerprint sensor and a vibrator were enumerated, and Android reported completion of a short vibration command. No fingerprint was enrolled. |
| Physical fixtures | No SIM was present, so the spare's carrier attachment, IMS and call audio were not exercised. Fingerprint enrollment, proximity response, GNSS fix, NFC transactions, Bluetooth audio, wired audio, Qi, USB-C display and physical inspection require their respective fixtures or observation. |

## Repeatable acceptance matrix

| Area | Procedure and success condition | Open coverage |
| --- | --- | --- |
| Boot and OTA | Check exact target, signatures, A/B state, slot after reboot, encryption, SELinux, recovery and retained data. Test a clean install and an update of the same signing family. | Public clean build, stock-to-custom path, and hosted Updater. |
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

Substitute `web`, `mic`, `camera`, `gps`, `media`, `pip` or `sensors` for `torch`. The sensor run logs event counts and leaves calibration to separate tests. Use `--es clip h264` or `--es clip hevc` with media. For camera use `--es lens rear` or `--es lens front`. Run `cameraids` to list app-accessible IDs, then `cameraid --es id <id>` to capture from one. If a requested runtime permission is denied, grant it on the device Settings page for that fixture before rerunning. Capture PIDs and relevant camera errors separately. Redact diagnostics before posting.

## Power and wake

On the spare, Android reported the battery in good health and a gauge estimate near 3,494 mAh. During brief USB-powered diagnostics the battery was near 31°C and sampled CPU zones were in the mid-30s °C. A gauge figure does not establish usable battery capacity. Compare real charge-counter change during an unplugged interval, the recorded time on battery, and the temperature trend. Run with a consistent network, screen and charging state.

In one 32 minute 50 second unplugged run on Wi-Fi with no SIM, the spare spent 30 minutes 52 seconds with its screen off. The battery cooled from 30.7°C to 26.3°C. Recorded on-battery samples reached a low of 25.3°C. Its display dropped from 72% to 71%, while the gauge counter decreased by 133 mAh. Android's separate battery estimate was about 105 mAh. The readings are insufficient to conclude that standby drain is low. Repeat a longer measurement before judging the battery or estimating runtime. The four little cores also entered C1 during this interval, despite the inherited boot flag. This complements the earlier USB-powered observation.

The Linux kernel thermal zones and the LG/Qualcomm `thermal-engine` daemon were present, but `adb shell dumpsys thermalservice` reported `HAL Ready: false`. Android's status value of 0 therefore cannot verify the absence of throttling. Do not infer a defective sensor, a verified mitigation path, or the cause of the drain from this observation alone. The stock 40b vendor manifest declares a vendor-specific LG HIDL thermal interface. The pinned Qualcomm legacy Android AIDL implementation supports Snapdragon 855, but it can write trip points and its generic SKIN profile uses a different sensor from the LG skin estimate. A framework HAL change needs a separate mitigation and standby test. Qualify the mapping and event path against stock on the exact model before enabling a framework HAL. [Android thermal HAL](https://source.android.com/docs/core/power/thermal-mitigation)

The CPU-idle boot flag experiment was reverted after it failed to improve the observed plugged-in little-core residency. To justify revisiting it, use repeated unplugged baselines with the same signal, SIM, initial charge, screen behavior, app load and test interval. Let indexing settle, disable USB Stay Awake for the measurement, and collect time on battery, screen time, charge-counter delta, temperature and CPU idle residency. Six hours is a useful initial comparison window. Do not simulate an unplugged measurement by changing BatteryService state.

The [battery collector](../tools/Measure-G8Battery.ps1) accepts explicit ADB, a phase label and an optional `-Serial` when more than one handset is connected. Compare results with a second run per build. Validate alarm wake, first incoming call after idle, notifications, Wi-Fi and Bluetooth resume and charging reconnect before accepting changes that affect wake behavior.

## v1.1.0 release validation

Build `1795533156` passed full OTA and A/B payload signature verification, VINTF, embedded platform signatures, stock target and partition size checks, and the optional Google Apps sizing check. The effective kernel identity uses generic labels. Boot, DTBO and vbmeta matched the signed payload bytes. The previous build `1795454921` was tested on a Canadian G8. The rebuilt package was verified offline.

### Independent rebuild checks

| Check | Result |
| --- | --- |
| Initialize the release tag, apply the IMS overlay, and resolve Android Repo projects | 1,246 source projects resolved. |
| Compare the pinned sources with the original build tree | The other 1,242 project heads matched. The four fork pins incorporate the checked release changes. All ten locally modified tracked files matched the corresponding files in the fresh checkout after IMS preparation. |
| Fresh public sync of all four component forks, both LG vendor repositories, CarrierConfig, IMS framework, and both WebView prebuilts | Passed. Both WebView APKs passed Git LFS and ZIP checks. |
| Download the OTA, certificate, verifier, Windows tools and IMS archive from the release | Checked the downloaded files against the published hashes. The ROM and A/B payload signatures verified using the released verifier. |
| Apply the IMS archive in the fresh selected-project checkout | Staged 59 files. The second pass found no missing inputs. A deliberate text edit required the developer option, and a deliberate binary edit was rejected with that option enabled. |
| Reproduce the native IMS media library from the stock 40b input | The output matched the released IMS archive byte for byte. |
| Generate a separate signing family from real target-files and sign an OTA | Generated 38 non-presigned APEX key pairs. The resulting OTA passed both signature checks and the three extracted boot-chain images matched the payload. This used the previously compiled unsigned Android baseline. |
| Sync and compile all projects from a blank build environment | Pending. |
| Factory-locked Canadian 40b to the exact released build | Pending. The tested clean migration used working Lineage Recovery and an earlier build in the same signing family. |
