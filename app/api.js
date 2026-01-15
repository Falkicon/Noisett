/**
 * Noisett API Client
 * Complete API surface for all backend endpoints
 */
const API = {
  baseUrl: 'http://localhost:8000',
  convexUrl: 'https://neighborly-gazelle-692.convex.site',

  /**
   * Make an API request and return CommandResult format.
   * @returns {{ success: boolean, data?: any, error?: { code: string, message: string, suggestion: string } }}
   */
  async request(method, path, body = null) {
    const options = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (body) options.body = JSON.stringify(body);

    try {
      const response = await fetch(`${this.baseUrl}${path}`, options);
      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: {
            code: `HTTP_${response.status}`,
            message: data.detail || 'Request failed',
            suggestion: response.status === 404
              ? 'Check that the endpoint exists and the server is running'
              : response.status >= 500
                ? 'The server encountered an error. Try again or check server logs'
                : 'Check your request parameters and try again',
          },
        };
      }

      // Backend already returns CommandResult format
      if (data.success === false && data.error) {
        return {
          success: false,
          error: {
            code: data.error.code || 'BACKEND_ERROR',
            message: data.error.message || 'Operation failed',
            suggestion: data.error.suggestion || 'Check the error details and try again',
          },
        };
      }

      // Success - wrap raw data in CommandResult
      return {
        success: true,
        data: data.data !== undefined ? data.data : data,
      };
    } catch (err) {
      return {
        success: false,
        error: {
          code: 'NETWORK_ERROR',
          message: err.message || 'Network request failed',
          suggestion: 'Check your network connection and ensure the server is running',
        },
      };
    }
  },

  // === Health ===
  async health() {
    return this.request('GET', '/health');
  },

  // === Generation ===
  async generate(prompt, assetType = 'product', quality = 'standard', count = 1, lora = null) {
    const body = { prompt, asset_type: assetType, quality, count };
    if (lora) body.lora = lora;
    return this.request('POST', '/api/generate', body);
  },

  async getJob(jobId) {
    return this.request('GET', `/api/jobs/${jobId}`);
  },

  async cancelJob(jobId) {
    return this.request('DELETE', `/api/jobs/${jobId}`);
  },

  async listJobs(limit = 50, status = null) {
    let path = `/api/jobs?limit=${limit}`;
    if (status) path += `&status=${status}`;
    return this.request('GET', path);
  },

  // === Asset Types (Convex) ===
  async getAssetTypes() {
    return ConvexAPI.listAssetTypes();
  },

  async getAssetType(id) {
    return ConvexAPI.getAssetType(id);
  },

  async getModels() {
    return this.request('GET', '/api/models');
  },

  // === Generations (Convex) ===
  async createGeneration(data) {
    return ConvexAPI.createGeneration(data);
  },

  async listGenerations(favorite = undefined) {
    return ConvexAPI.listGenerations(favorite);
  },

  async toggleGenerationFavorite(id) {
    return ConvexAPI.toggleFavorite(id);
  },

  async deleteGeneration(id) {
    return ConvexAPI.deleteGeneration(id);
  },

  // === LoRAs ===
  async listLoras() {
    return this.request('GET', '/api/loras');
  },

  async createLora(name, triggerWord, baseModel = 'flux', steps = 1000) {
    return this.request('POST', '/api/loras', {
      name,
      trigger_word: triggerWord,
      base_model: baseModel,
      steps,
    });
  },

  async getLora(loraId) {
    return this.request('GET', `/api/loras/${loraId}`);
  },

  async getUploadUrl(loraId) {
    return this.request('POST', `/api/lora/${loraId}/upload-url`);
  },

  async uploadImage(uploadUrl, file) {
    try {
      const response = await fetch(uploadUrl, {
        method: 'POST',
        body: file,
      });
      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: {
            code: 'UPLOAD_FAILED',
            message: 'Failed to upload image',
            suggestion: 'Check file size and format, then try again',
          },
        };
      }

      return { success: true, data };
    } catch (err) {
      return {
        success: false,
        error: {
          code: 'UPLOAD_ERROR',
          message: err.message || 'Upload failed',
          suggestion: 'Check your network connection and try again',
        },
      };
    }
  },

  async deleteLora(loraId) {
    return this.request('DELETE', `/api/loras/${loraId}`);
  },

  // SSE for training progress
  subscribeToTraining(loraId, onEvent) {
    const eventSource = new EventSource(`${this.baseUrl}/api/lora/${loraId}/events`);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onEvent(data);
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
    };

    return eventSource;
  },

  // === History ===
  async getHistory(limit = 50, status = null) {
    let path = `/api/history?limit=${limit}`;
    if (status) path += `&status=${status}`;
    return this.request('GET', path);
  },

  async deleteHistoryItem(jobId) {
    return this.request('DELETE', `/api/history/${jobId}`);
  },

  // === Favorites ===
  async getFavorites(limit = 50) {
    return this.request('GET', `/api/favorites?limit=${limit}`);
  },

  async addFavorite(jobId, imageIndex) {
    return this.request('POST', '/api/favorites', { job_id: jobId, image_index: imageIndex });
  },

  async removeFavorite(jobId, imageIndex) {
    return this.request('DELETE', `/api/favorites/${jobId}/${imageIndex}`);
  },
};

// Direct Convex calls for LoRA management
const ConvexAPI = {
  baseUrl: 'https://neighborly-gazelle-692.convex.site',

  /**
   * Make a Convex API request and return CommandResult format.
   * @returns {{ success: boolean, data?: any, error?: { code: string, message: string, suggestion: string } }}
   */
  async request(method, path, body = null) {
    const options = { method };
    if (body) {
      options.headers = { 'Content-Type': 'application/json' };
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(`${this.baseUrl}${path}`, options);
      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: {
            code: `CONVEX_HTTP_${response.status}`,
            message: data.message || 'Convex request failed',
            suggestion: 'Check Convex deployment status and try again',
          },
        };
      }

      return { success: true, data };
    } catch (err) {
      return {
        success: false,
        error: {
          code: 'CONVEX_ERROR',
          message: err.message || 'Convex request failed',
          suggestion: 'Check your network connection and Convex status',
        },
      };
    }
  },

  async listLoras() {
    return this.request('GET', '/api/loras/list');
  },

  async createLora(data) {
    return this.request('POST', '/api/loras/create', data);
  },

  async getLora(id) {
    return this.request('GET', `/api/loras/get?id=${id}`);
  },

  async deleteLora(id) {
    return this.request('DELETE', `/api/loras/delete?id=${id}`);
  },

  async generateUploadUrl() {
    return this.request('POST', '/api/storage/generate-upload-url');
  },

  // === Generations ===
  async listGenerations(favorite = undefined) {
    let path = '/api/generations/list';
    if (favorite !== undefined) {
      path += `?favorite=${favorite}`;
    }
    return this.request('GET', path);
  },

  async createGeneration(data) {
    return this.request('POST', '/api/generations/create', data);
  },

  async toggleFavorite(id) {
    return this.request('POST', '/api/generations/toggle-favorite', { id });
  },

  async deleteGeneration(id) {
    return this.request('DELETE', `/api/generations/delete?id=${id}`);
  },

  async getGeneration(id) {
    return this.request('GET', `/api/generations/get?id=${id}`);
  },

  // === Asset Types ===
  async listAssetTypes(activeOnly = true) {
    const path = activeOnly ? '/api/asset-types/list?activeOnly=true' : '/api/asset-types/list';
    return this.request('GET', path);
  },

  async getAssetType(id) {
    return this.request('GET', `/api/asset-types/get?id=${id}`);
  },

  // === Asset Types Seeding (Issue #24) ===
  async seedAssetTypes() {
    return this.request('POST', '/api/asset-types/seed');
  },

  async needsSeedAssetTypes() {
    return this.request('GET', '/api/asset-types/needs-seed');
  },
};
