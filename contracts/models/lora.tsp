/**
 * LoRA - Low-Rank Adaptation model for styled generation
 */
import "./common.tsp";

namespace Noisett.Models;

@doc("LoRA training and deployment status")
enum LoraStatus {
  @doc("Just created, no images uploaded")
  created,
  
  @doc("Uploading training images to storage")
  uploading,
  
  @doc("Images uploaded, ready to start training")
  ready_to_train,
  
  @doc("Training in progress on Replicate")
  training,
  
  @doc("Training completed successfully")
  completed,
  
  @doc("Deployment to Fireworks pending")
  deployment_pending,
  
  @doc("Deployment to Fireworks failed")
  deployment_failed,
  
  @doc("Training failed")
  failed,
  
  @doc("Deployed and ready for inference")
  deployed,
}

@doc("LoRA model for styled image generation")
model Lora {
  @doc("Convex document ID")
  _id: ConvexId;
  
  @doc("Display name")
  name: string;
  
  @doc("Word to include in prompts to activate this style")
  triggerWord: string;
  
  @doc("Base model: flux or sdxl")
  baseModel: string;
  
  @doc("Number of training steps")
  steps: int32;
  
  @doc("Current status")
  status: LoraStatus;
  
  @doc("Whether available for generation. Must be true to use.")
  isActive?: boolean;
  
  @doc("Replicate training job ID")
  replicateTrainingId?: string;
  
  @doc("URL to trained weights (after training completes)")
  loraUrl?: string;
  
  @doc("Fireworks model ID (after deployment)")
  fireworksModelId?: string;
  
  @doc("Training progress 0-100")
  progress?: float32;
  
  @doc("Current training step")
  currentStep?: int32;
  
  @doc("Timestamp when training started")
  trainStartedAt?: Timestamp;
  
  @doc("Timestamp when training completed")
  completedAt?: Timestamp;
  
  @doc("Error message if failed")
  errorMessage?: string;
  
  @doc("Error code if failed")
  errorCode?: string;
  
  @doc("Description/notes")
  description?: string;
}

@doc("Request to create a new LoRA")
model LoraCreateRequest {
  name: string;
  triggerWord: string;
  baseModel?: string;
  steps?: int32;
}

@doc("Request to update a LoRA")
model LoraUpdateRequest {
  id: ConvexId;
  status?: LoraStatus;
  isActive?: boolean;
  loraUrl?: string;
  fireworksModelId?: string;
  progress?: float32;
  currentStep?: int32;
  trainStartedAt?: Timestamp;
  completedAt?: Timestamp;
  errorMessage?: string;
  errorCode?: string;
  description?: string;
  name?: string;
  replicateTrainingId?: string;
}

@doc("Response from sync endpoint")
model LoraSyncResponse {
  lora_id: ConvexId;
  replicate_status: string;
  new_status: LoraStatus;
  lora_url?: string;
}
