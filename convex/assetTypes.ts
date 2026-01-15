import { v } from "convex/values";
import { internalMutation, internalQuery } from "./_generated/server";

// Create a new Asset Type
export const create = internalMutation({
  args: {
    name: v.string(),
    description: v.optional(v.string()),
    prePrompt: v.string(),
    postPrompt: v.string(),
    model: v.string(),                    // "replicate:flux-dev-lora"
    modelSettings: v.any(),               // Model-specific params
    loraId: v.optional(v.id("loras")),
    qualityPreset: v.optional(v.string()),
    isActive: v.boolean(),
    createdAt: v.number(),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("assetTypes", args);
  },
});

// Get an Asset Type by ID
export const get = internalQuery({
  args: { id: v.id("assetTypes") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

// List Asset Types with optional filters
export const list = internalQuery({
  args: {
    activeOnly: v.optional(v.boolean()),
  },
  handler: async (ctx, args) => {
    let query = ctx.db.query("assetTypes");

    // Use the by_active index when filtering by activeOnly
    if (args.activeOnly !== undefined) {
      query = query.withIndex("by_active", (q) => q.eq("isActive", args.activeOnly));
    }

    const results = await query.collect();

    // Sort by createdAt descending (newest first)
    return results.sort((a, b) => b.createdAt - a.createdAt);
  },
});

// Update an Asset Type
export const update = internalMutation({
  args: {
    id: v.id("assetTypes"),
    name: v.optional(v.string()),
    description: v.optional(v.string()),
    prePrompt: v.optional(v.string()),
    postPrompt: v.optional(v.string()),
    model: v.optional(v.string()),
    modelSettings: v.optional(v.any()),
    loraId: v.optional(v.id("loras")),
    qualityPreset: v.optional(v.string()),
    isActive: v.optional(v.boolean()),
  },
  handler: async (ctx, args) => {
    const { id, ...updates } = args;
    const filteredUpdates = Object.fromEntries(
      Object.entries(updates).filter(([_, value]) => value !== undefined)
    );
    await ctx.db.patch(id, filteredUpdates);
  },
});

// Soft delete an Asset Type by setting isActive to false
export const deleteById = internalMutation({
  args: { id: v.id("assetTypes") },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, { isActive: false });
  },
});