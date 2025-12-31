/**
 * Noisett Figma Plugin - UI Logic
 *
 * Handles plugin UI interactions and communication with main code.
 */

import type {
  MessageToCode,
  MessageToUI,
  PluginSettings,
  AssetType,
} from "./types";

// =============================================================================
// DOM Elements
// =============================================================================

const settingsToggle = document.getElementById("settingsToggle")!;
const settingsPanel = document.getElementById("settingsPanel")!;
const apiKeyInput = document.getElementById("apiKeyInput") as HTMLInputElement;
const saveSettingsBtn = document.getElementById("saveSettingsBtn")!;

const promptInput = document.getElementById(
  "promptInput"
) as HTMLTextAreaElement;
const assetTypeSelect = document.getElementById(
  "assetTypeSelect"
) as HTMLSelectElement;
const generateBtn = document.getElementById("generateBtn") as HTMLButtonElement;

const progressStatus = document.getElementById("progressStatus")!;
const progressBar = document.getElementById("progressBar")!;
const statusText = document.getElementById("statusText")!;

const errorStatus = document.getElementById("errorStatus")!;
const errorText = document.getElementById("errorText")!;
const retryBtn = document.getElementById("retryBtn")!;

const resultsGrid = document.getElementById("resultsGrid")!;

// =============================================================================
// State
// =============================================================================

let isGenerating = false;
let currentImages: string[] = [];

// =============================================================================
// Plugin Communication
// =============================================================================

function sendToCode(message: MessageToCode): void {
  parent.postMessage({ pluginMessage: message }, "*");
}

// Listen for messages from plugin code
window.onmessage = (event) => {
  const msg = event.data.pluginMessage as MessageToUI;
  if (!msg) return;

  switch (msg.type) {
    case "settings":
      handleSettings(msg.payload);
      break;

    case "generation-started":
      showProgress();
      statusText.textContent = "Generation started...";
      break;

    case "generation-progress":
      updateProgress(msg.payload.progress, msg.payload.status);
      break;

    case "generation-complete":
      handleGenerationComplete(msg.payload.images);
      break;

    case "generation-error":
      showError(msg.payload.message);
      break;

    case "image-inserted":
      showNotification(`Inserted: ${msg.payload.name}`);
      break;

    case "error":
      showError(msg.payload.message);
      break;
  }
};

// =============================================================================
// UI State Management
// =============================================================================

function handleSettings(settings: PluginSettings): void {
  apiKeyInput.value = settings.api_key || "";
  assetTypeSelect.value = settings.default_asset_type || "icons";
}

function showProgress(): void {
  isGenerating = true;
  generateBtn.disabled = true;
  progressStatus.classList.remove("hidden");
  errorStatus.classList.add("hidden");
  resultsGrid.classList.add("hidden");
  progressBar.style.width = "0%";
}

function updateProgress(progress: number, status: string): void {
  const percent = Math.round(progress * 100);
  progressBar.style.width = `${percent}%`;

  const statusLabels: Record<string, string> = {
    queued: "Queued...",
    processing: `Generating... ${percent}%`,
    complete: "Complete!",
  };

  statusText.textContent = statusLabels[status] || `${status}... ${percent}%`;
}

function handleGenerationComplete(images: string[]): void {
  isGenerating = false;
  generateBtn.disabled = false;
  progressStatus.classList.add("hidden");
  currentImages = images;

  if (images.length > 0) {
    showResults(images);
  } else {
    showError("No images generated");
  }
}

function showResults(images: string[]): void {
  resultsGrid.innerHTML = "";
  resultsGrid.classList.remove("hidden");

  images.forEach((url, index) => {
    const item = document.createElement("div");
    item.className = "result-item";
    item.innerHTML = `
      <img src="${url}" alt="Generated image ${index + 1}" />
      <div class="result-item-overlay">
        <span>Insert</span>
      </div>
    `;

    item.addEventListener("click", () => {
      sendToCode({
        type: "insert-image",
        payload: {
          url,
          name: `Noisett - ${promptInput.value.slice(0, 30)}`,
        },
      });
    });

    resultsGrid.appendChild(item);
  });
}

function showError(message: string): void {
  isGenerating = false;
  generateBtn.disabled = false;
  progressStatus.classList.add("hidden");
  resultsGrid.classList.add("hidden");
  errorStatus.classList.remove("hidden");
  errorText.textContent = message;
}

function showNotification(message: string): void {
  // Simple notification - could be enhanced with toast UI
  console.log("Notification:", message);
}

// =============================================================================
// Event Handlers
// =============================================================================

// Settings toggle
settingsToggle.addEventListener("click", () => {
  settingsPanel.classList.toggle("visible");
});

// Save settings
saveSettingsBtn.addEventListener("click", () => {
  sendToCode({
    type: "save-settings",
    payload: {
      api_key: apiKeyInput.value,
    },
  });
  settingsPanel.classList.remove("visible");
});

// Generate
generateBtn.addEventListener("click", () => {
  const prompt = promptInput.value.trim();

  if (!prompt) {
    promptInput.focus();
    return;
  }

  sendToCode({
    type: "generate",
    payload: {
      prompt,
      asset_type: assetTypeSelect.value as AssetType,
      count: 4,
    },
  });
});

// Retry
retryBtn.addEventListener("click", () => {
  errorStatus.classList.add("hidden");
  promptInput.focus();
});

// Keyboard shortcut (Cmd/Ctrl + Enter to generate)
promptInput.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && !isGenerating) {
    generateBtn.click();
  }
});

// =============================================================================
// Initialization
// =============================================================================

// Request initial settings
sendToCode({ type: "get-settings" });
