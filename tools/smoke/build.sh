#!/usr/bin/env bash
set -euo pipefail
test_dir="$(cd "$(dirname "$0")" && pwd)"
android_tree="$(cd "${ANDROID_TREE:?Set ANDROID_TREE to a built LineageOS checkout}" && pwd)"
build="$test_dir/out"
host="$android_tree/out/host/linux-x86/bin"
sdk="$android_tree/prebuilts/sdk/current/public/android.jar"
jdk="$android_tree/prebuilts/jdk/jdk21/linux-x86/bin"
export PATH="$jdk:$host:$PATH"
umask 077
mkdir -p "$build/"{classes,dex,assets}
for clip in h264 hevc; do
    target="$build/assets/$clip.mp4"
    if [[ -s "$target" ]]; then continue; fi
    codec=(-c:v libx264 -threads 2)
    if [[ "$clip" == hevc ]]; then
        codec=(-c:v libx265 -x265-params 'pools=1:frame-threads=1:log-level=error' -tag:v hvc1)
    fi
    ffmpeg -hide_banner -loglevel error -f lavfi -i testsrc2=size=1280x720:rate=30 \
        -f lavfi -i sine=frequency=660:sample_rate=48000 -t 5 \
        "${codec[@]}" -pix_fmt yuv420p -c:a aac -movflags +faststart "$target"
done
javac --release 17 -classpath "$sdk" -d "$build/classes" "$test_dir/SmokeActivity.java"
find "$build/classes" -name '*.class' -print > "$build/classes.rsp"
d8 --min-api 28 --lib "$sdk" --output "$build/dex" "@$build/classes.rsp"
aapt2 link -o "$build/unsigned.apk" -I "$sdk" --manifest "$test_dir/AndroidManifest.xml" \
    -A "$build/assets" -0 mp4
(cd "$build/dex" && zip -q -u "$build/unsigned.apk" classes.dex)
zipalign -f 4 "$build/unsigned.apk" "$build/aligned.apk"
if [[ ! -f "$build/local-test.p12" ]]; then
    keytool -genkeypair -keystore "$build/local-test.p12" -storetype PKCS12 -storepass fixture-only \
        -alias local-test -keyalg RSA -keysize 2048 -validity 60 -dname 'CN=G8 local diagnostic fixture'
fi
apksigner sign --ks "$build/local-test.p12" --ks-pass pass:fixture-only \
    --out "$build/compatibility-smoke.apk" "$build/aligned.apk"
apksigner verify "$build/compatibility-smoke.apk"
sha256sum "$build/compatibility-smoke.apk"
