# LG G8 LineageOS 24.0 source preview

This is an unofficial Android 17 source preview for the Canadian LG G8 ThinQ (LM-G820UM2, alphaplus) and stock 40b firmware. It publishes the source changes for the camera and flashlight, the call microphone route, NFC driver selection, and kernel page-table isolation. Other model, firmware and carrier combinations are outside the test scope.

The manifest pins the LineageOS platform and LG device dependencies and selects four fork branches for the reviewed patches. The fork commits are listed in the Git history of each component. The manifest is a source reference. It has not been built from a fresh checkout.

The LG IMS port still depends on firmware-specific files and compatibility changes that require a separate redistribution review. Those changes, the Google Apps add-on, and installable ROM packages are excluded from this preview. The device test evidence from the full development build does not establish feature parity for this source preview.

Upstream source and licenses remain with the individual projects. New changes in the device and camera repos follow their existing Android source licensing. The LG kernel tree retains its Linux kernel licensing.
