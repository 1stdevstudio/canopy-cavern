package com.yogi.canopycavern.client;

import com.mojang.blaze3d.platform.InputConstants;
import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.client.atmosphere.ClientAtmosphereTicker;
import com.yogi.canopycavern.client.gui.CanopyFieldGuideScreen;
import com.yogi.canopycavern.client.hud.WorldHudOverlay;
import com.yogi.canopycavern.client.render.VillageSentinelRenderer;
import com.yogi.canopycavern.config.CanopyCavernConfig;
import com.yogi.canopycavern.entity.ModEntities;
import com.yogi.canopycavern.network.ModNetworking.ClimateSyncPayload;
import com.yogi.canopycavern.network.ModNetworking.OpenGuidePayload;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.item.v1.ItemTooltipCallback;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;
import net.minecraft.client.KeyMapping;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.component.DataComponents;
import net.minecraft.locale.Language;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.item.enchantment.ItemEnchantments;

import java.util.List;

/**
 * Client-first entrypoint registering the ambient telemetry HUD, keybindings,
 * network receivers, custom entity renderers, and atmospheric effects.
 */
public final class CanopyCavernClient implements ClientModInitializer {
	private static final KeyMapping.Category KEY_CATEGORY = KeyMapping.Category.register(
		CanopyCavernMod.id("general")
	);

	private static KeyMapping toggleHudKey;
	private static KeyMapping openGuideKey;

	@Override
	public void onInitializeClient() {
		toggleHudKey = KeyMappingHelper.registerKeyMapping(
			new KeyMapping(
				"key.canopycavern.toggle_hud",
				InputConstants.Type.KEYBOARD,
				InputConstants.KEY_H,
				KEY_CATEGORY
			)
		);
		openGuideKey = KeyMappingHelper.registerKeyMapping(
			new KeyMapping(
				"key.canopycavern.open_guide",
				InputConstants.Type.KEYBOARD,
				InputConstants.KEY_G,
				KEY_CATEGORY
			)
		);

		EntityRendererRegistry.register(ModEntities.VILLAGE_SENTINEL, VillageSentinelRenderer::new);
		ItemTooltipCallback.EVENT.register((stack, context, flag, lines) -> {
			appendEnchantmentDescriptions(stack, DataComponents.ENCHANTMENTS, lines);
			appendEnchantmentDescriptions(stack, DataComponents.STORED_ENCHANTMENTS, lines);
		});

		ClientPlayNetworking.registerGlobalReceiver(ClimateSyncPayload.TYPE, (payload, context) ->
			ClientClimateCache.update(payload)
		);
		ClientPlayNetworking.registerGlobalReceiver(OpenGuidePayload.TYPE, (payload, context) ->
			context.client().execute(() -> context.client().gui.setScreen(new CanopyFieldGuideScreen()))
		);

		HudElementRegistry.attachElementBefore(
			VanillaHudElements.CHAT,
			CanopyCavernMod.id("world_telemetry_hud"),
			WorldHudOverlay::render
		);

		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			if (client.level == null) {
				ClientClimateCache.reset();
				return;
			}
			while (toggleHudKey.consumeClick()) {
				CanopyCavernConfig current = CanopyCavernMod.getConfig();
				CanopyCavernConfig updated = current.withClientHudEnabled(!current.clientHudEnabled());
				CanopyCavernMod.updateConfig(updated);

				if (client.player != null) {
					String key = updated.clientHudEnabled()
						? "message.canopycavern.hud_enabled"
						: "message.canopycavern.hud_disabled";
					client.player.sendSystemMessage(Component.translatable(key));
				}
			}
			while (openGuideKey.consumeClick()) {
				if (client.gui.screen() == null) {
					client.gui.setScreen(new CanopyFieldGuideScreen());
				}
			}
			ClientEnvironmentSampler.sampleTick(client);
			ClientAtmosphereTicker.tick(client);
		});
	}

	private static void appendEnchantmentDescriptions(
		ItemStack stack, DataComponentType<ItemEnchantments> type, List<Component> lines
	) {
		TooltipDisplay display = stack.getOrDefault(DataComponents.TOOLTIP_DISPLAY, TooltipDisplay.DEFAULT);
		ItemEnchantments enchantments = stack.get(type);
		if (enchantments == null || display.hideTooltip() || !display.shows(type)) {
			return;
		}
		for (var holder : enchantments.keySet()) {
			holder.unwrapKey().map(key -> key.identifier())
				.filter(id -> id.getNamespace().equals(CanopyCavernMod.MOD_ID))
				.map(id -> id.toLanguageKey("enchantment", "desc"))
				.filter(Language.getInstance()::has)
				.ifPresent(key -> lines.add(Component.translatable(key).withStyle(ChatFormatting.GRAY)));
		}
	}
}
