package com.yogi.canopycavern.core;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ExpeditionEnchantmentRulesTest {
	@Test
	void deepFocusRequiresContinuousUndergroundTime() {
		assertEquals(0, ExpeditionEnchantmentRules.caveTicks(59, false));
		assertEquals(60, ExpeditionEnchantmentRules.caveTicks(59, true));
		assertEquals(60, ExpeditionEnchantmentRules.caveTicks(60, true));
		assertEquals(1.0, ExpeditionEnchantmentRules.deepFocusMultiplier(2, 59, false));
		assertEquals(1.1, ExpeditionEnchantmentRules.deepFocusMultiplier(1, 60, false));
		assertEquals(1.2, ExpeditionEnchantmentRules.deepFocusMultiplier(2, 60, false));
	}

	@Test
	void onlyOverworldPlayersAtCaveDepthCanQualifyForDeepFocus() {
		assertTrue(ExpeditionEnchantmentRules.canBuildDeepFocus(true, false, 16));
		assertFalse(ExpeditionEnchantmentRules.canBuildDeepFocus(false, false, 16));
		assertFalse(ExpeditionEnchantmentRules.canBuildDeepFocus(true, true, 16));
		assertFalse(ExpeditionEnchantmentRules.canBuildDeepFocus(true, false, 17));
	}

	@Test
	void grottoPickaxeGetsTheSmallerDeepFocusMultiplierAndLevelsAreCapped() {
		assertEquals(1.05, ExpeditionEnchantmentRules.deepFocusMultiplier(1, 60, true));
		assertEquals(1.1, ExpeditionEnchantmentRules.deepFocusMultiplier(100, 60, true));
		assertEquals(1.0, ExpeditionEnchantmentRules.deepFocusMultiplier(0, 60, true));
	}

	@Test
	void bootsBonusesRequireSolidGroundAndDoNotWorkWhileSwimming() {
		assertEquals(0.20, ExpeditionEnchantmentRules.caveGrip(2, true, true, false));
		assertEquals(0.0, ExpeditionEnchantmentRules.caveGrip(2, true, false, false));
		assertEquals(0.0, ExpeditionEnchantmentRules.caveGrip(2, true, true, true));
		assertEquals(0.4, ExpeditionEnchantmentRules.ridgeStep(1, true, true, false, 0.6));
		assertEquals(0.0, ExpeditionEnchantmentRules.ridgeStep(1, true, true, false, 1.2));
		assertEquals(0.0, ExpeditionEnchantmentRules.ridgeStep(1, false, true, false, 0.6));
		assertEquals(0.30, ExpeditionEnchantmentRules.seabedStride(2, true, true, false));
		assertEquals(0.0, ExpeditionEnchantmentRules.seabedStride(2, true, true, true));
		assertEquals(0.0, ExpeditionEnchantmentRules.seabedStride(2, false, true, false));
	}
}
