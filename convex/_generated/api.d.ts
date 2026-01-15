/* eslint-disable */
/**
 * Generated `api` utility.
 *
 * THIS CODE IS AUTOMATICALLY GENERATED.
 *
 * To regenerate, run `npx convex dev`.
 * @module
 */

import type * as assetTypes from "../assetTypes.js";
import type * as generations from "../generations.js";
import type * as http from "../http.js";
import type * as loras from "../loras.js";
import type * as trainingImages from "../trainingImages.js";
import type * as webhookEvents from "../webhookEvents.js";

import type {
  ApiFromModules,
  FilterApi,
  FunctionReference,
} from "convex/server";

declare const fullApi: ApiFromModules<{
  assetTypes: typeof assetTypes;
  generations: typeof generations;
  http: typeof http;
  loras: typeof loras;
  trainingImages: typeof trainingImages;
  webhookEvents: typeof webhookEvents;
}>;

/**
 * A utility for referencing Convex functions in your app's public API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = api.myModule.myFunction;
 * ```
 */
export declare const api: FilterApi<
  typeof fullApi,
  FunctionReference<any, "public">
>;

/**
 * A utility for referencing Convex functions in your app's internal API.
 *
 * Usage:
 * ```js
 * const myFunctionReference = internal.myModule.myFunction;
 * ```
 */
export declare const internal: FilterApi<
  typeof fullApi,
  FunctionReference<any, "internal">
>;

export declare const components: {};
