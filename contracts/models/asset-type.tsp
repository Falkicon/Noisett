/**
 * Asset Type - Configuration for image generation presets
 * 
 * This is the contract that broke before due to loraId: null not being accepted.
 * Now explicitly defined as `string | null` to prevent future issues.
 */
import "./common.tsp";

namespace Noisett.Models;

@doc("Asset type configuration for image generation presets")
model AssetType {
  @doc("Convex document ID")
  _id: ConvexId;
  
  @doc("Display name shown in UI")
  name: string;
  
  @doc("Backend API identifier (e.g., 'icons', 'product')")
  slug?: string;
  
  @doc("Human-readable description")
  description?: string;
  
  @doc("Text prepended to user prompt")
  prePrompt: string;
  
  @doc("Text appended to user prompt")
  postPrompt: string;
  
  @doc("Model identifier (e.g., 'replicate:flux-2-max')")
  `model`: string;
  
  @doc("Model-specific settings (varies by model)")
  modelSettings: Record<unknown>;
  
  @doc("Optional LoRA ID for styled generation. NULL means no LoRA.")
  loraId?: ConvexId | null;
  
  @doc("Optional reference images for style guidance")
  referenceImages?: StorageId[];
  
  @doc("Quality preset: draft, standard, or high")
  qualityPreset?: string;
  
  @doc("Whether visible to users in the UI")
  isActive: boolean;
  
  @doc("Creation timestamp")
  createdAt: Timestamp;
}

@doc("Request to create a new asset type")
model AssetTypeCreateRequest {
  name: string;
  slug?: string;
  description?: string;
  prePrompt: string;
  postPrompt: string;
  `model`: string;
  modelSettings: Record<unknown>;
  
  @doc("LoRA ID or null for no LoRA. Both null and undefined are valid.")
  loraId?: ConvexId | null;
  
  qualityPreset?: string;
  isActive: boolean;
  createdAt: Timestamp;
}

@doc("Request to update an existing asset type")
model AssetTypeUpdateRequest {
  @doc("Asset type ID to update")
  id: ConvexId;
  
  name?: string;
  slug?: string;
  description?: string;
  prePrompt?: string;
  postPrompt?: string;
  `model`?: string;
  modelSettings?: Record<unknown>;
  
  @doc("LoRA ID, null to clear, or undefined to leave unchanged")
  loraId?: ConvexId | null;
  
  referenceImages?: StorageId[];
  qualityPreset?: string;
  isActive?: boolean;
}
