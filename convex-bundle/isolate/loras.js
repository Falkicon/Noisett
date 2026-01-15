import {
  a,
  b as e,
  g as l,
  i as o
} from "./_deps/P4Y5ARCJ.js";

// convex/loras.ts
var c = o({
  args: {
    name: e.string(),
    triggerWord: e.string(),
    description: e.optional(e.string()),
    baseModel: e.union(e.literal("flux"), e.literal("sdxl")),
    status: e.union(
      e.literal("created"),
      e.literal("uploading"),
      e.literal("ready_to_train"),
      e.literal("training"),
      e.literal("completed"),
      e.literal("deployment_pending"),
      e.literal("deployment_failed"),
      e.literal("failed"),
      e.literal("deployed")
    ),
    steps: e.number(),
    progress: e.optional(e.number()),
    currentStep: e.optional(e.number()),
    replicateTrainingId: e.optional(e.string()),
    fireworksModelId: e.optional(e.string()),
    loraUrl: e.optional(e.string()),
    isActive: e.boolean(),
    createdAt: e.number(),
    trainStartedAt: e.optional(e.number()),
    completedAt: e.optional(e.number()),
    userId: e.optional(e.string()),
    errorMessage: e.optional(e.string()),
    errorCode: e.optional(e.string())
  },
  handler: /* @__PURE__ */ a(async (r, t) => await r.db.insert("loras", t), "handler")
}), b = l({
  args: { id: e.id("loras") },
  handler: /* @__PURE__ */ a(async (r, t) => await r.db.get(t.id), "handler")
}), y = l({
  args: {
    userId: e.optional(e.string()),
    status: e.optional(e.string()),
    baseModel: e.optional(e.string()),
    activeOnly: e.boolean()
  },
  handler: /* @__PURE__ */ a(async (r, t) => {
    let i = r.db.query("loras");
    return t.userId ? i = i.withIndex("by_user", (n) => n.eq("userId", t.userId)) : t.status && (i = i.withIndex("by_status", (n) => n.eq("status", t.status))), (await i.collect()).filter((n) => !(t.baseModel && n.baseModel !== t.baseModel || t.activeOnly && !n.isActive));
  }, "handler")
}), m = o({
  args: {
    id: e.id("loras"),
    name: e.optional(e.string()),
    description: e.optional(e.string()),
    status: e.optional(e.union(
      e.literal("created"),
      e.literal("uploading"),
      e.literal("ready_to_train"),
      e.literal("training"),
      e.literal("completed"),
      e.literal("deployment_pending"),
      e.literal("deployment_failed"),
      e.literal("failed"),
      e.literal("deployed")
    )),
    progress: e.optional(e.number()),
    currentStep: e.optional(e.number()),
    replicateTrainingId: e.optional(e.string()),
    fireworksModelId: e.optional(e.string()),
    loraUrl: e.optional(e.string()),
    isActive: e.optional(e.boolean()),
    trainStartedAt: e.optional(e.number()),
    completedAt: e.optional(e.number()),
    errorMessage: e.optional(e.string()),
    errorCode: e.optional(e.string())
  },
  handler: /* @__PURE__ */ a(async (r, t) => {
    let { id: i, ...s } = t, n = Object.fromEntries(
      Object.entries(s).filter(([p, d]) => d !== void 0)
    );
    await r.db.patch(i, n);
  }, "handler")
}), f = o({
  args: { id: e.id("loras") },
  handler: /* @__PURE__ */ a(async (r, t) => {
    await r.db.delete(t.id);
  }, "handler")
}), I = l({
  args: { replicateTrainingId: e.string() },
  handler: /* @__PURE__ */ a(async (r, t) => await r.db.query("loras").filter((i) => i.eq(i.field("replicateTrainingId"), t.replicateTrainingId)).first(), "handler")
}), w = l({
  args: { triggerWord: e.string() },
  handler: /* @__PURE__ */ a(async (r, t) => await r.db.query("loras").withIndex("by_trigger_word", (i) => i.eq("triggerWord", t.triggerWord)).first(), "handler")
});
export {
  I as byReplicateId,
  w as byTriggerWord,
  c as create,
  f as deleteById,
  b as get,
  y as list,
  m as update
};
//# sourceMappingURL=loras.js.map
