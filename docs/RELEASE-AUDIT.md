# Full ROM distribution audit

**Decision for build 1795369605. The signed install kit passed offline checks. Public distribution of the complete kit is on hold.** The inspection found included proprietary components without an established redistribution basis. The normalized candidate subsequently completed a signing-family transition on a second Canadian G8. The first signed rehearsal also had malformed license notices. The subsequent signed candidate corrected their XML formatting. The [v0.1.2 engineering release](https://github.com/Magicolo/lg-g8-lineageos/releases/tag/v0.1.2-source-preview) contains the separately verified public development artifacts.

## Exact candidate checked

| Check | Result |
| --- | --- |
| Package target | Full physical A/B OTA for `alphaplus_lao_com`, incremental `1795369605`, SDK 37, framework SPL 2026-11-01. |
| Rehearsal OTA SHA-256 | `79802ce398cb9ab10b561002d7d382076567c5f155f2098f4f19900da24d46db`. This identifies the private build, so users can distinguish it from the original test-key build. It is not a download link. |
| Android signing | The complete ZIP and A/B payload verified with the private rehearsal certificate's public half. The public AOSP test certificate was rejected. The matching system and recovery trust stores contained the rehearsal certificate. |
| Install-kit images | The exact SHA-256 and byte lengths of boot/recovery, packaged DTBO and vbmeta matched their records in the signed A/B payload. Offline VINTF and partition size checks passed. |
| Optional Google Apps | The signed images had space for the verified MindTheGapps package. The archive did not contain the Play Store or Google Play Services APEX from that add-on. It does contain other inherited Google-branded vendor packages. |
| Physical validation | The original test-key build worked on the development handset. The normalized release-key candidate booted on the spare after an existing-Lineage recovery install. Trust's Build signature alert was enabled and posted no public-keys warning on restart. A subsequent local OTA using the same project keys booted successfully and preserved data and Google Apps. Stock-to-custom and a post-install downgrade remain outside these tests. [Signing results](SIGNING.md) · [OTA evidence](RELEASES.md#verified-private-key-ota-on-the-spare) |

A new signer changes the recovery trust chain and can change app and APEX identities. Android cannot establish stock-to-custom boot compatibility solely from a certificate or a correctly signed OTA. Keep the [installation paths](INSTALL.md) and [rollback procedure](RECOVERY.md) paired with the final tested kit. [AOSP signing and recovery trust](https://source.android.com/docs/core/ota/sign_builds)

## What is inside the exact binary

A file-level inventory of 10,884 installed and image entries was made from the signed target-files, with SHA-256 and byte length per entry. 1,756 entries matched files byte-for-byte in the two inherited LG vendor projects. Seven more matched by vendor source path without identical bytes. These matches establish provenance for review. The other entries still require normal license or source mapping as appropriate. The two pinned vendor projects contain 730 and 1,033 tracked paths under their respective `proprietary/` trees. No repository-level license file was found in either pinned tree.

| Component group | Evidence and action |
| --- | --- |
| Modified LG IMS | The installed `AlphaplusLgIms.apk` contains the same `classes.dex` as the locally adapted LG `Ims6.apk`. The installed `libimsmmpf.lge.so` matched the modified native media library byte-for-byte. Review a license or other legal basis that covers distributing these modified copies. |
| Stock LG IMS and native helpers | The candidate also carries `libims.lge.so`, LG camera and voice libraries, `imsipsecstarter`, `imsipsecclient` and LG framework JARs. Permission for a modified shim would cover only that shim. Inventory the original vendor components separately. |
| Inherited vendor stack | The packaged vendor and product files include proprietary Qualcomm/LG HALs and the common tree's Widevine service and Google hotword enrollment APKs. They are independent of the optional Google Apps add-on. Review each source group and any bundled firmware. Public GitHub availability and extraction from an owner's device do not establish permission for public mirrors. [G8 vendor source](https://github.com/lge-qcom-dev/proprietary_vendor_lge_alphaplus/tree/4f3ad483bf645b52252b04eb48c3d4a0ccab643a) · [Common vendor source](https://github.com/lge-qcom-dev/proprietary_vendor_lge_sm8150-common/tree/a38f97ce91a63fb50833111d6e0f37571557499e) |
| Recovery boot and kernel | A complete boot image includes the compiled kernel, DTB and a recovery ramdisk. Audit the exact kernel, modules, embedded firmware and ramdisk contents and satisfy the applicable source and notice obligations. Preserve the effective config, pinned source, and scripts controlling compilation and installation. The corresponding published kernel commit is `8817f5e6c9372e59e0c10a8dbe96517f64e927a8`. [Kernel source](https://github.com/Magicolo/android_kernel_lge_sm8150/tree/8817f5e6c9372e59e0c10a8dbe96517f64e927a8) · [GPLv2 source requirements](https://www.gnu.org/licenses/gpl-faq.html#InstallationInformation) |
| Stock firmware and third-party downloads | The stock KDZ, OEM flash utilities, any USB drivers, and optional Google Apps are separate inputs. Distribute download references and integrity information where available. Resolve independent redistribution terms before attaching those files to a ROM release. |

GitHub requires publishers to establish the right to post content they did not create. The LG open-source portal covers listed open-source components according to their individual licenses. It did not establish a license for these proprietary inputs. Canadian Copyright Act sections 30.61 and 41.12 concern limited interoperability activities and information, subject to their own conditions. The presence of those provisions does not settle permission to publish the extracted or modified vendor binaries in this kit. Keep the publisher's legal basis with the artifact ledger before distribution. [GitHub Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service#d-user-generated-content) · [LG Open Source terms](https://opensource.lge.com/terms) · [Canada Copyright Act section 30.61](https://laws-lois.justice.gc.ca/eng/acts/C-42/section-30.61.html) · [Section 41.12](https://laws-lois.justice.gc.ca/eng/acts/C-42/section-41.12.html)

## License notice packaging defect

All three built partitions carry a compressed `etc/NOTICE.xml.gz`. Product passed strict XML parsing. System and vendor failed because their license text includes raw XML 1.0-invalid form-feed characters, 65 and 23 respectively. A diagnostic copy of each parsed after replacing form feeds with line breaks. No staged ROM image was changed by the check.

A later candidate normalized the form feeds before signing and rebuilt the images. All three packaged notices parsed, both OTA signatures verified and VINTF passed. Its OTA SHA-256 is `b8b12479298fc8240d589f504e37fa488c512c82915d7f0167cfb5ceee68ce9f`. The earlier inventory and vendor rights findings still apply to the unchanged proprietary content. An Android-generated notice file cannot establish a license for every vendor blob.

```bash
python3 tools/check-target-notices.py /path/to/signed-target-files.zip
```

When the only issue is form feeds, use `--stage-normalized-to NEW_DIRECTORY` to prepare corrected entries without modifying the input ZIP. Replace the entries in a separate copy of the unsigned target-files, rebuild images through the signing tools, and check the final signed target-files. Preserve the applicable license text and source obligations.

The [repository license](../LICENSE) and [NOTICE file](../NOTICE) cover original public project material. They do not change the distribution status of the OEM files in this audit.

## Finish the publication decision

1. Resolve rights for the identified stock and modified proprietary inputs, including dependencies inherited through both vendor trees. Attach the recorded license or applicable basis to each included group. Verify that a distribution-ready source and notice set is complete.
2. If any files cannot be publicly distributed, a user-local build flow is the next option to qualify. Document exact firmware and input hashes, extract from a lawfully obtained input, and review the compatibility patch material separately. Validate the resulting build from a new checkout. The current public manifest does not reproduce the complete carrier build by itself.
3. Fix and rerun the notice check, freeze the final source and binary versions, then test the intended signing family on a dedicated device. Include clean stock-to-recovery and existing-Lineage migration, first inbound/outbound voice, data, recovery/rollback, and a second same-key update. Record the firmware and slot before and after. [Release procedure](RELEASES.md) · [Validation matrix](VALIDATION.md)

## Final build 1795454921

The final build retains the pinned proprietary inputs from the qualification above. Its signed A/B payload matched the exported boot, DTBO and vbmeta images by size and SHA-256. The recovery kernel includes compiled touchscreen and proximity-controller firmware inputs. The staged AVB metadata also contains a build-host identifier. The exact flashable kit stays private. Published engineering files use the raw DTB and DTBO without that metadata, the documented open source, and the project public certificate.
