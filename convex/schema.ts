import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  loras: defineTable({
    name: v.string(),
    triggerWord: v.string(),
    description: v.optional(v.string()),
    baseModel: v.union(v.literal("flux"), v.literal("sdxl")),  // Removed sd35 for Python consistency
    status: v.union(
      v.literal("created"),
      v.literal("uploading"),
      v.literal("ready_to_train"),
      v.literal("training"),
      v.literal("completed"),
      v.literal("deployment_pending"),   // Added for deployment status
      v.literal("deployment_failed"),    // Added for deployment status
      v.literal("failed"),
      v.literal("deployed")
    ),
    steps: v.number(),
    progress: v.optional(v.number()),
    currentStep: v.optional(v.number()),
    replicateTrainingId: v.optional(v.string()),
    fireworksModelId: v.optional(v.string()),
    loraUrl: v.optional(v.string()),
    isActive: v.boolean(),
    createdAt: v.number(),
    trainStartedAt: v.optional(v.number()),
    completedAt: v.optional(v.number()),
    userId: v.optional(v.string()),
    // Error tracking fields
    errorMessage: v.optional(v.string()),
    errorCode: v.optional(v.string()),
  })
    .index("by_user", ["userId"])
    .index("by_status", ["status"])
    .index("by_trigger_word", ["triggerWord"]),

  trainingImages: defineTable({
    loraId: v.id("loras"),
    storageId: v.id("_storage"),
    filename: v.string(),
    caption: v.optional(v.string()),
    sizeBytes: v.number(),
    width: v.optional(v.number()),
    height: v.optional(v.number()),
    uploadedAt: v.number(),
  })
    .index("by_lora", ["loraId"]),

  // Webhook idempotency tracking
  webhookEvents: defineTable({
    eventId: v.string(),  // Replicate webhook ID
    processedAt: v.number(),
    eventType: v.string(),
  })
    .index("by_event_id", ["eventId"]),

  // Director Mode tables
  assetTypes: defineTable({
    name: v.string(),
    slug: v.optional(v.string()),         // Backend API identifier (e.g., "icons", "product") - optional for migration
    description: v.optional(v.string()),
    prePrompt: v.string(),
    postPrompt: v.string(),
    model: v.string(),                    // "replicate:flux-dev-lora"
    modelSettings: v.any(),               // Model-specific params
    loraId: v.optional(v.union(v.id("loras"), v.null())),  // null clears the field
    referenceImages: v.optional(v.array(v.id("_storage"))),  // Reference images for models that support them
    qualityPreset: v.optional(v.string()),
    isActive: v.boolean(),
    createdAt: v.number(),
  }).index("by_active", ["isActive"])
    .index("by_slug", ["slug"]),

  generations: defineTable({
    assetTypeId: v.id("assetTypes"),
    userPrompt: v.string(),
    combinedPrompt: v.string(),
    images: v.array(v.object({
      url: v.string(),
      storageId: v.optional(v.id("_storage")),  // Permanent Convex storage
      width: v.number(),
      height: v.number(),
      seed: v.optional(v.number()),
    })),
    isFavorite: v.boolean(),
    createdAt: v.number(),
  }).index("by_favorite", ["isFavorite"])
    .index("by_created", ["createdAt"]),
});