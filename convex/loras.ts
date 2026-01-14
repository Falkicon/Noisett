import { v } from "convex/values";
import { internalMutation, internalQuery } from "./_generated/server";

// Create a new LoRA
export const create = internalMutation({
  args: {
    name: v.string(),
    triggerWord: v.string(),
    description: v.optional(v.string()),
    baseModel: v.union(v.literal("flux"), v.literal("sdxl")),
    status: v.union(
      v.literal("created"),
      v.literal("uploading"),
      v.literal("ready_to_train"),
      v.literal("training"),
      v.literal("completed"),
      v.literal("deployment_pending"),
      v.literal("deployment_failed"),
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
    errorMessage: v.optional(v.string()),
    errorCode: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("loras", args);
  },
});

// Get a LoRA by ID
export const get = internalQuery({
  args: { id: v.id("loras") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

// List LoRAs with optional filters
export const list = internalQuery({
  args: {
    userId: v.optional(v.string()),
    status: v.optional(v.string()),
    baseModel: v.optional(v.string()),
    activeOnly: v.boolean(),
  },
  handler: async (ctx, args) => {
    let query = ctx.db.query("loras");

    if (args.userId) {
      query = query.withIndex("by_user", (q) => q.eq("userId", args.userId));
    } else if (args.status) {
      query = query.withIndex("by_status", (q) => q.eq("status", args.status));
    }

    const results = await query.collect();

    return results.filter((lora) => {
      if (args.baseModel && lora.baseModel !== args.baseModel) return false;
      if (args.activeOnly && !lora.isActive) return false;
      return true;
    });
  },
});

// Update a LoRA
export const update = internalMutation({
  args: {
    id: v.id("loras"),
    name: v.optional(v.string()),
    description: v.optional(v.string()),
    status: v.optional(v.union(
      v.literal("created"),
      v.literal("uploading"),
      v.literal("ready_to_train"),
      v.literal("training"),
      v.literal("completed"),
      v.literal("deployment_pending"),
      v.literal("deployment_failed"),
      v.literal("failed"),
      v.literal("deployed")
    )),
    progress: v.optional(v.number()),
    currentStep: v.optional(v.number()),
    replicateTrainingId: v.optional(v.string()),
    fireworksModelId: v.optional(v.string()),
    loraUrl: v.optional(v.string()),
    isActive: v.optional(v.boolean()),
    trainStartedAt: v.optional(v.number()),
    completedAt: v.optional(v.number()),
    errorMessage: v.optional(v.string()),
    errorCode: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const { id, ...updates } = args;
    const filteredUpdates = Object.fromEntries(
      Object.entries(updates).filter(([_, value]) => value !== undefined)
    );
    await ctx.db.patch(id, filteredUpdates);
  },
});

// Delete a LoRA by ID
export const deleteById = internalMutation({
  args: { id: v.id("loras") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});

// Get LoRA by Replicate training ID
export const byReplicateId = internalQuery({
  args: { replicateTrainingId: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("loras")
      .filter((q) => q.eq(q.field("replicateTrainingId"), args.replicateTrainingId))
      .first();
  },
});

// Get LoRA by trigger word
export const byTriggerWord = internalQuery({
  args: { triggerWord: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("loras")
      .withIndex("by_trigger_word", (q) => q.eq("triggerWord", args.triggerWord))
      .first();
  },
});