export interface ReviewedFileSummary {
  fileName: string;
  featureCount: number;
  anchorCount: number;
  candidateCount: number;
  anchorIds: string[];
  candidateIds: string[];
  minimumAnchorDepthM: number;
  maximumAnchorDepthM: number;
}

type JsonRecord = Record<string, unknown>;

export function inspectOperatorLocalDepthGeojson(value: unknown, fileName: string): ReviewedFileSummary {
  const document = asRecord(value, "The selected file must contain a GeoJSON FeatureCollection.");
  if (document.type !== "FeatureCollection" || !Array.isArray(document.features) || document.features.length === 0) {
    throw new Error("The selected file must contain a non-empty GeoJSON FeatureCollection.");
  }
  if (document.template_only === true) {
    throw new Error("This file is still marked template_only. Replace every placeholder and remove template_only before use.");
  }

  const featureIds = new Set<string>();
  const anchorIds: string[] = [];
  const candidateIds: string[] = [];
  const anchorBestDepths: number[] = [];
  let minimumAnchorDepthM = Number.POSITIVE_INFINITY;
  let maximumAnchorDepthM = Number.NEGATIVE_INFINITY;

  document.features.forEach((rawFeature, index) => {
    const feature = asRecord(rawFeature, `Feature ${index + 1} is not a valid GeoJSON feature.`);
    if (feature.type !== "Feature") {
      throw new Error(`Feature ${index + 1} must have type Feature.`);
    }

    const properties = asRecord(feature.properties, `Feature ${index + 1} must contain properties.`);
    const featureId = requiredText(properties.feature_id, `Feature ${index + 1} must contain a non-empty feature_id.`);
    if (featureId.includes("replace-with")) {
      throw new Error(`Feature ${index + 1} still contains the placeholder feature_id ${featureId}.`);
    }
    if (featureIds.has(featureId)) {
      throw new Error(`Duplicate feature_id: ${featureId}.`);
    }
    featureIds.add(featureId);

    const role = requiredText(properties.role, `Feature ${featureId} must contain role anchor or candidate.`).toLowerCase();
    if (role !== "anchor" && role !== "candidate") {
      throw new Error(`Feature ${featureId} has unsupported role ${role}; use anchor or candidate.`);
    }

    validateGeometry(feature.geometry, featureId);

    if (role === "anchor") {
      const minimum = requiredDepth(properties.depth_min_m, featureId, "depth_min_m");
      const best = requiredDepth(properties.depth_best_m, featureId, "depth_best_m");
      const maximum = requiredDepth(properties.depth_max_m, featureId, "depth_max_m");
      if (!(minimum <= best && best <= maximum)) {
        throw new Error(`Anchor ${featureId} must satisfy depth_min_m <= depth_best_m <= depth_max_m.`);
      }
      anchorIds.push(featureId);
      anchorBestDepths.push(best);
      minimumAnchorDepthM = Math.min(minimumAnchorDepthM, minimum);
      maximumAnchorDepthM = Math.max(maximumAnchorDepthM, maximum);
    } else {
      candidateIds.push(featureId);
    }
  });

  if (anchorIds.length < 2) {
    throw new Error("At least two measured anchor features are required.");
  }
  if (candidateIds.length < 1) {
    throw new Error("At least one candidate feature is required.");
  }
  if (new Set(anchorBestDepths.map((value) => value.toPrecision(15))).size < 2) {
    throw new Error("Measured anchors must include at least two distinct best-depth values.");
  }

  return {
    fileName,
    featureCount: document.features.length,
    anchorCount: anchorIds.length,
    candidateCount: candidateIds.length,
    anchorIds,
    candidateIds,
    minimumAnchorDepthM,
    maximumAnchorDepthM,
  };
}

export function buildOperatorLocalDepthTemplate(): JsonRecord {
  return {
    type: "FeatureCollection",
    template_only: true,
    instructions: [
      "Replace every placeholder feature_id.",
      "Replace every null coordinate with the reviewed polygon coordinates.",
      "Enter measured depth ranges in metres for anchors only.",
      "Remove template_only before uploading the completed file.",
    ],
    features: [
      templateFeature("replace-with-shallow-anchor-id", "anchor", [0.4, 0.5, 0.6]),
      templateFeature("replace-with-deep-anchor-id", "anchor", [1.4, 1.5, 1.6]),
      templateFeature("replace-with-candidate-id", "candidate"),
    ],
  };
}

function templateFeature(featureId: string, role: "anchor" | "candidate", depth?: [number, number, number]): JsonRecord {
  const properties: JsonRecord = { feature_id: featureId, role };
  if (depth) {
    properties.depth_min_m = depth[0];
    properties.depth_best_m = depth[1];
    properties.depth_max_m = depth[2];
  }
  return {
    type: "Feature",
    properties,
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [null, null],
          [null, null],
          [null, null],
          [null, null],
          [null, null],
        ],
      ],
    },
  };
}

function asRecord(value: unknown, message: string): JsonRecord {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(message);
  }
  return value as JsonRecord;
}

function requiredText(value: unknown, message: string): string {
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(message);
  }
  return value.trim();
}

function requiredDepth(value: unknown, featureId: string, fieldName: string): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    throw new Error(`Anchor ${featureId} must contain a finite non-negative ${fieldName} value in metres.`);
  }
  return value;
}

function validateGeometry(value: unknown, featureId: string): void {
  const geometry = asRecord(value, `Feature ${featureId} must contain a Polygon or MultiPolygon geometry.`);
  if (geometry.type === "Polygon") {
    validatePolygonCoordinates(geometry.coordinates, featureId);
    return;
  }
  if (geometry.type === "MultiPolygon") {
    if (!Array.isArray(geometry.coordinates) || geometry.coordinates.length === 0) {
      throw new Error(`Feature ${featureId} contains an empty MultiPolygon.`);
    }
    geometry.coordinates.forEach((polygon, index) => validatePolygonCoordinates(polygon, `${featureId} polygon ${index + 1}`));
    return;
  }
  throw new Error(`Feature ${featureId} must use Polygon or MultiPolygon geometry.`);
}

function validatePolygonCoordinates(value: unknown, featureId: string): void {
  if (!Array.isArray(value) || value.length === 0) {
    throw new Error(`Feature ${featureId} contains an empty Polygon.`);
  }
  value.forEach((ring, ringIndex) => {
    if (!Array.isArray(ring) || ring.length < 4) {
      throw new Error(`Feature ${featureId} ring ${ringIndex + 1} must contain at least four positions.`);
    }
    const positions = ring.map((position, positionIndex) => validatePosition(position, featureId, ringIndex, positionIndex));
    const first = positions[0];
    const last = positions[positions.length - 1];
    if (first[0] !== last[0] || first[1] !== last[1]) {
      throw new Error(`Feature ${featureId} ring ${ringIndex + 1} must be closed.`);
    }
    const unique = new Set(positions.slice(0, -1).map((position) => `${position[0]},${position[1]}`));
    if (unique.size < 3) {
      throw new Error(`Feature ${featureId} ring ${ringIndex + 1} must contain at least three distinct positions.`);
    }
  });
}

function validatePosition(value: unknown, featureId: string, ringIndex: number, positionIndex: number): [number, number] {
  if (!Array.isArray(value) || value.length < 2) {
    throw new Error(`Feature ${featureId} ring ${ringIndex + 1} position ${positionIndex + 1} is invalid.`);
  }
  const x = value[0];
  const y = value[1];
  if (typeof x !== "number" || !Number.isFinite(x) || typeof y !== "number" || !Number.isFinite(y)) {
    throw new Error(`Feature ${featureId} ring ${ringIndex + 1} position ${positionIndex + 1} must contain finite numeric coordinates.`);
  }
  return [x, y];
}
