/**
 * Noisett API Client
 * Complete API surface for all backend endpoints
 */
const API = {
  baseUrl: 'http://localhost:8000',
  convexUrl: 'https://neighborly-gazelle-692.convex.site',

  async request(method, path, body = null) {
    const options = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (body) options.body = JSON.stringify(body);

    const response = await fetch(`${this.baseUrl}${path}`, options);
    const data = await response.json();

    if (!response.ok) {
      const error = new Error(data.detail || 'Request failed');
      error.status = response.status;
      throw error;
    }

    // Handle CommandResult format
    if (data.success === false && data.error) {
      const error = new Error(data.error.message);
      error.code = data.error.code;
      error.suggestion = data.error.suggestion;
      throw error;
    }

    return data;
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

  async getAssetTypes() {
    return this.request('GET', '/api/asset-types');
  },

  async getModels() {
    return this.request('GET', '/api/models');
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
    const response = await fetch(uploadUrl, {
      method: 'POST',
      body: file,
    });
    return response.json();
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

  async request(method, path, body = null) {
    const options = { method };
    if (body) {
      options.headers = { 'Content-Type': 'application/json' };
      options.body = JSON.stringify(body);
    }
    const response = await fetch(`${this.baseUrl}${path}`, options);
    return response.json();
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
};
