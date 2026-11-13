package com.yogi.canopycavern.mixin;

import com.yogi.canopycavern.world.spawn.SpawnSanctuaryProtection;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.ServerExplosion;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.List;

@Mixin(ServerExplosion.class)
public abstract class ServerExplosionMixin {

	@Shadow
	@Final
	private ServerLevel level;

	@Inject(method = "interactWithBlocks(Ljava/util/List;)V", at = @At("HEAD"))
	private void canopycavern$protectSanctuaryFromExplosions(List<BlockPos> targetBlocks, CallbackInfo ci) {
		if (targetBlocks == null || targetBlocks.isEmpty()) {
			return;
		}
		targetBlocks.removeIf(pos -> SpawnSanctuaryProtection.shouldBlockExplosion(this.level, pos));
	}
}
