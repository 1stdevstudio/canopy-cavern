package com.yogi.canopycavern.world;

import com.yogi.canopycavern.item.ModItems;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/** Voidwalker Tether: falling into the End's void pulls the player back to the last block they stood on. */
public final class VoidTether {
	private static final Map<UUID, BlockPos> LAST_SAFE = new ConcurrentHashMap<>();

	private VoidTether() {
	}

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			ServerLevel end = server.getLevel(Level.END);
			if (end == null) {
				return;
			}
			for (ServerPlayer player : end.players()) {
				tick(end, player);
			}
		});
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> LAST_SAFE.remove(handler.player.getUUID()));
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> LAST_SAFE.clear());
	}

	static boolean shouldRescue(double y, int minBuildHeight, boolean hasSafeSpot) {
		return hasSafeSpot && y < minBuildHeight - 8;
	}

	private static void tick(ServerLevel end, ServerPlayer player) {
		if (player.isSpectator() || player.isCreative()) {
			return;
		}
		if (player.onGround()) {
			LAST_SAFE.put(player.getUUID(), player.blockPosition());
			return;
		}
		BlockPos safe = LAST_SAFE.get(player.getUUID());
		if (!shouldRescue(player.getY(), end.getMinY(), safe != null)) {
			return;
		}
		ItemStack tether = findTether(player);
		if (tether.isEmpty()) {
			return;
		}
		tether.shrink(1);
		player.teleportTo(end, safe.getX() + 0.5, safe.getY(), safe.getZ() + 0.5, Set.of(), player.getYRot(), player.getXRot(), true);
		player.setDeltaMovement(0, 0, 0);
		player.resetFallDistance();
		player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 100, 0));
		end.playSound(null, safe, SoundEvents.CHORUS_FRUIT_TELEPORT, SoundSource.PLAYERS, 1.0F, 0.8F);
		player.sendSystemMessage(Component.translatable("item.canopycavern.voidwalker_tether.snapped"), true);
	}

	private static ItemStack findTether(ServerPlayer player) {
		var inv = player.getInventory();
		for (int i = 0; i < inv.getContainerSize(); i++) {
			ItemStack stack = inv.getItem(i);
			if (stack.is(ModItems.VOIDWALKER_TETHER)) {
				return stack;
			}
		}
		return ItemStack.EMPTY;
	}
}
