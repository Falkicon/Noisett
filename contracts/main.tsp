/**
 * Noisett API Contracts
 * 
 * Single source of truth for all API schemas.
 * All layers (Python, TypeScript, Convex) are generated from these definitions.
 */

import "@typespec/http";
import "@typespec/rest";
import "@typespec/openapi3";

// Import model definitions
import "./models/common.tsp";
import "./models/asset-type.tsp";
import "./models/lora.tsp";
import "./models/job.tsp";
import "./models/generation.tsp";

using TypeSpec.Http;
using TypeSpec.Rest;

@service
namespace Noisett {
  @route("/api")
  namespace Api {
    // Operations would go here
  }
}
