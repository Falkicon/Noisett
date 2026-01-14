import { v } from "convex/values";
import { internalMutation, internalQuery } from "./_generated/server";

// Create a new webhook event record
export const create = internalMutation({
  args: {
    eventId: v.string(),
    processedAt: v.number(),
    eventType: v.string(),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("webhookEvents", args);
  },
});

// Get webhook event by event ID
export const byEventId = internalQuery({
  args: { eventId: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("webhookEvents")
      .withIndex("by_event_id", (q) => q.eq("eventId", args.eventId))
      .first();
  },
});