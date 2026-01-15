import {
  a as t,
  b as a,
  f as i,
  h as d
} from "./_deps/P4Y5ARCJ.js";

// convex/trainingImages.ts
var g = d({
  args: {
    loraId: a.id("loras"),
    storageId: a.id("_storage"),
    filename: a.string(),
    caption: a.optional(a.string()),
    sizeBytes: a.number(),
    width: a.optional(a.number()),
    height: a.optional(a.number()),
    uploadedAt: a.number()
  },
  handler: /* @__PURE__ */ t(async (r, e) => await r.db.insert("trainingImages", e), "handler")
}), c = i({
  args: {
    loraId: a.id("loras")
  },
  handler: /* @__PURE__ */ t(async (r, e) => await r.db.query("trainingImages").withIndex("by_lora", (n) => n.eq("loraId", e.loraId)).collect(), "handler")
}), I = i({
  args: {
    loraId: a.id("loras")
  },
  handler: /* @__PURE__ */ t(async (r, e) => (await r.db.query("trainingImages").withIndex("by_lora", (o) => o.eq("loraId", e.loraId)).collect()).length, "handler")
}), m = d({
  args: {
    id: a.id("trainingImages")
  },
  handler: /* @__PURE__ */ t(async (r, e) => {
    await r.db.delete(e.id);
  }, "handler")
}), y = d({
  args: {
    loraId: a.id("loras")
  },
  handler: /* @__PURE__ */ t(async (r, e) => {
    let n = await r.db.query("trainingImages").withIndex("by_lora", (o) => o.eq("loraId", e.loraId)).collect();
    for (let o of n)
      await r.db.delete(o._id);
  }, "handler")
}), u = i({
  args: {
    id: a.id("trainingImages")
  },
  handler: /* @__PURE__ */ t(async (r, e) => await r.db.get(e.id), "handler")
});
export {
  I as countByLora,
  g as create,
  m as deleteById,
  y as deleteByLora,
  u as get,
  c as listByLora
};
//# sourceMappingURL=trainingImages.js.map
