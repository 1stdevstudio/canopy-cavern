# Vanilla structure coverage inventory

Source: local Minecraft 26.3 game JAR; audited 13 November 2026 against base commit `5613da0`.

52 structure definitions, 245 template pools, 1511 NBT templates. The definitions include biome variants, so these are not 52 distinct architectural styles.

Current mod overrides 10 village pools (houses and town centers across five themes), zero vanilla structure definitions and zero vanilla NBT paths. Missing structure-definition overrides alone do not prove a structure unchanged: pools may replace its contents. Current village replacement is partial because original zombie centers, streets, decoration and terminators remain reachable.

| Vanilla structure definition | Generation type | Current redesign coverage |
| --- | --- | --- |
| `abandoned_camp_bamboo_jungle` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_birch_forest` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_cherry_grove` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_dappled_forest` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_flower_forest` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_forest` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_meadow` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_old_growth_birch_forest` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_old_growth_pine_taiga` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_old_growth_spruce_taiga` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_pale_garden` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_savanna` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_snowy_taiga` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_sparse_jungle` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_swamp` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_taiga` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_windswept_forest` | `minecraft:jigsaw` | No replacement found |
| `abandoned_camp_wooded_badlands` | `minecraft:jigsaw` | No replacement found |
| `ancient_city` | `minecraft:jigsaw` | No replacement found |
| `bastion_remnant` | `minecraft:jigsaw` | No replacement found |
| `buried_treasure` | `minecraft:buried_treasure` | No replacement found |
| `desert_pyramid` | `minecraft:desert_pyramid` | No replacement found |
| `end_city` | `minecraft:end_city` | No replacement found |
| `fortress` | `minecraft:fortress` | No replacement found |
| `igloo` | `minecraft:igloo` | No replacement found |
| `jungle_pyramid` | `minecraft:jungle_temple` | No replacement found |
| `mansion` | `minecraft:woodland_mansion` | No replacement found |
| `mineshaft` | `minecraft:mineshaft` | No replacement found |
| `mineshaft_mesa` | `minecraft:mineshaft` | No replacement found |
| `monument` | `minecraft:ocean_monument` | No replacement found |
| `nether_fossil` | `minecraft:nether_fossil` | No replacement found |
| `ocean_ruin_cold` | `minecraft:ocean_ruin` | No replacement found |
| `ocean_ruin_warm` | `minecraft:ocean_ruin` | No replacement found |
| `pillager_outpost` | `minecraft:jigsaw` | No replacement found |
| `ruined_portal` | `minecraft:ruined_portal` | No replacement found |
| `ruined_portal_desert` | `minecraft:ruined_portal` | No replacement found |
| `ruined_portal_jungle` | `minecraft:ruined_portal` | No replacement found |
| `ruined_portal_mountain` | `minecraft:ruined_portal` | No replacement found |
| `ruined_portal_nether` | `minecraft:ruined_portal` | No replacement found |
| `ruined_portal_ocean` | `minecraft:ruined_portal` | No replacement found |
| `ruined_portal_swamp` | `minecraft:ruined_portal` | No replacement found |
| `shipwreck` | `minecraft:shipwreck` | No replacement found |
| `shipwreck_beached` | `minecraft:shipwreck` | No replacement found |
| `stronghold` | `minecraft:stronghold` | No replacement found |
| `swamp_hut` | `minecraft:swamp_hut` | No replacement found |
| `trail_ruins` | `minecraft:jigsaw` | No replacement found |
| `trial_chambers` | `minecraft:jigsaw` | No replacement found |
| `village_desert` | `minecraft:jigsaw` | Partial: normal houses and town centers only |
| `village_plains` | `minecraft:jigsaw` | Partial: normal houses and town centers only |
| `village_savanna` | `minecraft:jigsaw` | Partial: normal houses and town centers only |
| `village_snowy` | `minecraft:jigsaw` | Partial: normal houses and town centers only |
| `village_taiga` | `minecraft:jigsaw` | Partial: normal houses and town centers only |

## Acceptance for a complete redesign

- Track every reachable template pool and template, including rare zombie variants and fallbacks.
- Procedural structures need generator replacements or generation hooks; recoloring a template or editing a structure definition alone is insufficient.
- Preserve gameplay functions (portals, loot, mobs, raids, progression), terrain access and cross-chunk seams.
- Validate new world generation across unrelated seeds and measure server tick time and client frame time separately.
- Existing chunks retain their existing buildings. This inventory is a scope map, not a claim that the redesign is complete.
