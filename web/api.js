/**
 * Noisett API Client
 * Thin wrapper over fetch - all business logic is on the server.
 */
const API = {
  baseUrl: "/api",

  /**
   * Make API request.
   * @param {string} method - HTTP method
   * @param {string} path - API path
   * @param {object} body - Request body (optional)
   * @returns {Promise<object>} - Response data
   */
  async request(method, path, body = null) {
    const options = {
      method,
      headers: {
        "Content-Type": "application/json",
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${this.baseUrl}${path}`, options);
    const data = await response.json();

    // Server returns CommandResult format
    if (!data.success && data.error) {
      const error = new Error(data.error.message);
      error.code = data.error.code;
      error.suggestion = data.error.suggestion;
      throw error;
    }

    return data;
  },

  // --- Commands (mirror server commands) ---

  /**
   * Generate images from prompt.
   * @param {string} prompt - Text description
   * @param {string} assetType - Asset type (product, icons, logo, premium)
   * @param {string} quality - Quality preset (draft, standard, high)
   * @param {number} count - Number of variations (1-4)
   * @returns {Promise<object>} - Job information
   */
  async generate(
    prompt,
    assetType = "product",
    quality = "standard",
    count = 4
  ) {
    return this.request("POST", "/generate", {
      prompt,
      asset_type: assetType,
      quality,
      count,
    });
  },

  /**
   * Get job status.
   * @param {string} jobId - Job ID
   * @returns {Promise<object>} - Job status and images
   */
  async getJobStatus(jobId) {
    return this.request("GET", `/jobs/${jobId}`);
  },

  /**
   * Cancel a running job.
   * @param {string} jobId - Job ID
   * @returns {Promise<object>} - Cancellation result
   */
  async cancelJob(jobId) {
    return this.request("DELETE", `/jobs/${jobId}`);
  },

  /**
   * Get available asset types.
   * @returns {Promise<object>} - Asset types
   */
  async getAssetTypes() {
    return this.request("GET", "/asset-types");
  },

  /**
   * Get available models.
   * @returns {Promise<object>} - Models
   */
  async getModels() {
    return this.request("GET", "/models");
  },

  /**
   * Check API health.
   * @returns {Promise<object>} - Health status
   */
  async health() {
    const response = await fetch("/health");
    return response.json();
  },
};
