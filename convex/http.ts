import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";
import { internal } from "./_generated/api";

const http = httpRouter();

// CORS headers for cross-origin requests
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

// Helper to create JSON response with CORS headers
function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...corsHeaders,
    },
  });
}

// Handle OPTIONS preflight requests for all /api/* routes
http.route({
  path: "/api/asset-types/seed",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/asset-types/needs-seed",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/asset-types/create",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/asset-types/list",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/asset-types/get",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/asset-types/update",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/asset-types/delete",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/asset-types/add-reference-image",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/asset-types/remove-reference-image",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/asset-types/reorder-reference-images",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/generations/list",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/generations/create",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/generations/toggle-favorite",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/generations/delete",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

// Asset Types endpoints

// Seed default Asset Types (idempotent - safe to call multiple times)
http.route({
  path: "/api/asset-types/seed",
  method: "POST",
  handler: httpAction(async (ctx) => {
    const result = await ctx.runMutation(internal.assetTypes.seed, {});
    return jsonResponse(result);
  }),
});

// Migrate existing Asset Types to add slug field
http.route({
  path: "/api/asset-types/migrate-slugs",
  method: "POST",
  handler: httpAction(async (ctx) => {
    const result = await ctx.runMutation(internal.assetTypes.migrateSlugs, {});
    return jsonResponse(result);
  }),
});

// Check if Asset Types need seeding (read-only)
http.route({
  path: "/api/asset-types/needs-seed",
  method: "GET",
  handler: httpAction(async (ctx) => {
    const result = await ctx.runQuery(internal.assetTypes.needsSeed, {});
    return jsonResponse(result);
  }),
});

http.route({
  path: "/api/asset-types/create",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    const id = await ctx.runMutation(internal.assetTypes.create, body);
    return jsonResponse({ id });
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
    return jsonResponse(data);
  }),
});

http.route({
  path: "/api/asset-types/get",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const id = url.searchParams.get("id");
    if (!id) {
      return jsonResponse({ error: "id parameter required" }, 400);
    }
    const data = await ctx.runQuery(internal.assetTypes.get, { id });
    return jsonResponse(data);
  }),
});

http.route({
  path: "/api/asset-types/update",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    await ctx.runMutation(internal.assetTypes.update, body);
    return jsonResponse({ success: true });
  }),
});

http.route({
  path: "/api/asset-types/delete",
  method: "DELETE",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const id = url.searchParams.get("id");
    if (!id) {
      return jsonResponse({ error: "id parameter required" }, 400);
    }
    await ctx.runMutation(internal.assetTypes.deleteById, { id });
    return jsonResponse({ success: true });
  }),
});

// Reference Images endpoints
http.route({
  path: "/api/asset-types/add-reference-image",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    if (!body.id || !body.storageId) {
      return jsonResponse({ error: "id and storageId parameters required" }, 400);
    }
    const result = await ctx.runMutation(internal.assetTypes.addReferenceImage, {
      id: body.id,
      storageId: body.storageId,
    });
    return jsonResponse(result);
  }),
});

http.route({
  path: "/api/asset-types/remove-reference-image",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    if (!body.id || !body.storageId) {
      return jsonResponse({ error: "id and storageId parameters required" }, 400);
    }
    const result = await ctx.runMutation(internal.assetTypes.removeReferenceImage, {
      id: body.id,
      storageId: body.storageId,
    });
    return jsonResponse(result);
  }),
});

http.route({
  path: "/api/asset-types/reorder-reference-images",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    if (!body.id || !body.storageIds) {
      return jsonResponse({ error: "id and storageIds parameters required" }, 400);
    }
    const result = await ctx.runMutation(internal.assetTypes.reorderReferenceImages, {
      id: body.id,
      storageIds: body.storageIds,
    });
    return jsonResponse(result);
  }),
});

// LoRA endpoints
http.route({
  path: "/api/loras/create",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    const id = await ctx.runMutation(internal.loras.create, body);
    return jsonResponse({ id });
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
    return jsonResponse(data);
  }),
});

http.route({
  path: "/api/loras/get",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const id = url.searchParams.get("id");
    if (!id) {
      return jsonResponse({ error: "id parameter required" }, 400);
    }
    const data = await ctx.runQuery(internal.loras.get, { id });
    return jsonResponse(data);
  }),
});

http.route({
  path: "/api/loras/update",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    await ctx.runMutation(internal.loras.update, body);
    return jsonResponse({ success: true });
  }),
});

http.route({
  path: "/api/loras/delete",
  method: "DELETE",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const id = url.searchParams.get("id");
    if (!id) {
      return jsonResponse({ error: "id parameter required" }, 400);
    }
    await ctx.runMutation(internal.loras.deleteById, { id });
    return jsonResponse({ success: true });
  }),
});

http.route({
  path: "/api/loras/by-replicate-id",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const replicateTrainingId = url.searchParams.get("replicateTrainingId");
    if (!replicateTrainingId) {
      return jsonResponse({ error: "replicateTrainingId parameter required" }, 400);
    }
    const data = await ctx.runQuery(internal.loras.byReplicateId, { replicateTrainingId });
    return jsonResponse(data);
  }),
});

http.route({
  path: "/api/loras/by-trigger-word",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const triggerWord = url.searchParams.get("triggerWord");
    if (!triggerWord) {
      return jsonResponse({ error: "triggerWord parameter required" }, 400);
    }
    const data = await ctx.runQuery(internal.loras.byTriggerWord, { triggerWord });
    return jsonResponse(data);
  }),
});

// Webhook events endpoints
http.route({
  path: "/api/webhook-events/create",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    const id = await ctx.runMutation(internal.webhookEvents.create, body);
    return jsonResponse({ id });
  }),
});

http.route({
  path: "/api/webhook-events/by-event-id",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const eventId = url.searchParams.get("eventId");
    if (!eventId) {
      return jsonResponse({ error: "eventId parameter required" }, 400);
    }
    const data = await ctx.runQuery(internal.webhookEvents.byEventId, { eventId });
    return jsonResponse(data);
  }),
});

// Training Images endpoints
http.route({
  path: "/api/training-images/create",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    const id = await ctx.runMutation(internal.trainingImages.create, body);
    return jsonResponse({ id });
  }),
});

http.route({
  path: "/api/training-images/list-by-lora",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const loraId = url.searchParams.get("loraId");
    if (!loraId) {
      return jsonResponse({ error: "loraId parameter required" }, 400);
    }
    const data = await ctx.runQuery(internal.trainingImages.listByLora, { loraId });
    return jsonResponse(data);
  }),
});

http.route({
  path: "/api/training-images/count-by-lora",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const loraId = url.searchParams.get("loraId");
    if (!loraId) {
      return jsonResponse({ error: "loraId parameter required" }, 400);
    }
    const count = await ctx.runQuery(internal.trainingImages.countByLora, { loraId });
    return jsonResponse({ count });
  }),
});

http.route({
  path: "/api/training-images/delete",
  method: "DELETE",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const id = url.searchParams.get("id");
    if (!id) {
      return jsonResponse({ error: "id parameter required" }, 400);
    }
    await ctx.runMutation(internal.trainingImages.deleteById, { id });
    return jsonResponse({ success: true });
  }),
});

http.route({
  path: "/api/training-images/delete-by-lora",
  method: "DELETE",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const loraId = url.searchParams.get("loraId");
    if (!loraId) {
      return jsonResponse({ error: "loraId parameter required" }, 400);
    }
    await ctx.runMutation(internal.trainingImages.deleteByLora, { loraId });
    return jsonResponse({ success: true });
  }),
});

// Storage upload URL endpoint
http.route({
  path: "/api/storage/generate-upload-url",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/storage/generate-upload-url",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const uploadUrl = await ctx.storage.generateUploadUrl();
    return jsonResponse({ uploadUrl });
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
    return jsonResponse({
      used_bytes: 0,
      quota_bytes: 10737418240, // 10GB default
      usage_percent: 0
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
      return jsonResponse({ error: "storageId parameter required" }, 400);
    }
    const downloadUrl = await ctx.storage.getUrl(storageId);
    return jsonResponse({ url: downloadUrl });
  }),
});

// Generations endpoints
http.route({
  path: "/api/generations/create",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    const id = await ctx.runMutation(internal.generations.create, body);
    return jsonResponse({ id });
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
    return jsonResponse(data);
  }),
});

http.route({
  path: "/api/generations/toggle-favorite",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    const result = await ctx.runMutation(internal.generations.toggleFavorite, body);
    return jsonResponse({ success: true, ...result });
  }),
});

http.route({
  path: "/api/generations/delete",
  method: "DELETE",
  handler: httpAction(async (ctx, request) => {
    const url = new URL(request.url);
    const id = url.searchParams.get("id");
    if (!id) {
      return jsonResponse({ error: "id parameter required" }, 400);
    }
    await ctx.runMutation(internal.generations.deleteById, { id });
    return jsonResponse({ success: true });
  }),
});

// Upload image from external URL to Convex storage
http.route({
  path: "/api/storage/upload-from-url",
  method: "OPTIONS",
  handler: httpAction(async () => new Response(null, { status: 204, headers: corsHeaders })),
});

http.route({
  path: "/api/storage/upload-from-url",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const body = await request.json();
    const { url } = body;
    
    if (!url) {
      return jsonResponse({ error: "url parameter required" }, 400);
    }

    try {
      // Fetch the image from the external URL
      const response = await fetch(url);
      if (!response.ok) {
        return jsonResponse({ 
          error: `Failed to fetch image: ${response.status}` 
        }, 400);
      }

      // Get the image blob
      const blob = await response.blob();
      
      // Store in Convex storage
      const storageId = await ctx.storage.store(blob);
      
      // Get the permanent URL
      const permanentUrl = await ctx.storage.getUrl(storageId);

      return jsonResponse({ 
        storageId, 
        url: permanentUrl 
      });
    } catch (error) {
      return jsonResponse({ 
        error: `Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}` 
      }, 500);
    }
  }),
});

export default http;// Force redeploy Wed, Jan 14, 2026 11:22:37 PM
