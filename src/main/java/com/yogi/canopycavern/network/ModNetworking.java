package com.yogi.canopycavern.network;

import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.world.BlueprintBuilderService;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Shared play-phase network payloads for climate HUD telemetry sync, guidebook screen open cues,
 * and server-authoritative auto-shelter blueprint construction.
 */
public final class ModNetworking {

	private ModNetworking() {
	}

	/** Registers payload types on both client/server sides and binds C2S server receivers. */
	public static void register() {
		PayloadTypeRegistry.clientboundPlay().register(ClimateSyncPayload.TYPE, ClimateSyncPayload.CODEC);
		PayloadTypeRegistry.clientboundPlay().register(OpenGuidePayload.TYPE, OpenGuidePayload.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(BuildBlueprintPayload.TYPE, BuildBlueprintPayload.CODEC);

		ServerPlayNetworking.registerGlobalReceiver(BuildBlueprintPayload.TYPE, (payload, context) ->
			context.server().execute(() -> BlueprintBuilderService.handleBuildRequest(context.player(), payload.blueprintId()))
		);
	}

	public record ClimateSyncPayload(
		int humidityPercent,
		String microWeatherId,
		String climateStatusId,
		int thermalInsulationPercent,
		int cavernCoolingPercent,
		double perceivedCelsius,
		boolean frostPenalty,
		boolean heatPenalty,
		boolean warmthRecovery,
		boolean nearCampfire,
		boolean enclosedShelter
	) implements CustomPacketPayload {
		public static final Type<ClimateSyncPayload> TYPE = new Type<>(CanopyCavernMod.id("climate_sync"));

		public static final StreamCodec<RegistryFriendlyByteBuf, ClimateSyncPayload> CODEC = CustomPacketPayload.codec(
			(payload, buf) -> {
				buf.writeVarInt(payload.humidityPercent);
				buf.writeUtf(payload.microWeatherId);
				buf.writeUtf(payload.climateStatusId);
				buf.writeVarInt(payload.thermalInsulationPercent);
				buf.writeVarInt(payload.cavernCoolingPercent);
				buf.writeDouble(payload.perceivedCelsius);
				buf.writeBoolean(payload.frostPenalty);
				buf.writeBoolean(payload.heatPenalty);
				buf.writeBoolean(payload.warmthRecovery);
				buf.writeBoolean(payload.nearCampfire);
				buf.writeBoolean(payload.enclosedShelter);
			},
			buf -> new ClimateSyncPayload(
				buf.readVarInt(),
				buf.readUtf(),
				buf.readUtf(),
				buf.readVarInt(),
				buf.readVarInt(),
				buf.readDouble(),
				buf.readBoolean(),
				buf.readBoolean(),
				buf.readBoolean(),
				buf.readBoolean(),
				buf.readBoolean()
			)
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	public record OpenGuidePayload(boolean starterTip) implements CustomPacketPayload {
		public static final Type<OpenGuidePayload> TYPE = new Type<>(CanopyCavernMod.id("open_guide"));

		public static final StreamCodec<RegistryFriendlyByteBuf, OpenGuidePayload> CODEC = CustomPacketPayload.codec(
			(payload, buf) -> buf.writeBoolean(payload.starterTip),
			buf -> new OpenGuidePayload(buf.readBoolean())
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	public record BuildBlueprintPayload(String blueprintId) implements CustomPacketPayload {
		public static final Type<BuildBlueprintPayload> TYPE = new Type<>(CanopyCavernMod.id("build_blueprint"));

		public static final StreamCodec<RegistryFriendlyByteBuf, BuildBlueprintPayload> CODEC = CustomPacketPayload.codec(
			(payload, buf) -> buf.writeUtf(payload.blueprintId),
			buf -> new BuildBlueprintPayload(buf.readUtf())
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}
}
