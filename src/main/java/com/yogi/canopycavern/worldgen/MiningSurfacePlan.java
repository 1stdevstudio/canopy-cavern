package com.yogi.canopycavern.worldgen;

import java.util.ArrayList;
import java.util.List;

/** Placement and support footprint for the unrotated surface template. */
final class MiningSurfacePlan {
    static final int WIDTH = 89;
    static final int DEPTH = 33;
    static final int SUPPORT_DEPTH = 16;

    record Column(int x, int z) {}

    private MiningSurfacePlan() {}

    static Column origin(MiningShaftPlan.Landing top) {
        return new Column(12, top.z() - 12);
    }

    static List<Column> terrainProbes(MiningShaftPlan.Landing top) {
        Column origin = origin(top);
        List<Column> probes = new ArrayList<>();
        for (int dx = 0; ; dx = Math.min(dx + 8, WIDTH - 1)) {
            for (int dz = 0; ; dz = Math.min(dz + 8, DEPTH - 1)) {
                probes.add(new Column(origin.x() + dx, origin.z() + dz));
                if (dz == DEPTH - 1) break;
            }
            if (dx == WIDTH - 1) break;
        }
        probes.add(new Column(8, top.z()));
        probes.add(new Column(0, 0));
        probes.add(new Column(0, 9));
        probes.add(new Column(8, 0));
        probes.add(new Column(8, 9));
        return probes;
    }

    static boolean hasFoundation(int x, int z) {
        // Ground-level platforms in generate_mining_city_levels.surface().
        return (inside(x, 0, 28) && inside(z, 0, 24))
            || (inside(x, 29, 88) && inside(z, 7, 16))
            || (inside(x, 31, 47) && inside(z, 17, 28))
            || (inside(x, 50, 64) && inside(z, 17, 26))
            || (inside(x, 68, 87) && inside(z, 17, 31));
    }

    private static boolean inside(int value, int min, int max) {
        return value >= min && value <= max;
    }
}
