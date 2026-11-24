# LG IMS source and local inputs

This folder contains the project's Java compatibility bridge, carrier profile test, native Android 12-to-17 wrappers and Soong, permission and init definitions. See [Rebuild](../docs/REBUILD.md) for the version-matched input archive and automated source preparation. The [IMS guide](../docs/IMS.md) explains the carrier, subscription and modem checks.

1. Initialize the public checkout using the [build guide](../docs/BUILD.md).
2. Copy `local-manifest.xml` into `.repo/local_manifests/` and run `repo sync -c device/lge/alphaplus device/lge/sm8150-common` to select the Canadian device and carrier changes.
3. Copy the templates to their matching source paths. Place `LGImsFeature.java` in `frameworks/opt/net/ims/src/java/com/android/ims/`. Stage the matching legacy Binder and Java ABI declarations from the [release's IMS input archive](https://github.com/Magicolo/lg-g8-lineageos/releases/tag/v1.1.0). The device makefile expects LG's carrier table at `device/lge/alphaplus/ims/config/carrier_code.xml`.
4. Verify your inputs with `sha256sum -c /path/to/LOCAL-IMS-SHA256SUMS` from the Android checkout root. The IMS APK and media library hashes cover the final adapted files. Obtaining stock firmware alone does not produce them. That archive supplies the adapted inputs used by the build. A from-stock conversion remains separate work.
5. Apply `carrierconfig-upgrade-only.patch` from the CarrierConfig directory only to reproduce the already-installed experimental build migration. A clean-start build does not require that version-code change.

Run the dependency-free profile test from this folder using a JDK.

```sh
mkdir -p /tmp/g8-profile-test
javac -d /tmp/g8-profile-test \
  vendor/lge/alphaplus-ims/java/com/lge/ims/compat/LgImsCarrierProfile.java ProfileTest.java
java -ea -cp /tmp/g8-profile-test com.lge.ims.compat.ProfileTest reference-40b.properties
```

Before deploying changes, use a dedicated device and the [validation checklist](../docs/VALIDATION.md).
