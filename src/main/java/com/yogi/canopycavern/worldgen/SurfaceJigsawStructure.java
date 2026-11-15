package com.yogi.canopycavern.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.worldgen.SurfaceTerrainHelper.TerrainProfile;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.LevelHeightAccessor;
import net.minecraft.world.level.NoiseColumn;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.WorldGenerationContext;
import net.minecraft.world.level.levelgen.heightproviders.HeightProvider;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.PoolElementStructurePiece;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pieces.PiecesContainer;
import net.minecraft.world.level.levelgen.structure.pools.DimensionPadding;
import net.minecraft.world.level.levelgen.structure.pools.JigsawPlacement;
import net.minecraft.world.level.levelgen.structure.pools.StructureTemplatePool;
import net.minecraft.world.level.levelgen.structure.pools.alias.PoolAliasBinding;
import net.minecraft.world.level.levelgen.structure.pools.alias.PoolAliasLookup;
import net.minecraft.world.level.levelgen.structure.structures.JigsawStructure;
import net.minecraft.world.level.levelgen.structure.templatesystem.LiquidSettings;

/**
 * Terrain-aware Jigsaw structure for surface settlements, outposts, ruins, and towers.
 * Rejects steep cliffs, canyons, open rivers/lava, and buried cliff walls before placement, prunes
 * unsupported peripheral branches while keeping connected modular pieces cohesive, and extends
 * biome-matched downward foundations beneath sloped rigid piece footprints.
 */
public final class SurfaceJigsawStructure extends Structure {

	public record TerrainGuard(
		int coreProbeRadius,
		int maxCoreRelief,
		int maxPieceRelief,
		int maxPieceEmbed,
		int maxFoundationDepth,
		int minRigidPieces,
		int minPieceYAboveSea,
		boolean allowWater,
		int maxWaterDepth,
		boolean foundationStartOnly,
		Block foundationBlock,
		int minSolidThickness
	) {
		public TerrainGuard(
			int coreProbeRadius,
			int maxCoreRelief,
			int maxPieceRelief,
			int maxPieceEmbed,
			int maxFoundationDepth,
			int minRigidPieces,
			int minPieceYAboveSea,
			boolean allowWater,
			int maxWaterDepth,
			boolean foundationStartOnly,
			Block foundationBlock
		) {
			this(
				coreProbeRadius,
				maxCoreRelief,
				maxPieceRelief,
				maxPieceEmbed,
				maxFoundationDepth,
				minRigidPieces,
				minPieceYAboveSea,
				allowWater,
				maxWaterDepth,
				foundationStartOnly,
				foundationBlock,
				0
			);
		}

		public static final TerrainGuard DEFAULT = new TerrainGuard(
			8, 4, 5, 3, 6, 1, -64, false, 0, false, Blocks.COBBLESTONE, 0
		);

		public static final Codec<TerrainGuard> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.intRange(2, 32).optionalFieldOf("core_probe_radius", DEFAULT.coreProbeRadius()).forGetter(TerrainGuard::coreProbeRadius),
			Codec.intRange(0, 16).optionalFieldOf("max_core_relief", DEFAULT.maxCoreRelief()).forGetter(TerrainGuard::maxCoreRelief),
			Codec.intRange(0, 16).optionalFieldOf("max_piece_relief", DEFAULT.maxPieceRelief()).forGetter(TerrainGuard::maxPieceRelief),
			Codec.intRange(0, 12).optionalFieldOf("max_piece_embed", DEFAULT.maxPieceEmbed()).forGetter(TerrainGuard::maxPieceEmbed),
			Codec.intRange(0, 16).optionalFieldOf("max_foundation_depth", DEFAULT.maxFoundationDepth()).forGetter(TerrainGuard::maxFoundationDepth),
			Codec.intRange(1, 24).optionalFieldOf("min_rigid_pieces", DEFAULT.minRigidPieces()).forGetter(TerrainGuard::minRigidPieces),
			Codec.INT.optionalFieldOf("min_piece_y_above_sea", DEFAULT.minPieceYAboveSea()).forGetter(TerrainGuard::minPieceYAboveSea),
			Codec.BOOL.optionalFieldOf("allow_water", DEFAULT.allowWater()).forGetter(TerrainGuard::allowWater),
			Codec.intRange(0, 16).optionalFieldOf("max_water_depth", DEFAULT.maxWaterDepth()).forGetter(TerrainGuard::maxWaterDepth),
			Codec.BOOL.optionalFieldOf("foundation_start_only", DEFAULT.foundationStartOnly()).forGetter(TerrainGuard::foundationStartOnly),
			BuiltInRegistries.BLOCK.byNameCodec().optionalFieldOf("foundation_block", DEFAULT.foundationBlock()).forGetter(TerrainGuard::foundationBlock),
			Codec.intRange(0, 32).optionalFieldOf("min_solid_thickness", DEFAULT.minSolidThickness()).forGetter(TerrainGuard::minSolidThickness)
		).apply(instance, TerrainGuard::new));
	}

	public static final MapCodec<SurfaceJigsawStructure> CODEC = RecordCodecBuilder.<SurfaceJigsawStructure>mapCodec(
		instance -> instance.group(
			settingsCodec(instance),
			StructureTemplatePool.CODEC.fieldOf("start_pool").forGetter(s -> s.startPool),
			Identifier.CODEC.optionalFieldOf("start_jigsaw_name").forGetter(s -> s.startJigsawName),
			Codec.intRange(0, 20).fieldOf("size").forGetter(s -> s.maxDepth),
			HeightProvider.CODEC.fieldOf("start_height").forGetter(s -> s.startHeight),
			Codec.BOOL.optionalFieldOf("use_expansion_hack", false).forGetter(s -> s.useExpansionHack),
			Heightmap.Types.CODEC.optionalFieldOf("project_start_to_heightmap").forGetter(s -> s.projectStartToHeightmap),
			JigsawStructure.MaxDistance.CODEC.optionalFieldOf("max_distance_from_center", new JigsawStructure.MaxDistance(80))
				.forGetter(s -> s.maxDistanceFromCenter),
			Codec.list(PoolAliasBinding.CODEC).optionalFieldOf("pool_aliases", List.of()).forGetter(s -> s.poolAliases),
			DimensionPadding.CODEC.optionalFieldOf("dimension_padding", JigsawStructure.DEFAULT_DIMENSION_PADDING)
				.forGetter(s -> s.dimensionPadding),
			LiquidSettings.CODEC.optionalFieldOf("liquid_settings", JigsawStructure.DEFAULT_LIQUID_SETTINGS)
				.forGetter(s -> s.liquidSettings),
			TerrainGuard.CODEC.optionalFieldOf("terrain_guard", TerrainGuard.DEFAULT).forGetter(s -> s.terrainGuard)
		).apply(instance, SurfaceJigsawStructure::new)
	).validate(SurfaceJigsawStructure::verifyRange);

	public static final StructureType<SurfaceJigsawStructure> TYPE = () -> CODEC;

	private final Holder<StructureTemplatePool> startPool;
	private final Optional<Identifier> startJigsawName;
	private final int maxDepth;
	private final HeightProvider startHeight;
	private final boolean useExpansionHack;
	private final Optional<Heightmap.Types> projectStartToHeightmap;
	private final JigsawStructure.MaxDistance maxDistanceFromCenter;
	private final List<PoolAliasBinding> poolAliases;
	private final DimensionPadding dimensionPadding;
	private final LiquidSettings liquidSettings;
	private final TerrainGuard terrainGuard;

	private SurfaceJigsawStructure(
		StructureSettings settings,
		Holder<StructureTemplatePool> startPool,
		Optional<Identifier> startJigsawName,
		int maxDepth,
		HeightProvider startHeight,
		boolean useExpansionHack,
		Optional<Heightmap.Types> projectStartToHeightmap,
		JigsawStructure.MaxDistance maxDistanceFromCenter,
		List<PoolAliasBinding> poolAliases,
		DimensionPadding dimensionPadding,
		LiquidSettings liquidSettings,
		TerrainGuard terrainGuard
	) {
		super(settings);
		this.startPool = startPool;
		this.startJigsawName = startJigsawName;
		this.maxDepth = maxDepth;
		this.startHeight = startHeight;
		this.useExpansionHack = useExpansionHack;
		this.projectStartToHeightmap = projectStartToHeightmap;
		this.maxDistanceFromCenter = maxDistanceFromCenter;
		this.poolAliases = poolAliases;
		this.dimensionPadding = dimensionPadding;
		this.liquidSettings = liquidSettings;
		this.terrainGuard = terrainGuard;
	}

	/** Registers {@code canopycavern:surface_jigsaw} in the structure-type registry. */
	public static void register() {
		Registry.register(BuiltInRegistries.STRUCTURE_TYPE, CanopyCavernMod.id("surface_jigsaw"), TYPE);
	}

	private static DataResult<SurfaceJigsawStructure> verifyRange(SurfaceJigsawStructure structure) {
		int padding = switch (structure.terrainAdaptation()) {
			case NONE -> 0;
			case BURY, BEARD_THIN, BEARD_BOX, ENCAPSULATE -> 12;
		};
		if (structure.maxDistanceFromCenter.horizontal() + padding > 128) {
			return DataResult.error(() -> "Structure size including terrain adaptation must not exceed 128");
		}
		return DataResult.success(structure);
	}

	@Override
	public StructureType<?> type() {
		return TYPE;
	}

	@Override
	protected Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
		ChunkPos chunkPos = context.chunkPos();
		int middleX = chunkPos.getMiddleBlockX();
		int middleZ = chunkPos.getMiddleBlockZ();
		int radius = terrainGuard.coreProbeRadius();

		// Fast pre-filter before running Jigsaw piece assembly on obviously wet/cliff chunks.
		TerrainProfile precheck = SurfaceTerrainHelper.sampleFootprint(
			context.chunkGenerator(),
			context.heightAccessor(),
			context.randomState(),
			middleX - radius,
			middleZ - radius,
			middleX + radius,
			middleZ + radius,
			4
		);
		if (!SurfaceTerrainHelper.fitsStartTerrain(
			precheck,
			terrainGuard.maxCoreRelief() + 2,
			terrainGuard.allowWater(),
			terrainGuard.maxWaterDepth()
		)) {
			return Optional.empty();
		}

		int yOffset = startHeight.sample(
			context.random(),
			new WorldGenerationContext(context.chunkGenerator(), context.heightAccessor())
		);
		BlockPos startPos = new BlockPos(chunkPos.getMinBlockX(), yOffset, chunkPos.getMinBlockZ());

		Optional<GenerationStub> rawStub = JigsawPlacement.addPieces(
			context,
			startPool,
			startJigsawName,
			maxDepth,
			startPos,
			useExpansionHack,
			projectStartToHeightmap,
			maxDistanceFromCenter,
			PoolAliasLookup.create(poolAliases, startPos, context.seed()),
			dimensionPadding,
			liquidSettings
		);
		if (rawStub.isEmpty()) {
			return Optional.empty();
		}

		List<StructurePiece> rawPieces = rawStub.get().getPiecesBuilder().build().pieces();
		if (rawPieces.isEmpty()) {
			return Optional.empty();
		}

		StructurePiece startPiece = rawPieces.get(0);
		BoundingBox startBox = startPiece.getBoundingBox();
		TerrainProfile startProfile = SurfaceTerrainHelper.sampleFootprint(
			context.chunkGenerator(),
			context.heightAccessor(),
			context.randomState(),
			startBox.minX(),
			startBox.minZ(),
			startBox.maxX(),
			startBox.maxZ(),
			3
		);
		int seaLevel = context.chunkGenerator().getSeaLevel();
		if (!SurfaceTerrainHelper.fitsPiecePlacement(
			startProfile,
			startBox.minY(),
			terrainGuard.maxCoreRelief(),
			terrainGuard.maxPieceEmbed(),
			terrainGuard.maxFoundationDepth(),
			terrainGuard.minPieceYAboveSea(),
			seaLevel,
			terrainGuard.allowWater(),
			terrainGuard.maxWaterDepth()
		)) {
			return Optional.empty();
		}
		if (!hasSolidIslandBase(
			context.chunkGenerator(),
			context.heightAccessor(),
			context.randomState(),
			startBox,
			terrainGuard.minSolidThickness()
		)) {
			return Optional.empty();
		}

		List<StructurePiece> accepted = filterConnectedPieces(context, rawPieces, startBox.minY(), seaLevel);
		int rigidCount = 0;
		for (StructurePiece piece : accepted) {
			if (isRigidPiece(piece)) {
				rigidCount++;
			}
		}
		if (rigidCount < terrainGuard.minRigidPieces()) {
			return Optional.empty();
		}

		BlockPos stubPos = rawStub.get().position();
		return Optional.of(new GenerationStub(stubPos, builder -> {
			for (StructurePiece piece : accepted) {
				builder.addPiece(piece);
			}
		}));
	}

	private List<StructurePiece> filterConnectedPieces(
		GenerationContext context,
		List<StructurePiece> rawPieces,
		int startMinY,
		int seaLevel
	) {
		List<StructurePiece> accepted = new ArrayList<>();
		accepted.add(rawPieces.get(0));

		for (int i = 1; i < rawPieces.size(); i++) {
			StructurePiece candidate = rawPieces.get(i);
			if (!touchesAnyAccepted(candidate, accepted)) {
				continue;
			}
			BoundingBox box = candidate.getBoundingBox();
			if (terrainGuard.foundationStartOnly() && box.minY() > startMinY + 2) {
				// Preserve elevated sky-bridges above validated main towers (e.g. treetop bastions).
				accepted.add(candidate);
				continue;
			}

			TerrainProfile profile = SurfaceTerrainHelper.sampleFootprint(
				context.chunkGenerator(),
				context.heightAccessor(),
				context.randomState(),
				box.minX(),
				box.minZ(),
				box.maxX(),
				box.maxZ(),
				3
			);
			boolean ok;
			if (isRigidPiece(candidate)) {
				ok = SurfaceTerrainHelper.fitsPiecePlacement(
					profile,
					box.minY(),
					terrainGuard.maxPieceRelief(),
					terrainGuard.maxPieceEmbed(),
					terrainGuard.maxFoundationDepth(),
					terrainGuard.minPieceYAboveSea(),
					seaLevel,
					terrainGuard.allowWater(),
					terrainGuard.maxWaterDepth()
				) && hasSolidIslandBase(
					context.chunkGenerator(),
					context.heightAccessor(),
					context.randomState(),
					box,
					terrainGuard.minSolidThickness()
				);
			} else {
				ok = SurfaceTerrainHelper.fitsStartTerrain(
					profile,
					terrainGuard.maxPieceRelief() + 5,
					terrainGuard.allowWater(),
					terrainGuard.maxWaterDepth()
				);
			}
			if (ok) {
				accepted.add(candidate);
			}
		}
		return accepted;
	}

	private static boolean touchesAnyAccepted(StructurePiece candidate, List<StructurePiece> accepted) {
		BoundingBox box = candidate.getBoundingBox();
		for (StructurePiece parent : accepted) {
			if (parent.getBoundingBox().inflatedBy(1, 16, 1).intersects(box)) {
				return true;
			}
		}
		return false;
	}

	private static boolean isRigidPiece(StructurePiece piece) {
		if (piece instanceof PoolElementStructurePiece poolPiece) {
			return poolPiece.getElement().getProjection() == StructureTemplatePool.Projection.RIGID;
		}
		return true;
	}

	private static boolean hasSolidIslandBase(
		ChunkGenerator generator,
		LevelHeightAccessor heightAccessor,
		RandomState randomState,
		BoundingBox box,
		int minThickness
	) {
		if (minThickness <= 0) {
			return true;
		}
		int cx = (box.minX() + box.maxX()) >> 1;
		int cz = (box.minZ() + box.maxZ()) >> 1;
		int insetX0 = Math.min(cx, box.minX() + 2);
		int insetX1 = Math.max(cx, box.maxX() - 2);
		int insetZ0 = Math.min(cz, box.minZ() + 2);
		int insetZ1 = Math.max(cz, box.maxZ() - 2);
		int[][] probes = {
			{cx, cz},
			{insetX0, insetZ0},
			{insetX0, insetZ1},
			{insetX1, insetZ0},
			{insetX1, insetZ1}
		};
		for (int[] p : probes) {
			int surfaceY = generator.getBaseHeight(p[0], p[1], Heightmap.Types.WORLD_SURFACE_WG, heightAccessor, randomState);
			if (surfaceY - minThickness < heightAccessor.getMinY()) {
				return false;
			}
			NoiseColumn col = generator.getBaseColumn(p[0], p[1], heightAccessor, randomState);
			boolean thickEnough = NetherCavernHelper.hasMinimumSolidThickness(
				y -> {
					BlockState s = col.getBlock(y);
					return !s.isAir() && s.getFluidState().isEmpty() && !s.canBeReplaced();
				},
				surfaceY,
				minThickness
			);
			if (!thickEnough) {
				return false;
			}
		}
		return true;
	}

	@Override
	public void afterPlace(
		WorldGenLevel level,
		StructureManager manager,
		ChunkGenerator generator,
		RandomSource random,
		BoundingBox chunkBounds,
		ChunkPos chunkPos,
		PiecesContainer piecesContainer
	) {
		List<StructurePiece> pieces = piecesContainer.pieces();
		if (pieces.isEmpty()) {
			return;
		}
		BlockState foundationState = terrainGuard.foundationBlock().defaultBlockState();
		int foundationLimit = terrainGuard.maxFoundationDepth() + 2;
		StructurePiece firstPiece = pieces.get(0);

		for (StructurePiece piece : pieces) {
			if (terrainGuard.foundationStartOnly() && piece != firstPiece) {
				continue;
			}
			BoundingBox box = piece.getBoundingBox();
			int minX = Math.max(box.minX(), chunkBounds.minX());
			int maxX = Math.min(box.maxX(), chunkBounds.maxX());
			int minZ = Math.max(box.minZ(), chunkBounds.minZ());
			int maxZ = Math.min(box.maxZ(), chunkBounds.maxZ());
			if (minX > maxX || minZ > maxZ) {
				continue;
			}

			if (isRigidPiece(piece)) {
				extendRigidFoundation(level, minX, maxX, minZ, maxZ, box.minY(), foundationLimit, foundationState);
			} else if (terrainGuard.allowWater()) {
				extendMarshWalkwayPilings(level, minX, maxX, minZ, maxZ, foundationLimit, foundationState);
			}
		}
	}

	private static void extendRigidFoundation(
		WorldGenLevel level,
		int minX,
		int maxX,
		int minZ,
		int maxZ,
		int baseY,
		int maxDepth,
		BlockState foundationState
	) {
		if (level.isOutsideBuildHeight(baseY)) {
			return;
		}
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		for (int px = minX; px <= maxX; px++) {
			for (int pz = minZ; pz <= maxZ; pz++) {
				pos.set(px, baseY, pz);
				BlockState baseState = level.getBlockState(pos);
				if (baseState.isAir()
					|| !baseState.getFluidState().isEmpty()
					|| baseState.canBeReplaced()
					|| baseState.is(BlockTags.LEAVES)) {
					continue;
				}
				if (!baseState.isFaceSturdy(level, pos, Direction.DOWN)) {
					continue;
				}
				SurfaceTerrainHelper.extendColumnFoundation(level, px, pz, baseY, maxDepth, foundationState);
			}
		}
	}

	private static void extendMarshWalkwayPilings(
		WorldGenLevel level,
		int minX,
		int maxX,
		int minZ,
		int maxZ,
		int maxDepth,
		BlockState foundationState
	) {
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		for (int px = minX; px <= maxX; px++) {
			for (int pz = minZ; pz <= maxZ; pz++) {
				if (((px + pz) & 1) != 0) {
					continue;
				}
				int surfaceY = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, px, pz) - 1;
				if (level.isOutsideBuildHeight(surfaceY) || level.isOutsideBuildHeight(surfaceY - 1)) {
					continue;
				}
				pos.set(px, surfaceY, pz);
				BlockState topState = level.getBlockState(pos);
				if (topState.isAir() || !topState.getFluidState().isEmpty() || !topState.isFaceSturdy(level, pos, Direction.DOWN)) {
					continue;
				}
				pos.set(px, surfaceY - 1, pz);
				if (!level.getBlockState(pos).getFluidState().isEmpty()) {
					SurfaceTerrainHelper.extendColumnFoundation(level, px, pz, surfaceY, maxDepth, foundationState);
				}
			}
		}
	}
}
