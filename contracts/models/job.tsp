/**
 * Job - Image generation job tracking
 */
import "./common.tsp";

namespace Noisett.Models;

@doc("Job processing status")
enum JobStatus {
  @doc("Job created, waiting to be processed")
  queued,
  
  @doc("Job is being processed")
  processing,
  
  @doc("Job completed successfully")
  completed,
  
  @doc("Job failed")
  failed,
  
  @doc("Job was cancelled by user")
  cancelled,
}

@doc("Quality preset affecting speed vs quality tradeoff")
enum QualityPreset {
  @doc("Fastest, lower quality")
  draft,
  
  @doc("Balanced speed and quality")
  standard,
  
  @doc("Highest quality, slower")
  high,
}

@doc("Generated image result")
model GeneratedImage {
  @doc("Unique image ID")
  id: string;
  
  @doc("Public URL to the image")
  url: string;
  
  @doc("Image width in pixels")
  width?: int32;
  
  @doc("Image height in pixels")
  height?: int32;
  
  @doc("MIME type (image/png, image/webp, etc)")
  mime_type?: string;
}

@doc("Image generation job")
model Job {
  @doc("Unique job ID (UUID)")
  id: string;
  
  @doc("Current job status")
  status: JobStatus;
  
  @doc("Original prompt")
  prompt: string;
  
  @doc("Asset type used")
  asset_type: string;
  
  @doc("Model used for generation")
  `model`: string;
  
  @doc("Quality preset used")
  quality: QualityPreset;
  
  @doc("Number of images requested")
  imageCount: int32;
  
  @doc("Progress percentage 0-100")
  progress: int32;
  
  @doc("Generated images (when completed)")
  images: GeneratedImage[];
  
  @doc("Error message if failed")
  error_message?: string;
  
  @doc("LoRA ID if styled generation")
  lora_id?: ConvexId;
  
  @doc("Asset Type ID for reference images")
  asset_type_id?: ConvexId;
  
  @doc("Creation timestamp ISO string")
  created_at: string;
  
  @doc("Completion timestamp ISO string")
  completed_at?: string;
}
