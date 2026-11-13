package com.yogi.canopycavern.item;

import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.network.ModNetworking.OpenGuidePayload;
import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.LodestoneTracker;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.item.equipment.ArmorMaterial;
import net.minecraft.world.item.equipment.ArmorType;
import net.minecraft.world.item.equipment.EquipmentAsset;
import net.minecraft.world.item.equipment.EquipmentAssets;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.WallTorchBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Consumer;
import java.util.function.Function;

/**
 * Registers all Canopy Cavern armor sets, cavern/alpine tools, guidebook, tags, and Creative tab.
 */
public final class ModItems {
	private static final int COMPASS_SEARCH_COOLDOWN_TICKS = 100;

	public static final TagKey<Item> REPAIRS_THERMAL_ARMOR = itemTag("repairs_thermal_armor");
	public static final TagKey<Item> REPAIRS_MOSSWEAVE_ARMOR = itemTag("repairs_mossweave_armor");
	public static final TagKey<Item> REPAIRS_CRYSTAL_TOOLS = itemTag("repairs_crystal_tools");
	public static final TagKey<Structure> RELIC_COMPASS_TARGETS = TagKey.create(Registries.STRUCTURE, CanopyCavernMod.id("relic_compass_targets"));
	public static final TagKey<Structure> TIDE_COMPASS_TARGETS = TagKey.create(Registries.STRUCTURE, CanopyCavernMod.id("tide_compass_targets"));

	public static final ArmorMaterial PEAK_THERMAL_MATERIAL = armorMaterial(
		16, 2, 4, 3, 2, 15, 0.0F, 0.0F, REPAIRS_THERMAL_ARMOR, "peak_thermal"
	);
	public static final ArmorMaterial MOSSWEAVE_MATERIAL = armorMaterial(
		18, 1, 4, 3, 1, 18, 0.5F, 0.0F, REPAIRS_MOSSWEAVE_ARMOR, "mossweave"
	);
	public static final ToolMaterial GROTTO_CRYSTAL_MATERIAL = new ToolMaterial(
		BlockTags.INCORRECT_FOR_DIAMOND_TOOL,
		384,
		7.5F,
		2.5F,
		16,
		REPAIRS_CRYSTAL_TOOLS
	);

	private static final List<Item> REGISTERED_ITEMS = new ArrayList<>();

	public static final Item THERMAL_HOOD = registerArmor("thermal_hood", PEAK_THERMAL_MATERIAL, ArmorType.HELMET);
	public static final Item THERMAL_PARKA = registerArmor("thermal_parka", PEAK_THERMAL_MATERIAL, ArmorType.CHESTPLATE);
	public static final Item THERMAL_LEGGINGS = registerArmor("thermal_leggings", PEAK_THERMAL_MATERIAL, ArmorType.LEGGINGS);
	public static final Item THERMAL_BOOTS = registerArmor("thermal_boots", PEAK_THERMAL_MATERIAL, ArmorType.BOOTS);

	public static final Item MOSSWEAVE_CAP = registerArmor("mossweave_cap", MOSSWEAVE_MATERIAL, ArmorType.HELMET);
	public static final Item MOSSWEAVE_TUNIC = registerArmor("mossweave_tunic", MOSSWEAVE_MATERIAL, ArmorType.CHESTPLATE);
	public static final Item MOSSWEAVE_TROUSERS = registerArmor("mossweave_trousers", MOSSWEAVE_MATERIAL, ArmorType.LEGGINGS);
	public static final Item MOSSWEAVE_BOOTS = registerArmor("mossweave_boots", MOSSWEAVE_MATERIAL, ArmorType.BOOTS);

	public static final Item GROTTO_CRYSTAL_PICKAXE = register(
		"grotto_crystal_pickaxe",
		props -> new GrottoCrystalPickaxeItem(props.pickaxe(GROTTO_CRYSTAL_MATERIAL, 1.0F, -2.8F))
	);
	public static final Item ALPINE_CLIMBING_PICK = register(
		"alpine_climbing_pick",
		props -> new AlpineClimbingPickItem(props.durability(256))
	);
	public static final Item FLARE_TORCH = register(
		"flare_torch",
		props -> new FlareTorchItem(props.stacksTo(16))
	);
	public static final Item GLOW_LANTERN = register(
		"glow_lantern",
		props -> new GlowLanternItem(props.stacksTo(1))
	);
	public static final Item GROTTO_RELIC_COMPASS = register(
		"grotto_relic_compass",
		props -> new GrottoRelicCompassItem(props.stacksTo(1))
	);
	public static final Item CANOPY_FIELD_GUIDE = register(
		"canopy_field_guide",
		props -> new CanopyFieldGuideItem(props.stacksTo(1))
	);
	public static final Item ABYSSAL_TIDE_COMPASS = register(
		"abyssal_tide_compass",
		props -> new AbyssalTideCompassItem(props.stacksTo(1))
	);
	public static final Item SEA_GLASS_CHARM = register(
		"sea_glass_charm",
		props -> new SeaGlassCharmItem(props.stacksTo(1))
	);

	public static final CreativeModeTab GENERAL_TAB = Registry.register(
		BuiltInRegistries.CREATIVE_MODE_TAB,
		CanopyCavernMod.id("general"),
		FabricCreativeModeTab.builder()
			.title(Component.translatable("itemGroup.canopycavern.general"))
			.icon(() -> new ItemStack(CANOPY_FIELD_GUIDE))
			.displayItems((parameters, output) -> {
				for (Item item : REGISTERED_ITEMS) {
					output.accept(new ItemStack(item));
				}
			})
			.build()
	);

	private ModItems() {
	}

	/** Triggers static field registration cleanly during mod initialization. */
	public static void register() {
		CanopyCavernMod.LOGGER.info("Registered {} Canopy Cavern items & armor sets.", REGISTERED_ITEMS.size());
	}

	public static List<Item> allItems() {
		return List.copyOf(REGISTERED_ITEMS);
	}

	/** Counts worn pieces belonging to Peak Thermal armor set (0..4). */
	public static int countThermalArmor(Player player) {
		return countMatchingArmor(player, THERMAL_HOOD, THERMAL_PARKA, THERMAL_LEGGINGS, THERMAL_BOOTS);
	}

	/** Counts worn pieces belonging to Mossweave armor set (0..4). */
	public static int countMossweaveArmor(Player player) {
		return countMatchingArmor(player, MOSSWEAVE_CAP, MOSSWEAVE_TUNIC, MOSSWEAVE_TROUSERS, MOSSWEAVE_BOOTS);
	}

	/** Returns true when player holds Glow Lantern in either hand. */
	public static boolean hasGlowLantern(Player player) {
		return hasHeldItem(player, GLOW_LANTERN);
	}

	/** Returns true when player holds Sea Glass Charm in either hand. */
	public static boolean hasSeaGlassCharm(Player player) {
		return hasHeldItem(player, SEA_GLASS_CHARM);
	}

	private static boolean hasHeldItem(Player player, Item item) {
		return player.getMainHandItem().is(item) || player.getOffhandItem().is(item);
	}

	private static int countMatchingArmor(Player player, Item head, Item chest, Item legs, Item feet) {
		int count = 0;
		if (player.getItemBySlot(EquipmentSlot.HEAD).is(head)) count++;
		if (player.getItemBySlot(EquipmentSlot.CHEST).is(chest)) count++;
		if (player.getItemBySlot(EquipmentSlot.LEGS).is(legs)) count++;
		if (player.getItemBySlot(EquipmentSlot.FEET).is(feet)) count++;
		return count;
	}

	private static TagKey<Item> itemTag(String path) {
		return TagKey.create(Registries.ITEM, CanopyCavernMod.id(path));
	}

	private static void sendActionBar(Player player, Component message) {
		if (player instanceof ServerPlayer serverPlayer) {
			serverPlayer.sendSystemMessage(message, true);
		}
	}

	private static ArmorMaterial armorMaterial(
		int durability,
		int headDef,
		int chestDef,
		int legsDef,
		int feetDef,
		int enchantValue,
		float toughness,
		float knockbackResistance,
		TagKey<Item> repairTag,
		String assetName
	) {
		Map<ArmorType, Integer> defense = new EnumMap<>(ArmorType.class);
		defense.put(ArmorType.HELMET, headDef);
		defense.put(ArmorType.CHESTPLATE, chestDef);
		defense.put(ArmorType.LEGGINGS, legsDef);
		defense.put(ArmorType.BOOTS, feetDef);
		ResourceKey<EquipmentAsset> assetKey = ResourceKey.create(EquipmentAssets.ROOT_ID, CanopyCavernMod.id(assetName));
		return new ArmorMaterial(
			durability,
			defense,
			enchantValue,
			SoundEvents.ARMOR_EQUIP_LEATHER,
			toughness,
			knockbackResistance,
			repairTag,
			assetKey
		);
	}

	private static Item registerArmor(String name, ArmorMaterial material, ArmorType type) {
		return register(name, props -> new DescribedItem(props.humanoidArmor(material, type)));
	}

	private static Item register(String name, Function<Item.Properties, Item> factory) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, CanopyCavernMod.id(name));
		Item item = factory.apply(new Item.Properties().setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		REGISTERED_ITEMS.add(item);
		return item;
	}

	private static class DescribedItem extends Item {
		DescribedItem(Properties properties) {
			super(properties);
		}

		@Override
		public void appendHoverText(
			ItemStack stack, TooltipContext context, TooltipDisplay display,
			Consumer<Component> lines, TooltipFlag flag
		) {
			super.appendHoverText(stack, context, display, lines, flag);
			String tooltipKey = getDescriptionId() + ".tooltip";
			lines.accept(Component.translatable(tooltipKey).withStyle(ChatFormatting.GRAY));
			lines.accept(Component.translatable(tooltipKey + ".detail").withStyle(ChatFormatting.GRAY));
		}
	}

	/** Pickaxe with faster mining speed against tough subterranean stone variants. */
	private static final class GrottoCrystalPickaxeItem extends DescribedItem {
		GrottoCrystalPickaxeItem(Properties properties) {
			super(properties);
		}

		@Override
		public float getDestroySpeed(ItemStack stack, BlockState state) {
			float base = super.getDestroySpeed(stack, state);
			if (state.is(Blocks.TUFF) || state.is(Blocks.GRANITE) || state.is(Blocks.DEEPSLATE) || state.is(Blocks.COBBLED_DEEPSLATE)) {
				return base * 1.35F;
			}
			return base;
		}
	}

	/** Climbing pick allowing controlled vertical boosts up cliffs and cave walls. */
	private static final class AlpineClimbingPickItem extends DescribedItem {
		AlpineClimbingPickItem(Properties properties) {
			super(properties);
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			ItemStack stack = player.getItemInHand(hand);
			if (player.getCooldowns().isOnCooldown(stack)) {
				return InteractionResult.FAIL;
			}
			if (level instanceof ServerLevel serverLevel) {
				Vec3 from = player.getEyePosition();
				Vec3 look = player.getLookAngle();
				BlockHitResult hit = level.clip(new ClipContext(from, from.add(look.scale(3.4)), ClipContext.Block.OUTLINE, ClipContext.Fluid.NONE, player));
				boolean nearSurface = hit.getType() == HitResult.Type.BLOCK || player.onGround() || player.horizontalCollision;
				if (!nearSurface) {
					sendActionBar(player, Component.translatable("item.canopycavern.alpine_climbing_pick.need_surface"));
					return InteractionResult.FAIL;
				}
				player.setDeltaMovement(look.x * 0.42, Math.max(0.56, look.y * 0.45 + 0.48), look.z * 0.42);
				player.syncVelocity = true;
				player.resetFallDistance();
				player.getCooldowns().addCooldown(stack, 28);
				if (!player.isCreative()) {
					stack.hurtAndBreak(1, player, hand);
				}
				serverLevel.playSound(null, player.blockPosition(), SoundEvents.STONE_HIT, SoundSource.PLAYERS, 0.9F, 1.2F);
				serverLevel.sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY() + 0.2, player.getZ(), 8, 0.2, 0.1, 0.2, 0.04);
			}
			return InteractionResult.SUCCESS;
		}
	}

	/** Long-range throwable flare torch placing torches along distant cliffs and cavern ceilings. */
	private static final class FlareTorchItem extends DescribedItem {
		FlareTorchItem(Properties properties) {
			super(properties);
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			ItemStack stack = player.getItemInHand(hand);
			Vec3 start = player.getEyePosition();
			Vec3 look = player.getLookAngle();
			BlockHitResult hit = level.clip(new ClipContext(start, start.add(look.scale(24.0)), ClipContext.Block.OUTLINE, ClipContext.Fluid.NONE, player));
			if (hit.getType() != HitResult.Type.BLOCK) {
				if (!level.isClientSide()) {
					sendActionBar(player, Component.translatable("item.canopycavern.flare_torch.no_target"));
				}
				return InteractionResult.FAIL;
			}

			Direction face = hit.getDirection();
			BlockPos targetPos = hit.getBlockPos().relative(face);
			if (player.isSpectator() || !level.isInWorldBounds(targetPos)
				|| !level.mayInteract(player, hit.getBlockPos()) || !level.mayInteract(player, targetPos)
				|| !player.mayUseItemAt(targetPos, face, stack) || !level.getBlockState(targetPos).canBeReplaced()) {
				return InteractionResult.FAIL;
			}

			BlockState torchState = null;
			if (face == Direction.UP) {
				BlockState floorTorch = Blocks.TORCH.defaultBlockState();
				if (floorTorch.canSurvive(level, targetPos)) {
					torchState = floorTorch;
				}
			} else if (face.getAxis().isHorizontal()) {
				BlockState wallTorch = Blocks.WALL_TORCH.defaultBlockState().setValue(WallTorchBlock.FACING, face);
				if (wallTorch.canSurvive(level, targetPos)) {
					torchState = wallTorch;
				}
			}
			if (torchState == null) {
				if (!level.isClientSide()) {
					sendActionBar(player, Component.translatable("item.canopycavern.flare_torch.no_surface"));
				}
				return InteractionResult.FAIL;
			}

			if (level instanceof ServerLevel serverLevel) {
				if (!serverLevel.setBlock(targetPos, torchState, Block.UPDATE_ALL)) {
					return InteractionResult.FAIL;
				}
				if (!player.isCreative()) {
					stack.shrink(1);
				}
				serverLevel.playSound(null, targetPos, SoundEvents.CAMPFIRE_CRACKLE, SoundSource.PLAYERS, 0.9F, 1.35F);
				serverLevel.sendParticles(
					ParticleTypes.FLAME,
					targetPos.getX() + 0.5,
					targetPos.getY() + 0.5,
					targetPos.getZ() + 0.5,
					12,
					0.18,
					0.18,
					0.18,
					0.02
				);
			}
			return InteractionResult.SUCCESS;
		}
	}

	/** Portable bioluminescent lantern reducing damp cavern strain and pulsing short-term cave clarity. */
	private static final class GlowLanternItem extends DescribedItem {
		GlowLanternItem(Properties properties) {
			super(properties);
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			ItemStack stack = player.getItemInHand(hand);
			if (player.getCooldowns().isOnCooldown(stack)) {
				return InteractionResult.FAIL;
			}
			if (level instanceof ServerLevel serverLevel) {
				player.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, 260, 0, true, false, true));
				player.getCooldowns().addCooldown(stack, 160);
				serverLevel.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 0.7F, 1.3F);
				serverLevel.sendParticles(ParticleTypes.GLOW, player.getX(), player.getY() + 1.0, player.getZ(), 14, 0.5, 0.4, 0.5, 0.03);
			}
			return InteractionResult.SUCCESS;
		}
	}

	/** Shared tunable compass locking onto the nearest structure in a configured structure tag. */
	private static class StructureCompassItem extends DescribedItem {
		private final TagKey<Structure> targetTag;
		private final String translationKeyPrefix;
		private final int searchRadiusChunks;

		StructureCompassItem(
			Properties properties,
			TagKey<Structure> targetTag,
			String translationKeyPrefix,
			int searchRadiusChunks
		) {
			super(properties);
			this.targetTag = targetTag;
			this.translationKeyPrefix = translationKeyPrefix;
			this.searchRadiusChunks = searchRadiusChunks;
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			ItemStack stack = player.getItemInHand(hand);
			if (player.getCooldowns().isOnCooldown(stack)) {
				return InteractionResult.FAIL;
			}
			if (level instanceof ServerLevel serverLevel) {
				player.getCooldowns().addCooldown(stack, COMPASS_SEARCH_COOLDOWN_TICKS);
				BlockPos target = serverLevel.findNearestMapStructure(targetTag, player.blockPosition(), searchRadiusChunks, false);
				if (target == null) {
					sendActionBar(player, Component.translatable(translationKeyPrefix + ".not_found"));
					return InteractionResult.FAIL;
				}
				stack.set(
					DataComponents.LODESTONE_TRACKER,
					new LodestoneTracker(Optional.of(GlobalPos.of(serverLevel.dimension(), target)), false)
				);
				double dist = Math.sqrt(player.blockPosition().distSqr(target));
				serverLevel.playSound(null, player.blockPosition(), SoundEvents.LODESTONE_COMPASS_LOCK, SoundSource.PLAYERS, 0.85F, 1.15F);
				sendActionBar(
					player,
					Component.translatable(translationKeyPrefix + ".locked", Math.round(dist))
				);
			}
			return InteractionResult.SUCCESS;
		}
	}

	/** Tunable relic compass aligning to the nearest shrine or echoing mineshaft hub. */
	private static final class GrottoRelicCompassItem extends StructureCompassItem {
		GrottoRelicCompassItem(Properties properties) {
			super(properties, RELIC_COMPASS_TARGETS, "item.canopycavern.grotto_relic_compass", 100);
		}
	}

	/** Ocean exploration compass aligning to Sunken Citadels, Thermal Observatories, or Reef Lighthouses. */
	private static final class AbyssalTideCompassItem extends StructureCompassItem {
		AbyssalTideCompassItem(Properties properties) {
			super(properties, TIDE_COMPASS_TARGETS, "item.canopycavern.abyssal_tide_compass", 140);
		}
	}

	/** Sea Glass Charm providing passive underwater breath support and an active Airlock Bubble Pulse. */
	private static final class SeaGlassCharmItem extends DescribedItem {
		SeaGlassCharmItem(Properties properties) {
			super(properties);
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			ItemStack stack = player.getItemInHand(hand);
			if (player.getCooldowns().isOnCooldown(stack)) {
				return InteractionResult.FAIL;
			}
			if (level instanceof ServerLevel serverLevel) {
				player.setAirSupply(player.getMaxAirSupply());
				player.addEffect(new MobEffectInstance(MobEffects.WATER_BREATHING, 400, 0, true, false, true));
				player.addEffect(new MobEffectInstance(MobEffects.DOLPHINS_GRACE, 200, 0, true, false, true));
				player.getCooldowns().addCooldown(stack, 400);
				serverLevel.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 0.8F, 1.35F);
				serverLevel.sendParticles(ParticleTypes.BUBBLE_POP, player.getX(), player.getY() + 1.0, player.getZ(), 18, 0.55, 0.45, 0.55, 0.05);
				sendActionBar(player, Component.translatable("item.canopycavern.sea_glass_charm.activated"));
			}
			return InteractionResult.SUCCESS;
		}
	}

	/** Starter and craftable field guide opening the bilingual guide + auto-shelter builder GUI. */
	private static final class CanopyFieldGuideItem extends DescribedItem {
		CanopyFieldGuideItem(Properties properties) {
			super(properties);
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			if (player instanceof ServerPlayer serverPlayer) {
				ServerPlayNetworking.send(serverPlayer, new OpenGuidePayload(false));
			}
			return InteractionResult.SUCCESS;
		}
	}
}
