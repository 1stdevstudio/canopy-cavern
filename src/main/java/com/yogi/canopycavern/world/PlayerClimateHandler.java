package com.yogi.canopycavern.world;

import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.config.CanopyCavernConfig;
import com.yogi.canopycavern.core.ClimateSimulation;
import com.yogi.canopycavern.core.ClimateSimulation.ClimateInput;
import com.yogi.canopycavern.core.ClimateSimulation.ClimateSnapshot;
import com.yogi.canopycavern.core.EnvironmentTelemetry.AmbientInput;
import com.yogi.canopycavern.item.ModItems;
import com.yogi.canopycavern.network.ModNetworking.ClimateSyncPayload;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.ItemTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CampfireBlock;
import net.minecraft.world.level.block.state.BlockState;

import java.util.ArrayList;
import java.util.List;

/**
 * Server tick and join handler for starter guidebook gifts, automatic Recipe Book unlocks,
 * climate evaluation, armor set bonuses, campfire/shelter comfort buffs, and reactive cave flora.
 */
public final class PlayerClimateHandler {

	private static final String STARTER_GUIDE_TAG = "canopycavern_guided_v1";
	private static final int CLIMATE_EVAL_INTERVAL_TICKS = 10;
	private static final int RECIPE_CHECK_INTERVAL_TICKS = 40;

	private PlayerClimateHandler() {
	}

	public static void register() {
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> onPlayerJoin(handler.player));
		ServerTickEvents.END_SERVER_TICK.register(PlayerClimateHandler::onServerTick);
	}

	private static void onPlayerJoin(ServerPlayer player) {
		CanopyCavernConfig config = CanopyCavernMod.getConfig();
		if (config.starterFieldGuideEnabled() && !player.entityTags().contains(STARTER_GUIDE_TAG)) {
			player.addTag(STARTER_GUIDE_TAG);
			ItemStack guide = new ItemStack(ModItems.CANOPY_FIELD_GUIDE);
			if (!player.addItem(guide)) {
				player.spawnAtLocation(player.level(), guide);
			}
			player.awardRecipesByKey(List.of(recipeKey("canopy_field_guide"), recipeKey("flare_torch")));
			player.sendSystemMessage(Component.translatable("message.canopycavern.welcome_tip"), false);
		}
		evaluatePlayerClimate(player, player.level());
	}

	private static void onServerTick(MinecraftServer server) {
		long tick = server.getTickCount();
		if (tick % CLIMATE_EVAL_INTERVAL_TICKS != 0) {
			return;
		}
		boolean checkRecipes = (tick % RECIPE_CHECK_INTERVAL_TICKS == 0);
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			ServerLevel level = player.level();
			evaluatePlayerClimate(player, level);
			if (checkRecipes) {
				unlockMatchingRecipes(player);
			}
		}
	}

	private static void evaluatePlayerClimate(ServerPlayer player, ServerLevel level) {
		BlockPos pos = player.blockPosition();
		var biomeHolder = level.getBiome(pos);
		Biome biome = biomeHolder.value();
		String biomeId = biomeHolder.unwrapKey().map(key -> key.identifier().toString()).orElse("minecraft:plains");

		boolean canSeeSky = level.canSeeSky(pos.above());
		int skyLight = level.getBrightness(LightLayer.SKY, pos.above());
		long dayTime = level.getOverworldClockTime() % 24000L;
		boolean night = dayTime >= 13000L && dayTime <= 23000L;

		boolean nearCampfire = false;
		boolean nearLava = false;
		for (BlockPos scan : BlockPos.betweenClosed(pos.offset(-4, -2, -4), pos.offset(4, 2, 4))) {
			BlockState state = level.getBlockState(scan);
			if ((state.is(Blocks.CAMPFIRE) || state.is(Blocks.SOUL_CAMPFIRE)) && state.getValue(CampfireBlock.LIT)) {
				nearCampfire = true;
			} else if (state.is(Blocks.LAVA)) {
				nearLava = true;
			}
		}
		boolean enclosedShelter = isEnclosedShelter(level, pos);

		int thermalCount = ModItems.countThermalArmor(player);
		int mossCount = ModItems.countMossweaveArmor(player);
		boolean glowLantern = ModItems.hasGlowLantern(player);

		ClimateSnapshot snapshot = ClimateSimulation.evaluate(new ClimateInput(
			new AmbientInput(
				biome.getBaseTemperature(),
				pos.getY(),
				level.getSeaLevel(),
				canSeeSky,
				skyLight,
				level.isRainingAt(pos.above()),
				night,
				player.isInWater()
			),
			biomeId,
			thermalCount,
			mossCount,
			glowLantern,
			nearCampfire,
			enclosedShelter,
			nearLava,
			level.getGameTime()
		));

		ServerPlayNetworking.send(player, new ClimateSyncPayload(
			snapshot.humidityPercent(),
			snapshot.microWeather().id(),
			snapshot.status().id(),
			snapshot.thermalInsulationPercent(),
			snapshot.cavernCoolingPercent(),
			snapshot.perceivedCelsius(),
			snapshot.frostPenaltyActive(),
			snapshot.heatPenaltyActive(),
			snapshot.warmthRecoveryActive(),
			nearCampfire,
			enclosedShelter
		));

		applySurvivalEffects(player, level, snapshot, mossCount, nearCampfire);
		pulseReactiveCaveFlora(level, pos, snapshot, biomeId);
	}

	private static boolean isShelterBarrier(BlockState state) {
		return !state.isAir() && !state.canBeReplaced() && state.getFluidState().isEmpty();
	}

	private static boolean isEnclosedShelter(ServerLevel level, BlockPos pos) {
		if (!level.getBlockState(pos.above()).getFluidState().isEmpty()) {
			return false;
		}
		boolean roofFound = false;
		for (int dy = 2; dy <= 5; dy++) {
			BlockPos roofPos = pos.above(dy);
			if (isShelterBarrier(level.getBlockState(roofPos))) {
				roofFound = true;
				break;
			}
		}
		if (!roofFound) {
			return false;
		}
		int walledSides = 0;
		for (var dir : net.minecraft.core.Direction.Plane.HORIZONTAL) {
			for (int dist = 1; dist <= 3; dist++) {
				BlockPos sidePos = pos.above().relative(dir, dist);
				if (isShelterBarrier(level.getBlockState(sidePos))) {
					walledSides++;
					break;
				}
			}
		}
		return walledSides >= 3;
	}

	private static void applySurvivalEffects(
		ServerPlayer player,
		ServerLevel level,
		ClimateSnapshot snapshot,
		int mossCount,
		boolean nearCampfire
	) {
		if (!player.isCreative() && !player.isSpectator() && ModItems.hasSeaGlassCharm(player) && player.isInWater()) {
			player.addEffect(new MobEffectInstance(MobEffects.WATER_BREATHING, 45, 0, true, false, false));
		}

		CanopyCavernConfig config = CanopyCavernMod.getConfig();
		if (!config.climateSurvivalEnabled() || player.isCreative() || player.isSpectator()) {
			return;
		}

		if (snapshot.frostPenaltyActive()) {
			player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 35, 0, true, false, true));
			player.setTicksFrozen(Math.min(130, player.getTicksFrozen() + 18));
		} else if (nearCampfire && player.getTicksFrozen() > 0) {
			player.setTicksFrozen(Math.max(0, player.getTicksFrozen() - 25));
		}

		if (snapshot.heatPenaltyActive()) {
			player.addEffect(new MobEffectInstance(MobEffects.MINING_FATIGUE, 35, 0, true, false, true));
		}

		boolean inCave = switch (snapshot.telemetry().depthZone()) {
			case SHALLOW_CAVE, DEEP_CAVERN, ABYSSAL_DEPTHS -> true;
			case SURFACE, HIGH_RIDGE -> false;
		};
		if (mossCount >= 4 && inCave) {
			player.addEffect(new MobEffectInstance(MobEffects.SPEED, 40, 0, true, false, false));
		}

		if (snapshot.warmthRecoveryActive() && nearCampfire && player.getHealth() < player.getMaxHealth() && (level.getGameTime() % 60L == 0L)) {
			player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 40, 0, true, false, true));
		}
	}

	private static void pulseReactiveCaveFlora(ServerLevel level, BlockPos center, ClimateSnapshot snapshot, String biomeId) {
		if (snapshot.humidityPercent() < 70 && !biomeId.equals("canopycavern:verdant_grotto")) {
			return;
		}
		if (level.getGameTime() % 20L != 0L) {
			return;
		}
		for (BlockPos scan : BlockPos.betweenClosed(center.offset(-3, -1, -3), center.offset(3, 3, 3))) {
			BlockState state = level.getBlockState(scan);
			if (state.is(Blocks.CAVE_VINES) || state.is(Blocks.CAVE_VINES_PLANT) || state.is(Blocks.SPORE_BLOSSOM) || state.is(Blocks.GLOW_LICHEN)) {
				level.sendParticles(
					ParticleTypes.GLOW,
					scan.getX() + 0.5,
					scan.getY() + 0.4,
					scan.getZ() + 0.5,
					2,
					0.25,
					0.25,
					0.25,
					0.01
				);
				break;
			}
		}
	}

	private static void unlockMatchingRecipes(ServerPlayer player) {
		var inv = player.getInventory();
		boolean hasWoolOrLeather = hasTaggedItem(inv, ItemTags.WOOL) || hasItem(inv, Items.LEATHER);
		boolean hasMoss = hasItem(inv, Items.MOSS_BLOCK);
		boolean hasAmethyst = hasItem(inv, Items.AMETHYST_SHARD);
		boolean hasIron = hasItem(inv, Items.IRON_INGOT);
		boolean hasOceanMaterial =
			hasItem(inv, Items.PRISMARINE_CRYSTALS)
				|| hasItem(inv, Items.PRISMARINE_SHARD)
				|| hasItem(inv, Items.NAUTILUS_SHELL)
				|| hasItem(inv, Items.KELP);

		List<ResourceKey<Recipe<?>>> unlocks = new ArrayList<>();
		if (hasWoolOrLeather) {
			unlocks.add(recipeKey("thermal_hood"));
			unlocks.add(recipeKey("thermal_parka"));
			unlocks.add(recipeKey("thermal_leggings"));
			unlocks.add(recipeKey("thermal_boots"));
		}
		if (hasMoss) {
			unlocks.add(recipeKey("mossweave_cap"));
			unlocks.add(recipeKey("mossweave_tunic"));
			unlocks.add(recipeKey("mossweave_trousers"));
			unlocks.add(recipeKey("mossweave_boots"));
		}
		if (hasAmethyst) {
			unlocks.add(recipeKey("grotto_crystal_pickaxe"));
			unlocks.add(recipeKey("glow_lantern"));
			unlocks.add(recipeKey("grotto_relic_compass"));
		}
		if (hasIron) {
			unlocks.add(recipeKey("alpine_climbing_pick"));
		}
		if (hasOceanMaterial) {
			unlocks.add(recipeKey("abyssal_tide_compass"));
			unlocks.add(recipeKey("sea_glass_charm"));
		}
		if (!unlocks.isEmpty()) {
			player.awardRecipesByKey(unlocks);
		}
	}

	private static boolean hasItem(net.minecraft.world.entity.player.Inventory inv, Item target) {
		for (int i = 0; i < inv.getContainerSize(); i++) {
			if (inv.getItem(i).is(target)) {
				return true;
			}
		}
		return false;
	}

	private static boolean hasTaggedItem(net.minecraft.world.entity.player.Inventory inv, TagKey<Item> tag) {
		for (int i = 0; i < inv.getContainerSize(); i++) {
			if (inv.getItem(i).is(tag)) {
				return true;
			}
		}
		return false;
	}

	private static ResourceKey<Recipe<?>> recipeKey(String name) {
		return ResourceKey.create(Registries.RECIPE, CanopyCavernMod.id(name));
	}
}
