var Pt = Object.defineProperty;
var n = (t, e) => Pt(t, "name", { value: e, configurable: !0 });

// node_modules/convex/dist/esm/values/base64.js
var E = [], b = [], Ft = Uint8Array, ge = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
for (T = 0, ze = ge.length; T < ze; ++T)
  E[T] = ge[T], b[ge.charCodeAt(T)] = T;
var T, ze;
b[45] = 62;
b[95] = 63;
function Rt(t) {
  var e = t.length;
  if (e % 4 > 0)
    throw new Error("Invalid string. Length must be a multiple of 4");
  var r = t.indexOf("=");
  r === -1 && (r = e);
  var o = r === e ? 0 : 4 - r % 4;
  return [r, o];
}
n(Rt, "getLens");
function qt(t, e, r) {
  return (e + r) * 3 / 4 - r;
}
n(qt, "_byteLength");
function q(t) {
  var e, r = Rt(t), o = r[0], s = r[1], i = new Ft(qt(t, o, s)), a = 0, f = s > 0 ? o - 4 : o, d;
  for (d = 0; d < f; d += 4)
    e = b[t.charCodeAt(d)] << 18 | b[t.charCodeAt(d + 1)] << 12 | b[t.charCodeAt(d + 2)] << 6 | b[t.charCodeAt(d + 3)], i[a++] = e >> 16 & 255, i[a++] = e >> 8 & 255, i[a++] = e & 255;
  return s === 2 && (e = b[t.charCodeAt(d)] << 2 | b[t.charCodeAt(d + 1)] >> 4, i[a++] = e & 255), s === 1 && (e = b[t.charCodeAt(d)] << 10 | b[t.charCodeAt(d + 1)] << 4 | b[t.charCodeAt(d + 2)] >> 2, i[a++] = e >> 8 & 255, i[a++] = e & 255), i;
}
n(q, "toByteArray");
function Bt(t) {
  return E[t >> 18 & 63] + E[t >> 12 & 63] + E[t >> 6 & 63] + E[t & 63];
}
n(Bt, "tripletToBase64");
function jt(t, e, r) {
  for (var o, s = [], i = e; i < r; i += 3)
    o = (t[i] << 16 & 16711680) + (t[i + 1] << 8 & 65280) + (t[i + 2] & 255), s.push(Bt(o));
  return s.join("");
}
n(jt, "encodeChunk");
function B(t) {
  for (var e, r = t.length, o = r % 3, s = [], i = 16383, a = 0, f = r - o; a < f; a += i)
    s.push(
      jt(
        t,
        a,
        a + i > f ? f : a + i
      )
    );
  return o === 1 ? (e = t[r - 1], s.push(E[e >> 2] + E[e << 4 & 63] + "==")) : o === 2 && (e = (t[r - 2] << 8) + t[r - 1], s.push(
    E[e >> 10] + E[e >> 4 & 63] + E[e << 2 & 63] + "="
  )), s.join("");
}
n(B, "fromByteArray");

// node_modules/convex/dist/esm/common/index.js
function S(t) {
  if (t === void 0)
    return {};
  if (!be(t))
    throw new Error(
      `The arguments to a Convex function must be an object. Received: ${t}`
    );
  return t;
}
n(S, "parseArgs");
function be(t) {
  let e = typeof t == "object", r = Object.getPrototypeOf(t), o = r === null || r === Object.prototype || // Objects generated from other contexts (e.g. across Node.js `vm` modules) will not satisfy the previous
  // conditions but are still simple objects.
  r?.constructor?.name === "Object";
  return e && o;
}
n(be, "isSimpleObject");

// node_modules/convex/dist/esm/values/value.js
var Ze = !0, P = BigInt("-9223372036854775808"), Ie = BigInt("9223372036854775807"), Ae = BigInt("0"), Mt = BigInt("8"), Ut = BigInt("256");
function et(t) {
  return Number.isNaN(t) || !Number.isFinite(t) || Object.is(t, -0);
}
n(et, "isSpecial");
function Jt(t) {
  t < Ae && (t -= P + P);
  let e = t.toString(16);
  e.length % 2 === 1 && (e = "0" + e);
  let r = new Uint8Array(new ArrayBuffer(8)), o = 0;
  for (let s of e.match(/.{2}/g).reverse())
    r.set([parseInt(s, 16)], o++), t >>= Mt;
  return B(r);
}
n(Jt, "slowBigIntToBase64");
function Vt(t) {
  let e = q(t);
  if (e.byteLength !== 8)
    throw new Error(
      `Received ${e.byteLength} bytes, expected 8 for $integer`
    );
  let r = Ae, o = Ae;
  for (let s of e)
    r += BigInt(s) * Ut ** o, o++;
  return r > Ie && (r += P + P), r;
}
n(Vt, "slowBase64ToBigInt");
function Lt(t) {
  if (t < P || Ie < t)
    throw new Error(
      `BigInt ${t} does not fit into a 64-bit signed integer.`
    );
  let e = new ArrayBuffer(8);
  return new DataView(e).setBigInt64(0, t, !0), B(new Uint8Array(e));
}
n(Lt, "modernBigIntToBase64");
function kt(t) {
  let e = q(t);
  if (e.byteLength !== 8)
    throw new Error(
      `Received ${e.byteLength} bytes, expected 8 for $integer`
    );
  return new DataView(e.buffer).getBigInt64(0, !0);
}
n(kt, "modernBase64ToBigInt");
var Gt = DataView.prototype.setBigInt64 ? Lt : Jt, Qt = DataView.prototype.getBigInt64 ? kt : Vt, Ye = 1024;
function Ee(t) {
  if (t.length > Ye)
    throw new Error(
      `Field name ${t} exceeds maximum field name length ${Ye}.`
    );
  if (t.startsWith("$"))
    throw new Error(`Field name ${t} starts with a '$', which is reserved.`);
  for (let e = 0; e < t.length; e += 1) {
    let r = t.charCodeAt(e);
    if (r < 32 || r >= 127)
      throw new Error(
        `Field name ${t} has invalid character '${t[e]}': Field names can only contain non-control ASCII characters`
      );
  }
}
n(Ee, "validateObjectField");
function y(t) {
  if (t === null || typeof t == "boolean" || typeof t == "number" || typeof t == "string")
    return t;
  if (Array.isArray(t))
    return t.map((o) => y(o));
  if (typeof t != "object")
    throw new Error(`Unexpected type of ${t}`);
  let e = Object.entries(t);
  if (e.length === 1) {
    let o = e[0][0];
    if (o === "$bytes") {
      if (typeof t.$bytes != "string")
        throw new Error(`Malformed $bytes field on ${t}`);
      return q(t.$bytes).buffer;
    }
    if (o === "$integer") {
      if (typeof t.$integer != "string")
        throw new Error(`Malformed $integer field on ${t}`);
      return Qt(t.$integer);
    }
    if (o === "$float") {
      if (typeof t.$float != "string")
        throw new Error(`Malformed $float field on ${t}`);
      let s = q(t.$float);
      if (s.byteLength !== 8)
        throw new Error(
          `Received ${s.byteLength} bytes, expected 8 for $float`
        );
      let a = new DataView(s.buffer).getFloat64(0, Ze);
      if (!et(a))
        throw new Error(`Float ${a} should be encoded as a number`);
      return a;
    }
    if (o === "$set")
      throw new Error(
        "Received a Set which is no longer supported as a Convex type."
      );
    if (o === "$map")
      throw new Error(
        "Received a Map which is no longer supported as a Convex type."
      );
  }
  let r = {};
  for (let [o, s] of Object.entries(t))
    Ee(o), r[o] = y(s);
  return r;
}
n(y, "jsonToConvex");
var Ke = 16384;
function _(t) {
  let e = JSON.stringify(t, (r, o) => o === void 0 ? "undefined" : typeof o == "bigint" ? `${o.toString()}n` : o);
  if (e.length > Ke) {
    let r = "[...truncated]", o = Ke - r.length, s = e.codePointAt(o - 1);
    return s !== void 0 && s > 65535 && (o -= 1), e.substring(0, o) + r;
  }
  return e;
}
n(_, "stringifyValueForError");
function j(t, e, r, o) {
  if (t === void 0) {
    let a = r && ` (present at path ${r} in original object ${_(
      e
    )})`;
    throw new Error(
      `undefined is not a valid Convex value${a}. To learn about Convex's supported types, see https://docs.convex.dev/using/types.`
    );
  }
  if (t === null)
    return t;
  if (typeof t == "bigint") {
    if (t < P || Ie < t)
      throw new Error(
        `BigInt ${t} does not fit into a 64-bit signed integer.`
      );
    return { $integer: Gt(t) };
  }
  if (typeof t == "number")
    if (et(t)) {
      let a = new ArrayBuffer(8);
      return new DataView(a).setFloat64(0, t, Ze), { $float: B(new Uint8Array(a)) };
    } else
      return t;
  if (typeof t == "boolean" || typeof t == "string")
    return t;
  if (t instanceof ArrayBuffer)
    return { $bytes: B(new Uint8Array(t)) };
  if (Array.isArray(t))
    return t.map(
      (a, f) => j(a, e, r + `[${f}]`, !1)
    );
  if (t instanceof Set)
    throw new Error(
      ve(r, "Set", [...t], e)
    );
  if (t instanceof Map)
    throw new Error(
      ve(r, "Map", [...t], e)
    );
  if (!be(t)) {
    let a = t?.constructor?.name, f = a ? `${a} ` : "";
    throw new Error(
      ve(r, f, t, e)
    );
  }
  let s = {}, i = Object.entries(t);
  i.sort(([a, f], [d, O]) => a === d ? 0 : a < d ? -1 : 1);
  for (let [a, f] of i)
    f !== void 0 ? (Ee(a), s[a] = j(f, e, r + `.${a}`, !1)) : o && (Ee(a), s[a] = tt(
      f,
      e,
      r + `.${a}`
    ));
  return s;
}
n(j, "convexToJsonInternal");
function ve(t, e, r, o) {
  return t ? `${e}${_(
    r
  )} is not a supported Convex type (present at path ${t} in original object ${_(
    o
  )}). To learn about Convex's supported types, see https://docs.convex.dev/using/types.` : `${e}${_(
    r
  )} is not a supported Convex type.`;
}
n(ve, "errorMessageForUnsupportedType");
function tt(t, e, r) {
  if (t === void 0)
    return { $undefined: null };
  if (e === void 0)
    throw new Error(
      `Programming error. Current value is ${_(
        t
      )} but original value is undefined`
    );
  return j(t, e, r, !1);
}
n(tt, "convexOrUndefinedToJsonInternal");
function h(t) {
  return j(t, t, "", !1);
}
n(h, "convexToJson");
function v(t) {
  return tt(t, t, "");
}
n(v, "convexOrUndefinedToJson");
function rt(t) {
  return j(t, t, "", !0);
}
n(rt, "patchValueToJson");

// node_modules/convex/dist/esm/values/validators.js
var Dt = Object.defineProperty, Ht = /* @__PURE__ */ n((t, e, r) => e in t ? Dt(t, e, { enumerable: !0, configurable: !0, writable: !0, value: r }) : t[e] = r, "__defNormalProp"), m = /* @__PURE__ */ n((t, e, r) => Ht(t, typeof e != "symbol" ? e + "" : e, r), "__publicField"), Wt = "https://docs.convex.dev/error#undefined-validator";
function M(t, e) {
  let r = e !== void 0 ? ` for field "${e}"` : "";
  throw new Error(
    `A validator is undefined${r} in ${t}. This is often caused by circular imports. See ${Wt} for details.`
  );
}
n(M, "throwUndefinedValidatorError");
var g = class {
  static {
    n(this, "BaseValidator");
  }
  constructor({ isOptional: e }) {
    m(this, "type"), m(this, "fieldPaths"), m(this, "isOptional"), m(this, "isConvexValidator"), this.isOptional = e, this.isConvexValidator = !0;
  }
}, D = class t extends g {
  static {
    n(this, "VId");
  }
  /**
   * Usually you'd use `v.id(tableName)` instead.
   */
  constructor({
    isOptional: e,
    tableName: r
  }) {
    if (super({ isOptional: e }), m(this, "tableName"), m(this, "kind", "id"), typeof r != "string")
      throw new Error("v.id(tableName) requires a string");
    this.tableName = r;
  }
  /** @internal */
  get json() {
    return { type: "id", tableName: this.tableName };
  }
  /** @internal */
  asOptional() {
    return new t({
      isOptional: "optional",
      tableName: this.tableName
    });
  }
}, U = class t extends g {
  static {
    n(this, "VFloat64");
  }
  constructor() {
    super(...arguments), m(this, "kind", "float64");
  }
  /** @internal */
  get json() {
    return { type: "number" };
  }
  /** @internal */
  asOptional() {
    return new t({
      isOptional: "optional"
    });
  }
}, J = class t extends g {
  static {
    n(this, "VInt64");
  }
  constructor() {
    super(...arguments), m(this, "kind", "int64");
  }
  /** @internal */
  get json() {
    return { type: "bigint" };
  }
  /** @internal */
  asOptional() {
    return new t({ isOptional: "optional" });
  }
}, H = class t extends g {
  static {
    n(this, "VBoolean");
  }
  constructor() {
    super(...arguments), m(this, "kind", "boolean");
  }
  /** @internal */
  get json() {
    return { type: this.kind };
  }
  /** @internal */
  asOptional() {
    return new t({
      isOptional: "optional"
    });
  }
}, W = class t extends g {
  static {
    n(this, "VBytes");
  }
  constructor() {
    super(...arguments), m(this, "kind", "bytes");
  }
  /** @internal */
  get json() {
    return { type: this.kind };
  }
  /** @internal */
  asOptional() {
    return new t({ isOptional: "optional" });
  }
}, z = class t extends g {
  static {
    n(this, "VString");
  }
  constructor() {
    super(...arguments), m(this, "kind", "string");
  }
  /** @internal */
  get json() {
    return { type: this.kind };
  }
  /** @internal */
  asOptional() {
    return new t({
      isOptional: "optional"
    });
  }
}, X = class t extends g {
  static {
    n(this, "VNull");
  }
  constructor() {
    super(...arguments), m(this, "kind", "null");
  }
  /** @internal */
  get json() {
    return { type: this.kind };
  }
  /** @internal */
  asOptional() {
    return new t({ isOptional: "optional" });
  }
}, Y = class t extends g {
  static {
    n(this, "VAny");
  }
  constructor() {
    super(...arguments), m(this, "kind", "any");
  }
  /** @internal */
  get json() {
    return {
      type: this.kind
    };
  }
  /** @internal */
  asOptional() {
    return new t({
      isOptional: "optional"
    });
  }
}, K = class t extends g {
  static {
    n(this, "VObject");
  }
  /**
   * Usually you'd use `v.object({ ... })` instead.
   */
  constructor({
    isOptional: e,
    fields: r
  }) {
    super({ isOptional: e }), m(this, "fields"), m(this, "kind", "object"), globalThis.Object.entries(r).forEach(([o, s]) => {
      if (s === void 0 && M("v.object()", o), !s.isConvexValidator)
        throw new Error("v.object() entries must be validators");
    }), this.fields = r;
  }
  /** @internal */
  get json() {
    return {
      type: this.kind,
      value: globalThis.Object.fromEntries(
        globalThis.Object.entries(this.fields).map(([e, r]) => [
          e,
          {
            fieldType: r.json,
            optional: r.isOptional === "optional"
          }
        ])
      )
    };
  }
  /** @internal */
  asOptional() {
    return new t({
      isOptional: "optional",
      fields: this.fields
    });
  }
  /**
   * Create a new VObject with the specified fields omitted.
   * @param fields The field names to omit from this VObject.
   */
  omit(...e) {
    let r = { ...this.fields };
    for (let o of e)
      delete r[o];
    return new t({
      isOptional: this.isOptional,
      fields: r
    });
  }
  /**
   * Create a new VObject with only the specified fields.
   * @param fields The field names to pick from this VObject.
   */
  pick(...e) {
    let r = {};
    for (let o of e)
      r[o] = this.fields[o];
    return new t({
      isOptional: this.isOptional,
      fields: r
    });
  }
  /**
   * Create a new VObject with all fields marked as optional.
   */
  partial() {
    let e = {};
    for (let [r, o] of globalThis.Object.entries(this.fields))
      e[r] = o.asOptional();
    return new t({
      isOptional: this.isOptional,
      fields: e
    });
  }
  /**
   * Create a new VObject with additional fields merged in.
   * @param fields An object with additional validators to merge into this VObject.
   */
  extend(e) {
    return new t({
      isOptional: this.isOptional,
      fields: { ...this.fields, ...e }
    });
  }
}, Z = class t extends g {
  static {
    n(this, "VLiteral");
  }
  /**
   * Usually you'd use `v.literal(value)` instead.
   */
  constructor({ isOptional: e, value: r }) {
    if (super({ isOptional: e }), m(this, "value"), m(this, "kind", "literal"), typeof r != "string" && typeof r != "boolean" && typeof r != "number" && typeof r != "bigint")
      throw new Error("v.literal(value) must be a string, number, or boolean");
    this.value = r;
  }
  /** @internal */
  get json() {
    return {
      type: this.kind,
      value: h(this.value)
    };
  }
  /** @internal */
  asOptional() {
    return new t({
      isOptional: "optional",
      value: this.value
    });
  }
}, ee = class t extends g {
  static {
    n(this, "VArray");
  }
  /**
   * Usually you'd use `v.array(element)` instead.
   */
  constructor({
    isOptional: e,
    element: r
  }) {
    super({ isOptional: e }), m(this, "element"), m(this, "kind", "array"), r === void 0 && M("v.array()"), this.element = r;
  }
  /** @internal */
  get json() {
    return {
      type: this.kind,
      value: this.element.json
    };
  }
  /** @internal */
  asOptional() {
    return new t({
      isOptional: "optional",
      element: this.element
    });
  }
}, te = class t extends g {
  static {
    n(this, "VRecord");
  }
  /**
   * Usually you'd use `v.record(key, value)` instead.
   */
  constructor({
    isOptional: e,
    key: r,
    value: o
  }) {
    if (super({ isOptional: e }), m(this, "key"), m(this, "value"), m(this, "kind", "record"), r === void 0 && M("v.record()", "key"), o === void 0 && M("v.record()", "value"), r.isOptional === "optional")
      throw new Error("Record validator cannot have optional keys");
    if (o.isOptional === "optional")
      throw new Error("Record validator cannot have optional values");
    if (!r.isConvexValidator || !o.isConvexValidator)
      throw new Error("Key and value of v.record() but be validators");
    this.key = r, this.value = o;
  }
  /** @internal */
  get json() {
    return {
      type: this.kind,
      // This cast is needed because TypeScript thinks the key type is too wide
      keys: this.key.json,
      values: {
        fieldType: this.value.json,
        optional: !1
      }
    };
  }
  /** @internal */
  asOptional() {
    return new t({
      isOptional: "optional",
      key: this.key,
      value: this.value
    });
  }
}, re = class t extends g {
  static {
    n(this, "VUnion");
  }
  /**
   * Usually you'd use `v.union(...members)` instead.
   */
  constructor({ isOptional: e, members: r }) {
    super({ isOptional: e }), m(this, "members"), m(this, "kind", "union"), r.forEach((o, s) => {
      if (o === void 0 && M("v.union()", `member at index ${s}`), !o.isConvexValidator)
        throw new Error("All members of v.union() must be validators");
    }), this.members = r;
  }
  /** @internal */
  get json() {
    return {
      type: this.kind,
      value: this.members.map((e) => e.json)
    };
  }
  /** @internal */
  asOptional() {
    return new t({
      isOptional: "optional",
      members: this.members
    });
  }
};

// node_modules/convex/dist/esm/values/validator.js
function Se(t) {
  return !!t.isConvexValidator;
}
n(Se, "isValidator");
function ne(t) {
  return Se(t) ? t : u.object(t);
}
n(ne, "asObjectValidator");
var u = {
  /**
   * Validates that the value corresponds to an ID of a document in given table.
   * @param tableName The name of the table.
   */
  id: /* @__PURE__ */ n((t) => new D({
    isOptional: "required",
    tableName: t
  }), "id"),
  /**
   * Validates that the value is of type Null.
   */
  null: /* @__PURE__ */ n(() => new X({ isOptional: "required" }), "null"),
  /**
   * Validates that the value is of Convex type Float64 (Number in JS).
   *
   * Alias for `v.float64()`
   */
  number: /* @__PURE__ */ n(() => new U({ isOptional: "required" }), "number"),
  /**
   * Validates that the value is of Convex type Float64 (Number in JS).
   */
  float64: /* @__PURE__ */ n(() => new U({ isOptional: "required" }), "float64"),
  /**
   * @deprecated Use `v.int64()` instead
   */
  bigint: /* @__PURE__ */ n(() => new J({ isOptional: "required" }), "bigint"),
  /**
   * Validates that the value is of Convex type Int64 (BigInt in JS).
   */
  int64: /* @__PURE__ */ n(() => new J({ isOptional: "required" }), "int64"),
  /**
   * Validates that the value is of type Boolean.
   */
  boolean: /* @__PURE__ */ n(() => new H({ isOptional: "required" }), "boolean"),
  /**
   * Validates that the value is of type String.
   */
  string: /* @__PURE__ */ n(() => new z({ isOptional: "required" }), "string"),
  /**
   * Validates that the value is of Convex type Bytes (constructed in JS via `ArrayBuffer`).
   */
  bytes: /* @__PURE__ */ n(() => new W({ isOptional: "required" }), "bytes"),
  /**
   * Validates that the value is equal to the given literal value.
   * @param literal The literal value to compare against.
   */
  literal: /* @__PURE__ */ n((t) => new Z({ isOptional: "required", value: t }), "literal"),
  /**
   * Validates that the value is an Array of the given element type.
   * @param element The validator for the elements of the array.
   */
  array: /* @__PURE__ */ n((t) => new ee({ isOptional: "required", element: t }), "array"),
  /**
   * Validates that the value is an Object with the given properties.
   * @param fields An object specifying the validator for each property.
   */
  object: /* @__PURE__ */ n((t) => new K({ isOptional: "required", fields: t }), "object"),
  /**
   * Validates that the value is a Record with keys and values that match the given types.
   * @param keys The validator for the keys of the record. This cannot contain string literals.
   * @param values The validator for the values of the record.
   */
  record: /* @__PURE__ */ n((t, e) => new te({
    isOptional: "required",
    key: t,
    value: e
  }), "record"),
  /**
   * Validates that the value matches one of the given validators.
   * @param members The validators to match against.
   */
  union: /* @__PURE__ */ n((...t) => new re({
    isOptional: "required",
    members: t
  }), "union"),
  /**
   * Does not validate the value.
   */
  any: /* @__PURE__ */ n(() => new Y({ isOptional: "required" }), "any"),
  /**
   * Allows not specifying a value for a property in an Object.
   * @param value The property value validator to make optional.
   *
   * ```typescript
   * const objectWithOptionalFields = v.object({
   *   requiredField: v.string(),
   *   optionalField: v.optional(v.string()),
   * });
   * ```
   */
  optional: /* @__PURE__ */ n((t) => t.asOptional(), "optional"),
  /**
   * Allows specifying a value or null.
   */
  nullable: /* @__PURE__ */ n((t) => u.union(t, u.null()), "nullable")
};

// node_modules/convex/dist/esm/values/errors.js
var zt = Object.defineProperty, Xt = /* @__PURE__ */ n((t, e, r) => e in t ? zt(t, e, { enumerable: !0, configurable: !0, writable: !0, value: r }) : t[e] = r, "__defNormalProp"), Oe = /* @__PURE__ */ n((t, e, r) => Xt(t, typeof e != "symbol" ? e + "" : e, r), "__publicField"), nt, ot, Yt = Symbol.for("ConvexError"), oe = class extends (ot = Error, nt = Yt, ot) {
  static {
    n(this, "ConvexError");
  }
  constructor(e) {
    super(typeof e == "string" ? e : _(e)), Oe(this, "name", "ConvexError"), Oe(this, "data"), Oe(this, nt, !0), this.data = e;
  }
};

// node_modules/convex/dist/esm/values/compare_utf8.js
var st = /* @__PURE__ */ n(() => Array.from({ length: 4 }, () => 0), "arr"), Yr = st(), Kr = st();

// node_modules/convex/dist/esm/server/impl/syscall.js
function V(t, e) {
  if (typeof Convex > "u" || Convex.syscall === void 0)
    throw new Error(
      "The Convex database and auth objects are being used outside of a Convex backend. Did you mean to use `useQuery` or `useMutation` to call a Convex function?"
    );
  let r = Convex.syscall(t, JSON.stringify(e));
  return JSON.parse(r);
}
n(V, "performSyscall");
async function l(t, e) {
  if (typeof Convex > "u" || Convex.asyncSyscall === void 0)
    throw new Error(
      "The Convex database and auth objects are being used outside of a Convex backend. Did you mean to use `useQuery` or `useMutation` to call a Convex function?"
    );
  let r;
  try {
    r = await Convex.asyncSyscall(t, JSON.stringify(e));
  } catch (o) {
    if (o.data !== void 0) {
      let s = new oe(o.message);
      throw s.data = y(o.data), s;
    }
    throw new Error(o.message);
  }
  return JSON.parse(r);
}
n(l, "performAsyncSyscall");
function C(t, e) {
  if (typeof Convex > "u" || Convex.jsSyscall === void 0)
    throw new Error(
      "The Convex database and auth objects are being used outside of a Convex backend. Did you mean to use `useQuery` or `useMutation` to call a Convex function?"
    );
  return Convex.jsSyscall(t, e);
}
n(C, "performJsSyscall");

// node_modules/convex/dist/esm/server/router.js
var Kt = Object.defineProperty, Zt = /* @__PURE__ */ n((t, e, r) => e in t ? Kt(t, e, { enumerable: !0, configurable: !0, writable: !0, value: r }) : t[e] = r, "__defNormalProp"), $ = /* @__PURE__ */ n((t, e, r) => Zt(t, typeof e != "symbol" ? e + "" : e, r), "__publicField"), it = [
  "GET",
  "POST",
  "PUT",
  "DELETE",
  "OPTIONS",
  "PATCH"
];
function er(t) {
  return t === "HEAD" ? "GET" : t;
}
n(er, "normalizeMethod");
var tr = /* @__PURE__ */ n(() => new se(), "httpRouter"), se = class {
  static {
    n(this, "HttpRouter");
  }
  constructor() {
    $(this, "exactRoutes", /* @__PURE__ */ new Map()), $(this, "prefixRoutes", /* @__PURE__ */ new Map()), $(this, "isRouter", !0), $(this, "route", (e) => {
      if (!e.handler) throw new Error("route requires handler");
      if (!e.method) throw new Error("route requires method");
      let { method: r, handler: o } = e;
      if (!it.includes(r))
        throw new Error(
          `'${r}' is not an allowed HTTP method (like GET, POST, PUT etc.)`
        );
      if ("path" in e) {
        if ("pathPrefix" in e)
          throw new Error(
            "Invalid httpRouter route: cannot contain both 'path' and 'pathPrefix'"
          );
        if (!e.path.startsWith("/"))
          throw new Error(`path '${e.path}' does not start with a /`);
        if (e.path.startsWith("/.files/") || e.path === "/.files")
          throw new Error(`path '${e.path}' is reserved`);
        let s = this.exactRoutes.has(e.path) ? this.exactRoutes.get(e.path) : /* @__PURE__ */ new Map();
        if (s.has(r))
          throw new Error(
            `Path '${e.path}' for method ${r} already in use`
          );
        s.set(r, o), this.exactRoutes.set(e.path, s);
      } else if ("pathPrefix" in e) {
        if (!e.pathPrefix.startsWith("/"))
          throw new Error(
            `pathPrefix '${e.pathPrefix}' does not start with a /`
          );
        if (!e.pathPrefix.endsWith("/"))
          throw new Error(`pathPrefix ${e.pathPrefix} must end with a /`);
        if (e.pathPrefix.startsWith("/.files/"))
          throw new Error(`pathPrefix '${e.pathPrefix}' is reserved`);
        let s = this.prefixRoutes.get(r) || /* @__PURE__ */ new Map();
        if (s.has(e.pathPrefix))
          throw new Error(
            `${e.method} pathPrefix ${e.pathPrefix} is already defined`
          );
        s.set(e.pathPrefix, o), this.prefixRoutes.set(r, s);
      } else
        throw new Error(
          "Invalid httpRouter route entry: must contain either field 'path' or 'pathPrefix'"
        );
    }), $(this, "getRoutes", () => {
      let r = [...this.exactRoutes.keys()].sort().flatMap(
        (i) => [...this.exactRoutes.get(i).keys()].sort().map(
          (a) => [i, a, this.exactRoutes.get(i).get(a)]
        )
      ), s = [...this.prefixRoutes.keys()].sort().flatMap(
        (i) => [...this.prefixRoutes.get(i).keys()].sort().map(
          (a) => [
            `${a}*`,
            i,
            this.prefixRoutes.get(i).get(a)
          ]
        )
      );
      return [...r, ...s];
    }), $(this, "lookup", (e, r) => {
      r = er(r);
      let o = this.exactRoutes.get(e)?.get(r);
      if (o) return [o, r, e];
      let i = [...(this.prefixRoutes.get(r) || /* @__PURE__ */ new Map()).entries()].sort(
        ([a, f], [d, O]) => d.length - a.length
      );
      for (let [a, f] of i)
        if (e.startsWith(a))
          return [f, r, `${a}*`];
      return null;
    }), $(this, "runRequest", async (e, r) => {
      let o = C("requestFromConvexJson", {
        convexJson: JSON.parse(e)
      }), s = r;
      (!s || typeof s != "string") && (s = new URL(o.url).pathname);
      let i = o.method, a = this.lookup(s, i);
      if (!a) {
        let xe = new Response(`No HttpAction routed for ${s}`, {
          status: 404
        });
        return JSON.stringify(
          C("convexJsonFromResponse", { response: xe })
        );
      }
      let [f, d, O] = a, we = await f.invokeHttpAction(o);
      return JSON.stringify(
        C("convexJsonFromResponse", { response: we })
      );
    });
  }
};

// node_modules/convex/dist/esm/index.js
var w = "1.31.4";

// node_modules/convex/dist/esm/server/functionName.js
var L = Symbol.for("functionName");

// node_modules/convex/dist/esm/server/components/paths.js
var Te = Symbol.for("toReferencePath");
function rr(t) {
  return t[Te] ?? null;
}
n(rr, "extractReferencePath");
function nr(t) {
  return t.startsWith("function://");
}
n(nr, "isFunctionHandle");
function A(t) {
  let e;
  if (typeof t == "string")
    nr(t) ? e = { functionHandle: t } : e = { name: t };
  else if (t[L])
    e = { name: t[L] };
  else {
    let r = rr(t);
    if (!r)
      throw new Error(`${t} is not a functionReference`);
    e = { reference: r };
  }
  return e;
}
n(A, "getFunctionAddress");

// node_modules/convex/dist/esm/server/impl/actions_impl.js
function _e(t, e, r) {
  return {
    ...A(e),
    args: h(S(r)),
    version: w,
    requestId: t
  };
}
n(_e, "syscallArgs");
function at(t) {
  return {
    runQuery: /* @__PURE__ */ n(async (e, r) => {
      let o = await l(
        "1.0/actions/query",
        _e(t, e, r)
      );
      return y(o);
    }, "runQuery"),
    runMutation: /* @__PURE__ */ n(async (e, r) => {
      let o = await l(
        "1.0/actions/mutation",
        _e(t, e, r)
      );
      return y(o);
    }, "runMutation"),
    runAction: /* @__PURE__ */ n(async (e, r) => {
      let o = await l(
        "1.0/actions/action",
        _e(t, e, r)
      );
      return y(o);
    }, "runAction")
  };
}
n(at, "setupActionCalls");

// node_modules/convex/dist/esm/server/vector_search.js
var or = Object.defineProperty, sr = /* @__PURE__ */ n((t, e, r) => e in t ? or(t, e, { enumerable: !0, configurable: !0, writable: !0, value: r }) : t[e] = r, "__defNormalProp"), ut = /* @__PURE__ */ n((t, e, r) => sr(t, typeof e != "symbol" ? e + "" : e, r), "__publicField"), ie = class {
  static {
    n(this, "FilterExpression");
  }
  /**
   * @internal
   */
  constructor() {
    ut(this, "_isExpression"), ut(this, "_value");
  }
};

// node_modules/convex/dist/esm/server/impl/validate.js
function c(t, e, r, o) {
  if (t === void 0)
    throw new TypeError(
      `Must provide arg ${e} \`${o}\` to \`${r}\``
    );
}
n(c, "validateArg");
function ct(t, e, r, o) {
  if (!Number.isInteger(t) || t < 0)
    throw new TypeError(
      `Arg ${e} \`${o}\` to \`${r}\` must be a non-negative integer`
    );
}
n(ct, "validateArgIsNonNegativeInteger");

// node_modules/convex/dist/esm/server/impl/vector_search_impl.js
var ir = Object.defineProperty, ar = /* @__PURE__ */ n((t, e, r) => e in t ? ir(t, e, { enumerable: !0, configurable: !0, writable: !0, value: r }) : t[e] = r, "__defNormalProp"), Ce = /* @__PURE__ */ n((t, e, r) => ar(t, typeof e != "symbol" ? e + "" : e, r), "__publicField");
function lt(t) {
  return async (e, r, o) => {
    if (c(e, 1, "vectorSearch", "tableName"), c(r, 2, "vectorSearch", "indexName"), c(o, 3, "vectorSearch", "query"), !o.vector || !Array.isArray(o.vector) || o.vector.length === 0)
      throw Error("`vector` must be a non-empty Array in vectorSearch");
    return await new $e(
      t,
      e + "." + r,
      o
    ).collect();
  };
}
n(lt, "setupActionVectorSearch");
var $e = class {
  static {
    n(this, "VectorQueryImpl");
  }
  constructor(e, r, o) {
    Ce(this, "requestId"), Ce(this, "state"), this.requestId = e;
    let s = o.filter ? ae(o.filter(ur)) : null;
    this.state = {
      type: "preparing",
      query: {
        indexName: r,
        limit: o.limit,
        vector: o.vector,
        expressions: s
      }
    };
  }
  async collect() {
    if (this.state.type === "consumed")
      throw new Error("This query is closed and can't emit any more values.");
    let e = this.state.query;
    this.state = { type: "consumed" };
    let { results: r } = await l("1.0/actions/vectorSearch", {
      requestId: this.requestId,
      version: w,
      query: e
    });
    return r;
  }
}, F = class extends ie {
  static {
    n(this, "ExpressionImpl");
  }
  constructor(e) {
    super(), Ce(this, "inner"), this.inner = e;
  }
  serialize() {
    return this.inner;
  }
};
function ae(t) {
  return t instanceof F ? t.serialize() : { $literal: v(t) };
}
n(ae, "serializeExpression");
var ur = {
  //  Comparisons  /////////////////////////////////////////////////////////////
  eq(t, e) {
    if (typeof t != "string")
      throw new Error("The first argument to `q.eq` must be a field name.");
    return new F({
      $eq: [
        ae(new F({ $field: t })),
        ae(e)
      ]
    });
  },
  //  Logic  ///////////////////////////////////////////////////////////////////
  or(...t) {
    return new F({ $or: t.map(ae) });
  }
};

// node_modules/convex/dist/esm/server/impl/authentication_impl.js
function ue(t) {
  return {
    getUserIdentity: /* @__PURE__ */ n(async () => await l("1.0/getUserIdentity", {
      requestId: t
    }), "getUserIdentity")
  };
}
n(ue, "setupAuth");

// node_modules/convex/dist/esm/server/filter_builder.js
var cr = Object.defineProperty, lr = /* @__PURE__ */ n((t, e, r) => e in t ? cr(t, e, { enumerable: !0, configurable: !0, writable: !0, value: r }) : t[e] = r, "__defNormalProp"), ft = /* @__PURE__ */ n((t, e, r) => lr(t, typeof e != "symbol" ? e + "" : e, r), "__publicField"), ce = class {
  static {
    n(this, "Expression");
  }
  /**
   * @internal
   */
  constructor() {
    ft(this, "_isExpression"), ft(this, "_value");
  }
};

// node_modules/convex/dist/esm/server/impl/filter_builder_impl.js
var fr = Object.defineProperty, pr = /* @__PURE__ */ n((t, e, r) => e in t ? fr(t, e, { enumerable: !0, configurable: !0, writable: !0, value: r }) : t[e] = r, "__defNormalProp"), dr = /* @__PURE__ */ n((t, e, r) => pr(t, typeof e != "symbol" ? e + "" : e, r), "__publicField"), x = class extends ce {
  static {
    n(this, "ExpressionImpl");
  }
  constructor(e) {
    super(), dr(this, "inner"), this.inner = e;
  }
  serialize() {
    return this.inner;
  }
};
function p(t) {
  return t instanceof x ? t.serialize() : { $literal: v(t) };
}
n(p, "serializeExpression");
var pt = {
  //  Comparisons  /////////////////////////////////////////////////////////////
  eq(t, e) {
    return new x({
      $eq: [p(t), p(e)]
    });
  },
  neq(t, e) {
    return new x({
      $neq: [p(t), p(e)]
    });
  },
  lt(t, e) {
    return new x({
      $lt: [p(t), p(e)]
    });
  },
  lte(t, e) {
    return new x({
      $lte: [p(t), p(e)]
    });
  },
  gt(t, e) {
    return new x({
      $gt: [p(t), p(e)]
    });
  },
  gte(t, e) {
    return new x({
      $gte: [p(t), p(e)]
    });
  },
  //  Arithmetic  //////////////////////////////////////////////////////////////
  add(t, e) {
    return new x({
      $add: [p(t), p(e)]
    });
  },
  sub(t, e) {
    return new x({
      $sub: [p(t), p(e)]
    });
  },
  mul(t, e) {
    return new x({
      $mul: [p(t), p(e)]
    });
  },
  div(t, e) {
    return new x({
      $div: [p(t), p(e)]
    });
  },
  mod(t, e) {
    return new x({
      $mod: [p(t), p(e)]
    });
  },
  neg(t) {
    return new x({ $neg: p(t) });
  },
  //  Logic  ///////////////////////////////////////////////////////////////////
  and(...t) {
    return new x({ $and: t.map(p) });
  },
  or(...t) {
    return new x({ $or: t.map(p) });
  },
  not(t) {
    return new x({ $not: p(t) });
  },
  //  Other  ///////////////////////////////////////////////////////////////////
  field(t) {
    return new x({ $field: t });
  }
};

// node_modules/convex/dist/esm/server/index_range_builder.js
var hr = Object.defineProperty, mr = /* @__PURE__ */ n((t, e, r) => e in t ? hr(t, e, { enumerable: !0, configurable: !0, writable: !0, value: r }) : t[e] = r, "__defNormalProp"), yr = /* @__PURE__ */ n((t, e, r) => mr(t, typeof e != "symbol" ? e + "" : e, r), "__publicField"), le = class {
  static {
    n(this, "IndexRange");
  }
  /**
   * @internal
   */
  constructor() {
    yr(this, "_isIndexRange");
  }
};

// node_modules/convex/dist/esm/server/impl/index_range_builder_impl.js
var wr = Object.defineProperty, xr = /* @__PURE__ */ n((t, e, r) => e in t ? wr(t, e, { enumerable: !0, configurable: !0, writable: !0, value: r }) : t[e] = r, "__defNormalProp"), dt = /* @__PURE__ */ n((t, e, r) => xr(t, typeof e != "symbol" ? e + "" : e, r), "__publicField"), fe = class t extends le {
  static {
    n(this, "IndexRangeBuilderImpl");
  }
  constructor(e) {
    super(), dt(this, "rangeExpressions"), dt(this, "isConsumed"), this.rangeExpressions = e, this.isConsumed = !1;
  }
  static new() {
    return new t([]);
  }
  consume() {
    if (this.isConsumed)
      throw new Error(
        "IndexRangeBuilder has already been used! Chain your method calls like `q => q.eq(...).eq(...)`. See https://docs.convex.dev/using/indexes"
      );
    this.isConsumed = !0;
  }
  eq(e, r) {
    return this.consume(), new t(
      this.rangeExpressions.concat({
        type: "Eq",
        fieldPath: e,
        value: v(r)
      })
    );
  }
  gt(e, r) {
    return this.consume(), new t(
      this.rangeExpressions.concat({
        type: "Gt",
        fieldPath: e,
        value: v(r)
      })
    );
  }
  gte(e, r) {
    return this.consume(), new t(
      this.rangeExpressions.concat({
        type: "Gte",
        fieldPath: e,
        value: v(r)
      })
    );
  }
  lt(e, r) {
    return this.consume(), new t(
      this.rangeExpressions.concat({
        type: "Lt",
        fieldPath: e,
        value: v(r)
      })
    );
  }
  lte(e, r) {
    return this.consume(), new t(
      this.rangeExpressions.concat({
        type: "Lte",
        fieldPath: e,
        value: v(r)
      })
    );
  }
  export() {
    return this.consume(), this.rangeExpressions;
  }
};

// node_modules/convex/dist/esm/server/search_filter_builder.js
var gr = Object.defineProperty, br = /* @__PURE__ */ n((t, e, r) => e in t ? gr(t, e, { enumerable: !0, configurable: !0, writable: !0, value: r }) : t[e] = r, "__defNormalProp"), vr = /* @__PURE__ */ n((t, e, r) => br(t, typeof e != "symbol" ? e + "" : e, r), "__publicField"), pe = class {
  static {
    n(this, "SearchFilter");
  }
  /**
   * @internal
   */
  constructor() {
    vr(this, "_isSearchFilter");
  }
};

// node_modules/convex/dist/esm/server/impl/search_filter_builder_impl.js
var Ar = Object.defineProperty, Er = /* @__PURE__ */ n((t, e, r) => e in t ? Ar(t, e, { enumerable: !0, configurable: !0, writable: !0, value: r }) : t[e] = r, "__defNormalProp"), ht = /* @__PURE__ */ n((t, e, r) => Er(t, typeof e != "symbol" ? e + "" : e, r), "__publicField"), de = class t extends pe {
  static {
    n(this, "SearchFilterBuilderImpl");
  }
  constructor(e) {
    super(), ht(this, "filters"), ht(this, "isConsumed"), this.filters = e, this.isConsumed = !1;
  }
  static new() {
    return new t([]);
  }
  consume() {
    if (this.isConsumed)
      throw new Error(
        "SearchFilterBuilder has already been used! Chain your method calls like `q => q.search(...).eq(...)`."
      );
    this.isConsumed = !0;
  }
  search(e, r) {
    return c(e, 1, "search", "fieldName"), c(r, 2, "search", "query"), this.consume(), new t(
      this.filters.concat({
        type: "Search",
        fieldPath: e,
        value: r
      })
    );
  }
  eq(e, r) {
    return c(e, 1, "eq", "fieldName"), arguments.length !== 2 && c(r, 2, "search", "value"), this.consume(), new t(
      this.filters.concat({
        type: "Eq",
        fieldPath: e,
        value: v(r)
      })
    );
  }
  export() {
    return this.consume(), this.filters;
  }
};

// node_modules/convex/dist/esm/server/impl/query_impl.js
var Ir = Object.defineProperty, Sr = /* @__PURE__ */ n((t, e, r) => e in t ? Ir(t, e, { enumerable: !0, configurable: !0, writable: !0, value: r }) : t[e] = r, "__defNormalProp"), Ne = /* @__PURE__ */ n((t, e, r) => Sr(t, typeof e != "symbol" ? e + "" : e, r), "__publicField"), mt = 256, R = class {
  static {
    n(this, "QueryInitializerImpl");
  }
  constructor(e) {
    Ne(this, "tableName"), this.tableName = e;
  }
  withIndex(e, r) {
    c(e, 1, "withIndex", "indexName");
    let o = fe.new();
    return r !== void 0 && (o = r(o)), new N({
      source: {
        type: "IndexRange",
        indexName: this.tableName + "." + e,
        range: o.export(),
        order: null
      },
      operators: []
    });
  }
  withSearchIndex(e, r) {
    c(e, 1, "withSearchIndex", "indexName"), c(r, 2, "withSearchIndex", "searchFilter");
    let o = de.new();
    return new N({
      source: {
        type: "Search",
        indexName: this.tableName + "." + e,
        filters: r(o).export()
      },
      operators: []
    });
  }
  fullTableScan() {
    return new N({
      source: {
        type: "FullTableScan",
        tableName: this.tableName,
        order: null
      },
      operators: []
    });
  }
  order(e) {
    return this.fullTableScan().order(e);
  }
  // This is internal API and should not be exposed to developers yet.
  async count() {
    let e = await l("1.0/count", {
      table: this.tableName
    });
    return y(e);
  }
  filter(e) {
    return this.fullTableScan().filter(e);
  }
  limit(e) {
    return this.fullTableScan().limit(e);
  }
  collect() {
    return this.fullTableScan().collect();
  }
  take(e) {
    return this.fullTableScan().take(e);
  }
  paginate(e) {
    return this.fullTableScan().paginate(e);
  }
  first() {
    return this.fullTableScan().first();
  }
  unique() {
    return this.fullTableScan().unique();
  }
  [Symbol.asyncIterator]() {
    return this.fullTableScan()[Symbol.asyncIterator]();
  }
};
function yt(t) {
  throw new Error(
    t === "consumed" ? "This query is closed and can't emit any more values." : "This query has been chained with another operator and can't be reused."
  );
}
n(yt, "throwClosedError");
var N = class t {
  static {
    n(this, "QueryImpl");
  }
  constructor(e) {
    Ne(this, "state"), Ne(this, "tableNameForErrorMessages"), this.state = { type: "preparing", query: e }, e.source.type === "FullTableScan" ? this.tableNameForErrorMessages = e.source.tableName : this.tableNameForErrorMessages = e.source.indexName.split(".")[0];
  }
  takeQuery() {
    if (this.state.type !== "preparing")
      throw new Error(
        "A query can only be chained once and can't be chained after iteration begins."
      );
    let e = this.state.query;
    return this.state = { type: "closed" }, e;
  }
  startQuery() {
    if (this.state.type === "executing")
      throw new Error("Iteration can only begin on a query once.");
    (this.state.type === "closed" || this.state.type === "consumed") && yt(this.state.type);
    let e = this.state.query, { queryId: r } = V("1.0/queryStream", { query: e, version: w });
    return this.state = { type: "executing", queryId: r }, r;
  }
  closeQuery() {
    if (this.state.type === "executing") {
      let e = this.state.queryId;
      V("1.0/queryCleanup", { queryId: e });
    }
    this.state = { type: "consumed" };
  }
  order(e) {
    c(e, 1, "order", "order");
    let r = this.takeQuery();
    if (r.source.type === "Search")
      throw new Error(
        "Search queries must always be in relevance order. Can not set order manually."
      );
    if (r.source.order !== null)
      throw new Error("Queries may only specify order at most once");
    return r.source.order = e, new t(r);
  }
  filter(e) {
    c(e, 1, "filter", "predicate");
    let r = this.takeQuery();
    if (r.operators.length >= mt)
      throw new Error(
        `Can't construct query with more than ${mt} operators`
      );
    return r.operators.push({
      filter: p(e(pt))
    }), new t(r);
  }
  limit(e) {
    c(e, 1, "limit", "n");
    let r = this.takeQuery();
    return r.operators.push({ limit: e }), new t(r);
  }
  [Symbol.asyncIterator]() {
    return this.startQuery(), this;
  }
  async next() {
    (this.state.type === "closed" || this.state.type === "consumed") && yt(this.state.type);
    let e = this.state.type === "preparing" ? this.startQuery() : this.state.queryId, { value: r, done: o } = await l("1.0/queryStreamNext", {
      queryId: e
    });
    return o && this.closeQuery(), { value: y(r), done: o };
  }
  return() {
    return this.closeQuery(), Promise.resolve({ done: !0, value: void 0 });
  }
  async paginate(e) {
    if (c(e, 1, "paginate", "options"), typeof e?.numItems != "number" || e.numItems < 0)
      throw new Error(
        `\`options.numItems\` must be a positive number. Received \`${e?.numItems}\`.`
      );
    let r = this.takeQuery(), o = e.numItems, s = e.cursor, i = e?.endCursor ?? null, a = e.maximumRowsRead ?? null, { page: f, isDone: d, continueCursor: O, splitCursor: we, pageStatus: xe } = await l("1.0/queryPage", {
      query: r,
      cursor: s,
      endCursor: i,
      pageSize: o,
      maximumRowsRead: a,
      maximumBytesRead: e.maximumBytesRead,
      version: w
    });
    return {
      page: f.map((Nt) => y(Nt)),
      isDone: d,
      continueCursor: O,
      splitCursor: we,
      pageStatus: xe
    };
  }
  async collect() {
    let e = [];
    for await (let r of this)
      e.push(r);
    return e;
  }
  async take(e) {
    return c(e, 1, "take", "n"), ct(e, 1, "take", "n"), this.limit(e).collect();
  }
  async first() {
    let e = await this.take(1);
    return e.length === 0 ? null : e[0];
  }
  async unique() {
    let e = await this.take(2);
    if (e.length === 0)
      return null;
    if (e.length === 2)
      throw new Error(`unique() query returned more than one result from table ${this.tableNameForErrorMessages}:
 [${e[0]._id}, ${e[1]._id}, ...]`);
    return e[0];
  }
};

// node_modules/convex/dist/esm/server/impl/database_impl.js
async function Pe(t, e, r) {
  if (c(e, 1, "get", "id"), typeof e != "string")
    throw new Error(
      `Invalid argument \`id\` for \`db.get\`, expected string but got '${typeof e}': ${e}`
    );
  let o = {
    id: h(e),
    isSystem: r,
    version: w,
    table: t
  }, s = await l("1.0/get", o);
  return y(s);
}
n(Pe, "get");
function je() {
  let t = /* @__PURE__ */ n((s = !1) => ({
    get: /* @__PURE__ */ n(async (i, a) => a !== void 0 ? await Pe(i, a, s) : await Pe(void 0, i, s), "get"),
    query: /* @__PURE__ */ n((i) => new k(i, s).query(), "query"),
    normalizeId: /* @__PURE__ */ n((i, a) => {
      c(i, 1, "normalizeId", "tableName"), c(a, 2, "normalizeId", "id");
      let f = i.startsWith("_");
      if (f !== s)
        throw new Error(
          `${f ? "System" : "User"} tables can only be accessed from db.${s ? "" : "system."}normalizeId().`
        );
      let d = V("1.0/db/normalizeId", {
        table: i,
        idString: a
      });
      return y(d).id;
    }, "normalizeId"),
    // We set the system reader on the next line
    system: null,
    table: /* @__PURE__ */ n((i) => new k(i, s), "table")
  }), "reader"), { system: e, ...r } = t(!0), o = t();
  return o.system = r, o;
}
n(je, "setupReader");
async function wt(t, e) {
  if (t.startsWith("_"))
    throw new Error("System tables (prefixed with `_`) are read-only.");
  c(t, 1, "insert", "table"), c(e, 2, "insert", "value");
  let r = await l("1.0/insert", {
    table: t,
    value: h(e)
  });
  return y(r)._id;
}
n(wt, "insert");
async function Fe(t, e, r) {
  c(e, 1, "patch", "id"), c(r, 2, "patch", "value"), await l("1.0/shallowMerge", {
    id: h(e),
    value: rt(r),
    table: t
  });
}
n(Fe, "patch");
async function Re(t, e, r) {
  c(e, 1, "replace", "id"), c(r, 2, "replace", "value"), await l("1.0/replace", {
    id: h(e),
    value: h(r),
    table: t
  });
}
n(Re, "replace");
async function qe(t, e) {
  c(e, 1, "delete", "id"), await l("1.0/remove", {
    id: h(e),
    table: t
  });
}
n(qe, "delete_");
function xt() {
  let t = je();
  return {
    get: t.get,
    query: t.query,
    normalizeId: t.normalizeId,
    system: t.system,
    insert: /* @__PURE__ */ n(async (e, r) => await wt(e, r), "insert"),
    patch: /* @__PURE__ */ n(async (e, r, o) => o !== void 0 ? await Fe(e, r, o) : await Fe(void 0, e, r), "patch"),
    replace: /* @__PURE__ */ n(async (e, r, o) => o !== void 0 ? await Re(e, r, o) : await Re(void 0, e, r), "replace"),
    delete: /* @__PURE__ */ n(async (e, r) => r !== void 0 ? await qe(e, r) : await qe(void 0, e), "delete"),
    table: /* @__PURE__ */ n((e) => new Be(e, !1), "table")
  };
}
n(xt, "setupWriter");
var k = class {
  static {
    n(this, "TableReader");
  }
  constructor(e, r) {
    this.tableName = e, this.isSystem = r;
  }
  async get(e) {
    return Pe(this.tableName, e, this.isSystem);
  }
  query() {
    let e = this.tableName.startsWith("_");
    if (e !== this.isSystem)
      throw new Error(
        `${e ? "System" : "User"} tables can only be accessed from db.${this.isSystem ? "" : "system."}query().`
      );
    return new R(this.tableName);
  }
}, Be = class extends k {
  static {
    n(this, "TableWriter");
  }
  async insert(e) {
    return wt(this.tableName, e);
  }
  async patch(e, r) {
    return Fe(this.tableName, e, r);
  }
  async replace(e, r) {
    return Re(this.tableName, e, r);
  }
  async delete(e) {
    return qe(this.tableName, e);
  }
};

// node_modules/convex/dist/esm/server/impl/scheduler_impl.js
function gt() {
  return {
    runAfter: /* @__PURE__ */ n(async (t, e, r) => {
      let o = vt(t, e, r);
      return await l("1.0/schedule", o);
    }, "runAfter"),
    runAt: /* @__PURE__ */ n(async (t, e, r) => {
      let o = At(
        t,
        e,
        r
      );
      return await l("1.0/schedule", o);
    }, "runAt"),
    cancel: /* @__PURE__ */ n(async (t) => {
      c(t, 1, "cancel", "id");
      let e = { id: h(t) };
      await l("1.0/cancel_job", e);
    }, "cancel")
  };
}
n(gt, "setupMutationScheduler");
function bt(t) {
  return {
    runAfter: /* @__PURE__ */ n(async (e, r, o) => {
      let s = {
        requestId: t,
        ...vt(e, r, o)
      };
      return await l("1.0/actions/schedule", s);
    }, "runAfter"),
    runAt: /* @__PURE__ */ n(async (e, r, o) => {
      let s = {
        requestId: t,
        ...At(e, r, o)
      };
      return await l("1.0/actions/schedule", s);
    }, "runAt"),
    cancel: /* @__PURE__ */ n(async (e) => {
      c(e, 1, "cancel", "id");
      let r = { id: h(e) };
      return await l("1.0/actions/cancel_job", r);
    }, "cancel")
  };
}
n(bt, "setupActionScheduler");
function vt(t, e, r) {
  if (typeof t != "number")
    throw new Error("`delayMs` must be a number");
  if (!isFinite(t))
    throw new Error("`delayMs` must be a finite number");
  if (t < 0)
    throw new Error("`delayMs` must be non-negative");
  let o = S(r), s = A(e), i = (Date.now() + t) / 1e3;
  return {
    ...s,
    ts: i,
    args: h(o),
    version: w
  };
}
n(vt, "runAfterSyscallArgs");
function At(t, e, r) {
  let o;
  if (t instanceof Date)
    o = t.valueOf() / 1e3;
  else if (typeof t == "number")
    o = t / 1e3;
  else
    throw new Error("The invoke time must a Date or a timestamp");
  let s = A(e), i = S(r);
  return {
    ...s,
    ts: o,
    args: h(i),
    version: w
  };
}
n(At, "runAtSyscallArgs");

// node_modules/convex/dist/esm/server/impl/storage_impl.js
function Me(t) {
  return {
    getUrl: /* @__PURE__ */ n(async (e) => (c(e, 1, "getUrl", "storageId"), await l("1.0/storageGetUrl", {
      requestId: t,
      version: w,
      storageId: e
    })), "getUrl"),
    getMetadata: /* @__PURE__ */ n(async (e) => await l("1.0/storageGetMetadata", {
      requestId: t,
      version: w,
      storageId: e
    }), "getMetadata")
  };
}
n(Me, "setupStorageReader");
function Ue(t) {
  let e = Me(t);
  return {
    generateUploadUrl: /* @__PURE__ */ n(async () => await l("1.0/storageGenerateUploadUrl", {
      requestId: t,
      version: w
    }), "generateUploadUrl"),
    delete: /* @__PURE__ */ n(async (r) => {
      await l("1.0/storageDelete", {
        requestId: t,
        version: w,
        storageId: r
      });
    }, "delete"),
    getUrl: e.getUrl,
    getMetadata: e.getMetadata
  };
}
n(Ue, "setupStorageWriter");
function Et(t) {
  return {
    ...Ue(t),
    store: /* @__PURE__ */ n(async (r, o) => await C("storage/storeBlob", {
      requestId: t,
      version: w,
      blob: r,
      options: o
    }), "store"),
    get: /* @__PURE__ */ n(async (r) => await C("storage/getBlob", {
      requestId: t,
      version: w,
      storageId: r
    }), "get")
  };
}
n(Et, "setupStorageActionWriter");

// node_modules/convex/dist/esm/server/impl/registration_impl.js
async function It(t, e) {
  let o = y(JSON.parse(e)), s = {
    db: xt(),
    auth: ue(""),
    storage: Ue(""),
    scheduler: gt(),
    runQuery: /* @__PURE__ */ n((a, f) => Je("query", a, f), "runQuery"),
    runMutation: /* @__PURE__ */ n((a, f) => Je("mutation", a, f), "runMutation")
  }, i = await Ve(t, s, o);
  return St(i), JSON.stringify(h(i === void 0 ? null : i));
}
n(It, "invokeMutation");
function St(t) {
  if (t instanceof R || t instanceof N)
    throw new Error(
      "Return value is a Query. Results must be retrieved with `.collect()`, `.take(n), `.unique()`, or `.first()`."
    );
}
n(St, "validateReturnValue");
async function Ve(t, e, r) {
  let o;
  try {
    o = await Promise.resolve(t(e, ...r));
  } catch (s) {
    throw Or(s);
  }
  return o;
}
n(Ve, "invokeFunction");
function G(t, e) {
  return (r, o) => (globalThis.console.warn(
    `Convex functions should not directly call other Convex functions. Consider calling a helper function instead. e.g. \`export const foo = ${t}(...); await foo(ctx);\` is not supported. See https://docs.convex.dev/production/best-practices/#use-helper-functions-to-write-shared-code`
  ), e(r, o));
}
n(G, "dontCallDirectly");
function Or(t) {
  if (typeof t == "object" && t !== null && Symbol.for("ConvexError") in t) {
    let e = t;
    return e.data = JSON.stringify(
      h(e.data === void 0 ? null : e.data)
    ), e.ConvexErrorSymbol = Symbol.for("ConvexError"), e;
  } else
    return t;
}
n(Or, "serializeConvexErrorData");
function Q() {
  if (typeof window > "u" || window.__convexAllowFunctionsInBrowser)
    return;
  (Object.getOwnPropertyDescriptor(globalThis, "window")?.get?.toString().includes("[native code]") ?? !1) && console.error(
    "Convex functions should not be imported in the browser. This will throw an error in future versions of `convex`. If this is a false negative, please report it to Convex support."
  );
}
n(Q, "assertNotBrowser");
function Ot(t, e) {
  if (e === void 0)
    throw new Error(
      `A validator is undefined for field "${t}". This is often caused by circular imports. See https://docs.convex.dev/error#undefined-validator for details.`
    );
  return e;
}
n(Ot, "strictReplacer");
function he(t) {
  return () => {
    let e = u.any();
    return typeof t == "object" && t.args !== void 0 && (e = ne(t.args)), JSON.stringify(e.json, Ot);
  };
}
n(he, "exportArgs");
function me(t) {
  return () => {
    let e;
    return typeof t == "object" && t.returns !== void 0 && (e = ne(t.returns)), JSON.stringify(e ? e.json : null, Ot);
  };
}
n(me, "exportReturns");
var Le = /* @__PURE__ */ n(((t) => {
  let e = typeof t == "function" ? t : t.handler, r = G("mutation", e);
  return Q(), r.isMutation = !0, r.isPublic = !0, r.invokeMutation = (o) => It(e, o), r.exportArgs = he(t), r.exportReturns = me(t), r._handler = e, r;
}), "mutationGeneric"), ke = /* @__PURE__ */ n(((t) => {
  let e = typeof t == "function" ? t : t.handler, r = G(
    "internalMutation",
    e
  );
  return Q(), r.isMutation = !0, r.isInternal = !0, r.invokeMutation = (o) => It(e, o), r.exportArgs = he(t), r.exportReturns = me(t), r._handler = e, r;
}), "internalMutationGeneric");
async function Tt(t, e) {
  let o = y(JSON.parse(e)), s = {
    db: je(),
    auth: ue(""),
    storage: Me(""),
    runQuery: /* @__PURE__ */ n((a, f) => Je("query", a, f), "runQuery")
  }, i = await Ve(t, s, o);
  return St(i), JSON.stringify(h(i === void 0 ? null : i));
}
n(Tt, "invokeQuery");
var Ge = /* @__PURE__ */ n(((t) => {
  let e = typeof t == "function" ? t : t.handler, r = G("query", e);
  return Q(), r.isQuery = !0, r.isPublic = !0, r.invokeQuery = (o) => Tt(e, o), r.exportArgs = he(t), r.exportReturns = me(t), r._handler = e, r;
}), "queryGeneric"), Qe = /* @__PURE__ */ n(((t) => {
  let e = typeof t == "function" ? t : t.handler, r = G("internalQuery", e);
  return Q(), r.isQuery = !0, r.isInternal = !0, r.invokeQuery = (o) => Tt(e, o), r.exportArgs = he(t), r.exportReturns = me(t), r._handler = e, r;
}), "internalQueryGeneric");
async function Tr(t, e) {
  let s = {
    ...at(""),
    auth: ue(""),
    storage: Et(""),
    scheduler: bt(""),
    vectorSearch: lt("")
  };
  return await Ve(t, s, [e]);
}
n(Tr, "invokeHttpAction");
var De = /* @__PURE__ */ n((t) => {
  let e = G("httpAction", t);
  return Q(), e.isHttp = !0, e.invokeHttpAction = (r) => Tr(t, r), e._handler = t, e;
}, "httpActionGeneric");
async function Je(t, e, r) {
  let o = S(r), s = {
    udfType: t,
    args: h(o),
    ...A(e)
  }, i = await l("1.0/runUdf", s);
  return y(i);
}
n(Je, "runUdf");

// node_modules/convex/dist/esm/server/pagination.js
var rs = u.object({
  numItems: u.number(),
  cursor: u.union(u.string(), u.null()),
  endCursor: u.optional(u.union(u.string(), u.null())),
  id: u.optional(u.number()),
  maximumRowsRead: u.optional(u.number()),
  maximumBytesRead: u.optional(u.number())
});

// node_modules/convex/dist/esm/server/api.js
function _t(t = []) {
  let e = {
    get(r, o) {
      if (typeof o == "string") {
        let s = [...t, o];
        return _t(s);
      } else if (o === L) {
        if (t.length < 2) {
          let a = ["api", ...t].join(".");
          throw new Error(
            `API path is expected to be of the form \`api.moduleName.functionName\`. Found: \`${a}\``
          );
        }
        let s = t.slice(0, -1).join("/"), i = t[t.length - 1];
        return i === "default" ? s : s + ":" + i;
      } else return o === Symbol.toStringTag ? "FunctionReference" : void 0;
    }
  };
  return new Proxy({}, e);
}
n(_t, "createApi");
var _r = _t();

// node_modules/convex/dist/esm/server/components/index.js
function Ct(t, e) {
  let r = {
    get(o, s) {
      if (typeof s == "string") {
        let i = [...e, s];
        return Ct(t, i);
      } else if (s === Te) {
        if (e.length < 1) {
          let i = [t, ...e].join(".");
          throw new Error(
            `API path is expected to be of the form \`${t}.childComponent.functionName\`. Found: \`${i}\``
          );
        }
        return "_reference/childComponent/" + e.join("/");
      } else
        return;
    }
  };
  return new Proxy({}, r);
}
n(Ct, "createChildComponents");
var $r = /* @__PURE__ */ n(() => Ct("components", []), "componentsGeneric");

// node_modules/convex/dist/esm/server/schema.js
var Nr = Object.defineProperty, Pr = /* @__PURE__ */ n((t, e, r) => e in t ? Nr(t, e, { enumerable: !0, configurable: !0, writable: !0, value: r }) : t[e] = r, "__defNormalProp"), I = /* @__PURE__ */ n((t, e, r) => Pr(t, typeof e != "symbol" ? e + "" : e, r), "__publicField"), ye = class {
  static {
    n(this, "TableDefinition");
  }
  /**
   * @internal
   */
  constructor(e) {
    I(this, "indexes"), I(this, "stagedDbIndexes"), I(this, "searchIndexes"), I(this, "stagedSearchIndexes"), I(this, "vectorIndexes"), I(this, "stagedVectorIndexes"), I(this, "validator"), this.indexes = [], this.stagedDbIndexes = [], this.searchIndexes = [], this.stagedSearchIndexes = [], this.vectorIndexes = [], this.stagedVectorIndexes = [], this.validator = e;
  }
  /**
   * This API is experimental: it may change or disappear.
   *
   * Returns indexes defined on this table.
   * Intended for the advanced use cases of dynamically deciding which index to use for a query.
   * If you think you need this, please chime in on ths issue in the Convex JS GitHub repo.
   * https://github.com/get-convex/convex-js/issues/49
   */
  " indexes"() {
    return this.indexes;
  }
  index(e, r) {
    return Array.isArray(r) ? this.indexes.push({
      indexDescriptor: e,
      fields: r
    }) : r.staged ? this.stagedDbIndexes.push({
      indexDescriptor: e,
      fields: r.fields
    }) : this.indexes.push({
      indexDescriptor: e,
      fields: r.fields
    }), this;
  }
  searchIndex(e, r) {
    return r.staged ? this.stagedSearchIndexes.push({
      indexDescriptor: e,
      searchField: r.searchField,
      filterFields: r.filterFields || []
    }) : this.searchIndexes.push({
      indexDescriptor: e,
      searchField: r.searchField,
      filterFields: r.filterFields || []
    }), this;
  }
  vectorIndex(e, r) {
    return r.staged ? this.stagedVectorIndexes.push({
      indexDescriptor: e,
      vectorField: r.vectorField,
      dimensions: r.dimensions,
      filterFields: r.filterFields || []
    }) : this.vectorIndexes.push({
      indexDescriptor: e,
      vectorField: r.vectorField,
      dimensions: r.dimensions,
      filterFields: r.filterFields || []
    }), this;
  }
  /**
   * Work around for https://github.com/microsoft/TypeScript/issues/57035
   */
  self() {
    return this;
  }
  /**
   * Export the contents of this definition.
   *
   * This is called internally by the Convex framework.
   * @internal
   */
  export() {
    let e = this.validator.json;
    if (typeof e != "object")
      throw new Error(
        "Invalid validator: please make sure that the parameter of `defineTable` is valid (see https://docs.convex.dev/database/schemas)"
      );
    return {
      indexes: this.indexes,
      stagedDbIndexes: this.stagedDbIndexes,
      searchIndexes: this.searchIndexes,
      stagedSearchIndexes: this.stagedSearchIndexes,
      vectorIndexes: this.vectorIndexes,
      stagedVectorIndexes: this.stagedVectorIndexes,
      documentType: e
    };
  }
};
function He(t) {
  return Se(t) ? new ye(t) : new ye(u.object(t));
}
n(He, "defineTable");
var We = class {
  static {
    n(this, "SchemaDefinition");
  }
  /**
   * @internal
   */
  constructor(e, r) {
    I(this, "tables"), I(this, "strictTableNameTypes"), I(this, "schemaValidation"), this.tables = e, this.schemaValidation = r?.schemaValidation === void 0 ? !0 : r.schemaValidation;
  }
  /**
   * Export the contents of this definition.
   *
   * This is called internally by the Convex framework.
   * @internal
   */
  export() {
    return JSON.stringify({
      tables: Object.entries(this.tables).map(([e, r]) => {
        let {
          indexes: o,
          stagedDbIndexes: s,
          searchIndexes: i,
          stagedSearchIndexes: a,
          vectorIndexes: f,
          stagedVectorIndexes: d,
          documentType: O
        } = r.export();
        return {
          tableName: e,
          indexes: o,
          stagedDbIndexes: s,
          searchIndexes: i,
          stagedSearchIndexes: a,
          vectorIndexes: f,
          stagedVectorIndexes: d,
          documentType: O
        };
      }),
      schemaValidation: this.schemaValidation
    });
  }
};
function $t(t, e) {
  return new We(t, e);
}
n($t, "defineSchema");
var Es = $t({
  _scheduled_functions: He({
    name: u.string(),
    args: u.array(u.any()),
    scheduledTime: u.float64(),
    completedTime: u.optional(u.float64()),
    state: u.union(
      u.object({ kind: u.literal("pending") }),
      u.object({ kind: u.literal("inProgress") }),
      u.object({ kind: u.literal("success") }),
      u.object({ kind: u.literal("failed"), error: u.string() }),
      u.object({ kind: u.literal("canceled") })
    )
  }),
  _storage: He({
    sha256: u.string(),
    size: u.float64(),
    contentType: u.optional(u.string())
  })
});

// convex/_generated/server.js
var Hs = Ge, Ws = Qe, zs = Le, Xs = ke;
var Ys = De;

export {
  n as a,
  u as b,
  _r as c,
  tr as d,
  $r as e,
  Hs as f,
  Ws as g,
  zs as h,
  Xs as i,
  Ys as j
};
//# sourceMappingURL=P4Y5ARCJ.js.map
