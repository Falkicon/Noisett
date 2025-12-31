/**
 * Noisett Figma Plugin - API Client
 *
 * Handles communication with the Noisett backend.
 */

import type {
  GenerateRequest,
  GenerateResponse,
  JobStatusResponse,
  PluginSettings,
} from "./types";

/**
 * API client for Noisett backend
 */
export class NoisettAPI {
  private baseUrl: string;
  private apiKey: string;

  constructor(settings: PluginSettings) {
    this.baseUrl = settings.backend_url;
    this.apiKey = settings.api_key;
  }

  /**
   * Update settings (e.g., after user changes API key)
   */
  updateSettings(settings: Partial<PluginSettings>): void {
    if (settings.backend_url) this.baseUrl = settings.backend_url;
    if (settings.api_key) this.apiKey = settings.api_key;
  }

  /**
   * Start image generation
   */
  async generate(request: GenerateRequest): Promise<GenerateResponse> {
    const response = await fetch(`${this.baseUrl}/api/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(this.apiKey && { Authorization: `Bearer ${this.apiKey}` }),
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return {
        success: false,
        error: {
          code: "API_ERROR",
          message: error.detail || `HTTP ${response.status}`,
        },
      };
    }

    return response.json();
  }

  /**
   * Get job status
   */
  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const response = await fetch(`${this.baseUrl}/api/jobs/${jobId}`, {
      headers: {
        ...(this.apiKey && { Authorization: `Bearer ${this.apiKey}` }),
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return {
        success: false,
        error: {
          code: "API_ERROR",
          message: error.detail || `HTTP ${response.status}`,
        },
      };
    }

    return response.json();
  }

  /**
   * Poll job status until complete or failed
   * @param jobId - Job ID to poll
   * @param onProgress - Callback for progress updates
   * @param maxAttempts - Maximum poll attempts (default: 60 = ~2 minutes)
   * @param intervalMs - Poll interval in milliseconds (default: 2000ms)
   */
  async pollJobStatus(
    jobId: string,
    onProgress?: (progress: number, status: string) => void,
    maxAttempts = 60,
    intervalMs = 2000
  ): Promise<JobStatusResponse> {
    let attempts = 0;

    while (attempts < maxAttempts) {
      const result = await this.getJobStatus(jobId);

      if (!result.success) {
        return result;
      }

      const status = result.data?.status;
      const progress = result.data?.progress ?? 0;

      onProgress?.(progress, status || "unknown");

      if (status === "complete") {
        return result;
      }

      if (status === "failed" || status === "cancelled") {
        return {
          success: false,
          error: {
            code: "GENERATION_FAILED",
            message: result.data?.error_message || "Generation failed",
          },
        };
      }

      // Wait before next poll
      await new Promise((resolve) => setTimeout(resolve, intervalMs));
      attempts++;
    }

    return {
      success: false,
      error: {
        code: "TIMEOUT",
        message: "Generation timed out after 2 minutes",
      },
    };
  }

  /**
   * Fetch image as bytes (for Figma insertion)
   */
  async fetchImageBytes(url: string): Promise<Uint8Array | null> {
    try {
      // Handle relative URLs
      const fullUrl = url.startsWith("http") ? url : `${this.baseUrl}${url}`;

      const response = await fetch(fullUrl, {
        headers: {
          ...(this.apiKey && { Authorization: `Bearer ${this.apiKey}` }),
        },
      });

      if (!response.ok) {
        console.error("Failed to fetch image:", response.status);
        return null;
      }

      const buffer = await response.arrayBuffer();
      return new Uint8Array(buffer);
    } catch (error) {
      console.error("Error fetching image:", error);
      return null;
    }
  }
}
