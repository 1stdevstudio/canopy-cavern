package com.yogi.canopycavern.item;

import com.yogi.canopycavern.CanopyCavernMod;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.fabricmc.fabric.api.event.player.UseItemCallback;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import net.minecraft.tags.BlockTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.LodestoneTracker;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.pattern.BlockInWorld;
import net.minecraft.world.phys.BlockHitResult;

import java.util.Optional;

public final class ExpeditionGearActions {
    private ExpeditionGearActions() {}

    public static void register() {
        UseItemCallback.EVENT.register(ExpeditionGearActions::markTrail);
        UseBlockCallback.EVENT.register(ExpeditionGearActions::useOnBlock);
    }

    private static InteractionResult markTrail(Player player, Level level, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (player.isSpectator() || !player.isShiftKeyDown() || !stack.is(Items.COMPASS)
                || !has(level, stack, "trail_echo")) return InteractionResult.PASS;
        if (player instanceof ServerPlayer serverPlayer) {
            stack.set(DataComponents.LODESTONE_TRACKER,
                new LodestoneTracker(Optional.of(GlobalPos.of(level.dimension(), player.blockPosition())), false));
            serverPlayer.sendSystemMessage(Component.translatable("message.canopycavern.trail_marked"), true);
        }
        return InteractionResult.SUCCESS;
    }

    private static InteractionResult useOnBlock(Player player, Level level, InteractionHand hand, BlockHitResult hit) {
        if (player.isSpectator() || !player.isShiftKeyDown()) return InteractionResult.PASS;
        ItemStack stack = player.getItemInHand(hand);
        // Horizontal clicks place a torch. Clicking the top of stone surveys a cave.
        if (hit.getDirection().getAxis().isHorizontal() && has(level, stack, "torchkeeper")) {
            return placeTorch(player, level, hand, hit);
        }
        if (hit.getDirection() != Direction.UP || !level.getBlockState(hit.getBlockPos()).is(BlockTags.BASE_STONE_OVERWORLD)
                || !has(level, stack, "resonant_survey")) return InteractionResult.PASS;
        if (level instanceof ServerLevel server && player instanceof ServerPlayer serverPlayer && !player.getCooldowns().isOnCooldown(stack)) {
            player.getCooldowns().addCooldown(stack, 160);
            Direction direction = survey(server, hit.getBlockPos());
            Component result = direction == null
                ? Component.translatable("message.canopycavern.survey_empty")
                : Component.translatable("message.canopycavern.survey_found",
                    Component.translatable("message.canopycavern.direction." + direction.getName()));
            serverPlayer.sendSystemMessage(result, true);
        }
        return InteractionResult.SUCCESS;
    }

    private static InteractionResult placeTorch(Player player, Level level, InteractionHand hand, BlockHitResult hit) {
        var inventory = player.getInventory();
        for (int i = 0; i < inventory.getContainerSize(); i++) {
            ItemStack supply = inventory.getItem(i);
            if (supply.is(Items.TORCH)) {
                BlockPlaceContext placement = new BlockPlaceContext(player, hand, supply, hit);
                BlockPos target = placement.getClickedPos();
                if (!level.isInWorldBounds(target) || !level.mayInteract(player, hit.getBlockPos())
                        || !level.mayInteract(player, target)) return InteractionResult.FAIL;
                if (!player.mayBuild()
                        && !supply.canPlaceOnBlockInAdventureMode(new BlockInWorld(level, hit.getBlockPos(), false))) {
                    return InteractionResult.FAIL;
                }
                if (level.isClientSide()) return InteractionResult.SUCCESS;
                return ((BlockItem) Items.TORCH).place(placement);
            }
        }
        return InteractionResult.PASS;
    }

    private static Direction survey(ServerLevel level, BlockPos origin) {
        // Check short rays below the clicked surface, without forcing chunks to load.
        for (int distance = 2; distance <= 10; distance++) {
            for (Direction direction : Direction.Plane.HORIZONTAL) {
                BlockPos pos = origin.relative(direction, distance).below(2);
                if (level.hasChunkAt(pos) && level.getBlockState(pos).isAir()
                        && level.getBlockState(pos.above()).isAir()
                        && !level.canSeeSky(pos)) return direction;
            }
        }
        return null;
    }

    private static boolean has(Level level, ItemStack stack, String id) {
        return level.registryAccess().lookupOrThrow(Registries.ENCHANTMENT).get(CanopyCavernMod.id(id))
            .map(holder -> EnchantmentHelper.getItemEnchantmentLevel(holder, stack) > 0).orElse(false);
    }
}
