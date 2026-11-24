package com.lge.ims.compat;

import android.app.ActivityThread;
import android.app.Application;
import android.os.Build;
import android.telephony.SubscriptionManager;
import android.telephony.TelephonyManager;
import android.util.Log;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.Properties;

/** Selects an LG operator profile for a matching device and subscription. */
public final class LgCarrierCompat {
    private static final String PROFILE_PATH = "/product/etc/lg-ims/compat-profile.properties";
    private static final LgImsCarrierProfile PROFILE = loadProfile();

    private LgCarrierCompat() {}

    /** Compatibility entry point for the patched LG IMS APK. */
    public static String[] getProvisioningProfile(int slotId) {
        LgImsCarrierProfile profile = getActiveProfile(slotId);
        return profile == null ? null
                : new String[]{profile.operator(), profile.country(), profile.subOperator()};
    }

    static LgImsCarrierProfile getActiveProfile(int slotId) {
        if (PROFILE == null || !PROFILE.matchesTarget(Build.DEVICE, slotId)) {
            return null;
        }
        Application app = ActivityThread.currentApplication();
        int subId = SubscriptionManager.getSubscriptionId(slotId);
        if (app == null || !SubscriptionManager.isValidSubscriptionId(subId)) {
            return null;
        }
        TelephonyManager manager = app.getSystemService(TelephonyManager.class);
        if (manager == null) {
            return null;
        }
        try {
            TelephonyManager subscription = manager.createForSubscriptionId(subId);
            return PROFILE.matchesCarrier(subscription.getSimCarrierId(),
                    subscription.getSimOperator(), subscription.getGroupIdLevel1()) ? PROFILE : null;
        } catch (SecurityException | IllegalStateException e) {
            return null;
        }
    }

    private static LgImsCarrierProfile loadProfile() {
        try (FileInputStream source = new FileInputStream(PROFILE_PATH)) {
            Properties data = new Properties();
            data.load(source);
            return LgImsCarrierProfile.parse(data);
        } catch (FileNotFoundException e) {
            return null;
        } catch (IOException | IllegalArgumentException e) {
            Log.w("LgCarrierCompat", "Invalid LG IMS device profile", e);
            return null;
        }
    }
}
