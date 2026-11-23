package com.yogi.canopycavern.mixin;

import com.yogi.canopycavern.item.ModItems;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.block.PowderSnowBlock;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(PowderSnowBlock.class)
public abstract class PowderSnowBlockMixin {
	@Inject(method = "canEntityWalkOnPowderSnow", at = @At("HEAD"), cancellable = true)
	private static void canopycavern$cramponsWalkOnPowderSnow(Entity entity, CallbackInfoReturnable<Boolean> cir) {
		if (entity instanceof LivingEntity living && ModItems.wearsFrostspireCrampons(living)) {
			cir.setReturnValue(true);
		}
	}
}
