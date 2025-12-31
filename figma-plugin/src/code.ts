/**
 * Noisett Figma Plugin - Main Code
 *
 * This runs in the Figma sandbox and handles:
 * - Plugin initialization
 * - Settings persistence (clientStorage)
 * - Image insertion into canvas
 * - Communication with UI
 */

import { NoisettAPI } from "./api";
import type { MessageToCode, MessageToUI, PluginSettings } from "./types";
import { DEFAULT_SETTINGS } from "./types";

// Storage keys
const SETTINGS_KEY = "noisett_settings";

// API client instance
let api: NoisettAPI | null = null;

// =============================================================================
// Settings Management
// =============================================================================

async function loadSettings(): Promise<PluginSettings> {
  try {
    const stored = await figma.clientStorage.getAsync(SETTINGS_KEY);
    if (stored) {
      return { ...DEFAULT_SETTINGS, ...stored };
    }
  } catch (error) {
    console.error("Failed to load settings:", error);
  }
  return { ...DEFAULT_SETTINGS };
}

async function saveSettings(
  settings: Partial<PluginSettings>
): Promise<PluginSettings> {
  const current = await loadSettings();
  const updated = { ...current, ...settings };
  try {
    await figma.clientStorage.setAsync(SETTINGS_KEY, updated);
  } catch (error) {
    console.error("Failed to save settings:", error);
  }
  return updated;
}

// =============================================================================
// Image Insertion
// =============================================================================

async function insertImage(url: string, name: string): Promise<boolean> {
  if (!api) {
    sendToUI({ type: "error", payload: { message: "API not initialized" } });
    return false;
  }

  try {
    // Fetch image bytes
    const bytes = await api.fetchImageBytes(url);
    if (!bytes) {
      sendToUI({
        type: "error",
        payload: { message: "Failed to fetch image" },
      });
      return false;
    }

    // Create Figma image
    const image = figma.createImage(bytes);
    const { width, height } = await image.getSizeAsync();

    // Create frame for the image
    const frame = figma.createFrame();
    frame.name = name || "Noisett Generated Image";
    frame.resize(width, height);

    // Apply image as fill
    frame.fills = [
      {
        type: "IMAGE",
        imageHash: image.hash,
        scaleMode: "FILL",
      },
    ];

    // Position at viewport center
    const viewportCenter = figma.viewport.center;
    frame.x = viewportCenter.x - width / 2;
    frame.y = viewportCenter.y - height / 2;

    // Select the new frame
    figma.currentPage.selection = [frame];

    // Scroll to the frame
    figma.viewport.scrollAndZoomIntoView([frame]);

    sendToUI({ type: "image-inserted", payload: { name: frame.name } });
    return true;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    sendToUI({
      type: "error",
      payload: { message: `Insert failed: ${message}` },
    });
    return false;
  }
}

// =============================================================================
// Generation Workflow
// =============================================================================

async function handleGenerate(request: {
  prompt: string;
  asset_type: string;
  count?: number;
}): Promise<void> {
  if (!api) {
    sendToUI({
      type: "generation-error",
      payload: { code: "NO_API", message: "API not initialized" },
    });
    return;
  }

  // Start generation
  const result = await api.generate({
    prompt: request.prompt,
    asset_type: request.asset_type as any,
    count: request.count || 4,
  });

  if (!result.success || !result.data) {
    sendToUI({
      type: "generation-error",
      payload: {
        code: result.error?.code || "UNKNOWN",
        message: result.error?.message || "Generation failed",
      },
    });
    return;
  }

  const jobId = result.data.job_id;
  sendToUI({ type: "generation-started", payload: { job_id: jobId } });

  // Poll for completion
  const pollResult = await api.pollJobStatus(jobId, (progress, status) => {
    sendToUI({
      type: "generation-progress",
      payload: { progress, status: status as any },
    });
  });

  if (!pollResult.success || !pollResult.data?.images) {
    sendToUI({
      type: "generation-error",
      payload: {
        code: pollResult.error?.code || "POLL_FAILED",
        message: pollResult.error?.message || "Failed to get results",
      },
    });
    return;
  }

  sendToUI({
    type: "generation-complete",
    payload: { images: pollResult.data.images },
  });
}

// =============================================================================
// UI Communication
// =============================================================================

function sendToUI(message: MessageToUI): void {
  figma.ui.postMessage(message);
}

function handleUIMessage(msg: MessageToCode): void {
  switch (msg.type) {
    case "generate":
      handleGenerate(msg.payload);
      break;

    case "insert-image":
      insertImage(msg.payload.url, msg.payload.name);
      break;

    case "get-settings":
      loadSettings().then((settings) => {
        sendToUI({ type: "settings", payload: settings });
      });
      break;

    case "save-settings":
      saveSettings(msg.payload).then((settings) => {
        sendToUI({ type: "settings", payload: settings });
        // Update API client
        if (api) {
          api.updateSettings(settings);
        }
      });
      break;

    case "close":
      figma.closePlugin();
      break;
  }
}

// =============================================================================
// Plugin Initialization
// =============================================================================

async function initPlugin(): Promise<void> {
  // Load settings and initialize API
  const settings = await loadSettings();
  api = new NoisettAPI(settings);

  // Show UI
  figma.showUI(__html__, {
    width: 360,
    height: 480,
    title: "Noisett",
  });

  // Send initial settings to UI
  sendToUI({ type: "settings", payload: settings });

  // Listen for messages from UI
  figma.ui.onmessage = handleUIMessage;
}

// Start the plugin
initPlugin();
