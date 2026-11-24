package com.yogi.canopycavern.worldgen;

import com.yogi.canopycavern.CanopyCavernMod;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.biome.Biome;

import java.util.List;

/**
 * Resource keys for Canopy Cavern's custom Overworld and subterranean biomes.
 */
public final class ModBiomes {
	public static final ResourceKey<Biome> WHISPERING_PEAKS = key("whispering_peaks");
	public static final ResourceKey<Biome> MOSSY_CANOPY = key("mossy_canopy");
	public static final ResourceKey<Biome> VERDANT_GROTTO = key("verdant_grotto");
	public static final ResourceKey<Biome> CRYSTAL_STEPPE = key("crystal_steppe");
	public static final ResourceKey<Biome> AMBER_CAVERNS = key("amber_caverns");
	public static final ResourceKey<Biome> ELDER_BOUGH_GROVE = key("elder_bough_grove");
	public static final ResourceKey<Biome> FROSTSPIRE_CRAGS = key("frostspire_crags");
	public static final ResourceKey<Biome> WINDCARVED_CLIFFS = key("windcarved_cliffs");
	public static final ResourceKey<Biome> LUMINOUS_DEPTHS = key("luminous_depths");
	public static final ResourceKey<Biome> SUNLIT_SHALLOWS = key("sunlit_shallows");
	public static final ResourceKey<Biome> CORAL_DRIFT = key("coral_drift");
	public static final ResourceKey<Biome> TEMPERATE_SOUND = key("temperate_sound");
	public static final ResourceKey<Biome> ABYSSAL_TRENCH = key("abyssal_trench");
	public static final ResourceKey<Biome> KELPWOOD_SEA = key("kelpwood_sea");
	public static final ResourceKey<Biome> FLOE_SEA = key("floe_sea");
	public static final ResourceKey<Biome> MEANDERING_RIVER = key("meandering_river");
	public static final ResourceKey<Biome> FROSTBOUND_RIVER = key("frostbound_river");
	public static final ResourceKey<Biome> GOLDEN_STRAND = key("golden_strand");
	public static final ResourceKey<Biome> FROSTLINE_SHORE = key("frostline_shore");
	public static final ResourceKey<Biome> WILDGRASS_PLAINS = key("wildgrass_plains");
	public static final ResourceKey<Biome> SUNBAKED_SAVANNA = key("sunbaked_savanna");
	public static final ResourceKey<Biome> DUNE_EXPANSE = key("dune_expanse");
	public static final ResourceKey<Biome> RUSTROCK_BADLANDS = key("rustrock_badlands");
	public static final ResourceKey<Biome> OAKHOLLOW_WOODS = key("oakhollow_woods");
	public static final ResourceKey<Biome> BLOOMVEIL_FOREST = key("bloomveil_forest");
	public static final ResourceKey<Biome> SILVERBIRCH_GLADE = key("silverbirch_glade");
	public static final ResourceKey<Biome> BLOSSOM_TERRACE = key("blossom_terrace");
	public static final ResourceKey<Biome> DAPPLELIGHT_WOOD = key("dapplelight_wood");
	public static final ResourceKey<Biome> ASHEN_GARDEN = key("ashen_garden");
	public static final ResourceKey<Biome> SPRUCE_HOLLOW = key("spruce_hollow");
	public static final ResourceKey<Biome> GIANT_SPRUCE_REACH = key("giant_spruce_reach");
	public static final ResourceKey<Biome> TANGLEWILD_JUNGLE = key("tanglewild_jungle");
	public static final ResourceKey<Biome> BAMBOO_THICKET = key("bamboo_thicket");
	public static final ResourceKey<Biome> BOGWATER_FEN = key("bogwater_fen");
	public static final ResourceKey<Biome> MANGROVE_TANGLE = key("mangrove_tangle");
	public static final ResourceKey<Biome> SNOWBOUND_TUNDRA = key("snowbound_tundra");
	public static final ResourceKey<Biome> RIME_SPIRES = key("rime_spires");
	public static final ResourceKey<Biome> FROSTPINE_TAIGA = key("frostpine_taiga");
	public static final ResourceKey<Biome> HOARFROST_GROVE = key("hoarfrost_grove");
	public static final ResourceKey<Biome> POWDER_SLOPES = key("powder_slopes");
	public static final ResourceKey<Biome> GLACIER_CROWN = key("glacier_crown");
	public static final ResourceKey<Biome> SLATESTONE_PEAKS = key("slatestone_peaks");
	public static final ResourceKey<Biome> GRAVEL_BARRENS = key("gravel_barrens");
	public static final ResourceKey<Biome> WINDBENT_FOREST = key("windbent_forest");
	public static final ResourceKey<Biome> GALE_SAVANNA = key("gale_savanna");
	public static final ResourceKey<Biome> MYCELIUM_ISLES = key("mycelium_isles");
	public static final ResourceKey<Biome> HUSHED_DEPTHS = key("hushed_depths");
	public static final ResourceKey<Biome> SULFUR_HOLLOWS = key("sulfur_hollows");

	public static final List<ResourceKey<Biome>> ALL_BIOMES = List.of(
		WHISPERING_PEAKS,
		MOSSY_CANOPY,
		VERDANT_GROTTO,
		CRYSTAL_STEPPE,
		AMBER_CAVERNS,
		ELDER_BOUGH_GROVE,
		FROSTSPIRE_CRAGS,
		WINDCARVED_CLIFFS,
		LUMINOUS_DEPTHS,
		SUNLIT_SHALLOWS,
		CORAL_DRIFT,
		TEMPERATE_SOUND,
		ABYSSAL_TRENCH,
		KELPWOOD_SEA,
		FLOE_SEA,
		MEANDERING_RIVER,
		FROSTBOUND_RIVER,
		GOLDEN_STRAND,
		FROSTLINE_SHORE,
		WILDGRASS_PLAINS,
		SUNBAKED_SAVANNA,
		DUNE_EXPANSE,
		RUSTROCK_BADLANDS,
		OAKHOLLOW_WOODS,
		BLOOMVEIL_FOREST,
		SILVERBIRCH_GLADE,
		BLOSSOM_TERRACE,
		DAPPLELIGHT_WOOD,
		ASHEN_GARDEN,
		SPRUCE_HOLLOW,
		GIANT_SPRUCE_REACH,
		TANGLEWILD_JUNGLE,
		BAMBOO_THICKET,
		BOGWATER_FEN,
		MANGROVE_TANGLE,
		SNOWBOUND_TUNDRA,
		RIME_SPIRES,
		FROSTPINE_TAIGA,
		HOARFROST_GROVE,
		POWDER_SLOPES,
		GLACIER_CROWN,
		SLATESTONE_PEAKS,
		GRAVEL_BARRENS,
		WINDBENT_FOREST,
		GALE_SAVANNA,
		MYCELIUM_ISLES,
		HUSHED_DEPTHS,
		SULFUR_HOLLOWS
	);

	private ModBiomes() {
	}

	private static ResourceKey<Biome> key(String path) {
		return ResourceKey.create(Registries.BIOME, CanopyCavernMod.id(path));
	}
}
