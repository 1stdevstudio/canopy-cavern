package com.yogi.canopycavern.mixin;

import com.yogi.canopycavern.world.spawn.SpawnSanctuaryProtection;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.level.NaturalSpawner;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.biome.MobSpawnSettings;
import net.minecraft.world.level.chunk.ChunkGenerator;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(NaturalSpawner.class)
public abstract class NaturalSpawnerMixin {

	@Inject(
		method = "isValidSpawnPostitionForType(Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/world/entity/MobCategory;Lnet/minecraft/world/level/StructureManager;Lnet/minecraft/world/level/chunk/ChunkGenerator;Lnet/minecraft/world/level/biome/MobSpawnSettings$SpawnerData;Lnet/minecraft/core/BlockPos$MutableBlockPos;D)Z",
		at = @At("HEAD"),
		cancellable = true
	)
	private static void canopycavern$blockSanctuaryHostileSpawns(
		ServerLevel level,
		MobCategory category,
		StructureManager structureManager,
		ChunkGenerator generator,
		MobSpawnSettings.SpawnerData spawnerData,
		BlockPos.MutableBlockPos pos,
		double distanceSq,
		CallbackInfoReturnable<Boolean> cir
	) {
		if (SpawnSanctuaryProtection.shouldSuppressNaturalSpawn(level, category, pos)) {
			cir.setReturnValue(false);
		}
	}
}
