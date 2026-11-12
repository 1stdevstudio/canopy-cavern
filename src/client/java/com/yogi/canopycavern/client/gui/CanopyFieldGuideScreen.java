package com.yogi.canopycavern.client.gui;

import com.mojang.blaze3d.platform.InputConstants;
import com.yogi.canopycavern.core.ShelterBlueprints;
import com.yogi.canopycavern.core.ShelterBlueprints.BlueprintDefinition;
import com.yogi.canopycavern.core.ShelterBlueprints.EquipmentEntry;
import com.yogi.canopycavern.core.ShelterBlueprints.MaterialCost;
import com.yogi.canopycavern.network.ModNetworking.BuildBlueprintPayload;
import com.yogi.canopycavern.world.BlueprintBuilderService;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import java.util.List;
import java.util.Map;

/**
 * In-game Canopy Field Guide screen featuring a beginner manual, live equipment material tracker,
 * and interactive Auto-Shelter Blueprint Builder GUI.
 */
public class CanopyFieldGuideScreen extends Screen {

	private static final int PANEL_WIDTH = 368;
	private static final int PANEL_HEIGHT = 236;

	private int activeTab = 0; // 0 = Guide, 1 = Gear & Materials, 2 = Shelter Builder
	private int equipmentScroll = 0;
	private int selectedBlueprintIndex = 0;
	private Button buildButton;

	public CanopyFieldGuideScreen() {
		super(Component.translatable("screen.canopycavern.field_guide.title"));
	}

	@Override
	protected void init() {
		this.clearWidgets();
		int left = (this.width - PANEL_WIDTH) / 2;
		int top = (this.height - PANEL_HEIGHT) / 2;

		addTabButton(left + 12, top + 28, 108, 20, "screen.canopycavern.tab.guide", 0);
		addTabButton(left + 126, top + 28, 112, 20, "screen.canopycavern.tab.gear", 1);
		addTabButton(left + 244, top + 28, 112, 20, "screen.canopycavern.tab.builder", 2);

		if (activeTab == 1) {
			this.addRenderableWidget(Button.builder(Component.literal("<"), b -> {
				equipmentScroll = Math.max(0, equipmentScroll - 4);
			}).bounds(left + PANEL_WIDTH - 56, top + PANEL_HEIGHT - 28, 20, 18).build());
			this.addRenderableWidget(Button.builder(Component.literal(">"), b -> {
				int maxStart = Math.max(0, ShelterBlueprints.equipmentCatalog().size() - 4);
				equipmentScroll = Math.min(maxStart, equipmentScroll + 4);
			}).bounds(left + PANEL_WIDTH - 32, top + PANEL_HEIGHT - 28, 20, 18).build());
		} else if (activeTab == 2) {
			List<BlueprintDefinition> blueprints = ShelterBlueprints.allBlueprints();
			for (int i = 0; i < blueprints.size(); i++) {
				final int idx = i;
				BlueprintDefinition bp = blueprints.get(i);
				this.addRenderableWidget(
					Button.builder(Component.translatable(bp.titleKey()), b -> {
						selectedBlueprintIndex = idx;
						refreshBuildButtonState();
					}).bounds(left + 12 + idx * 116, top + 56, 110, 20).build()
				);
			}
			buildButton = this.addRenderableWidget(
				Button.builder(Component.translatable("screen.canopycavern.builder.build_now"), b -> triggerBuild())
					.bounds(left + 14, top + PANEL_HEIGHT - 30, 170, 20)
					.build()
			);
			refreshBuildButtonState();
		}

		this.addRenderableWidget(
			Button.builder(Component.translatable("gui.done"), b -> this.onClose())
				.bounds(left + PANEL_WIDTH - 86, top + PANEL_HEIGHT - 30, 74, 20)
				.build()
		);
	}

	private void addTabButton(int x, int y, int w, int h, String key, int tabIndex) {
		Button btn = Button.builder(Component.translatable(key), b -> {
			activeTab = tabIndex;
			this.init();
		}).bounds(x, y, w, h).build();
		btn.active = (activeTab != tabIndex);
		this.addRenderableWidget(btn);
	}

	private void refreshBuildButtonState() {
		if (buildButton == null) {
			return;
		}
		BlueprintDefinition selected = ShelterBlueprints.allBlueprints().get(selectedBlueprintIndex);
		boolean creative = this.minecraft != null && this.minecraft.player != null && this.minecraft.player.isCreative();
		boolean ready = creative || ShelterBlueprints.hasAllMaterials(currentInventoryCounts(), selected.materials());
		buildButton.active = ready;
	}

	private void triggerBuild() {
		BlueprintDefinition selected = ShelterBlueprints.allBlueprints().get(selectedBlueprintIndex);
		ClientPlayNetworking.send(new BuildBlueprintPayload(selected.id()));
		this.onClose();
	}

	private Map<String, Integer> currentInventoryCounts() {
		if (this.minecraft == null || this.minecraft.player == null) {
			return Map.of();
		}
		return BlueprintBuilderService.countInventoryItems(this.minecraft.player.getInventory());
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		int left = (this.width - PANEL_WIDTH) / 2;
		int top = (this.height - PANEL_HEIGHT) / 2;

		graphics.fill(0, 0, this.width, this.height, 0x9007100E);
		graphics.fill(left, top, left + PANEL_WIDTH, top + PANEL_HEIGHT, 0xE6101B18);
		graphics.outline(left, top, PANEL_WIDTH, PANEL_HEIGHT, 0xFF56B88D);
		graphics.centeredText(this.font, this.title, left + PANEL_WIDTH / 2, top + 10, 0xFFE8F7EE);

		super.extractRenderState(graphics, mouseX, mouseY, partialTick);

		if (activeTab == 0) {
			renderGuideTab(graphics, left, top);
		} else if (activeTab == 1) {
			renderGearTab(graphics, left, top);
		} else {
			renderBuilderTab(graphics, left, top);
		}
	}

	private void renderGuideTab(GuiGraphicsExtractor graphics, int left, int top) {
		int x = left + 16;
		int y = top + 58;
		int wrapWidth = PANEL_WIDTH - 32;
		String[] keys = {
			"guide.canopycavern.section.basics",
			"guide.canopycavern.section.climate",
			"guide.canopycavern.section.gear",
			"guide.canopycavern.section.world"
		};
		int[] colors = {0xFFAEE8A8, 0xFF9CD4FF, 0xFFF3C677, 0xFFC5A3FF};
		for (int i = 0; i < keys.length; i++) {
			graphics.text(this.font, Component.translatable(keys[i] + ".title"), x, y, colors[i], false);
			y += 12;
			graphics.textWithWordWrap(this.font, Component.translatable(keys[i] + ".body"), x, y, wrapWidth, 0xFFD9E6DF, false);
			y += 28;
		}
	}

	private void renderGearTab(GuiGraphicsExtractor graphics, int left, int top) {
		Map<String, Integer> inv = currentInventoryCounts();
		List<EquipmentEntry> entries = ShelterBlueprints.equipmentCatalog();
		int y = top + 56;
		int end = Math.min(entries.size(), equipmentScroll + 4);
		for (int i = equipmentScroll; i < end; i++) {
			EquipmentEntry entry = entries.get(i);
			boolean ready = ShelterBlueprints.hasAllMaterials(inv, entry.materials());
			graphics.fill(left + 14, y, left + PANEL_WIDTH - 14, y + 34, 0x801A2B26);
			Item icon = BuiltInRegistries.ITEM.getValue(Identifier.parse(entry.itemId()));
			graphics.item(new ItemStack(icon), left + 20, y + 8);
			graphics.text(
				this.font,
				Component.translatable(entry.titleKey()),
				left + 44,
				y + 5,
				ready ? 0xFF9DF0B8 : 0xFFE6EFEA,
				false
			);
			graphics.text(
				this.font,
				formatMaterialsLine(inv, entry.materials()),
				left + 44,
				y + 18,
				ready ? 0xFF7BE0C3 : 0xFFB8C7C0,
				false
			);
			y += 38;
		}
	}

	private void renderBuilderTab(GuiGraphicsExtractor graphics, int left, int top) {
		BlueprintDefinition selected = ShelterBlueprints.allBlueprints().get(selectedBlueprintIndex);
		Map<String, Integer> inv = currentInventoryCounts();
		boolean creative = this.minecraft != null && this.minecraft.player != null && this.minecraft.player.isCreative();

		Item icon = BuiltInRegistries.ITEM.getValue(Identifier.parse(selected.iconItemId()));
		graphics.item(new ItemStack(icon), left + 16, top + 84);
		graphics.text(
			this.font,
			Component.translatable(selected.descKey()),
			left + 40,
			top + 88,
			0xFFD5E6DE,
			false
		);

		int y = top + 108;
		graphics.text(
			this.font,
			Component.translatable("screen.canopycavern.builder.requirements", selected.width(), selected.height(), selected.depth()),
			left + 16,
			y,
			0xFF9CD4FF,
			false
		);
		y += 14;

		int col = 0;
		for (MaterialCost cost : selected.materials()) {
			int owned = inv.getOrDefault(cost.itemId(), 0);
			boolean ok = creative || owned >= cost.count();
			int rx = left + 16 + (col * 172);
			int ry = y;
			Item reqItem = BuiltInRegistries.ITEM.getValue(Identifier.parse(cost.itemId()));
			graphics.item(new ItemStack(reqItem), rx, ry);
			String status = (ok ? "✓ " : "✗ ") + owned + "/" + cost.count();
			graphics.text(this.font, Component.literal(status), rx + 20, ry + 4, ok ? 0xFF8BE8A8 : 0xFFFF9885, false);
			col++;
			if (col == 2) {
				col = 0;
				y += 18;
			}
		}
	}

	private Component formatMaterialsLine(Map<String, Integer> inv, List<MaterialCost> costs) {
		StringBuilder sb = new StringBuilder();
		for (int i = 0; i < costs.size(); i++) {
			MaterialCost cost = costs.get(i);
			Item reqItem = BuiltInRegistries.ITEM.getValue(Identifier.parse(cost.itemId()));
			int owned = inv.getOrDefault(cost.itemId(), 0);
			String mark = owned >= cost.count() ? "✓" : "✗";
			if (i > 0) {
				sb.append("  |  ");
			}
			sb.append(mark).append(' ').append(reqItem.getName(new ItemStack(reqItem)).getString())
				.append(' ').append(owned).append('/').append(cost.count());
		}
		return Component.literal(sb.toString());
	}

	@Override
	public boolean keyPressed(KeyEvent event) {
		if (event.key() == InputConstants.KEY_ESCAPE) {
			this.onClose();
			return true;
		}
		return super.keyPressed(event);
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}
}
