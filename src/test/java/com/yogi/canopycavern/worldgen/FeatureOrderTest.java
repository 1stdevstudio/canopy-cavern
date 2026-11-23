package com.yogi.canopycavern.worldgen;

import com.google.gson.JsonArray;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileSystem;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.fail;

/**
 * Minecraft refuses to load a world ("Feature order cycle found") when two biomes list the same
 * features in a different relative order. Check mod biomes together with every vanilla biome.
 */
class FeatureOrderTest {
	@Test
	void modBiomesKeepVanillaFeatureOrder() throws Exception {
		Map<String, Set<String>> edges = new HashMap<>();
		var vanillaUrl = getClass().getResource("/data/minecraft/worldgen/biome/plains.json");
		assertNotNull(vanillaUrl, "vanilla biome data on test classpath");
		URI uri = vanillaUrl.toURI();
		FileSystem jarFs = null;
		Path vanillaDir;
		if ("jar".equals(uri.getScheme())) {
			jarFs = FileSystems.newFileSystem(uri, Map.of());
			vanillaDir = jarFs.getPath("/data/minecraft/worldgen/biome");
		} else {
			vanillaDir = Path.of(uri).getParent();
		}
		try {
			for (Path dir : List.of(vanillaDir, Path.of("src/main/resources/data/canopycavern/worldgen/biome"))) {
				try (var files = Files.list(dir)) {
					for (Path file : files.filter(p -> p.toString().endsWith(".json")).toList()) {
						JsonArray steps = JsonParser.parseString(Files.readString(file, StandardCharsets.UTF_8))
							.getAsJsonObject().getAsJsonArray("features");
						String prev = null;
						for (int i = 0; i < steps.size(); i++) {
							for (var feature : steps.get(i).getAsJsonArray()) {
								String node = i + ":" + feature.getAsString();
								if (prev != null) edges.computeIfAbsent(prev, k -> new HashSet<>()).add(node);
								prev = node;
							}
						}
					}
				}
			}
		} finally {
			if (jarFs != null) jarFs.close();
		}
		Map<String, Integer> state = new HashMap<>();
		Deque<String> path = new ArrayDeque<>();
		for (String start : edges.keySet()) {
			if (!state.containsKey(start)) visit(start, edges, state, path);
		}
	}

	private static void visit(String node, Map<String, Set<String>> edges, Map<String, Integer> state, Deque<String> path) {
		state.put(node, 1);
		path.push(node);
		for (String next : edges.getOrDefault(node, Set.of())) {
			Integer s = state.get(next);
			if (s != null && s == 1) fail("Feature order cycle through " + next + " (path " + path + ")");
			if (s == null) visit(next, edges, state, path);
		}
		path.pop();
		state.put(node, 2);
	}
}
