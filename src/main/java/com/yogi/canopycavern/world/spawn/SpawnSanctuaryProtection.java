package com.yogi.canopycavern.world.spawn;

import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.config.CanopyCavernConfig;
import com.yogi.canopycavern.entity.VillageSentinelEntity;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.player.AttackBlockCallback;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.permission.v1.PermissionPredicates;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.permissions.PermissionLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.decoration.ItemFrame;
import net.minecraft.world.entity.decoration.painting.Painting;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BellBlock;
import net.minecraft.world.level.block.ButtonBlock;
import net.minecraft.world.level.block.CartographyTableBlock;
import net.minecraft.world.level.block.CraftingTableBlock;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.FenceGateBlock;
import net.minecraft.world.level.block.LecternBlock;
import net.minecraft.world.level.block.TrapDoorBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.BoundingBox;

import java.util.function.Predicate;

/**
 * Server-side spawn protection, explosion guard, hostile-spawn suppression, and arrival
 * climate-safe zone queries for installed Canopy Sanctuary hubs.
 */
public final class SpawnSanctuaryProtection {
	public static final Identifier PERMISSION_MANAGE = Identifier.fromNamespaceAndPath(CanopyCavernMod.MOD_ID, "command.sanctuary");
	public static final Identifier PERMISSION_BYPASS = Identifier.fromNamespaceAndPath(CanopyCavernMod.MOD_ID, "sanctuary.bypass");

	private static final Predicate<CommandSourceStack> MANAGE_PREDICATE =
		PermissionPredicates.require(PERMISSION_MANAGE, PermissionLevel.ADMINS);
	private static final Predicate<CommandSourceStack> BYPASS_PREDICATE =
		PermissionPredicates.require(PERMISSION_BYPASS, PermissionLevel.ADMINS);

	private SpawnSanctuaryProtection() {
	}

	/** Registers Fabric server-side block, entity, and damage protection listeners. */
	public static void registerEvents() {
		PlayerBlockBreakEvents.BEFORE.register((world, player, pos, state, blockEntity) -> {
			if (!(world instanceof ServerLevel serverLevel)) {
				return true;
			}
			if (canModifyProtectedBlock(serverLevel, player, pos)) {
				return true;
			}
			notifyProtected(player);
			return false;
		});

		AttackBlockCallback.EVENT.register((player, world, hand, pos, direction) -> {
			if (!(world instanceof ServerLevel serverLevel)) {
				return InteractionResult.PASS;
			}
			if (canModifyProtectedBlock(serverLevel, player, pos)) {
				return InteractionResult.PASS;
			}
			return InteractionResult.FAIL;
		});

		UseBlockCallback.EVENT.register((player, world, hand, hitResult) -> {
			if (!(world instanceof ServerLevel serverLevel)) {
				return InteractionResult.PASS;
			}
			BlockPos targetPos = hitResult.getBlockPos();
			BlockPos adjacentPos = targetPos.relative(hitResult.getDirection());
			if (!isPositionProtected(serverLevel, targetPos) && !isPositionProtected(serverLevel, adjacentPos)) {
				return InteractionResult.PASS;
			}
			if (hasAdminBypass(player)) {
				return InteractionResult.PASS;
			}
			BlockState state = serverLevel.getBlockState(targetPos);
			ItemStack held = player.getItemInHand(hand);
			if (isSafeUtilityInteraction(state, held, player.isShiftKeyDown())) {
				return InteractionResult.PASS;
			}
			notifyProtected(player);
			return InteractionResult.FAIL;
		});

		AttackEntityCallback.EVENT.register((player, world, hand, entity, hitResult) -> {
			if (!(world instanceof ServerLevel serverLevel)) {
				return InteractionResult.PASS;
			}
			if (!isPositionProtected(serverLevel, entity.blockPosition())) {
				return InteractionResult.PASS;
			}
			if (hasAdminBypass(player)) {
				return InteractionResult.PASS;
			}
			if (isProtectedSanctuaryEntity(entity)) {
				notifyProtected(player);
				return InteractionResult.FAIL;
			}
			return InteractionResult.PASS;
		});

		UseEntityCallback.EVENT.register((player, world, hand, entity, hitResult) -> {
			if (!(world instanceof ServerLevel serverLevel)) {
				return InteractionResult.PASS;
			}
			if (!isPositionProtected(serverLevel, entity.blockPosition()) || hasAdminBypass(player)) {
				return InteractionResult.PASS;
			}
			if (entity instanceof ItemFrame || entity instanceof ArmorStand || entity instanceof Painting) {
				notifyProtected(player);
				return InteractionResult.FAIL;
			}
			return InteractionResult.PASS;
		});

		ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) -> {
			if (!(entity.level() instanceof ServerLevel serverLevel)) {
				return true;
			}
			if (!isPositionProtected(serverLevel, entity.blockPosition())) {
				return true;
			}
			if (isProtectedSanctuaryEntity(entity)) {
				Entity attacker = source.getEntity();
				if (attacker instanceof Player player && hasAdminBypass(player)) {
					return true;
				}
				return false;
			}
			return true;
		});
	}

	/** Server-side check used by Sanctuary admin commands. */
	public static boolean hasAdminPermission(CommandSourceStack source) {
		return source != null && MANAGE_PREDICATE.test(source);
	}

	/** Server-side check determining if a player may alter blocks/decor inside an active Sanctuary. */
	public static boolean hasAdminBypass(Player player) {
		if (player instanceof ServerPlayer serverPlayer && serverPlayer.isCreative()) {
			return BYPASS_PREDICATE.test(serverPlayer.createCommandSourceStack());
		}
		return false;
	}

	public static boolean canModifyProtectedBlock(ServerLevel level, Player player, BlockPos pos) {
		if (!isPositionProtected(level, pos)) {
			return true;
		}
		return hasAdminBypass(player);
	}

	/** Returns true when explosion block changes at {@code pos} should be suppressed. */
	public static boolean shouldBlockExplosion(ServerLevel level, BlockPos pos) {
		return isPositionProtected(level, pos);
	}

	/** Returns true when natural hostile mob spawns inside Sanctuary should be blocked. */
	public static boolean shouldSuppressNaturalSpawn(ServerLevel level, MobCategory category, BlockPos pos) {
		if (category != MobCategory.MONSTER) {
			return false;
		}
		return isPositionProtected(level, pos);
	}

	/** Checks whether a world coordinate lies inside an installed and protected Sanctuary. */
	public static boolean isPositionProtected(ServerLevel level, BlockPos pos) {
		if (level == null || pos == null || !Level.OVERWORLD.equals(level.dimension())) {
			return false;
		}
		MinecraftServer server = level.getServer();
		if (server == null) {
			return false;
		}
		SanctuarySavedState state = SanctuarySavedState.get(server);
		if (!state.isProtectionActive()) {
			return false;
		}
		return isProtectedCoordinate(pos, state.center(), state.rotation(), SanctuaryManifest.loadDefault(), state.safeZoneRadius());
	}

	/** Pure coordinate geometry predicate (unit-testable without a running server). */
	public static boolean isProtectedCoordinate(
		BlockPos pos,
		BlockPos center,
		net.minecraft.world.level.block.Rotation rotation,
		SanctuaryManifest manifest,
		int safeZoneRadius
	) {
		if (pos == null || center == null || manifest == null) {
			return false;
		}
		BoundingBox env = manifest.envelopeBoundingBoxWorld(center, rotation);
		// Include slight headroom & foundation cushion around the full rotated Sanctuary envelope
		if (pos.getX() >= env.minX() - 2 && pos.getX() <= env.maxX() + 2
			&& pos.getZ() >= env.minZ() - 2 && pos.getZ() <= env.maxZ() + 2
			&& pos.getY() >= env.minY() - 6 && pos.getY() <= env.maxY() + 8) {
			return true;
		}
		int radius = Math.max(16, safeZoneRadius);
		int dx = Math.abs(pos.getX() - center.getX());
		int dz = Math.abs(pos.getZ() - center.getZ());
		return dx <= radius && dz <= radius
			&& pos.getY() >= env.minY() - 6
			&& pos.getY() <= env.maxY() + 8;
	}

	/**
	 * Checks whether the player stands inside an active Sanctuary's arrival climate-safe zone
	 * so new arrivals suffer neither cold frostbite nor cave heat inside the safe hub.
	 */
	public static boolean isInsideArrivalClimateSafeZone(ServerLevel level, BlockPos pos, CanopyCavernConfig config) {
		if (level == null || pos == null || config == null || !config.spawnHubClimateSafeZoneEnabled()) {
			return false;
		}
		if (!Level.OVERWORLD.equals(level.dimension())) {
			return false;
		}
		MinecraftServer server = level.getServer();
		if (server == null) {
			return false;
		}
		SanctuarySavedState state = SanctuarySavedState.get(server);
		if (!state.isInstalled()) {
			return false;
		}
		int radius = Math.max(CanopyCavernConfig.MIN_SPAWN_SAFE_RADIUS, config.spawnHubArrivalSafeRadius());
		return isWithinChebyshevClimateZone(pos, state.center(), radius);
	}

	/** Pure climate-zone radius predicate covering surface arrival plaza through Crystal Grotto. */
	public static boolean isWithinChebyshevClimateZone(BlockPos pos, BlockPos center, int radius) {
		if (pos == null || center == null) {
			return false;
		}
		int dx = Math.abs(pos.getX() - center.getX());
		int dz = Math.abs(pos.getZ() - center.getZ());
		int dy = pos.getY() - center.getY();
		return dx <= radius && dz <= radius && dy >= -38 && dy <= 34;
	}

	private static boolean isProtectedSanctuaryEntity(Entity entity) {
		return entity instanceof VillageSentinelEntity
			|| entity instanceof AbstractVillager
			|| entity instanceof ArmorStand
			|| entity instanceof ItemFrame
			|| entity instanceof Painting;
	}

	/** Allows players to inspect lecterns, ring the pavilion bell, or use doors without placing/breaking blocks. */
	private static boolean isSafeUtilityInteraction(BlockState state, ItemStack held, boolean sneaking) {
		net.minecraft.world.level.block.Block block = state.getBlock();
		boolean interactive = block instanceof LecternBlock
			|| block instanceof BellBlock
			|| block instanceof DoorBlock
			|| block instanceof TrapDoorBlock
			|| block instanceof FenceGateBlock
			|| block instanceof ButtonBlock
			|| block instanceof CraftingTableBlock
			|| block instanceof CartographyTableBlock
			|| state.is(BlockTags.WOODEN_DOORS)
			|| state.is(BlockTags.FENCE_GATES);
		if (!interactive) {
			return false;
		}
		// Require empty hand or non-block/non-destructive hand when sneaking so placing blocks against doors still fails.
		return !sneaking || held.isEmpty();
	}

	private static void notifyProtected(Player player) {
		if (player instanceof ServerPlayer serverPlayer) {
			serverPlayer.sendSystemMessage(
				Component.translatableWithFallback(
					"message.canopycavern.sanctuary.protected",
					"Canopy Sanctuary is protected."
				),
				true
			);
		}
	}
}
