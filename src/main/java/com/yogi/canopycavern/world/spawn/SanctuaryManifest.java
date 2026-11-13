package com.yogi.canopycavern.world.spawn;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;

/**
 * Immutable manifest describing the Canopy Sanctuary modular server spawn hub,
 * its piece placement order, connections, sign/lectern bindings, and rotation transforms.
 */
public record SanctuaryManifest(
	int schemaVersion,
	String hubId,
	int dataVersion,
	int[] arrivalLocalPos,
	double arrivalBaseYaw,
	int safePadRadius,
	int safeZoneDefaultRadius,
	int[] envelopeMin,
	int[] envelopeMax,
	List<String> supportedRotations,
	List<PieceSpec> pieces
) {
	public static final String MANIFEST_RESOURCE = "/data/canopycavern/server_spawn/manifest.json";
	private static final Gson GSON = new GsonBuilder().create();
	private static volatile SanctuaryManifest cached;

	public record PieceConnection(String name, int[] offset, String direction) {
	}

	public record SignSpec(int[] offset, boolean glowing, List<String> lines) {
	}

	public record LecternSpec(int[] offset, String bookKey) {
	}

	public record PieceSpec(
		String id,
		String template,
		String role,
		int[] offset,
		int[] size,
		boolean excavateBelow,
		int foundationSkirt,
		int nonAirBlocks,
		String sha256Prefix,
		List<PieceConnection> connections,
		List<SignSpec> signs,
		List<LecternSpec> lecterns
	) {
		public Identifier templateIdentifier() {
			return Identifier.parse(template);
		}
	}

	/** Loads and caches the bundled Canopy Sanctuary manifest. */
	public static SanctuaryManifest loadDefault() {
		SanctuaryManifest local = cached;
		if (local != null) {
			return local;
		}
		try (InputStream stream = SanctuaryManifest.class.getResourceAsStream(MANIFEST_RESOURCE)) {
			if (stream == null) {
				throw new IllegalStateException("Missing bundled Canopy Sanctuary manifest: " + MANIFEST_RESOURCE);
			}
			SanctuaryManifest loaded = loadFromStream(stream);
			cached = loaded;
			return loaded;
		} catch (IOException ex) {
			throw new IllegalStateException("Failed reading Canopy Sanctuary manifest", ex);
		}
	}

	/** Parses a manifest JSON stream (used by runtime loader and unit tests). */
	public static SanctuaryManifest loadFromStream(InputStream stream) throws IOException {
		try (InputStreamReader reader = new InputStreamReader(Objects.requireNonNull(stream), StandardCharsets.UTF_8)) {
			SanctuaryManifest manifest = GSON.fromJson(reader, SanctuaryManifest.class);
			if (manifest == null || manifest.pieces == null || manifest.pieces.isEmpty()) {
				throw new IllegalStateException("Canopy Sanctuary manifest contains no pieces");
			}
			return manifest;
		}
	}

	/** Parses user/command rotation strings flexibly (`none`, `0`, `cw_90`, `CLOCKWISE_90`, etc.). */
	public static Rotation parseRotation(String raw) {
		if (raw == null || raw.isBlank()) {
			return Rotation.NONE;
		}
		return switch (raw.trim().toLowerCase(Locale.ROOT)) {
			case "none", "north", "0" -> Rotation.NONE;
			case "clockwise_90", "cw_90", "cw90", "east", "90" -> Rotation.CLOCKWISE_90;
			case "clockwise_180", "180", "south" -> Rotation.CLOCKWISE_180;
			case "counterclockwise_90", "ccw_90", "ccw90", "west", "270" -> Rotation.COUNTERCLOCKWISE_90;
			default -> throw new IllegalArgumentException(
				"Unsupported rotation '" + raw + "'. Use none, clockwise_90, clockwise_180, or counterclockwise_90."
			);
		};
	}

	/** Transforms a hub-relative point `(hx, hy, hz)` around `(0,0,0)` via Minecraft's native transform. */
	public static BlockPos transformHubOffset(int hx, int hy, int hz, Rotation rotation) {
		return StructureTemplate.transform(new BlockPos(hx, hy, hz), Mirror.NONE, rotation, BlockPos.ZERO);
	}

	/** Transforms a hub-relative point into world coordinates around {@code center}. */
	public static BlockPos toWorldPos(BlockPos center, int hx, int hy, int hz, Rotation rotation) {
		return center.offset(transformHubOffset(hx, hy, hz, rotation));
	}

	/** Computes the world-space placement origin to pass to {@code StructureTemplate.placeInWorld} with pivot ZERO. */
	public BlockPos pieceOriginWorld(BlockPos center, PieceSpec piece, Rotation rotation) {
		return toWorldPos(center, piece.offset()[0], piece.offset()[1], piece.offset()[2], rotation);
	}

	/** Computes the inclusive world-space bounding box of one rotated piece. */
	public BoundingBox pieceBoundingBoxWorld(BlockPos center, PieceSpec piece, Rotation rotation) {
		int ox = piece.offset()[0];
		int oy = piece.offset()[1];
		int oz = piece.offset()[2];
		int sx = piece.size()[0];
		int sy = piece.size()[1];
		int sz = piece.size()[2];
		BlockPos cornerMin = toWorldPos(center, ox, oy, oz, rotation);
		BlockPos cornerMax = toWorldPos(center, ox + sx - 1, oy + sy - 1, oz + sz - 1, rotation);
		return BoundingBox.fromCorners(cornerMin, cornerMax);
	}

	/** Computes the inclusive world-space bounding box of the full ~191x65x191 rotated hub envelope. */
	public BoundingBox envelopeBoundingBoxWorld(BlockPos center, Rotation rotation) {
		BlockPos pMin = toWorldPos(center, envelopeMin[0], envelopeMin[1], envelopeMin[2], rotation);
		BlockPos pMax = toWorldPos(center, envelopeMax[0], envelopeMax[1], envelopeMax[2], rotation);
		return BoundingBox.fromCorners(pMin, pMax);
	}

	/** Computes the rotated arrival block position atop the central 13x13 arrival pad. */
	public BlockPos arrivalWorldPos(BlockPos center, Rotation rotation) {
		return toWorldPos(center, arrivalLocalPos[0], arrivalLocalPos[1], arrivalLocalPos[2], rotation);
	}

	/** Computes the exact facing yaw so arriving players face the welcome gateway plinths. */
	public float arrivalYaw(Rotation rotation) {
		// Base Sanctuary layout faces North (180 deg) toward welcome pedestals and Expedition Gate.
		return rotation.rotate(Direction.NORTH).toYRot();
	}

	/**
	 * Splits large bounding boxes into vertical Y-bands so multi-tick placement stays bounded
	 * well under server tick budget while keeping horizontal walls/floors intact per band.
	 */
	public static List<BoundingBox> sliceVerticalBands(BoundingBox box, int maxBandHeight) {
		List<BoundingBox> bands = new ArrayList<>();
		int step = Math.max(1, maxBandHeight);
		for (int y = box.minY(); y <= box.maxY(); y += step) {
			int yEnd = Math.min(box.maxY(), y + step - 1);
			bands.add(new BoundingBox(box.minX(), y, box.minZ(), box.maxX(), yEnd, box.maxZ()));
		}
		return bands;
	}
}
