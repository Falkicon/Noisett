import {
  c as p,
  d as u,
  e as d,
  j as a
} from "./_deps/P4Y5ARCJ.js";

// convex/_generated/api.js
var o = p, g = d();

// convex/http.ts
var s = u();
s.route({
  path: "/api/loras/create",
  method: "POST",
  handler: a(async (t, r) => {
    let n = await r.json(), e = await t.runMutation(o.loras.create, n);
    return new Response(JSON.stringify({ id: e }), {
      headers: { "Content-Type": "application/json" }
    });
  })
});
s.route({
  path: "/api/loras/list",
  method: "GET",
  handler: a(async (t, r) => {
    let n = new URL(r.url), e = n.searchParams.get("userId"), i = n.searchParams.get("status"), c = n.searchParams.get("baseModel"), l = n.searchParams.get("activeOnly") === "true", y = await t.runQuery(o.loras.list, {
      userId: e || void 0,
      status: i || void 0,
      baseModel: c || void 0,
      activeOnly: l
    });
    return new Response(JSON.stringify(y), {
      headers: { "Content-Type": "application/json" }
    });
  })
});
s.route({
  path: "/api/loras/get",
  method: "GET",
  handler: a(async (t, r) => {
    let e = new URL(r.url).searchParams.get("id");
    if (!e)
      return new Response(JSON.stringify({ error: "id parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    let i = await t.runQuery(o.loras.get, { id: e });
    return new Response(JSON.stringify(i), {
      headers: { "Content-Type": "application/json" }
    });
  })
});
s.route({
  path: "/api/loras/update",
  method: "POST",
  handler: a(async (t, r) => {
    let n = await r.json();
    return await t.runMutation(o.loras.update, n), new Response(JSON.stringify({ success: !0 }), {
      headers: { "Content-Type": "application/json" }
    });
  })
});
s.route({
  path: "/api/loras/delete",
  method: "DELETE",
  handler: a(async (t, r) => {
    let e = new URL(r.url).searchParams.get("id");
    return e ? (await t.runMutation(o.loras.deleteById, { id: e }), new Response(JSON.stringify({ success: !0 }), {
      headers: { "Content-Type": "application/json" }
    })) : new Response(JSON.stringify({ error: "id parameter required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" }
    });
  })
});
s.route({
  path: "/api/loras/by-replicate-id",
  method: "GET",
  handler: a(async (t, r) => {
    let e = new URL(r.url).searchParams.get("replicateTrainingId");
    if (!e)
      return new Response(JSON.stringify({ error: "replicateTrainingId parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    let i = await t.runQuery(o.loras.byReplicateId, { replicateTrainingId: e });
    return new Response(JSON.stringify(i), {
      headers: { "Content-Type": "application/json" }
    });
  })
});
s.route({
  path: "/api/loras/by-trigger-word",
  method: "GET",
  handler: a(async (t, r) => {
    let e = new URL(r.url).searchParams.get("triggerWord");
    if (!e)
      return new Response(JSON.stringify({ error: "triggerWord parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    let i = await t.runQuery(o.loras.byTriggerWord, { triggerWord: e });
    return new Response(JSON.stringify(i), {
      headers: { "Content-Type": "application/json" }
    });
  })
});
s.route({
  path: "/api/webhook-events/create",
  method: "POST",
  handler: a(async (t, r) => {
    let n = await r.json(), e = await t.runMutation(o.webhookEvents.create, n);
    return new Response(JSON.stringify({ id: e }), {
      headers: { "Content-Type": "application/json" }
    });
  })
});
s.route({
  path: "/api/webhook-events/by-event-id",
  method: "GET",
  handler: a(async (t, r) => {
    let e = new URL(r.url).searchParams.get("eventId");
    if (!e)
      return new Response(JSON.stringify({ error: "eventId parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    let i = await t.runQuery(o.webhookEvents.byEventId, { eventId: e });
    return new Response(JSON.stringify(i), {
      headers: { "Content-Type": "application/json" }
    });
  })
});
s.route({
  path: "/api/training-images/create",
  method: "POST",
  handler: a(async (t, r) => {
    let n = await r.json(), e = await t.runMutation(o.trainingImages.create, n);
    return new Response(JSON.stringify({ id: e }), {
      headers: { "Content-Type": "application/json" }
    });
  })
});
s.route({
  path: "/api/training-images/list-by-lora",
  method: "GET",
  handler: a(async (t, r) => {
    let e = new URL(r.url).searchParams.get("loraId");
    if (!e)
      return new Response(JSON.stringify({ error: "loraId parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    let i = await t.runQuery(o.trainingImages.listByLora, { loraId: e });
    return new Response(JSON.stringify(i), {
      headers: { "Content-Type": "application/json" }
    });
  })
});
s.route({
  path: "/api/training-images/count-by-lora",
  method: "GET",
  handler: a(async (t, r) => {
    let e = new URL(r.url).searchParams.get("loraId");
    if (!e)
      return new Response(JSON.stringify({ error: "loraId parameter required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    let i = await t.runQuery(o.trainingImages.countByLora, { loraId: e });
    return new Response(JSON.stringify({ count: i }), {
      headers: { "Content-Type": "application/json" }
    });
  })
});
s.route({
  path: "/api/training-images/delete",
  method: "DELETE",
  handler: a(async (t, r) => {
    let e = new URL(r.url).searchParams.get("id");
    return e ? (await t.runMutation(o.trainingImages.deleteById, { id: e }), new Response(JSON.stringify({ success: !0 }), {
      headers: { "Content-Type": "application/json" }
    })) : new Response(JSON.stringify({ error: "id parameter required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" }
    });
  })
});
s.route({
  path: "/api/training-images/delete-by-lora",
  method: "DELETE",
  handler: a(async (t, r) => {
    let e = new URL(r.url).searchParams.get("loraId");
    return e ? (await t.runMutation(o.trainingImages.deleteByLora, { loraId: e }), new Response(JSON.stringify({ success: !0 }), {
      headers: { "Content-Type": "application/json" }
    })) : new Response(JSON.stringify({ error: "loraId parameter required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" }
    });
  })
});
s.route({
  path: "/api/storage/generate-upload-url",
  method: "POST",
  handler: a(async (t, r) => {
    let n = await t.storage.generateUploadUrl();
    return new Response(JSON.stringify({ uploadUrl: n }), {
      headers: { "Content-Type": "application/json" }
    });
  })
});
s.route({
  path: "/api/storage/usage",
  method: "GET",
  handler: a(async (t, r) => new Response(JSON.stringify({
    used_bytes: 0,
    quota_bytes: 10737418240,
    // 10GB default
    usage_percent: 0
  }), {
    headers: { "Content-Type": "application/json" }
  }))
});
var R = s;
export {
  R as default
};
//# sourceMappingURL=http.js.map
