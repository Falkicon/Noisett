import { v } from "convex/values";
import { internalMutation, internalQuery } from "./_generated/server";

// Default Asset Types configuration (matching src/core/types.py ASSET_TYPE_CONFIGS)
const DEFAULT_ASSET_TYPES = [
  {
    name: "Icons (Fluent 2)",
    slug: "icons",  // Backend API identifier
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
    slug: "product",  // Backend API identifier
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
    slug: "logo",  // Backend API identifier
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
    slug: "premium",  // Backend API identifier
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
    slug: v.optional(v.string()),         // Backend API identifier (optional for backwards compat)
    description: v.optional(v.string()),
    prePrompt: v.string(),
    postPrompt: v.string(),
    hiddenPrompt: v.optional(v.string()), // Appended after post-prompt but not shown in preview
    tip: v.optional(v.string()),          // User guidance shown below prompt input
    model: v.string(),                    // "replicate:flux-dev-lora"
    modelSettings: v.any(),               // Model-specific params
    loraId: v.optional(v.union(v.id("loras"), v.null())),  // null means no LoRA
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
    slug: v.optional(v.string()),         // Backend API identifier
    description: v.optional(v.string()),
    prePrompt: v.optional(v.string()),
    postPrompt: v.optional(v.string()),
    hiddenPrompt: v.optional(v.string()), // Appended after post-prompt but not shown in preview
    tip: v.optional(v.string()),          // User guidance shown below prompt input
    model: v.optional(v.string()),
    modelSettings: v.optional(v.any()),
    loraId: v.optional(v.union(v.id("loras"), v.null())),  // null clears the field
    referenceImages: v.optional(v.array(v.id("_storage"))),
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

// Add a reference image to an Asset Type
export const addReferenceImage = internalMutation({
  args: {
    id: v.id("assetTypes"),
    storageId: v.id("_storage"),
  },
  handler: async (ctx, args) => {
    const assetType = await ctx.db.get(args.id);
    if (!assetType) throw new Error("Asset type not found");

    const currentImages = assetType.referenceImages ?? [];
    // Prevent duplicates
    if (currentImages.includes(args.storageId)) {
      return { added: false, message: "Image already exists" };
    }

    await ctx.db.patch(args.id, {
      referenceImages: [...currentImages, args.storageId],
    });
    return { added: true, count: currentImages.length + 1 };
  },
});

// Remove a reference image from an Asset Type
export const removeReferenceImage = internalMutation({
  args: {
    id: v.id("assetTypes"),
    storageId: v.id("_storage"),
  },
  handler: async (ctx, args) => {
    const assetType = await ctx.db.get(args.id);
    if (!assetType) throw new Error("Asset type not found");

    const currentImages = assetType.referenceImages ?? [];
    const filteredImages = currentImages.filter((id) => id !== args.storageId);

    // Also delete the file from storage
    await ctx.storage.delete(args.storageId);

    await ctx.db.patch(args.id, {
      referenceImages: filteredImages,
    });
    return { removed: true, count: filteredImages.length };
  },
});

// Reorder reference images for an Asset Type
export const reorderReferenceImages = internalMutation({
  args: {
    id: v.id("assetTypes"),
    storageIds: v.array(v.id("_storage")),
  },
  handler: async (ctx, args) => {
    const assetType = await ctx.db.get(args.id);
    if (!assetType) throw new Error("Asset type not found");

    await ctx.db.patch(args.id, {
      referenceImages: args.storageIds,
    });
    return { reordered: true, count: args.storageIds.length };
  },
});

// Delete an Asset Type permanently
export const deleteById = internalMutation({
  args: { id: v.id("assetTypes") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});

// Migration: Add slugs to existing asset types without them
const NAME_TO_SLUG_MAP: Record<string, string> = {
  "Icons (Fluent 2)": "icons",
  "Product Illustrations": "product",
  "Logo Illustrations": "logo",
  "Premium Illustrations": "premium",
};

export const migrateSlugs = internalMutation({
  args: {},
  handler: async (ctx) => {
    const assetTypes = await ctx.db.query("assetTypes").collect();
    let updated = 0;

    for (const assetType of assetTypes) {
      // Skip if already has a slug
      if ((assetType as any).slug) continue;

      const slug = NAME_TO_SLUG_MAP[assetType.name];
      if (slug) {
        await ctx.db.patch(assetType._id, { slug });
        updated++;
      }
    }

    return {
      message: `Migrated ${updated} asset types with slugs`,
      updated,
    };
  },
});