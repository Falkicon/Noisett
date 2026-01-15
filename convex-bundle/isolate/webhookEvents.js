import {
  a as r,
  b as e,
  g as s,
  i as a
} from "./_deps/P4Y5ARCJ.js";

// convex/webhookEvents.ts
var v = a({
  args: {
    eventId: e.string(),
    processedAt: e.number(),
    eventType: e.string()
  },
  handler: /* @__PURE__ */ r(async (t, n) => await t.db.insert("webhookEvents", n), "handler")
}), b = s({
  args: { eventId: e.string() },
  handler: /* @__PURE__ */ r(async (t, n) => await t.db.query("webhookEvents").withIndex("by_event_id", (i) => i.eq("eventId", n.eventId)).first(), "handler")
});
export {
  b as byEventId,
  v as create
};
//# sourceMappingURL=webhookEvents.js.map
