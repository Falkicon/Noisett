import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

/**
 * Convex functions for training images table.
 * Manages metadata for training images stored in Convex file storage.
 */

// Create a training image record
export const create = mutation({
  args: {
    loraId: v.id("loras"),
    storageId: v.id("_storage"),
    filename: v.string(),
    caption: v.optional(v.string()),
    sizeBytes: v.number(),
    width: v.optional(v.number()),
    height: v.optional(v.number()),
    uploadedAt: v.number(),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("trainingImages", args);
  },
});

// List training images for a LoRA
export const listByLora = query({
  args: {
    loraId: v.id("loras"),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("trainingImages")
      .withIndex("by_lora", (q) => q.eq("loraId", args.loraId))
      .collect();
  },
});

// Count training images for a LoRA
export const countByLora = query({
  args: {
    loraId: v.id("loras"),
  },
  handler: async (ctx, args) => {
    const images = await ctx.db
      .query("trainingImages")
      .withIndex("by_lora", (q) => q.eq("loraId", args.loraId))
      .collect();
    return images.length;
  },
});

// Delete a training image
export const deleteById = mutation({
  args: {
    id: v.id("trainingImages"),
  },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});

// Delete all training images for a LoRA
export const deleteByLora = mutation({
  args: {
    loraId: v.id("loras"),
  },
  handler: async (ctx, args) => {
    const images = await ctx.db
      .query("trainingImages")
      .withIndex("by_lora", (q) => q.eq("loraId", args.loraId))
      .collect();

    for (const image of images) {
      await ctx.db.delete(image._id);
      // Note: We don't delete the actual file from storage here
      // as that should be handled separately if needed
    }
  },
});

// Get a single training image by ID
export const get = query({
  args: {
    id: v.id("trainingImages"),
  },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});