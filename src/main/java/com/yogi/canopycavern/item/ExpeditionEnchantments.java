package com.yogi.canopycavern.item;

import com.yogi.canopycavern.CanopyCavernMod;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;

public final class ExpeditionEnchantments {
	public static final ResourceKey<Enchantment> CAVE_GRIP = key("cave_grip");
	public static final ResourceKey<Enchantment> RIDGE_STEP = key("ridge_step");
	public static final ResourceKey<Enchantment> SEABED_STRIDE = key("seabed_stride");
	public static final ResourceKey<Enchantment> THERMAL_WEAVE = key("thermal_weave");
	public static final ResourceKey<Enchantment> SPORE_FILTER = key("spore_filter");
	public static final ResourceKey<Enchantment> DEEP_FOCUS = key("deep_focus");

	private ExpeditionEnchantments() {
	}

	private static ResourceKey<Enchantment> key(String path) {
		return ResourceKey.create(Registries.ENCHANTMENT, CanopyCavernMod.id(path));
	}

	public static int level(LivingEntity wearer, ResourceKey<Enchantment> enchantment, EquipmentSlot slot) {
		var item = wearer.getItemBySlot(slot);
		if (!item.isEnchanted()) {
			return 0;
		}
		return wearer.registryAccess().lookupOrThrow(Registries.ENCHANTMENT).get(enchantment)
			.map(holder -> EnchantmentHelper.getItemEnchantmentLevel(holder, item))
			.orElse(0);
	}
}
