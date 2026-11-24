package com.lge.ims.compat;

import java.util.Properties;

/** A device's explicit opt-in to the legacy LG IMS compatibility hooks. */
record LgImsCarrierProfile(String device, int slot, int carrierId, String plmn,
        String gid1, String operator, String country, String subOperator,
        boolean refreshLteVops, int voiceMaskFrom, int voiceMaskTo) {

    static LgImsCarrierProfile parse(Properties data) {
        int from = Integer.parseInt(data.getProperty("voiceMaskFrom", "-1"));
        int to = Integer.parseInt(data.getProperty("voiceMaskTo", "-1"));
        if (!(from == -1 && to == -1)
                && (from <= 0 || to < 0 || from == to || (to & ~from) != 0)) {
            throw new IllegalArgumentException("Voice mask change must clear existing bits");
        }
        return new LgImsCarrierProfile(
                require(data, "device", "[a-zA-Z0-9_.-]+"),
                Integer.parseInt(require(data, "slot", "[0-9]+")),
                Integer.parseInt(require(data, "carrierId", "[0-9]+")),
                require(data, "plmn", "[0-9]{5,6}"),
                require(data, "gid1", "[0-9a-fA-F]*"),
                require(data, "operator", "[A-Z0-9_]+"),
                require(data, "country", "[A-Z]{2}"),
                require(data, "subOperator", "[A-Z0-9_]+"),
                Boolean.parseBoolean(require(data, "refreshLteVops", "true|false")),
                from, to);
    }

    private static String require(Properties data, String key, String pattern) {
        String value = data.getProperty(key);
        if (value == null || !value.matches(pattern)) {
            throw new IllegalArgumentException("Invalid IMS profile attribute: " + key);
        }
        return value;
    }

    boolean matchesTarget(String model, int slotId) {
        return device.equals(model) && slot == slotId;
    }

    boolean matchesCarrier(int id, String simPlmn, String simGid1) {
        return carrierId == id && plmn.equals(simPlmn)
                && gid1.equalsIgnoreCase(simGid1 == null ? "" : simGid1);
    }
}
