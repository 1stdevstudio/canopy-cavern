package com.yogi.canopycavern.worldgen;

import com.mojang.serialization.MapCodec;
import com.yogi.canopycavern.CanopyCavernMod;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.Vec3i;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.Identifier;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.NoiseColumn;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.TemplateStructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceType;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockIgnoreProcessor;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplateManager;

/**
 * Multi-chunk {@code elder_great_tree} monument structure for {@code canopycavern:elder_bough_grove}.
 * Stacks three vertical modular templates around a continuous spiral core and anchors overhanging
 * buttress roots down into uneven terrain.
 */
public final class ElderTreeStructure extends Structure {
	public static final MapCodec<ElderTreeStructure> CODEC = simpleCodec(ElderTreeStructure::new);
	public static final StructureType<ElderTreeStructure> STRUCTURE_TYPE = () -> CODEC;
	public static final StructurePieceType PIECE_TYPE = (StructurePieceType.StructureTemplateType) Piece::new;

	public ElderTreeStructure(StructureSettings settings) {
		super(settings);
	}

	/** Registers the {@code elder_great_tree} structure type and template piece type. */
	public static void register() {
		Registry.register(BuiltInRegistries.STRUCTURE_TYPE, CanopyCavernMod.id("elder_great_tree"), STRUCTURE_TYPE);
		Registry.register(BuiltInRegistries.STRUCTURE_PIECE, CanopyCavernMod.id("elder_great_tree_piece"), PIECE_TYPE);
	}

	@Override
	protected Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
		int centerX = context.chunkPos().getMiddleBlockX();
		int centerZ = context.chunkPos().getMiddleBlockZ();
		Optional<Integer> groundY = probeDryGentleTerrain(context, centerX, centerZ);
		if (groundY.isEmpty()) {
			return Optional.empty();
		}

		BlockPos treeCenter = new BlockPos(centerX, groundY.get(), centerZ);
		Rotation rotation = Rotation.getRandom(context.random());

		return Optional.of(new GenerationStub(treeCenter, builder -> {
			for (ElderTreePlan.PieceSpec spec : ElderTreePlan.PIECES) {
				BlockPos origin = ElderTreePlan.rotatedOrigin(treeCenter, spec, rotation);
				builder.addPiece(new Piece(
					context.structureTemplateManager(),
					spec.templateId(),
					origin,
					rotation,
					spec.anchorRootsToTerrain()
				));
			}
		}));
	}

	@Override
	public StructureType<?> type() {
		return STRUCTURE_TYPE;
	}

	private static Optional<Integer> probeDryGentleTerrain(GenerationContext context, int centerX, int centerZ) {
		int minY = Integer.MAX_VALUE;
		int maxY = Integer.MIN_VALUE;
		int centerY = Integer.MIN_VALUE;

		for (Vec3i offset : ElderTreePlan.terrainProbes()) {
			int px = centerX + offset.getX();
			int pz = centerZ + offset.getZ();
			int surfaceY = context.chunkGenerator().getFirstOccupiedHeight(
				px,
				pz,
				Heightmap.Types.WORLD_SURFACE_WG,
				context.heightAccessor(),
				context.randomState()
			);
			if (surfaceY < ElderTreePlan.MIN_GROUND_Y) {
				return Optional.empty();
			}

			NoiseColumn column = context.chunkGenerator().getBaseColumn(
				px,
				pz,
				context.heightAccessor(),
				context.randomState()
			);
			if (!column.getBlock(surfaceY).getFluidState().isEmpty()
				|| !column.getBlock(surfaceY + 1).getFluidState().isEmpty()) {
				return Optional.empty();
			}

			if (offset.getX() == 0 && offset.getZ() == 0) {
				centerY = surfaceY;
			}
			minY = Math.min(minY, surfaceY);
			maxY = Math.max(maxY, surfaceY);
		}

		if (centerY < ElderTreePlan.MIN_GROUND_Y || (maxY - minY) > ElderTreePlan.MAX_RELIEF) {
			return Optional.empty();
		}
		return Optional.of(centerY);
	}

	/**
	 * Template-backed piece for {@code elder_great_tree}, supporting per-chunk placement and
	 * post-process root grounding into sloped terrain.
	 */
	public static final class Piece extends TemplateStructurePiece {
		private final boolean anchorRoots;

		public Piece(
			StructureTemplateManager manager,
			Identifier templateId,
			BlockPos origin,
			Rotation rotation,
			boolean anchorRoots
		) {
			super(PIECE_TYPE, 0, manager, templateId, templateId.toString(), createPlaceSettings(rotation), origin);
			this.anchorRoots = anchorRoots;
		}

		public Piece(StructureTemplateManager manager, CompoundTag tag) {
			super(
				PIECE_TYPE,
				tag,
				manager,
				id -> createPlaceSettings(parseRotation(tag.getStringOr("Rot", Rotation.NONE.name())))
			);
			this.anchorRoots = tag.getBooleanOr("AnchorRoots", false);
		}

		private static StructurePlaceSettings createPlaceSettings(Rotation rotation) {
			return new StructurePlaceSettings()
				.setRotation(rotation)
				.setMirror(Mirror.NONE)
				.setIgnoreEntities(false)
				.addProcessor(BlockIgnoreProcessor.STRUCTURE_BLOCK);
		}

		private static Rotation parseRotation(String rawName) {
			try {
				return Rotation.valueOf(rawName);
			} catch (IllegalArgumentException ignored) {
				return Rotation.NONE;
			}
		}

		@Override
		protected void addAdditionalSaveData(StructurePieceSerializationContext context, CompoundTag tag) {
			super.addAdditionalSaveData(context, tag);
			tag.putString("Rot", this.placeSettings.getRotation().name());
			tag.putBoolean("AnchorRoots", this.anchorRoots);
		}

		@Override
		protected void handleDataMarker(
			String marker,
			BlockPos pos,
			ServerLevelAccessor level,
			RandomSource random,
			BoundingBox box
		) {
			// Loot containers are embedded directly in the structure NBT as chest block entities.
		}

		@Override
		public void postProcess(
			WorldGenLevel level,
			StructureManager structureManager,
			ChunkGenerator generator,
			RandomSource random,
			BoundingBox chunkBox,
			ChunkPos chunkPos,
			BlockPos pivot
		) {
			super.postProcess(level, structureManager, generator, random, chunkBox, chunkPos, pivot);
			if (this.anchorRoots) {
				extendRootAnchors(level, chunkBox);
			}
		}

		private void extendRootAnchors(WorldGenLevel level, BoundingBox chunkBox) {
			int minX = Math.max(this.boundingBox.minX(), chunkBox.minX());
			int maxX = Math.min(this.boundingBox.maxX(), chunkBox.maxX());
			int minZ = Math.max(this.boundingBox.minZ(), chunkBox.minZ());
			int maxZ = Math.min(this.boundingBox.maxZ(), chunkBox.maxZ());
			if (minX > maxX || minZ > maxZ) {
				return;
			}

			int baseY = this.templatePosition.getY();
			int minWorldY = level.getMinY() + 1;
			BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();

			for (int x = minX; x <= maxX; x++) {
				for (int z = minZ; z <= maxZ; z++) {
					cursor.set(x, baseY, z);
					if (!isRootAnchorSource(level.getBlockState(cursor))) {
						continue;
					}

					for (int drop = 1; drop <= ElderTreePlan.MAX_ROOT_ANCHOR_DROP; drop++) {
						int targetY = baseY - drop;
						if (targetY <= minWorldY) {
							break;
						}
						cursor.set(x, targetY, z);
						BlockState existing = level.getBlockState(cursor);
						if (existing.isFaceSturdy(level, cursor, Direction.UP) && existing.getFluidState().isEmpty()) {
							break;
						}
						level.setBlock(cursor, selectRootBlock(x, targetY, z, drop), Block.UPDATE_CLIENTS);
					}
				}
			}
		}

		private static boolean isRootAnchorSource(BlockState state) {
			return state.is(Blocks.DARK_OAK_WOOD)
				|| state.is(Blocks.DARK_OAK_LOG)
				|| state.is(Blocks.MANGROVE_WOOD)
				|| state.is(Blocks.MOSSY_COBBLESTONE);
		}

		private static BlockState selectRootBlock(int x, int y, int z, int drop) {
			int hash = Math.floorMod(x * 73428767 ^ z * 912931 ^ y * 19349663, 12);
			if (drop >= 5 && hash < 3) {
				return Blocks.MOSSY_COBBLESTONE.defaultBlockState();
			}
			if (hash == 3 || hash == 4) {
				return Blocks.MANGROVE_WOOD.defaultBlockState();
			}
			return Blocks.DARK_OAK_WOOD.defaultBlockState();
		}
	}
}
