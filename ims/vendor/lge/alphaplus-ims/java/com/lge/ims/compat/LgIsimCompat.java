package com.lge.ims.compat;

import android.app.ActivityThread;
import android.app.Application;
import android.telephony.SubscriptionManager;
import android.telephony.TelephonyManager;
import android.text.TextUtils;

import com.android.internal.telephony.ILGImsIsim;

import java.util.function.Function;

/** Process-local ISIM adapter for the G8 IMS app when the LG phone service is absent. */
public final class LgIsimCompat extends ILGImsIsim.Default {
    private final int mSlotId;

    private LgIsimCompat(int slotId) {
        mSlotId = slotId;
    }

    public static ILGImsIsim create(int slotId) {
        return new LgIsimCompat(slotId);
    }

    private TelephonyManager getTelephony() {
        Application app = ActivityThread.currentApplication();
        int subId = SubscriptionManager.getSubscriptionId(mSlotId);
        if (app == null || !SubscriptionManager.isValidSubscriptionId(subId)) {
            return null;
        }
        TelephonyManager telephony = app.getSystemService(TelephonyManager.class);
        return telephony != null ? telephony.createForSubscriptionId(subId) : null;
    }

    private <T> T read(Function<TelephonyManager, T> request, T unavailable) {
        TelephonyManager telephony = getTelephony();
        if (telephony == null) {
            return unavailable;
        }
        try {
            return request.apply(telephony);
        } catch (SecurityException | IllegalStateException e) {
            return unavailable;
        }
    }

    @Override
    public String getState() {
        return read(telephony -> {
            if (telephony.getSimApplicationState() != TelephonyManager.SIM_STATE_LOADED) {
                return "NOT_READY";
            }
            if (!telephony.isApplicationOnUicc(TelephonyManager.APPTYPE_ISIM)) {
                return "NOT_PRESENT";
            }
            String[] publicIdentities = telephony.getIsimImpu();
            return !TextUtils.isEmpty(telephony.getIsimDomain())
                    && !TextUtils.isEmpty(telephony.getIsimImpi())
                    && publicIdentities != null && publicIdentities.length != 0
                    && !TextUtils.isEmpty(publicIdentities[0]) ? "LOADED" : "NOT_READY";
        }, "NOT_READY");
    }

    @Override
    public String getDomain() {
        return read(TelephonyManager::getIsimDomain, null);
    }

    @Override
    public String getImpi() {
        return read(TelephonyManager::getIsimImpi, null);
    }

    @Override
    public String[] getImpu() {
        return read(TelephonyManager::getIsimImpu, null);
    }

    @Override
    public String getIst() {
        return read(TelephonyManager::getIsimIst, null);
    }

    @Override
    public String[] getPcscfAddress() {
        return read(TelephonyManager::getIsimPcscf, null);
    }

    @Override
    public String getChallengeResponse(String nonce) {
        if (TextUtils.isEmpty(nonce)) {
            return null;
        }
        return read(telephony -> telephony.getIccAuthentication(
                TelephonyManager.APPTYPE_ISIM, TelephonyManager.AUTHTYPE_EAP_AKA, nonce), null);
    }
}
