package com.yogi.canopycavern.worldgen;

import com.yogi.canopycavern.core.ClimateSimulation;
import com.yogi.canopycavern.core.ClimateSimulation.ClimateInput;
import com.yogi.canopycavern.core.ClimateSimulation.ClimateSnapshot;
import com.yogi.canopycavern.core.EnvironmentTelemetry.AmbientInput;
import com.yogi.canopycavern.worldgen.tree.ComplexTreeGeometry;
import com.yogi.canopycavern.worldgen.tree.ComplexTreeGeometry.BoughSegment;
import com.yogi.canopycavern.worldgen.tree.ComplexTreeGeometry.CrownAnchor;
import com.yogi.canopycavern.worldgen.tree.ComplexTreeGeometry.SkeletonPlan;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Rotation;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ComplexTreeWorldgenTest {

	@Test
	void elderTreePlanAlignsVerticalShaftAxesAcrossAllRotations() {
		BlockPos treeCenter = new BlockPos(120, 72, -64);
		assertEquals(9, ElderTreePlan.terrainProbes().size());

		for (ElderTreePlan.PieceSpec piece : ElderTreePlan.PIECES) {
			assertTrue(piece.fitsVanillaTemplateLimit(), piece.templateId() + " must fit 48x48x48");
		}
		assertEquals(
			ElderTreePlan.ROOT_HOLLOW_BASE.relativeY() + ElderTreePlan.ROOT_HOLLOW_BASE.sizeY(),
			ElderTreePlan.MID_BOUGH_BRIDGES.relativeY()
		);
		assertEquals(
			ElderTreePlan.MID_BOUGH_BRIDGES.relativeY() + ElderTreePlan.MID_BOUGH_BRIDGES.sizeY(),
			ElderTreePlan.CROWN_OBSERVATORY.relativeY()
		);

		for (Rotation rotation : Rotation.values()) {
			for (ElderTreePlan.PieceSpec piece : ElderTreePlan.PIECES) {
				BlockPos alignedAxis = ElderTreePlan.transformLocalPos(
					treeCenter,
					piece,
					rotation,
					piece.axisX(),
					0,
					piece.axisZ()
				);
				assertEquals(treeCenter.getX(), alignedAxis.getX(), "X axis mismatch for " + rotation);
				assertEquals(treeCenter.getZ(), alignedAxis.getZ(), "Z axis mismatch for " + rotation);
				assertEquals(treeCenter.getY() + piece.relativeY(), alignedAxis.getY());
			}
		}
	}

	@Test
	void archingRootPathRemainsContinuousAndWithinChunkBudget() {
		BlockPos origin = new BlockPos(0, 70, 0);
		int collarY = 72;
		for (int i = 0; i < 6; i++) {
			double angle = (Math.PI * 2.0 * i) / 6.0;
			List<BlockPos> path = ComplexTreeGeometry.planArchPath(origin, collarY, angle, 4);
			assertTrue(path.size() >= 4, "Arch path should span outwards");
			assertEquals(collarY, path.getFirst().getY());
			assertTrue(path.getLast().getY() <= origin.getY(), "Arch should descend to ground level");

			for (int step = 1; step < path.size(); step++) {
				BlockPos prev = path.get(step - 1);
				BlockPos cur = path.get(step);
				int dx = Math.abs(cur.getX() - prev.getX());
				int dy = Math.abs(cur.getY() - prev.getY());
				int dz = Math.abs(cur.getZ() - prev.getZ());
				assertTrue(dx <= 1 && dy <= 1 && dz <= 1, "Root arch step must remain connected");
				assertTrue(Math.abs(cur.getX() - origin.getX()) <= 5);
				assertTrue(Math.abs(cur.getZ() - origin.getZ()) <= 5);
			}
		}
	}

	@Test
	void gnarledBoughTrunkPlacerProducesBoundedBranchedSkeletons() {
		BlockPos origin = new BlockPos(10, 68, 10);
		RandomSource random = RandomSource.create(4242L);
		SkeletonPlan plan = ComplexTreeGeometry.planSkeleton(
			origin,
			14,
			5,
			() -> 3 + random.nextInt(2),
			true,
			random
		);

		assertFalse(plan.trunkBlocks().isEmpty());
		assertFalse(plan.boughSegments().isEmpty());
		assertTrue(plan.attachments().size() >= 6, "Hero trunk should emit crown + bough foliage anchors");

		boolean hasHorizontalBough = plan.boughSegments().stream()
			.map(BoughSegment::axis)
			.anyMatch(axis -> axis == Direction.Axis.X || axis == Direction.Axis.Z);
		assertTrue(hasHorizontalBough, "Boughs should orient horizontally along X or Z");

		for (CrownAnchor attachment : plan.attachments()) {
			int dx = Math.abs(attachment.pos().getX() - origin.getX());
			int dz = Math.abs(attachment.pos().getZ() - origin.getZ());
			assertTrue(dx <= 8 && dz <= 8, "Attachment exceeded safe tree write radius: dx=" + dx + ", dz=" + dz);
		}
	}

	@Test
	void elderBoughGroveSimulatesHumidWoodlandMicroclimate() {
		AmbientInput clearDay = new AmbientInput(0.65f, 70, 63, false, 15, false, false, false);
		ClimateSnapshot grove = ClimateSimulation.evaluate(
			new ClimateInput(clearDay, "canopycavern:elder_bough_grove", 0, 0, false, false, false, false, 0L)
		);
		ClimateSnapshot plains = ClimateSimulation.evaluate(
			new ClimateInput(clearDay, "minecraft:plains", 0, 0, false, false, false, false, 0L)
		);

		assertEquals(82, grove.humidityPercent());
		assertTrue(grove.humidityPercent() > plains.humidityPercent());
	}
}
