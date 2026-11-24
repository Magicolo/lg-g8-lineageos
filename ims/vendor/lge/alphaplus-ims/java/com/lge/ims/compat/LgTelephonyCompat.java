package com.lge.ims.compat;

import android.app.ActivityThread;
import android.app.Application;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteException;
import android.net.ConnectivityManager;
import android.net.LinkProperties;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.TelephonyNetworkSpecifier;
import android.net.Uri;
import android.os.ServiceManager;
import android.telephony.AccessNetworkConstants;
import android.telephony.DataSpecificRegistrationInfo;
import android.telephony.LteVopsSupportInfo;
import android.telephony.NetworkRegistrationInfo;
import android.telephony.ServiceState;
import android.telephony.SubscriptionManager;
import android.telephony.TelephonyManager;
import android.util.Log;

import java.net.InetAddress;

/** Android telephony compatibility for the G8 IMS APK. */
public final class LgTelephonyCompat {
    private static final String TAG = "G8VoiceAvailability";
    private static final Uri ORDINARY_VOICE = Uri.parse(
            "content://com.lge.ims.provider.lgims/lgims_uc_session_voip");
    private static final String LOCAL_FEATURE = "nLocalFeature";

    private LgTelephonyCompat() {}

    public static boolean hasLgPhoneService() {
        return ServiceManager.checkService("com.lge.ims.phone") != null;
    }

    /** Refresh a native listener from the modem after listener creation or call release. */
    public static boolean shouldRefreshProfileVops(int slotId) {
        LgImsCarrierProfile profile = LgCarrierCompat.getActiveProfile(slotId);
        boolean supported = profile != null && profile.refreshLteVops()
                && !hasLgPhoneService()
                && isLteVopsSupportedForSlot(slotId);
        if (supported) {
            Log.i(TAG, "Refreshing modem LTE VoPS for slot " + slotId);
        }
        return supported;
    }

    /** Apply the configured ordinary voice mask before native IMS reads it. */
    public static void applyProfileVoiceBeforeStart(int slotId) {
        LgImsCarrierProfile profile = LgCarrierCompat.getActiveProfile(slotId);
        if (profile == null || profile.voiceMaskFrom() < 0 || hasLgPhoneService()) {
            return;
        }
        Application app = ActivityThread.currentApplication();
        if (app == null || !"com.lge.ims".equals(app.getPackageName())) {
            return;
        }
        ContentResolver resolver = app.getContentResolver();
        try (Cursor row = resolver.query(ORDINARY_VOICE, new String[] {LOCAL_FEATURE},
                null, null, null)) {
            if (row == null || row.getCount() != 1 || !row.moveToFirst()
                    || row.getInt(0) != profile.voiceMaskFrom()) {
                return;
            }
        } catch (SecurityException | IllegalArgumentException | SQLiteException e) {
            Log.w(TAG, "Could not read LG voice profile", e);
            return;
        }
        if (LgCarrierCompat.getActiveProfile(slotId) != profile) {
            return;
        }
        ContentValues values = new ContentValues();
        values.put(LOCAL_FEATURE, profile.voiceMaskTo());
        try {
            int changed = resolver.update(ORDINARY_VOICE, values, LOCAL_FEATURE + "=?",
                    new String[] {Integer.toString(profile.voiceMaskFrom())});
            if (changed == 1) {
                Log.i(TAG, "Updated LG ordinary voice mask to " + profile.voiceMaskTo());
            }
        } catch (SecurityException | IllegalArgumentException | SQLiteException e) {
            Log.w(TAG, "Could not update LG voice profile", e);
        }
    }

    public static boolean isLteVopsSupportedForSlot(int slotId) {
        Application app = ActivityThread.currentApplication();
        int subId = SubscriptionManager.getSubscriptionId(slotId);
        if (app == null || !SubscriptionManager.isValidSubscriptionId(subId)) {
            return false;
        }
        TelephonyManager telephony = app.getSystemService(TelephonyManager.class);
        if (telephony == null) {
            return false;
        }
        try {
            return isLteVopsSupported(telephony.createForSubscriptionId(subId).getServiceState());
        } catch (SecurityException e) {
            return false;
        }
    }

    public static boolean isLteVopsSupported(ServiceState serviceState) {
        if (serviceState == null) {
            return false;
        }
        NetworkRegistrationInfo registration = serviceState.getNetworkRegistrationInfo(
                NetworkRegistrationInfo.DOMAIN_PS, AccessNetworkConstants.TRANSPORT_TYPE_WWAN);
        if (registration == null || !registration.isRegistered()) {
            return false;
        }
        DataSpecificRegistrationInfo details = registration.getDataSpecificInfo();
        return details != null
                && details.getVopsSupportInfo() instanceof LteVopsSupportInfo lte
                && lte.isVopsSupported();
    }

    public static int getCallStateForSlot(TelephonyManager telephony, int slotId) {
        int subId = SubscriptionManager.getSubscriptionId(slotId);
        return SubscriptionManager.isValidSubscriptionId(subId)
                ? telephony.createForSubscriptionId(subId).getCallStateForSubscription()
                : TelephonyManager.CALL_STATE_IDLE;
    }

    public static void setCellInfoListRate(TelephonyManager telephony, int rate) {
        int subId = telephony.getSubscriptionId();
        if (SubscriptionManager.isValidSubscriptionId(subId)) {
            telephony.setCellInfoListRate(rate, subId);
        }
    }

    public static String[] getPcscfAddress(TelephonyManager telephony, String apnType) {
        if (!"ims".equals(apnType)) {
            return null;
        }
        Application app = ActivityThread.currentApplication();
        int subId = telephony.getSubscriptionId();
        if (app == null || !SubscriptionManager.isValidSubscriptionId(subId)) {
            return null;
        }
        ConnectivityManager connectivity = app.getSystemService(ConnectivityManager.class);
        if (connectivity == null) {
            return null;
        }
        for (Network network : connectivity.getAllNetworks()) {
            NetworkCapabilities capabilities = connectivity.getNetworkCapabilities(network);
            if (capabilities == null
                    || !capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)
                    || !capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_IMS)
                    || !matchesSubscription(capabilities, subId)) {
                continue;
            }
            LinkProperties link = connectivity.getLinkProperties(network);
            if (link != null && !link.getPcscfServers().isEmpty()) {
                return link.getPcscfServers().stream()
                        .map(InetAddress::getHostAddress).toArray(String[]::new);
            }
        }
        return null;
    }

    private static boolean matchesSubscription(NetworkCapabilities capabilities, int subId) {
        return capabilities.getSubscriptionIds().contains(subId)
                || capabilities.getNetworkSpecifier() instanceof TelephonyNetworkSpecifier specifier
                && specifier.getSubscriptionId() == subId;
    }
}
