/**
 * Noisett Figma Plugin - Type Definitions
 *
 * Shared types for plugin code and UI.
 */

// =============================================================================
// API Types (match backend)
// =============================================================================

export type AssetType = "icons" | "product" | "logo" | "premium";

export type JobStatus =
  | "queued"
  | "processing"
  | "complete"
  | "failed"
  | "cancelled";

export interface GenerateRequest {
  prompt: string;
  asset_type: AssetType;
  count?: number;
  quality?: "draft" | "standard" | "high";
}

export interface GenerateResponse {
  success: boolean;
  data?: {
    job_id: string;
    prompt: string;
    asset_type: AssetType;
    count: number;
  };
  error?: {
    code: string;
    message: string;
    suggestion?: string;
  };
  reasoning?: string;
}

export interface JobStatusResponse {
  success: boolean;
  data?: {
    job_id: string;
    status: JobStatus;
    images?: string[];
    progress?: number;
    error_message?: string;
  };
  error?: {
    code: string;
    message: string;
  };
}

// =============================================================================
// Plugin Types
// =============================================================================

export interface PluginSettings {
  api_key: string;
  default_asset_type: AssetType;
  default_count: number;
  backend_url: string;
}

export const DEFAULT_SETTINGS: PluginSettings = {
  api_key: "",
  default_asset_type: "icons",
  default_count: 4,
  backend_url:
    "https://noisett.thankfulplant-c547bdac.eastus.azurecontainerapps.io",
};

// =============================================================================
// Plugin Messages (UI ↔ Code communication)
// =============================================================================

export type MessageToCode =
  | { type: "generate"; payload: GenerateRequest }
  | { type: "insert-image"; payload: { url: string; name: string } }
  | { type: "get-settings" }
  | { type: "save-settings"; payload: Partial<PluginSettings> }
  | { type: "close" };

export type MessageToUI =
  | { type: "settings"; payload: PluginSettings }
  | { type: "generation-started"; payload: { job_id: string } }
  | {
      type: "generation-progress";
      payload: { progress: number; status: JobStatus };
    }
  | { type: "generation-complete"; payload: { images: string[] } }
  | { type: "generation-error"; payload: { code: string; message: string } }
  | { type: "image-inserted"; payload: { name: string } }
  | { type: "error"; payload: { message: string } };
