import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";
import { internal } from "./_generated/api";

const http = httpRouter();

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

export default http;