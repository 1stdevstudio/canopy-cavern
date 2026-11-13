package com.yogi.canopycavern.world;

import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.core.ShelterBlueprints;
import com.yogi.canopycavern.core.ShelterBlueprints.BlockSpec;
import com.yogi.canopycavern.core.ShelterBlueprints.BlueprintDefinition;
import com.yogi.canopycavern.core.ShelterBlueprints.MaterialCost;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CampfireBlock;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.FurnaceBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Authoritative server-side material verification and safe 3D construction service
 * for Canopy Cavern player-selected auto-shelter blueprints.
 */
public final class BlueprintBuilderService {

	private BlueprintBuilderService() {
	}

	/** Aggregates player inventory counts keyed by namespaced item ID. */
	public static Map<String, Integer> countInventoryItems(Inventory inventory) {
		Map<String, Integer> counts = new HashMap<>();
		for (int slot = 0; slot < inventory.getContainerSize(); slot++) {
			ItemStack stack = inventory.getItem(slot);
			if (stack.isEmpty()) {
				continue;
			}
			Identifier key = BuiltInRegistries.ITEM.getKey(stack.getItem());
			counts.merge(key.toString(), stack.getCount(), Integer::sum);
		}
		return counts;
	}

	/** Validates materials, verifies clear build site ahead of player, consumes items, and constructs shelter. */
	public static void handleBuildRequest(ServerPlayer player, String blueprintId) {
		BlueprintDefinition blueprint = ShelterBlueprints.findBlueprint(blueprintId);
		if (blueprint == null || player.isSpectator() || !(player.level() instanceof ServerLevel level)) {
			return;
		}

		boolean creative = player.isCreative();
		if (!creative && !ShelterBlueprints.hasAllMaterials(countInventoryItems(player.getInventory()), blueprint.materials())) {
			player.sendSystemMessage(Component.translatable("canopycavern.builder.missing_materials"), false);
			return;
		}

		Direction forward = player.getDirection();
		Direction right = forward.getClockWise();
		BlockPos origin = player.blockPosition();

		for (BlockSpec spec : blueprint.blocks()) {
			BlockPos targetPos = transformOffset(origin, forward, right, spec);
			if (!level.isInWorldBounds(targetPos)
				|| !level.getWorldBorder().isWithinBounds(targetPos)
				|| !isSafeToPlace(level, targetPos, spec.dy())) {
				player.sendSystemMessage(Component.translatable("canopycavern.builder.obstructed"), false);
				return;
			}
		}

		if (!creative) {
			consumeMaterials(player.getInventory(), blueprint.materials());
			player.getInventory().setChanged();
		}

		placeBlueprintBlocks(level, origin, forward, right, blueprint.blocks());
		BlockPos center = transformOffset(origin, forward, right, new BlockSpec(0, 1, 3, "minecraft:air"));
		level.playSound(null, center, SoundEvents.AMETHYST_BLOCK_PLACE, SoundSource.PLAYERS, 1.0F, 1.0F);
		level.sendParticles(ParticleTypes.HAPPY_VILLAGER, center.getX() + 0.5, center.getY() + 0.5, center.getZ() + 0.5, 24, 1.8, 1.0, 1.8, 0.05);
		player.sendSystemMessage(
			Component.translatable("canopycavern.builder.success", Component.translatable(blueprint.titleKey())),
			false
		);
		var adv = level.getServer().getAdvancements().get(CanopyCavernMod.id("build_shelter"));
		if (adv != null) {
			player.getAdvancements().award(adv, "built_shelter");
		}
	}

	private static BlockPos transformOffset(BlockPos origin, Direction forward, Direction right, BlockSpec spec) {
		return origin.relative(right, spec.dx()).relative(forward, spec.dz()).offset(0, spec.dy(), 0);
	}

	private static boolean isSafeToPlace(ServerLevel level, BlockPos pos, int localY) {
		BlockState existing = level.getBlockState(pos);
		// Even a replaceable-looking block can carry persistent player data.
		if (level.getBlockEntity(pos) != null) {
			return false;
		}
		if (existing.isAir() || existing.canBeReplaced()
			|| existing.is(BlockTags.LEAVES) || existing.is(BlockTags.FLOWERS)) {
			return true;
		}
		if (localY >= 0) {
			return false;
		}
		// Foundation can replace ordinary terrain, but never ores, player containers,
		// obsidian, machinery or arbitrary breakable construction.
		return existing.is(Blocks.STONE)
			|| existing.is(Blocks.DEEPSLATE)
			|| existing.is(Blocks.TUFF)
			|| existing.is(Blocks.CALCITE)
			|| existing.is(Blocks.GRANITE)
			|| existing.is(Blocks.DIORITE)
			|| existing.is(Blocks.ANDESITE)
			|| existing.is(Blocks.DIRT)
			|| existing.is(Blocks.GRASS_BLOCK)
			|| existing.is(Blocks.COARSE_DIRT)
			|| existing.is(Blocks.ROOTED_DIRT)
			|| existing.is(Blocks.PODZOL)
			|| existing.is(Blocks.MOSS_BLOCK)
			|| existing.is(Blocks.MUD)
			|| existing.is(Blocks.CLAY)
			|| existing.is(Blocks.GRAVEL)
			|| existing.is(Blocks.SAND)
			|| existing.is(Blocks.RED_SAND)
			|| existing.is(Blocks.SANDSTONE)
			|| existing.is(Blocks.RED_SANDSTONE)
			|| existing.is(Blocks.SNOW_BLOCK);
	}

	private static void consumeMaterials(Inventory inventory, List<MaterialCost> costs) {
		for (MaterialCost cost : costs) {
			Item requiredItem = BuiltInRegistries.ITEM.getValue(Identifier.parse(cost.itemId()));
			int remaining = cost.count();
			for (int slot = 0; slot < inventory.getContainerSize() && remaining > 0; slot++) {
				ItemStack stack = inventory.getItem(slot);
				if (stack.isEmpty() || !stack.is(requiredItem)) {
					continue;
				}
				int take = Math.min(remaining, stack.getCount());
				stack.shrink(take);
				remaining -= take;
			}
		}
	}

	private static void placeBlueprintBlocks(
		ServerLevel level,
		BlockPos origin,
		Direction forward,
		Direction right,
		List<BlockSpec> blocks
	) {
		// The last specification for a coordinate wins. This prevents intermediate
		// interior-air specs from deleting subsequently placed furniture.
		Map<BlockPos, BlockSpec> finalPlacements = new java.util.LinkedHashMap<>();
		for (BlockSpec spec : blocks) {
			finalPlacements.put(transformOffset(origin, forward, right, spec), spec);
		}

		List<Map.Entry<BlockPos, BlockSpec>> deferredAir = new java.util.ArrayList<>();
		List<Map.Entry<BlockPos, BlockSpec>> deferredDoors = new java.util.ArrayList<>();
		// Build floor, walls and roof before clearing underwater interiors.
		for (var entry : finalPlacements.entrySet()) {
			BlockSpec spec = entry.getValue();
			Block block = BuiltInRegistries.BLOCK.getValue(Identifier.parse(spec.blockId()));
			if (block instanceof DoorBlock) {
				deferredDoors.add(entry);
			} else if (block == Blocks.AIR) {
				deferredAir.add(entry);
			} else {
				level.setBlock(entry.getKey(), configureBlockState(block, forward, spec), Block.UPDATE_ALL);
			}
		}
		for (var entry : deferredAir) {
			level.setBlock(entry.getKey(), Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
		}
		for (var entry : deferredDoors) {
			BlockPos pos = entry.getKey();
			Block block = BuiltInRegistries.BLOCK.getValue(Identifier.parse(entry.getValue().blockId()));
			BlockState lower = block.defaultBlockState()
				.setValue(DoorBlock.FACING, forward.getOpposite())
				.setValue(DoorBlock.HALF, DoubleBlockHalf.LOWER);
			BlockState upper = lower.setValue(DoorBlock.HALF, DoubleBlockHalf.UPPER);
			level.setBlock(pos, lower, Block.UPDATE_ALL);
			level.setBlock(pos.above(), upper, Block.UPDATE_ALL);
		}
	}

	private static BlockState configureBlockState(Block block, Direction forward, BlockSpec spec) {
		BlockState state = block.defaultBlockState();
		if (block instanceof CampfireBlock) {
			return state.setValue(CampfireBlock.LIT, true);
		}
		if (block instanceof net.minecraft.world.level.block.LanternBlock && spec.dy() >= 2) {
			return state.setValue(net.minecraft.world.level.block.LanternBlock.HANGING, true);
		}
		if (block instanceof ChestBlock) {
			return state.setValue(ChestBlock.FACING, forward.getOpposite());
		}
		if (block instanceof FurnaceBlock) {
			return state.setValue(FurnaceBlock.FACING, forward.getOpposite());
		}
		return state;
	}
}
