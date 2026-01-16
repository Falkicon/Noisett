/**
 * Common types used across the API
 */
namespace Noisett.Models;

@doc("Standard API response wrapper")
model ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
}

@doc("API error details")
model ApiError {
  code?: string;
  message: string;
  suggestion?: string;
}

@doc("Convex document ID (opaque string)")
scalar ConvexId extends string;

@doc("Convex storage ID for uploaded files")
scalar StorageId extends string;

@doc("Unix timestamp in milliseconds")
scalar Timestamp extends int64;
