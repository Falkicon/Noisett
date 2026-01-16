/**
 * Generation - Image generation request/response
 */
import "./common.tsp";
import "./job.tsp";

namespace Noisett.Models;

@doc("Request to generate images")
model GenerateRequest {
  @doc("Text description of the image to generate")
  @minLength(1)
  @maxLength(500)
  prompt: string;
  
  @doc("Type of asset to generate")
  asset_type?: string;
  
  @doc("Model ID (e.g., 'hidream', 'replicate:flux-2-max')")
  `model`?: string;
  
  @doc("Quality preset")
  quality?: QualityPreset;
  
  @doc("Number of variations (1-4)")
  @minValue(1)
  @maxValue(4)
  imageCount?: int32;
  
  @doc("LoRA ID for styled generation")
  lora?: ConvexId;
  
  @doc("Asset Type ID for reference images")
  asset_type_id?: ConvexId;
}

@doc("Response from generation endpoint")
model GenerateResponse {
  @doc("Created job")
  job: Job;
  
  @doc("Estimated seconds until completion")
  estimated_seconds: int32;
}
