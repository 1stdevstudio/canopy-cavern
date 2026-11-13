package com.yogi.canopycavern.world.spawn;

import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.network.Filterable;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.WrittenBookContent;
import net.minecraft.world.level.block.entity.SignText;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Provides localized translation keys and English fallback copy for Canopy Sanctuary
 * wayfinding signs and lectern guidebooks.
 */
public final class SanctuaryLocalization {
	private static final Map<String, String> EN_FALLBACKS;

	static {
		Map<String, String> m = new LinkedHashMap<>();

		// Plaza & Hub Wayfinding Signs (kept <= 15 chars per line for crisp rendering)
		putSign(m, "welcome", "CANOPY SANCTUARY", "Safe Arrival", "Explore World", "Your Own Path");
		putSign(m, "choices", "CHOOSE A ROUTE", "N: Wilds Gate", "E: Guild Hall", "W:Garden S:Cave");
		putSign(m, "dir_east", "EAST WING ->", "Adventurer", "Guild Hall &", "Field Guide");
		putSign(m, "dir_west", "<- WEST WING", "Nature Garden", "Quiet Terrace", "& West Trail");
		putSign(m, "dir_south", "SOUTH WING ->", "Rest Pavilion", "& Twin Cavern", "Descent Stairs");
		putSign(m, "north_gate", "EXPEDITION GATE", "Surface Wilds", "Lie Ahead ->", "Gear Up Safely");
		putSign(m, "trail_exit", "SAFE BOUNDARY", "Beyond Sanctuary", "Full Vanilla", "Survival Rules");
		putSign(m, "guild_guide", "FIELD GUIDE", "Read Lecterns", "Micro-Climate", "& Shelter Info");
		putSign(m, "guild_map", "ROUTE ATLAS", "4 Surface Roads", "Deep Cavern Hub", "3 Exit Routes");
		putSign(m, "guild_notice", "GUILD CHARTER", "Free Exploration", "Beds Preserved", "Sentinels Guard");
		putSign(m, "garden_lore", "NATURE GARDEN", "Azalea Pools", "Calm Air Zone", "West Trail ->");
		putSign(m, "cavern_stair", "CAVERN STAIRS", "Follow Lanterns", "2x Entry Stairs", "3x Return Ways");
		putSign(m, "pavilion_sign", "REST PAVILION", "Open Shelter", "Stall Alcoves", "Bell Watchtower");
		putSign(m, "cavern_escape_w", "<- RETURN UP", "West Stairway", "Back To Plaza", "Safe Daylight");
		putSign(m, "cavern_escape_e", "RETURN UP ->", "East Stairway", "Back To Plaza", "Safe Daylight");
		putSign(m, "cavern_escape_s", "SOUTH EXIT ->", "Daylight Stair", "Direct Surface", "Return Route");
		putSign(m, "grotto_exit", "^ REAR STAIRS", "Climb Southward", "Direct Surface", "Daylight Trail");
		putSign(m, "grotto_lore", "CRYSTAL GROTTO", "Amethyst Vault", "East/West Wings", "3 Exit Routes");
		putSign(m, "cavern_surface_portal", "DAYLIGHT EXIT", "3rd Return Path", "Safe Stair Up", "From Grotto");

		// Lectern Book Metadata & Pages
		m.put("book.canopycavern.canopy_sanctuary_welcome.title", "Canopy Sanctuary Guide");
		m.put("book.canopycavern.canopy_sanctuary_welcome.author", "Sanctuary Wardens");
		m.put("book.canopycavern.canopy_sanctuary_welcome.page.1",
			"Welcome to Canopy Sanctuary!\n\nThis optional server arrival hub connects surface biomes and subterranean caverns with clear roads, shelter, and safe return routes."
		);
		m.put("book.canopycavern.canopy_sanctuary_welcome.page.2",
			"Four Trails From Plaza:\n\n- North: Expedition Gate & Overworld Wilds\n- East: Adventurer Guild Hall & Exhibits\n- West: Nature Garden & Brook\n- South: Trading Pavilion & Crystal Cavern"
		);
		m.put("book.canopycavern.canopy_sanctuary_welcome.page.3",
			"Your Freedom:\n\nNo forced teleports or paywalls stand between you and adventure. Leave via any surface road or climb back out from the underground Crystal Grotto through three marked stairways."
		);

		m.put("book.canopycavern.guild_field_guide.title", "Canopy Field Guide Notes");
		m.put("book.canopycavern.guild_field_guide.author", "Guild Archivists");
		m.put("book.canopycavern.guild_field_guide.page.1",
			"Field Guide Basics:\n\nOpen your personal Canopy Field Guide to read micro-climate hazards, underground thermal balance, and instant emergency camp shelters for expeditions."
		);
		m.put("book.canopycavern.guild_field_guide.page.2",
			"Survival Tips:\n\nInside the central Sanctuary arrival zone, harsh surface frost and cave heat calm gently so new arrivals can orient, read boards, and craft starter gear safely."
		);

		m.put("book.canopycavern.guild_expedition_routes.title", "Cavern & Surface Atlas");
		m.put("book.canopycavern.guild_expedition_routes.author", "Survey Corps");
		m.put("book.canopycavern.guild_expedition_routes.page.1",
			"Subterranean Descent:\n\nTwin broad staircases on the South Pavilion descend into the Upper Cavern Atrium and overlook the vaulted Crystal Grotto Gallery."
		);
		m.put("book.canopycavern.guild_expedition_routes.page.2",
			"Guaranteed Safe Exit:\n\nNever trap yourself below ground: the West Stair, East Stair, and South Daylight Escape Stair lead directly back up to open daylight."
		);

		EN_FALLBACKS = Collections.unmodifiableMap(m);
	}

	private SanctuaryLocalization() {
	}

	private static void putSign(Map<String, String> map, String keyPrefix, String l1, String l2, String l3, String l4) {
		map.put("sign.canopycavern." + keyPrefix + ".1", l1);
		map.put("sign.canopycavern." + keyPrefix + ".2", l2);
		map.put("sign.canopycavern." + keyPrefix + ".3", l3);
		map.put("sign.canopycavern." + keyPrefix + ".4", l4);
	}

	/** Exposes every Sanctuary translation key and its English fallback for localization test validation. */
	public static Map<String, String> allEnglishFallbacks() {
		return EN_FALLBACKS;
	}

	/** Creates a localized SignText payload using translatable keys with crisp English fallbacks. */
	public static SignText buildSignText(List<String> keys, boolean glowing) {
		Component[] lines = new Component[4];
		for (int i = 0; i < 4; i++) {
			String key = i < keys.size() ? keys.get(i) : "";
			String fallback = key.isEmpty() ? "" : EN_FALLBACKS.getOrDefault(key, "");
			lines[i] = key.isEmpty()
				? Component.empty()
				: Component.translatableWithFallback(key, fallback);
		}
		List<Component> front = List.of(lines[0], lines[1], lines[2], lines[3]);
		return new SignText(front, front, DyeColor.WHITE, glowing);
	}

	/** Creates an immutable written guidebook ItemStack for a Sanctuary lectern. */
	public static ItemStack buildLecternBook(String bookKey) {
		String prefix = "book.canopycavern." + bookKey;
		String title = EN_FALLBACKS.getOrDefault(prefix + ".title", "Canopy Sanctuary Guide");
		String author = EN_FALLBACKS.getOrDefault(prefix + ".author", "Sanctuary Wardens");

		int pageIndex = 1;
		java.util.ArrayList<Filterable<Component>> pages = new java.util.ArrayList<>();
		while (true) {
			String pageKey = prefix + ".page." + pageIndex;
			String fallback = EN_FALLBACKS.get(pageKey);
			if (fallback == null) {
				break;
			}
			pages.add(Filterable.passThrough(Component.translatableWithFallback(pageKey, fallback)));
			pageIndex++;
		}
		if (pages.isEmpty()) {
			pages.add(Filterable.passThrough(Component.translatableWithFallback(
				"book.canopycavern.canopy_sanctuary_welcome.page.1",
				EN_FALLBACKS.get("book.canopycavern.canopy_sanctuary_welcome.page.1")
			)));
		}

		ItemStack stack = new ItemStack(Items.WRITTEN_BOOK);
		WrittenBookContent content = new WrittenBookContent(
			Filterable.passThrough(title),
			author,
			0,
			List.copyOf(pages),
			true
		);
		stack.set(DataComponents.WRITTEN_BOOK_CONTENT, content);
		return stack;
	}
}
