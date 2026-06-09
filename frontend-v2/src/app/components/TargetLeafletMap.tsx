import L from "leaflet";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";
import { useEffect, useMemo } from "react";

interface TargetPoint {
  lat: number;
  lon: number;
}

interface TargetLeafletMapProps {
  externalTilesEnabled: boolean;
  tileUrlTemplate: string;
  target: TargetPoint | null;
  onTargetChange: (target: TargetPoint) => void;
}

const DEFAULT_CENTER: [number, number] = [0, 0];
const DEFAULT_ZOOM = 13;

export function TargetLeafletMap({ externalTilesEnabled, tileUrlTemplate, target, onTargetChange }: TargetLeafletMapProps) {
  const tileTemplateValid = tileUrlTemplate.includes("{z}") && tileUrlTemplate.includes("{x}") && tileUrlTemplate.includes("{y}");
  const center: [number, number] = target ? [target.lat, target.lon] : DEFAULT_CENTER;
  const markerIcon = useMemo(
    () =>
      L.divIcon({
        className: "gs-target-marker",
        html: '<div class="gs-target-marker-pin">⌖</div><div class="gs-target-marker-label">Target</div>',
        iconSize: [48, 54],
        iconAnchor: [24, 48],
      }),
    [],
  );

  if (!externalTilesEnabled) {
    return (
      <MapDisabledMessage
        title="Map disabled"
        detail="Enable External map tiles in Settings to open the large mouse-driven map picker. Manual latitude and longitude entry still works."
      />
    );
  }

  if (!tileTemplateValid) {
    return <MapDisabledMessage title="Map unavailable" detail="Tile URL template must include {z}, {x}, and {y}." />;
  }

  return (
    <div className="rounded overflow-hidden" style={{ height: "620px", border: "1px solid rgba(28,43,94,0.16)" }}>
      <MapContainer
        center={center}
        zoom={DEFAULT_ZOOM}
        scrollWheelZoom
        doubleClickZoom
        dragging
        zoomControl
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer url={tileUrlTemplate} attribution="Map tiles configured by operator" />
        <MapClickHandler onTargetChange={onTargetChange} />
        <MapTargetSync target={target} />
        {target && <Marker position={[target.lat, target.lon]} icon={markerIcon} />}
      </MapContainer>
    </div>
  );
}

function MapClickHandler({ onTargetChange }: { onTargetChange: (target: TargetPoint) => void }) {
  useMapEvents({
    click(event) {
      onTargetChange({ lat: event.latlng.lat, lon: event.latlng.lng });
    },
  });
  return null;
}

function MapTargetSync({ target }: { target: TargetPoint | null }) {
  const map = useMap();
  useEffect(() => {
    if (target) {
      map.setView([target.lat, target.lon], Math.max(map.getZoom(), DEFAULT_ZOOM), { animate: false });
    }
  }, [map, target]);
  return null;
}

function MapDisabledMessage({ title, detail }: { title: string; detail: string }) {
  return (
    <div
      className="rounded flex flex-col items-center justify-center gap-1 px-4 py-6"
      style={{
        minHeight: "420px",
        border: "1px solid rgba(28,43,94,0.16)",
        backgroundColor: "rgba(248,247,242,0.95)",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--gs-navy)" }}>{title}</div>
      <div style={{ fontSize: "11px", color: "var(--gs-slate)", maxWidth: "420px" }}>{detail}</div>
    </div>
  );
}
