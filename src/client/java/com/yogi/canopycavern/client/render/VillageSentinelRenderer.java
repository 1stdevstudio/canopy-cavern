package com.yogi.canopycavern.client.render;

import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.entity.VillageSentinelEntity;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.resources.Identifier;

/**
 * Renders Village Sentinels as uniformed watchmen wielding their patrol sword.
 */
public class VillageSentinelRenderer extends HumanoidMobRenderer<VillageSentinelEntity, HumanoidRenderState, HumanoidModel<HumanoidRenderState>> {

	private static final Identifier TEXTURE = CanopyCavernMod.id("textures/entity/village_sentinel.png");

	public VillageSentinelRenderer(EntityRendererProvider.Context context) {
		super(context, new HumanoidModel<>(context.bakeLayer(ModelLayers.PLAYER)), 0.5F);
	}

	@Override
	public HumanoidRenderState createRenderState() {
		return new HumanoidRenderState();
	}

	@Override
	public Identifier getTextureLocation(HumanoidRenderState state) {
		return TEXTURE;
	}
}
