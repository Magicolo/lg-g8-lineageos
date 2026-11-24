package com.android.ims;

import android.net.Uri;
import android.os.SystemProperties;

import java.io.File;

/** LG G8 IMS configuration contract used by the Canadian stock IMS app. */
public final class LGImsFeature {
    public static final Uri CONTENT_URI = Uri.parse("content://com.lge.ims.provider.ims_feature");
    public static final boolean FEATURE_VOLTE_OPEN =
            SystemProperties.getInt("persist.product.lge.ims.volte_open", 0) > 0;

    private static final String CONFIG_DIRECTORY = "/product/etc/lg-ims";

    private LGImsFeature() {}

    public static String getCupssConfigDir() {
        return CONFIG_DIRECTORY;
    }

    public static File getFile(String name) {
        if (name == null || name.isEmpty() || !new File(name).getName().equals(name)) {
            return null;
        }
        File file = new File(CONFIG_DIRECTORY, name);
        return file.isFile() ? file : null;
    }
}
