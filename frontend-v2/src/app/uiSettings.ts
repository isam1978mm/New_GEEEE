export interface UiSettings {
  externalTilesEnabled: boolean;
  tileUrlTemplate: string;
  showAdvancedUnavailableOutputs: boolean;
  operatorPrivateOverlayEnabled: boolean;
}

const UI_SETTINGS_STORAGE_KEY = "gs_operator_ui_settings_v1";
const DEFAULT_TILE_URL_TEMPLATE = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";

export function defaultUiSettings(): UiSettings {
  return {
    externalTilesEnabled: false,
    tileUrlTemplate: DEFAULT_TILE_URL_TEMPLATE,
    showAdvancedUnavailableOutputs: false,
    operatorPrivateOverlayEnabled: false,
  };
}

export function loadUiSettings(): UiSettings {
  if (typeof window === "undefined") {
    return defaultUiSettings();
  }
  try {
    const raw = window.localStorage.getItem(UI_SETTINGS_STORAGE_KEY);
    if (!raw) {
      return defaultUiSettings();
    }
    const parsed = JSON.parse(raw) as Partial<UiSettings>;
    return {
      externalTilesEnabled: parsed.externalTilesEnabled === true,
      tileUrlTemplate:
        typeof parsed.tileUrlTemplate === "string" && parsed.tileUrlTemplate.trim().length > 0
          ? parsed.tileUrlTemplate
          : DEFAULT_TILE_URL_TEMPLATE,
      showAdvancedUnavailableOutputs: parsed.showAdvancedUnavailableOutputs === true,
      operatorPrivateOverlayEnabled: parsed.operatorPrivateOverlayEnabled === true,
    };
  } catch (_error) {
    return defaultUiSettings();
  }
}

export function saveUiSettings(uiSettings: UiSettings): void {
  window.localStorage.setItem(UI_SETTINGS_STORAGE_KEY, JSON.stringify(uiSettings));
}
