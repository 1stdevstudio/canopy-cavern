package com.yogi.canopycavern.mixin;

import com.yogi.canopycavern.core.ExpeditionEnchantmentRules;
import com.yogi.canopycavern.item.ExpeditionBoots;
import com.yogi.canopycavern.item.ExpeditionEnchantments;
import com.yogi.canopycavern.item.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(Player.class)
abstract class DeepFocusPlayerMixin {
	@Unique
	private int canopycavern$undergroundTicks;

	@Inject(method = "tick", at = @At("TAIL"))
	private void canopycavern$trackUndergroundTime(CallbackInfo callback) {
		Player player = (Player) (Object) this;
		if (player instanceof ServerPlayer serverPlayer) {
			ExpeditionBoots.tick(serverPlayer);
		}
		BlockPos head = player.blockPosition().above();
		Level level = player.level();
		boolean underground = ExpeditionEnchantmentRules.canBuildDeepFocus(
			level.dimension().equals(Level.OVERWORLD), player.isSpectator(), head.getY()
		) && level.getBrightness(LightLayer.SKY, head) <= 2;
		canopycavern$undergroundTicks =
			ExpeditionEnchantmentRules.caveTicks(canopycavern$undergroundTicks, underground);
	}

	@Inject(method = "getDestroySpeed", at = @At("RETURN"), cancellable = true)
	private void canopycavern$applyDeepFocus(BlockState state, CallbackInfoReturnable<Float> callback) {
		if (canopycavern$undergroundTicks < 60 || !(state.is(Blocks.DEEPSLATE) || state.is(Blocks.COBBLED_DEEPSLATE)
			|| state.is(Blocks.TUFF))) {
			return;
		}
		Player player = (Player) (Object) this;
		var tool = player.getMainHandItem();
		if (!tool.is(ItemTags.PICKAXES)) {
			return;
		}
		int level = ExpeditionEnchantments.level(player, ExpeditionEnchantments.DEEP_FOCUS, EquipmentSlot.MAINHAND);
		double multiplier = ExpeditionEnchantmentRules.deepFocusMultiplier(
			level, canopycavern$undergroundTicks, tool.is(ModItems.GROTTO_CRYSTAL_PICKAXE));
		if (multiplier > 1.0) {
			callback.setReturnValue((float) (callback.getReturnValue() * multiplier));
		}
	}
}
