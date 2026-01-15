"""Manual script to sync LoRA status from Replicate training."""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load env
load_dotenv('.env.local')

# Must have API token
if not os.getenv("REPLICATE_API_TOKEN"):
    print("ERROR: Set REPLICATE_API_TOKEN environment variable")
    sys.exit(1)

import replicate
from src.core.convex_client import get_convex_client

async def sync_training(training_id: str):
    """Fetch training from Replicate and update LoRA in Convex."""
    print(f"Fetching training {training_id} from Replicate...")
    
    training = await replicate.trainings.async_get(training_id)
    print(f"Status: {training.status}")
    print(f"Output: {training.output}")
    
    if training.status != "succeeded":
        print(f"Training not succeeded yet: {training.status}")
        return
    
    # Get weights URL
    weights_url = training.output.get("weights") if training.output else None
    if not weights_url:
        print("ERROR: No weights URL in training output")
        return
    
    print(f"Weights URL: {weights_url}")
    
    # Find LoRA in Convex
    convex = get_convex_client()
    lora = await convex.get_lora_by_replicate_id(training_id)
    
    if not lora:
        print(f"ERROR: No LoRA found with replicateTrainingId={training_id}")
        return
    
    lora_id = lora["_id"]
    print(f"Found LoRA: {lora['name']} (ID: {lora_id})")
    print(f"Current status: {lora['status']}")
    
    # Update LoRA
    import time
    await convex.update_lora(lora_id, {
        "status": "completed",
        "loraUrl": weights_url,
        "completedAt": int(time.time() * 1000),
        "progress": 100,
        "currentStep": lora.get("steps", 1000),
    })
    
    print(f"✅ Updated LoRA to completed with loraUrl!")
    print(f"   The LoRA should now appear in the dropdown on the Generate tab.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python sync_training.py <training_id>")
        sys.exit(1)
    
    asyncio.run(sync_training(sys.argv[1]))
