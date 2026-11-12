package com.yogi.canopycavern.entity;

import com.yogi.canopycavern.CanopyCavernMod;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;

/**
 * Registers custom Canopy Cavern entities and default mob attributes.
 */
public final class ModEntities {

	private static final ResourceKey<EntityType<?>> VILLAGE_SENTINEL_KEY = ResourceKey.create(
		Registries.ENTITY_TYPE,
		CanopyCavernMod.id("village_sentinel")
	);

	public static final EntityType<VillageSentinelEntity> VILLAGE_SENTINEL = Registry.register(
		BuiltInRegistries.ENTITY_TYPE,
		VILLAGE_SENTINEL_KEY,
		EntityType.Builder.of(VillageSentinelEntity::new, MobCategory.MISC)
			.sized(0.6F, 1.95F)
			.eyeHeight(1.62F)
			.clientTrackingRange(10)
			.build(VILLAGE_SENTINEL_KEY)
	);

	private ModEntities() {
	}

	public static void register() {
		FabricDefaultAttributeRegistry.register(VILLAGE_SENTINEL, VillageSentinelEntity.createAttributes());
		CanopyCavernMod.LOGGER.info("Registered Canopy Cavern entities.");
	}
}
