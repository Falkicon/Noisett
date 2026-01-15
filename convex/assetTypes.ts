import { v } from "convex/values";
import { internalMutation, internalQuery } from "./_generated/server";

// Default Asset Types configuration (matching src/core/types.py ASSET_TYPE_CONFIGS)
const DEFAULT_ASSET_TYPES = [
  {
    name: "Icons (Fluent 2)",
    description: "Minimal vector-style icons for UI",
    prePrompt: "",
    postPrompt: "Fluent 2 design icon, minimal vector style, simple shapes, clean lines, professional UI icon",
    model: "replicate:flux-dev-lora",
    modelSettings: {
      num_inference_steps: 28,
      guidance_scale: 3.5,
      aspect_ratio: "1:1",
    },
    qualityPreset: "standard",
    isActive: true,
  },
  {
    name: "Product Illustrations",
    description: "Clean illustrations for product pages and documentation",
    prePrompt: "",
    postPrompt: "product illustration style, clean modern design, soft gradients, professional, brand-aligned",
    model: "replicate:flux-dev-lora",
    modelSettings: {
      num_inference_steps: 28,
      guidance_scale: 3.5,
      aspect_ratio: "1:1",
    },
    qualityPreset: "standard",
    isActive: true,
  },
  {
    name: "Logo Illustrations",
    description: "Simple iconic illustrations for branding",
    prePrompt: "",
    postPrompt: "simple iconic illustration, minimal design, memorable, scalable, brand-friendly",
    model: "replicate:flux-dev-lora",
    modelSettings: {
      num_inference_steps: 28,
      guidance_scale: 3.5,
      aspect_ratio: "1:1",
    },
    qualityPreset: "standard",
    isActive: true,
  },
  {
    name: "Premium Illustrations",
    description: "Rich marketing-grade illustrations",
    prePrompt: "",
    postPrompt: "premium editorial illustration, high quality, detailed, professional marketing art, rich colors",
    model: "replicate:flux-dev-lora",
    modelSettings: {
      num_inference_steps: 28,
      guidance_scale: 3.5,
      aspect_ratio: "1:1",
    },
    qualityPreset: "high",
    isActive: true,
  },
];

// Seed default Asset Types if none exist (idempotent)
export const seed = internalMutation({
  args: {},
  handler: async (ctx) => {
    // Check if any Asset Types already exist
    const existing = await ctx.db.query("assetTypes").first();
    if (existing) {
      return { seeded: false, message: "Asset Types already exist", count: 0 };
    }

    // Create default Asset Types
    const createdIds: string[] = [];
    const now = Date.now();

    for (const assetType of DEFAULT_ASSET_TYPES) {
      const id = await ctx.db.insert("assetTypes", {
        ...assetType,
        createdAt: now,
      });
      createdIds.push(id);
    }

    return {
      seeded: true,
      message: `Created ${createdIds.length} default Asset Types`,
      count: createdIds.length,
      ids: createdIds,
    };
  },
});

// Check if seeding is needed (read-only check)
export const needsSeed = internalQuery({
  args: {},
  handler: async (ctx) => {
    const existing = await ctx.db.query("assetTypes").first();
    return { needsSeed: !existing };
  },
});

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