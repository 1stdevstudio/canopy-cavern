package com.yogi.canopycavern.mixin;

import com.yogi.canopycavern.world.spawn.SpawnSanctuaryProtection;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.LecternMenu;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(LecternMenu.class)
public abstract class LecternMenuMixin {

	@Inject(method = "clickMenuButton(Lnet/minecraft/world/entity/player/Player;I)Z", at = @At("HEAD"), cancellable = true)
	private void canopycavern$preventTakingProtectedLecternBook(
		Player player,
		int buttonId,
		CallbackInfoReturnable<Boolean> cir
	) {
		if (buttonId == LecternMenu.BUTTON_TAKE_BOOK
			&& player instanceof ServerPlayer serverPlayer
			&& SpawnSanctuaryProtection.isPositionProtected(serverPlayer.level(), serverPlayer.blockPosition())
			&& !SpawnSanctuaryProtection.hasAdminBypass(serverPlayer)) {
			cir.setReturnValue(false);
		}
	}
}
