import { v } from "convex/values";
import { internalMutation, internalQuery } from "./_generated/server";

// Create a new generation
export const create = internalMutation({
  args: {
    assetTypeId: v.id("assetTypes"),
    userPrompt: v.string(),
    combinedPrompt: v.string(),
    images: v.array(v.object({
      url: v.string(),
      width: v.number(),
      height: v.number(),
      seed: v.optional(v.number()),
    })),
    isFavorite: v.boolean(),
    createdAt: v.number(),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("generations", args);
  },
});

// List generations with optional favorite filter
export const list = internalQuery({
  args: {
    favorite: v.optional(v.boolean()),
  },
  handler: async (ctx, args) => {
    let query = ctx.db.query("generations");

    if (args.favorite !== undefined) {
      query = query.withIndex("by_favorite", (q) => q.eq("isFavorite", args.favorite));
    }

    // Order by creation date, newest first
    return await query
      .order("desc")
      .collect();
  },
});

// Get a generation by ID
export const get = internalQuery({
  args: { id: v.id("generations") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

// Toggle favorite status
export const toggleFavorite = internalMutation({
  args: {
    id: v.id("generations"),
  },
  handler: async (ctx, args) => {
    const generation = await ctx.db.get(args.id);
    if (!generation) {
      throw new Error("Generation not found");
    }

    await ctx.db.patch(args.id, {
      isFavorite: !generation.isFavorite
    });

    return { isFavorite: !generation.isFavorite };
  },
});

// Delete a generation by ID (hard delete)
export const deleteById = internalMutation({
  args: { id: v.id("generations") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});