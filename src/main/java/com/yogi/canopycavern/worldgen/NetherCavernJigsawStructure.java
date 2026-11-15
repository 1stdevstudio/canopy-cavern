package com.yogi.canopycavern.worldgen;

import com.mojang.serialization.Codec;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.worldgen.NetherCavernHelper.CavernFootprint;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.OptionalInt;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
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
 * Interior cavern Jigsaw structure for the Nether dimension.
 * Avoids heightmap roof projection, probes 3D cavern shelves between the lava sea and bedrock
 * ceiling, prunes lava-exposed or roof-clipped wings, and extends sturdy Nether piers downward.
 */
public final class NetherCavernJigsawStructure extends Structure {

	public record CavernGuard(
		int minFloorY,
		int maxFloorY,
		int minHeadroom,
		int maxCeilingY,
		int coreProbeRadius,
		int maxCoreRelief,
		int maxPieceRelief,
		int maxPieceEmbed,
		int maxFoundationDepth,
		int minRigidPieces,
		Block foundationBlock
	) {
		public static final CavernGuard DEFAULT = new CavernGuard(
			34, 96, 16, 118, 7, 7, 8, 5, 16, 2, Blocks.POLISHED_BLACKSTONE_BRICKS
		);

		public static final Codec<CavernGuard> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.intRange(32, 100).optionalFieldOf("min_floor_y", DEFAULT.minFloorY()).forGetter(CavernGuard::minFloorY),
			Codec.intRange(40, 112).optionalFieldOf("max_floor_y", DEFAULT.maxFloorY()).forGetter(CavernGuard::maxFloorY),
			Codec.intRange(6, 48).optionalFieldOf("min_headroom", DEFAULT.minHeadroom()).forGetter(CavernGuard::minHeadroom),
			Codec.intRange(64, 124).optionalFieldOf("max_ceiling_y", DEFAULT.maxCeilingY()).forGetter(CavernGuard::maxCeilingY),
			Codec.intRange(2, 24).optionalFieldOf("core_probe_radius", DEFAULT.coreProbeRadius()).forGetter(CavernGuard::coreProbeRadius),
			Codec.intRange(0, 20).optionalFieldOf("max_core_relief", DEFAULT.maxCoreRelief()).forGetter(CavernGuard::maxCoreRelief),
			Codec.intRange(0, 20).optionalFieldOf("max_piece_relief", DEFAULT.maxPieceRelief()).forGetter(CavernGuard::maxPieceRelief),
			Codec.intRange(0, 12).optionalFieldOf("max_piece_embed", DEFAULT.maxPieceEmbed()).forGetter(CavernGuard::maxPieceEmbed),
			Codec.intRange(0, 24).optionalFieldOf("max_foundation_depth", DEFAULT.maxFoundationDepth()).forGetter(CavernGuard::maxFoundationDepth),
			Codec.intRange(1, 24).optionalFieldOf("min_rigid_pieces", DEFAULT.minRigidPieces()).forGetter(CavernGuard::minRigidPieces),
			BuiltInRegistries.BLOCK.byNameCodec().optionalFieldOf("foundation_block", DEFAULT.foundationBlock()).forGetter(CavernGuard::foundationBlock)
		).apply(instance, CavernGuard::new));
	}

	public static final MapCodec<NetherCavernJigsawStructure> CODEC = RecordCodecBuilder.<NetherCavernJigsawStructure>mapCodec(
		instance -> instance.group(
			settingsCodec(instance),
			StructureTemplatePool.CODEC.fieldOf("start_pool").forGetter(s -> s.startPool),
			Identifier.CODEC.optionalFieldOf("start_jigsaw_name").forGetter(s -> s.startJigsawName),
			Codec.intRange(0, 20).fieldOf("size").forGetter(s -> s.maxDepth),
			Codec.BOOL.optionalFieldOf("use_expansion_hack", false).forGetter(s -> s.useExpansionHack),
			JigsawStructure.MaxDistance.CODEC.optionalFieldOf("max_distance_from_center", new JigsawStructure.MaxDistance(64))
				.forGetter(s -> s.maxDistanceFromCenter),
			Codec.list(PoolAliasBinding.CODEC).optionalFieldOf("pool_aliases", List.of()).forGetter(s -> s.poolAliases),
			DimensionPadding.CODEC.optionalFieldOf("dimension_padding", JigsawStructure.DEFAULT_DIMENSION_PADDING)
				.forGetter(s -> s.dimensionPadding),
			LiquidSettings.CODEC.optionalFieldOf("liquid_settings", JigsawStructure.DEFAULT_LIQUID_SETTINGS)
				.forGetter(s -> s.liquidSettings),
			CavernGuard.CODEC.optionalFieldOf("cavern_guard", CavernGuard.DEFAULT).forGetter(s -> s.cavernGuard)
		).apply(instance, NetherCavernJigsawStructure::new)
	).validate(NetherCavernJigsawStructure::verifyRange);

	public static final StructureType<NetherCavernJigsawStructure> TYPE = () -> CODEC;

	private final Holder<StructureTemplatePool> startPool;
	private final Optional<Identifier> startJigsawName;
	private final int maxDepth;
	private final boolean useExpansionHack;
	private final JigsawStructure.MaxDistance maxDistanceFromCenter;
	private final List<PoolAliasBinding> poolAliases;
	private final DimensionPadding dimensionPadding;
	private final LiquidSettings liquidSettings;
	private final CavernGuard cavernGuard;

	private NetherCavernJigsawStructure(
		StructureSettings settings,
		Holder<StructureTemplatePool> startPool,
		Optional<Identifier> startJigsawName,
		int maxDepth,
		boolean useExpansionHack,
		JigsawStructure.MaxDistance maxDistanceFromCenter,
		List<PoolAliasBinding> poolAliases,
		DimensionPadding dimensionPadding,
		LiquidSettings liquidSettings,
		CavernGuard cavernGuard
	) {
		super(settings);
		this.startPool = startPool;
		this.startJigsawName = startJigsawName;
		this.maxDepth = maxDepth;
		this.useExpansionHack = useExpansionHack;
		this.maxDistanceFromCenter = maxDistanceFromCenter;
		this.poolAliases = poolAliases;
		this.dimensionPadding = dimensionPadding;
		this.liquidSettings = liquidSettings;
		this.cavernGuard = cavernGuard;
	}

	/** Registers {@code canopycavern:nether_cavern_jigsaw} in the structure-type registry. */
	public static void register() {
		Registry.register(BuiltInRegistries.STRUCTURE_TYPE, CanopyCavernMod.id("nether_cavern_jigsaw"), TYPE);
	}

	private static DataResult<NetherCavernJigsawStructure> verifyRange(NetherCavernJigsawStructure structure) {
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
		OptionalInt anchorFloor = NetherCavernHelper.findAnchorFloorY(
			context.chunkGenerator(),
			context.heightAccessor(),
			context.randomState(),
			middleX,
			middleZ,
			cavernGuard.minFloorY(),
			cavernGuard.maxFloorY(),
			cavernGuard.minHeadroom(),
			cavernGuard.maxCeilingY()
		);
		if (anchorFloor.isEmpty()) {
			return Optional.empty();
		}

		int anchorY = anchorFloor.getAsInt();
		int radius = cavernGuard.coreProbeRadius();
		CavernFootprint precheck = NetherCavernHelper.sampleFootprint(
			context.chunkGenerator(),
			context.heightAccessor(),
			context.randomState(),
			middleX - radius,
			middleZ - radius,
			middleX + radius,
			middleZ + radius,
			4,
			anchorY,
			cavernGuard.maxFoundationDepth(),
			cavernGuard.maxPieceEmbed(),
			cavernGuard.minFloorY(),
			cavernGuard.maxCeilingY(),
			cavernGuard.minHeadroom()
		);
		if (!NetherCavernHelper.fitsStartFootprint(precheck, cavernGuard.maxCoreRelief())) {
			return Optional.empty();
		}

		BlockPos startPos = new BlockPos(chunkPos.getMinBlockX(), anchorY, chunkPos.getMinBlockZ());
		Optional<GenerationStub> rawStub = JigsawPlacement.addPieces(
			context,
			startPool,
			startJigsawName,
			maxDepth,
			startPos,
			useExpansionHack,
			Optional.empty(),
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

		BoundingBox startBox = rawPieces.get(0).getBoundingBox();
		CavernFootprint startFootprint = NetherCavernHelper.sampleFootprint(
			context.chunkGenerator(),
			context.heightAccessor(),
			context.randomState(),
			startBox.minX(),
			startBox.minZ(),
			startBox.maxX(),
			startBox.maxZ(),
			3,
			startBox.minY(),
			cavernGuard.maxFoundationDepth(),
			cavernGuard.maxPieceEmbed(),
			cavernGuard.minFloorY(),
			cavernGuard.maxCeilingY(),
			Math.max(cavernGuard.minHeadroom(), startBox.getYSpan())
		);
		if (!NetherCavernHelper.fitsPiecePlacement(
			startFootprint,
			startBox.minY(),
			startBox.maxY(),
			cavernGuard.maxCoreRelief(),
			cavernGuard.maxPieceEmbed(),
			cavernGuard.maxFoundationDepth(),
			cavernGuard.minFloorY(),
			cavernGuard.maxCeilingY()
		)) {
			return Optional.empty();
		}

		List<StructurePiece> accepted = filterConnectedPieces(context, rawPieces);
		int rigidCount = 0;
		for (StructurePiece piece : accepted) {
			if (isRigidPiece(piece)) {
				rigidCount++;
			}
		}
		if (rigidCount < cavernGuard.minRigidPieces()) {
			return Optional.empty();
		}

		BlockPos stubPos = rawStub.get().position();
		return Optional.of(new GenerationStub(stubPos, builder -> {
			for (StructurePiece piece : accepted) {
				builder.addPiece(piece);
			}
		}));
	}

	private List<StructurePiece> filterConnectedPieces(GenerationContext context, List<StructurePiece> rawPieces) {
		List<StructurePiece> accepted = new ArrayList<>();
		accepted.add(rawPieces.get(0));
		for (int i = 1; i < rawPieces.size(); i++) {
			StructurePiece candidate = rawPieces.get(i);
			if (!touchesAnyAccepted(candidate, accepted)) {
				continue;
			}
			BoundingBox box = candidate.getBoundingBox();
			int clearHeight = Math.max(8, box.getYSpan());
			CavernFootprint footprint = NetherCavernHelper.sampleFootprint(
				context.chunkGenerator(),
				context.heightAccessor(),
				context.randomState(),
				box.minX(),
				box.minZ(),
				box.maxX(),
				box.maxZ(),
				3,
				box.minY(),
				cavernGuard.maxFoundationDepth(),
				cavernGuard.maxPieceEmbed(),
				cavernGuard.minFloorY(),
				cavernGuard.maxCeilingY(),
				clearHeight
			);
			boolean ok = isRigidPiece(candidate)
				? NetherCavernHelper.fitsPiecePlacement(
					footprint,
					box.minY(),
					box.maxY(),
					cavernGuard.maxPieceRelief(),
					cavernGuard.maxPieceEmbed(),
					cavernGuard.maxFoundationDepth(),
					cavernGuard.minFloorY(),
					cavernGuard.maxCeilingY()
				)
				: NetherCavernHelper.fitsStartFootprint(footprint, cavernGuard.maxPieceRelief() + 4)
					&& box.minY() >= cavernGuard.minFloorY()
					&& box.maxY() <= cavernGuard.maxCeilingY();
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
		BlockState foundationState = cavernGuard.foundationBlock().defaultBlockState();
		int foundationLimit = cavernGuard.maxFoundationDepth() + 4;
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();

		for (StructurePiece piece : pieces) {
			if (!isRigidPiece(piece)) {
				continue;
			}
			BoundingBox box = piece.getBoundingBox();
			int minX = Math.max(box.minX(), chunkBounds.minX());
			int maxX = Math.min(box.maxX(), chunkBounds.maxX());
			int minZ = Math.max(box.minZ(), chunkBounds.minZ());
			int maxZ = Math.min(box.maxZ(), chunkBounds.maxZ());
			if (minX > maxX || minZ > maxZ || level.isOutsideBuildHeight(box.minY())) {
				continue;
			}
			for (int px = minX; px <= maxX; px++) {
				for (int pz = minZ; pz <= maxZ; pz++) {
					pos.set(px, box.minY(), pz);
					BlockState baseState = level.getBlockState(pos);
					if (baseState.isAir() || !baseState.getFluidState().isEmpty() || baseState.canBeReplaced()) {
						continue;
					}
					if (!baseState.isFaceSturdy(level, pos, Direction.DOWN)) {
						continue;
					}
					NetherCavernHelper.extendColumnFoundation(level, px, pz, box.minY(), foundationLimit, foundationState);
				}
			}
		}
	}
}
