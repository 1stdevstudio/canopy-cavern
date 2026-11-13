package com.yogi.canopycavern.worldgen;

import com.mojang.serialization.MapCodec;
import com.yogi.canopycavern.CanopyCavernMod;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.Identifier;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.TemplateStructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceType;
import net.minecraft.world.level.levelgen.structure.templatesystem.LiquidSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;

import java.util.Optional;

public final class MiningCityStructure extends Structure {
    private static final MapCodec<MiningCityStructure> CODEC = simpleCodec(MiningCityStructure::new);
    private static final StructureType<MiningCityStructure> TYPE = () -> CODEC;
    private static final StructurePieceType ROOM = Room::new;
    private static final StructurePieceType SHAFT = MiningShaftPiece::new;
    static StructurePieceType shaftType() { return SHAFT; }


    public static void register() {
        Registry.register(BuiltInRegistries.STRUCTURE_TYPE, CanopyCavernMod.id("mining_city"), TYPE);
        Registry.register(BuiltInRegistries.STRUCTURE_PIECE, CanopyCavernMod.id("mining_city_room"), ROOM);
        Registry.register(BuiltInRegistries.STRUCTURE_PIECE, CanopyCavernMod.id("mining_city_shaft"), SHAFT);
    }

    private MiningCityStructure(StructureSettings settings) {
        super(settings);
    }

    @Override
    public StructureType<?> type() {
        return TYPE;
    }

    @Override
    protected Optional<GenerationStub> findGenerationPoint(GenerationContext ctx) {
        int x = ctx.chunkPos().getMiddleBlockX();
        int z = ctx.chunkPos().getMiddleBlockZ();
        int y = surface(ctx, x + 16, z);
        if (y < 48 || y > 144 || ctx.heightAccessor().isOutsideBuildHeight(y + 19)
                || ctx.heightAccessor().isOutsideBuildHeight(-33)) return Optional.empty();
        var top = MiningShaftPlan.build(y).landings().getLast();
        for (var probe : MiningSurfacePlan.terrainProbes(top)) {
            int px = x + probe.x();
            int pz = z + probe.z();
            int terrain = surface(ctx, px, pz);
            if (Math.abs(terrain - y) > 3 || !ctx.chunkGenerator()
                    .getBaseColumn(px, pz, ctx.heightAccessor(), ctx.randomState())
                    .getBlock(terrain - 1).getFluidState().isEmpty()) return Optional.empty();
        }
        return Optional.of(new GenerationStub(new BlockPos(x, y, z), pieces -> {
            var shaft = new MiningShaftPiece(SHAFT, x, y, z);
            pieces.addPiece(shaft);
            pieces.addPiece(new Room(ctx, "surface", shaft.surfaceRoom()));
            pieces.addPiece(new Room(ctx, "industry_district", new BlockPos(x + 12, -17, z - 12)));
            pieces.addPiece(new Room(ctx, "excavation_district", new BlockPos(x + 12, -33, z - 12)));
            pieces.addPiece(new Room(ctx, "city_districts", new BlockPos(x + 13 - 50, -1, z + 16)));
        }));
    }

    private static int surface(GenerationContext ctx, int x, int z) {
        return ctx.chunkGenerator().getBaseHeight(x, z, Heightmap.Types.WORLD_SURFACE_WG,
            ctx.heightAccessor(), ctx.randomState());
    }

    private static final class Room extends TemplateStructurePiece {
        private Room(GenerationContext ctx, String name, BlockPos pos) {
            super(ROOM, 0, ctx.structureTemplateManager(), CanopyCavernMod.id("mining_city/" + name),
                "canopycavern:mining_city/" + name, settings(), pos);
            if (isSurface()) {
                boundingBox.encapsulate(pos.below(MiningSurfacePlan.SUPPORT_DEPTH));
            }
        }

        private Room(StructurePieceSerializationContext ctx, CompoundTag tag) {
            super(ROOM, tag, ctx.structureTemplateManager(), id -> settings());
        }

        private boolean isSurface() {
            return templateName.equals("canopycavern:mining_city/surface");
        }

        @Override
        public void postProcess(WorldGenLevel level, StructureManager manager, ChunkGenerator generator,
                                RandomSource random, BoundingBox bounds, ChunkPos chunk, BlockPos pivot) {
            super.postProcess(level, manager, generator, random, bounds, chunk, pivot);
            if (!isSurface()) return;
            // TemplateStructurePiece recomputes its own bounds during placement.
            boundingBox.encapsulate(templatePosition.below(MiningSurfacePlan.SUPPORT_DEPTH));
            int originX = templatePosition.getX();
            int originY = templatePosition.getY();
            int originZ = templatePosition.getZ();
            int minX = Math.max(originX, bounds.minX());
            int minZ = Math.max(originZ, bounds.minZ());
            int maxX = Math.min(originX + MiningSurfacePlan.WIDTH - 1, bounds.maxX());
            int maxZ = Math.min(originZ + MiningSurfacePlan.DEPTH - 1, bounds.maxZ());
            int minY = Math.max(originY - MiningSurfacePlan.SUPPORT_DEPTH, bounds.minY());
            var stone = Blocks.COBBLED_DEEPSLATE.defaultBlockState();
            var pos = new BlockPos.MutableBlockPos();
            for (int px = minX; px <= maxX; px++) {
                for (int pz = minZ; pz <= maxZ; pz++) {
                    if (!MiningSurfacePlan.hasFoundation(px - originX, pz - originZ)) continue;
                    for (int py = originY - 1; py >= minY; py--) {
                        pos.set(px, py, pz);
                        if (level.getBlockState(pos).isFaceSturdy(level, pos, Direction.UP)) break;
                        level.setBlock(pos, stone, 2);
                    }
                }
            }
        }

        private static StructurePlaceSettings settings() {
            return new StructurePlaceSettings().setLiquidSettings(LiquidSettings.IGNORE_WATERLOGGING);
        }

        @Override
        protected void handleDataMarker(String name, BlockPos pos, ServerLevelAccessor level,
                                        RandomSource random, BoundingBox bounds) {
        }
    }
}
