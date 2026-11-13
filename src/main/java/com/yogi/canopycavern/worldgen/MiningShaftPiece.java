package com.yogi.canopycavern.worldgen;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceType;

final class MiningShaftPiece extends StructurePiece {
    private static final BlockState STONE = Blocks.DEEPSLATE_BRICKS.defaultBlockState();
    private static final BlockState AIR = Blocks.AIR.defaultBlockState();
    private final int x, y, z;

    MiningShaftPiece(StructurePieceType type, int x, int y, int z) {
        super(type, 0, new BoundingBox(x, -33, z - 3, x + 15, y + 4, z + 15));
        this.x = x;
        this.y = y;
        this.z = z;
    }

    MiningShaftPiece(StructurePieceSerializationContext context, CompoundTag tag) {
        super(MiningCityStructure.shaftType(), tag);
        x = tag.getIntOr("OriginX", boundingBox.minX());
        y = tag.getIntOr("SurfaceY", boundingBox.maxY() - 4);
        z = tag.getIntOr("OriginZ", boundingBox.minZ() + 3);
    }

    BlockPos surfaceRoom() {
        var top = MiningShaftPlan.build(y).landings().getLast();
        var origin = MiningSurfacePlan.origin(top);
        return new BlockPos(x + origin.x(), y - 1, z + origin.z());
    }

    @Override
    protected void addAdditionalSaveData(StructurePieceSerializationContext context, CompoundTag tag) {
        tag.putInt("OriginX", x);
        tag.putInt("SurfaceY", y);
        tag.putInt("OriginZ", z);
    }

    @Override
    public void postProcess(WorldGenLevel level, StructureManager manager, ChunkGenerator generator,
                            RandomSource random, BoundingBox bounds, ChunkPos chunk, BlockPos pivot) {
        if (!bounds.intersects(x, z - 2, x + 14, z + 15)) return;
        var plan = MiningShaftPlan.build(y);
        for (int h = -33; h <= y + 3; h++) {
            for (int dx = 0; dx <= 8; dx++) {
                for (int dz = -1; dz <= 10; dz++) {
                    boolean shell = h == -33 || h == y + 3 || dx == 0 || dx == 8 || dx == 4 || dz == -1 || dz == 10;
                    put(level, bounds, dx, h, dz, shell ? STONE : AIR);
                }
            }
        }
        for (var step : plan.steps()) {
            BlockState floor = switch (step.uphill()) {
                case NORTH -> Blocks.DEEPSLATE_BRICK_STAIRS.defaultBlockState().setValue(StairBlock.FACING, Direction.NORTH);
                case SOUTH -> Blocks.DEEPSLATE_BRICK_STAIRS.defaultBlockState().setValue(StairBlock.FACING, Direction.SOUTH);
                case FLAT -> STONE;
            };
            put(level, bounds, step.x(), step.y(), step.z(), floor);
        }
        for (var landing : plan.landings()) {
            for (int dx = 1; dx <= 7; dx++) {
                for (int dy = 0; dy <= 2; dy++) {
                    put(level, bounds, dx, landing.walkY() + dy, landing.z(), AIR);
                }
            }
            put(level, bounds, 0, landing.walkY() + 2, landing.z(), Blocks.SEA_LANTERN.defaultBlockState());
            if (landing.walkY() == 0 || landing.walkY() == -16 || landing.walkY() == -32 || landing.walkY() == y) {
                corridor(level, bounds, 8, landing.z() - 1, landing.walkY() == 0 ? 14 : 11, landing.z() + 1, landing.walkY());
            }
        }
        var top = plan.landings().getLast();
        supportSurfaceApproach(level, bounds, top);
        var guard = MiningShaftPlan.surfaceGuard(top);
        for (int dx = guard.minX(); dx <= guard.maxX(); dx++) {
            for (int dy = -1; dy <= 1; dy++) {
                put(level, bounds, dx, guard.walkY() + dy, guard.z(), STONE);
            }
        }
        corridor(level, bounds, 12, 2, 14, 15, 0);
        for (int dx = 12; dx <= 14; dx++) {
            for (int dy = 0; dy < 3; dy++) put(level, bounds, dx, dy, 1, AIR);
        }
    }

    private void supportSurfaceApproach(WorldGenLevel level, BoundingBox bounds, MiningShaftPlan.Landing top) {
        // The bridge to the platform begins beyond the shaft's supporting east wall.
        var pos = new BlockPos.MutableBlockPos();
        for (int dx = 9; dx <= 11; dx++) {
            for (int dz = top.z() - 1; dz <= top.z() + 1; dz++) {
                for (int py = top.walkY() - 2; py >= top.walkY() - 1 - MiningSurfacePlan.SUPPORT_DEPTH; py--) {
                    if (!bounds.isInside(x + dx, py, z + dz)) break;
                    pos.set(x + dx, py, z + dz);
                    if (level.getBlockState(pos).isFaceSturdy(level, pos, Direction.UP)) break;
                    level.setBlock(pos, STONE, 2);
                }
            }
        }
    }

    private void corridor(WorldGenLevel level, BoundingBox bounds, int x0, int z0, int x1, int z1, int walkY) {
        for (int dx = x0 - 1; dx <= x1 + 1; dx++) {
            for (int dz = z0 - 1; dz <= z1 + 1; dz++) {
                boolean inside = dx >= x0 && dx <= x1 && dz >= z0 && dz <= z1;
                if (inside) {
                    put(level, bounds, dx, walkY - 1, dz, STONE);
                    put(level, bounds, dx, walkY + 3, dz, STONE);
                    for (int dy = 0; dy < 3; dy++) put(level, bounds, dx, walkY + dy, dz, AIR);
                } else {
                    boolean longCorridor = z1 - z0 > x1 - x0;
                    boolean wall = longCorridor ? dx < x0 || dx > x1 : dz < z0 || dz > z1;
                    if (wall && dz < 16 && dx >= 8 && (longCorridor || dx < 12 || walkY == 0)) {
                        for (int dy = 0; dy < 3; dy++) put(level, bounds, dx, walkY + dy, dz, STONE);
                    }
                }
            }
        }
    }

    private void put(WorldGenLevel level, BoundingBox bounds, int dx, int y, int dz, BlockState state) {
        if (bounds.isInside(x + dx, y, z + dz)) {
            level.setBlock(new BlockPos(x + dx, y, z + dz), state, 2);
        }
    }
}
