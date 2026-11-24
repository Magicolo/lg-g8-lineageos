package com.lge.ims.compat;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Properties;

final class ProfileTest {
    public static void main(String[] args) throws Exception {
        Properties config = new Properties();
        try (var input = Files.newInputStream(Path.of(args[0]))) {
            config.load(input);
        }
        LgImsCarrierProfile profile = LgImsCarrierProfile.parse(config);
        assert profile.matchesTarget("alphaplus_lao_com", 0);
        assert !profile.matchesTarget("alphaplus", 0);
        assert !profile.matchesTarget("alphaplus_lao_com", 1);
        assert profile.matchesCarrier(2417, "302500", "55");
        assert !profile.matchesCarrier(2417, "302500", "99");
        assert !profile.matchesCarrier(2417, "302500", null);
        assert !profile.matchesCarrier(2417, "302510", "55");
        assert !profile.matchesCarrier(0, "302500", "55");
        assert profile.operator().equals("VTR") && profile.country().equals("CA")
                && profile.subOperator().equals("FZZ");
        assert profile.refreshLteVops() && profile.voiceMaskFrom() == 31 && profile.voiceMaskTo() == 27;

        config.replace("voiceMaskTo", "63");
        try {
            LgImsCarrierProfile.parse(config);
            throw new AssertionError("Adding voice mask bits was accepted");
        } catch (IllegalArgumentException expected) {
            // The profile must never enable bits that were absent.
        }
        config.remove("voiceMaskTo");
        try {
            LgImsCarrierProfile.parse(config);
            throw new AssertionError("An incomplete voice mask pair was accepted");
        } catch (IllegalArgumentException expected) {
            // Both mask fields are required if either is present.
        }
        config.remove("voiceMaskFrom");
        config.replace("device", "another_lg_model");
        config.replace("slot", "1");
        config.replace("carrierId", "123");
        config.replace("plmn", "123456");
        config.replace("gid1", "aB");
        config.replace("refreshLteVops", "false");
        profile = LgImsCarrierProfile.parse(config);
        assert profile.matchesTarget("another_lg_model", 1);
        assert profile.matchesCarrier(123, "123456", "Ab");
        assert !profile.matchesCarrier(2417, "302500", "55");
        assert !profile.refreshLteVops() && profile.voiceMaskFrom() < 0 && profile.voiceMaskTo() < 0;
        System.out.println("PASS: exact G8 match, negative scope, reject unsafe masks, synthetic alternate profile");
    }
}
