package com.yogi.canopycavern.item;

import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.core.ExpeditionEnchantmentRules;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.block.Block;

public final class ExpeditionBoots {
	private static final TagKey<Block> ROCKY_GROUND =
		TagKey.create(Registries.BLOCK, CanopyCavernMod.id("rocky_ground"));
	private static final Identifier CAVE_GRIP_ID = CanopyCavernMod.id("expedition.cave_grip");
	private static final Identifier RIDGE_STEP_ID = CanopyCavernMod.id("expedition.ridge_step");
	private static final Identifier SEABED_STRIDE_ID = CanopyCavernMod.id("expedition.seabed_stride");

	private ExpeditionBoots() {
	}

	public static void tick(ServerPlayer player) {
		if (player.getItemBySlot(EquipmentSlot.FEET).isEnchanted() && player.onGround() && !player.isSpectator()) {
			boolean wet = player.isInWater();
			if (wet && !player.isSwimming()) {
				int stride = ExpeditionEnchantments.level(player, ExpeditionEnchantments.SEABED_STRIDE, EquipmentSlot.FEET);
				update(player, Attributes.WATER_MOVEMENT_EFFICIENCY, SEABED_STRIDE_ID,
					ExpeditionEnchantmentRules.seabedStride(stride, true, true, false));
				update(player, Attributes.KNOCKBACK_RESISTANCE, CAVE_GRIP_ID, 0.0);
				update(player, Attributes.STEP_HEIGHT, RIDGE_STEP_ID, 0.0);
				return;
			}
			if (!wet && player.level().getBlockState(player.getBlockPosBelowThatAffectsMyMovement()).is(ROCKY_GROUND)) {
				int grip = ExpeditionEnchantments.level(player, ExpeditionEnchantments.CAVE_GRIP, EquipmentSlot.FEET);
				int step = ExpeditionEnchantments.level(player, ExpeditionEnchantments.RIDGE_STEP, EquipmentSlot.FEET);
				var stepHeight = player.getAttribute(Attributes.STEP_HEIGHT);
				if (stepHeight != null) {
					var ownStep = stepHeight.getModifier(RIDGE_STEP_ID);
					double previous = ownStep == null ? 0.0 : ownStep.amount();
					update(player, Attributes.STEP_HEIGHT, RIDGE_STEP_ID,
						ExpeditionEnchantmentRules.ridgeStep(step, true, true, false, stepHeight.getValue() - previous));
				}
				update(player, Attributes.KNOCKBACK_RESISTANCE, CAVE_GRIP_ID,
					ExpeditionEnchantmentRules.caveGrip(grip, true, true, false));
				update(player, Attributes.WATER_MOVEMENT_EFFICIENCY, SEABED_STRIDE_ID, 0.0);
				return;
			}
		}
		update(player, Attributes.KNOCKBACK_RESISTANCE, CAVE_GRIP_ID, 0.0);
		update(player, Attributes.STEP_HEIGHT, RIDGE_STEP_ID, 0.0);
		update(player, Attributes.WATER_MOVEMENT_EFFICIENCY, SEABED_STRIDE_ID, 0.0);
	}

	private static void update(ServerPlayer player, Holder<Attribute> type, Identifier id, double amount) {
		var attribute = player.getAttribute(type);
		if (attribute == null) {
			return;
		}
		var current = attribute.getModifier(id);
		if (amount <= 0.0) {
			if (current != null) {
				attribute.removeModifier(id);
			}
		} else if (current == null || Math.abs(current.amount() - amount) > 1.0e-8) {
			attribute.addOrUpdateTransientModifier(new AttributeModifier(id, amount, AttributeModifier.Operation.ADD_VALUE));
		}
	}
}
