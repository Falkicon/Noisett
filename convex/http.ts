import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";
import { internal } from "./_generated/api";

const http = httpRouter();

// Asset Types endpoints

// Seed default Asset Types (idempotent - safe to call multiple times)
http.route({
  path: "/api/asset-types/seed",
  method: "POST",
  handler: httpAction(async (ctx) => {
    const result = await ctx.runMutation(internal.assetTypes.seed, {});
    return new Response(JSON.stringify(result), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

// Check if Asset Types need seeding (read-only)
http.route({
  path: "/api/asset-types/needs-seed",
  method: "GET",
  handler: httpAction(async (ctx) => {
    const result = await ctx.runQuery(internal.assetTypes.needsSeed, {});
    return new Response(JSON.stringify(result), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/asset-types/create",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    const id = await ctx.runMutation(internal.assetTypes.create, body);
    return new Response(JSON.stringify({ id }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/asset-types/list",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const activeOnly = url.searchParams.get("activeOnly");

    const data = await ctx.runQuery(internal.assetTypes.list, {
      activeOnly: activeOnly === "true" ? true : activeOnly === "false" ? false : undefined
    });
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/asset-types/get",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const id = url.searchParams.get("id");
    if (!id) {
      return new Response(JSON.stringify({ error: "id parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
    const data = await ctx.runQuery(internal.assetTypes.get, { id });
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/asset-types/update",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    await ctx.runMutation(internal.assetTypes.update, body);
    return new Response(JSON.stringify({ success: true }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/asset-types/delete",
  method: "DELETE",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const id = url.searchParams.get("id");
    if (!id) {
      return new Response(JSON.stringify({ error: "id parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
    await ctx.runMutation(internal.assetTypes.deleteById, { id });
    return new Response(JSON.stringify({ success: true }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

// LoRA endpoints
http.route({
  path: "/api/loras/create",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    const id = await ctx.runMutation(internal.loras.create, body);
    return new Response(JSON.stringify({ id }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/loras/list",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const userId = url.searchParams.get("userId");
    const status = url.searchParams.get("status");
    const baseModel = url.searchParams.get("baseModel");
    const activeOnly = url.searchParams.get("activeOnly") === "true";

    const data = await ctx.runQuery(internal.loras.list, {
      userId: userId || undefined,
      status: status || undefined,
      baseModel: baseModel || undefined,
      activeOnly
    });
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/loras/get",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const id = url.searchParams.get("id");
    if (!id) {
      return new Response(JSON.stringify({ error: "id parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
    const data = await ctx.runQuery(internal.loras.get, { id });
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/loras/update",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    await ctx.runMutation(internal.loras.update, body);
    return new Response(JSON.stringify({ success: true }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/loras/delete",
  method: "DELETE",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const id = url.searchParams.get("id");
    if (!id) {
      return new Response(JSON.stringify({ error: "id parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
    await ctx.runMutation(internal.loras.deleteById, { id });
    return new Response(JSON.stringify({ success: true }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/loras/by-replicate-id",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const replicateTrainingId = url.searchParams.get("replicateTrainingId");
    if (!replicateTrainingId) {
      return new Response(JSON.stringify({ error: "replicateTrainingId parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
    const data = await ctx.runQuery(internal.loras.byReplicateId, { replicateTrainingId });
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/loras/by-trigger-word",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const triggerWord = url.searchParams.get("triggerWord");
    if (!triggerWord) {
      return new Response(JSON.stringify({ error: "triggerWord parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
    const data = await ctx.runQuery(internal.loras.byTriggerWord, { triggerWord });
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

// Webhook events endpoints
http.route({
  path: "/api/webhook-events/create",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    const id = await ctx.runMutation(internal.webhookEvents.create, body);
    return new Response(JSON.stringify({ id }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/webhook-events/by-event-id",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const eventId = url.searchParams.get("eventId");
    if (!eventId) {
      return new Response(JSON.stringify({ error: "eventId parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
    const data = await ctx.runQuery(internal.webhookEvents.byEventId, { eventId });
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

// Training Images endpoints
http.route({
  path: "/api/training-images/create",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    const id = await ctx.runMutation(internal.trainingImages.create, body);
    return new Response(JSON.stringify({ id }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/training-images/list-by-lora",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const loraId = url.searchParams.get("loraId");
    if (!loraId) {
      return new Response(JSON.stringify({ error: "loraId parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
    const data = await ctx.runQuery(internal.trainingImages.listByLora, { loraId });
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/training-images/count-by-lora",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const loraId = url.searchParams.get("loraId");
    if (!loraId) {
      return new Response(JSON.stringify({ error: "loraId parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
    const count = await ctx.runQuery(internal.trainingImages.countByLora, { loraId });
    return new Response(JSON.stringify({ count }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/training-images/delete",
  method: "DELETE",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const id = url.searchParams.get("id");
    if (!id) {
      return new Response(JSON.stringify({ error: "id parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
    await ctx.runMutation(internal.trainingImages.deleteById, { id });
    return new Response(JSON.stringify({ success: true }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/training-images/delete-by-lora",
  method: "DELETE",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const loraId = url.searchParams.get("loraId");
    if (!loraId) {
      return new Response(JSON.stringify({ error: "loraId parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
    await ctx.runMutation(internal.trainingImages.deleteByLora, { loraId });
    return new Response(JSON.stringify({ success: true }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

// Storage upload URL endpoint
http.route({
  path: "/api/storage/generate-upload-url",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const uploadUrl = await ctx.storage.generateUploadUrl();
    return new Response(JSON.stringify({ uploadUrl }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

// Storage usage endpoint (for quota checking)
http.route({
  path: "/api/storage/usage",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    // Note: Convex doesn't expose storage usage in the API yet
    // For now, return a mock response that can be used for quota checking
    // In a real implementation, this would query actual storage usage
    return new Response(JSON.stringify({
      used_bytes: 0,
      quota_bytes: 10737418240, // 10GB default
      usage_percent: 0
    }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

// Storage URL endpoint (get download URL for a storage ID)
http.route({
  path: "/api/storage/get-url",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const storageId = url.searchParams.get("storageId");
    if (!storageId) {
      return new Response(JSON.stringify({ error: "storageId parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
    const downloadUrl = await ctx.storage.getUrl(storageId);
    return new Response(JSON.stringify({ url: downloadUrl }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

// Generations endpoints
http.route({
  path: "/api/generations/create",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    const id = await ctx.runMutation(internal.generations.create, body);
    return new Response(JSON.stringify({ id }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/generations/list",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const favoriteParam = url.searchParams.get("favorite");
    const favorite = favoriteParam === "true" ? true : favoriteParam === "false" ? false : undefined;

    const data = await ctx.runQuery(internal.generations.list, {
      favorite
    });
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/generations/toggle-favorite",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    const result = await ctx.runMutation(internal.generations.toggleFavorite, body);
    return new Response(JSON.stringify({ success: true, ...result }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

http.route({
  path: "/api/generations/delete",
  method: "DELETE",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const id = url.searchParams.get("id");
    if (!id) {
      return new Response(JSON.stringify({ error: "id parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }
    await ctx.runMutation(internal.generations.deleteById, { id });
    return new Response(JSON.stringify({ success: true }), {
      headers: { "Content-Type": "application/json" }
    });
  }),
});

export default http;