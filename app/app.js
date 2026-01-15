/**
 * Noisett App
 * Main application logic
 */

// State
const state = {
  loras: [],
  currentJob: null,
  history: [],
  historyFilter: 'all', // 'all' or 'favorites'
  isConnected: false,
  assetTypes: [], // Loaded from API
  currentAssetType: null, // Currently selected asset type with pre/post prompts
  pendingGeneration: null, // Stores generation context for saving to history
  isDirector: false, // Director mode flag
};

// DOM Elements
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

// === Director Mode Auth (Issue #23) ===
const DIRECTOR_STORAGE_KEY = 'noisett_isDirector';

/**
 * Initialize Director mode from URL params and localStorage
 * URL param ?director=true sets the flag and persists to localStorage
 */
function initDirectorMode() {
  // Check URL params first
  const urlParams = new URLSearchParams(window.location.search);
  const directorParam = urlParams.get('director');

  if (directorParam === 'true') {
    // Set flag in localStorage when URL param is present
    localStorage.setItem(DIRECTOR_STORAGE_KEY, 'true');
    state.isDirector = true;

    // Clean up URL (remove the param to avoid sharing)
    urlParams.delete('director');
    const newUrl = urlParams.toString()
      ? `${window.location.pathname}?${urlParams.toString()}`
      : window.location.pathname;
    window.history.replaceState({}, '', newUrl);
  } else {
    // Load from localStorage
    state.isDirector = localStorage.getItem(DIRECTOR_STORAGE_KEY) === 'true';
  }

  updateDirectorNavVisibility();
}

/**
 * Check if user has Director mode access
 * @returns {boolean}
 */
function isDirectorMode() {
  return state.isDirector;
}

/**
 * Update the visibility of the Director nav link based on auth state
 */
function updateDirectorNavVisibility() {
  const directorNav = $('#director-nav');
  if (directorNav) {
    directorNav.classList.toggle('hidden', !state.isDirector);
  }
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  initDirectorMode();
  setupGenerate();
  setupPromptBuilder();
  setupHistorySidebar();

  await checkHealth();
  await loadAssetTypes();
  await loadLoras();
  await loadHistorySidebar();
});

// === Health Check ===
async function checkHealth() {
  const result = await API.health();
  if (result.success) {
    const health = result.data;
    state.isConnected = health.status !== 'error';
    updateStatusIndicator(health.status === 'healthy' ? 'connected' : 'degraded');
    updateStatusText(health.status === 'healthy' ? 'Ready' : 'Degraded (No GPU)');
  } else {
    state.isConnected = false;
    updateStatusIndicator('error');
    updateStatusText('Disconnected');
  }
}

function updateStatusText(text) {
  $('#status-text').textContent = text;
}

function updateStatusIndicator(status) {
  const dot = $('#status-indicator');
  dot.className = `status-dot ${status}`;
}

// === History Sidebar ===
function setupHistorySidebar() {
  // Filter buttons
  $$('.filter-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const filter = btn.dataset.filter;
      state.historyFilter = filter;

      // Update active state
      $$('.filter-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');

      renderHistorySidebar();
    });
  });
}

async function loadHistorySidebar() {
  // Load from Convex generations API
  const result = await API.listGenerations();
  if (result.success) {
    const items = result.data || [];
    state.history = Array.isArray(items) ? items : [];
  } else {
    console.error('Failed to load history:', result.error?.message);
    state.history = [];
  }
  renderHistorySidebar();
}

function renderHistorySidebar() {
  const list = $('#history-list');
  const empty = $('#history-empty');

  // Filter history based on current filter
  let filteredHistory = state.history;
  if (state.historyFilter === 'favorites') {
    filteredHistory = state.history.filter((item) => item.isFavorite);
  }

  if (filteredHistory.length === 0) {
    list.innerHTML = '';
    empty.classList.remove('hidden');
    return;
  }

  empty.classList.add('hidden');
  list.innerHTML = filteredHistory.map((item) => {
    const thumb = item.thumbnail || item.images?.[0]?.url || '';
    const thumbUrl = thumb.startsWith('http') ? thumb : (thumb ? `${API.baseUrl}${thumb}` : '');
    const isFavorite = item.isFavorite || false;

    return `
      <div class="history-sidebar-item" data-id="${item._id || item.id}">
        ${thumbUrl ? `<img class="history-sidebar-thumb" src="${thumbUrl}" alt="">` : '<div class="history-sidebar-thumb"></div>'}
        <div class="history-sidebar-info">
          <div class="history-sidebar-prompt">${item.userPrompt || item.prompt || ''}</div>
          <div class="history-sidebar-meta">
            <span>${formatRelativeTime(item.createdAt || item.created_at)}</span>
          </div>
        </div>
        <div class="history-sidebar-actions">
          <button class="history-action-btn ${isFavorite ? 'favorited' : ''}" onclick="toggleHistoryFavorite('${item._id || item.id}')" title="Favorite">
            ${isFavorite ? '★' : '☆'}
          </button>
          <button class="history-action-btn" onclick="regenerateFromHistory('${item._id || item.id}')" title="Regenerate">
            ↻
          </button>
          <button class="history-action-btn delete" onclick="deleteHistoryItem('${item._id || item.id}')" title="Delete">
            ×
          </button>
        </div>
      </div>
    `;
  }).join('');
}

function formatRelativeTime(timestamp) {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

// History Actions
async function toggleHistoryFavorite(id) {
  const result = await API.toggleGenerationFavorite(id);
  if (result.success) {
    // Update local state
    const item = state.history.find((h) => (h._id || h.id) === id);
    if (item) {
      item.isFavorite = !item.isFavorite;
    }
    renderHistorySidebar();
  } else {
    console.error('Failed to toggle favorite:', result.error?.message);
    showError('Failed to toggle favorite', result.error?.message || 'Unknown error');
  }
}

async function regenerateFromHistory(id) {
  // Find the history item
  const item = state.history.find((h) => (h._id || h.id) === id);
  if (!item) {
    showError('Regenerate failed', 'Generation not found in history');
    return;
  }

  // Populate the prompt field with the original prompt
  const promptInput = $('#prompt');
  if (promptInput) {
    promptInput.value = item.userPrompt || item.prompt || '';
    // Trigger input event to update char count and preview
    promptInput.dispatchEvent(new Event('input'));
  }

  // Set the asset type if available
  if (item.assetTypeId) {
    const assetTypeSelect = $('#asset-type');
    if (assetTypeSelect) {
      assetTypeSelect.value = item.assetTypeId;
      assetTypeSelect.dispatchEvent(new Event('change'));
    }
  }

  // Start generation with the same parameters
  startGeneration();
}

async function deleteHistoryItem(id) {
  if (!confirm('Are you sure you want to delete this generation?')) {
    return;
  }

  const result = await API.deleteGeneration(id);
  if (result.success) {
    // Remove from local state
    state.history = state.history.filter((h) => (h._id || h.id) !== id);
    renderHistorySidebar();
  } else {
    console.error('Failed to delete generation:', result.error?.message);
    showError('Failed to delete', result.error?.message || 'Unknown error');
  }
}

// === Asset Types ===

/**
 * Default asset types (fallback when API unavailable)
 */
const DEFAULT_ASSET_TYPES = [
  {
    id: 'product',
    name: 'Product Illustrations',
    prePrompt: 'A clean, modern product illustration of',
    postPrompt: ', minimalist style, white background, professional lighting',
    isActive: true,
  },
  {
    id: 'icons',
    name: 'Icons (Fluent 2)',
    prePrompt: 'A Fluent 2 design system icon of',
    postPrompt: ', simple shapes, consistent stroke width, monochrome',
    isActive: true,
  },
  {
    id: 'logo',
    name: 'Logo Illustrations',
    prePrompt: 'A modern logo design featuring',
    postPrompt: ', vector style, scalable, brand-appropriate',
    isActive: true,
  },
  {
    id: 'premium',
    name: 'Premium Illustrations',
    prePrompt: 'A premium, high-quality illustration of',
    postPrompt: ', detailed, artistic, publication-ready',
    isActive: true,
  },
];

/**
 * Load asset types from API (falls back to defaults)
 * Automatically seeds default Asset Types on first run (Issue #24)
 */
async function loadAssetTypes() {
  try {
    // First, check if we need to seed default Asset Types
    const needsSeedResult = await ConvexAPI.needsSeedAssetTypes();
    if (needsSeedResult?.success && needsSeedResult.data?.needsSeed) {
      console.log('First run detected - seeding default Asset Types...');
      const seedResult = await ConvexAPI.seedAssetTypes();
      if (seedResult.success) {
        console.log('Seed result:', seedResult.data?.message);
      }
    }

    // Now load the Asset Types
    const result = await API.getAssetTypes();
    if (result.success) {
      const items = result.data || [];
      // Filter to only active items
      const activeItems = Array.isArray(items)
        ? items.filter((at) => at.isActive !== false)
        : [];

      if (activeItems.length > 0) {
        state.assetTypes = activeItems;
      } else {
        console.log('No active asset types from API, using defaults');
        state.assetTypes = DEFAULT_ASSET_TYPES;
      }
    } else {
      console.log('Using default asset types (API not available)');
      state.assetTypes = DEFAULT_ASSET_TYPES;
    }
  } catch (error) {
    console.log('Using default asset types (unexpected error):', error);
    state.assetTypes = DEFAULT_ASSET_TYPES;
  }

  populateAssetTypeSelector();
  updatePromptBuilder();
}

/**
 * Populate the asset type dropdown from state
 */
function populateAssetTypeSelector() {
  const select = $('#asset-type');
  if (!select) return;

  const activeTypes = state.assetTypes.filter((at) => at.isActive !== false);
  select.innerHTML = activeTypes
    .map((at) => `<option value="${at._id || at.id}">${at.name}</option>`)
    .join('');

  // Set initial current asset type
  if (activeTypes.length > 0) {
    state.currentAssetType = activeTypes[0];
  }
}

// === Prompt Builder ===

/**
 * Setup prompt builder event listeners
 */
function setupPromptBuilder() {
  const assetTypeSelect = $('#asset-type');
  const promptInput = $('#prompt');

  if (assetTypeSelect) {
    assetTypeSelect.addEventListener('change', () => {
      const selectedId = assetTypeSelect.value;
      state.currentAssetType = state.assetTypes.find(
        (at) => (at._id || at.id) === selectedId
      ) || null;
      updatePromptBuilder();
    });
  }

  if (promptInput) {
    promptInput.addEventListener('input', updateCombinedPromptPreview);
  }
}

/**
 * Update the prompt builder UI with current asset type's pre/post prompts
 */
function updatePromptBuilder() {
  const prePromptLabel = $('#pre-prompt-label');
  const postPromptLabel = $('#post-prompt-label');

  if (state.currentAssetType) {
    if (prePromptLabel) {
      prePromptLabel.textContent = state.currentAssetType.prePrompt || '';
    }
    if (postPromptLabel) {
      postPromptLabel.textContent = state.currentAssetType.postPrompt || '';
    }
  } else {
    if (prePromptLabel) prePromptLabel.textContent = '';
    if (postPromptLabel) postPromptLabel.textContent = '';
  }

  updateCombinedPromptPreview();
}

/**
 * Update the combined prompt preview
 */
function updateCombinedPromptPreview() {
  const preview = $('#combined-prompt-preview');
  const userPrompt = $('#prompt')?.value?.trim() || '';

  if (!preview) return;

  const combined = buildCombinedPrompt(userPrompt);
  preview.textContent = combined;
}

/**
 * Build combined prompt from pre + user + post
 * Concatenation Rules (from spec 3.2):
 * - Empty pre/post: omit entirely (no leading/trailing space)
 * - Formula: "{pre} {user} {post}".strip()
 *
 * @param {string} userPrompt - The user's input prompt
 * @returns {string} The combined prompt
 */
function buildCombinedPrompt(userPrompt) {
  const pre = state.currentAssetType?.prePrompt?.trim() || '';
  const post = state.currentAssetType?.postPrompt?.trim() || '';
  const user = userPrompt?.trim() || '';

  // Build parts array, filtering out empty strings
  const parts = [pre, user, post].filter((p) => p.length > 0);

  // Join with single space and trim
  return parts.join(' ').trim();
}

// === Generate Tab ===
function setupGenerate() {
  const prompt = $('#prompt');
  const charCount = $('#char-current');
  const generateBtn = $('#generate-btn');
  const cancelBtn = $('#cancel-btn');

  prompt.addEventListener('input', () => {
    charCount.textContent = prompt.value.length;
  });

  // Ctrl+Enter to generate
  prompt.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
      generateBtn.click();
    }
  });

  generateBtn.addEventListener('click', startGeneration);
  cancelBtn.addEventListener('click', cancelGeneration);
}

async function startGeneration() {
  const userPrompt = $('#prompt').value.trim();
  if (!userPrompt) {
    alert('Please enter a prompt');
    return;
  }

  // Get current asset type settings
  const assetTypeId = $('#asset-type').value;
  const assetType = state.currentAssetType;

  // Build combined prompt from Asset Type pre/post prompts
  const combinedPrompt = buildCombinedPrompt(userPrompt);

  // Get quality - use Asset Type's qualityPreset if available, else UI selection
  const quality = assetType?.qualityPreset || $('#quality').value;

  // Get LoRA - use Asset Type's loraId if available, else UI selection
  const lora = assetType?.loraId || $('#lora-select').value || null;

  // Store generation context for saving to history after completion
  state.pendingGeneration = {
    assetTypeId: assetType?._id || assetTypeId,
    userPrompt,
    combinedPrompt,
  };

  // Show loading
  showGenerationLoading();

  console.log('[DEBUG] Starting generation:', {
    userPrompt,
    combinedPrompt,
    assetTypeId,
    quality,
    lora,
    modelSettings: assetType?.modelSettings,
  });

  // Use combined prompt for generation (applies Asset Type's pre/post prompts)
  const result = await API.generate(combinedPrompt, assetTypeId, quality, 1, lora);
  console.log('[DEBUG] Generate response:', JSON.stringify(result, null, 2));

  if (!result.success) {
    console.error('[DEBUG] Generation error:', result.error);
    showError('Generation failed', result.error?.message || 'Unknown error');
    resetGenerateUI();
    state.pendingGeneration = null;
    return;
  }

  // Extract job ID from various possible structures
  state.currentJob = result.data?.job?.id || result.data?.job_id;
  console.log('[DEBUG] Job ID extracted:', state.currentJob);

  if (!state.currentJob) {
    showError('Generation failed', 'No job ID in response');
    resetGenerateUI();
    state.pendingGeneration = null;
    return;
  }
  pollJobStatus();
}

function showGenerationLoading() {
  $('#results-empty').classList.add('hidden');
  $('#results-grid').classList.add('hidden');
  $('#results-loading').classList.remove('hidden');
}

async function pollJobStatus() {
  if (!state.currentJob) return;

  const result = await API.getJob(state.currentJob);
  console.log('[DEBUG] Job response:', JSON.stringify(result, null, 2));

  if (!result.success) {
    console.error('[DEBUG] Poll error:', result.error);
    showError('Failed to get job status', result.error?.message || 'Unknown error');
    resetGenerateUI();
    return;
  }

  // Job is nested at result.data.job
  const job = result.data?.job || result.data;
  console.log('[DEBUG] Job object:', { status: job.status, progress: job.progress, hasImages: !!job.images });

  updateProgress(job.progress || 0);

  // Backend uses 'complete' not 'completed'
  if (job.status === 'complete') {
    console.log('[DEBUG] Job complete, images:', job.images);
    await showResults(job.images);
  } else if (job.status === 'failed') {
    console.log('[DEBUG] Job failed:', job.error_message);
    showError('Generation failed', job.error_message || job.error || 'Unknown error');
    resetGenerateUI();
  } else {
    console.log('[DEBUG] Job still processing, polling again...');
    setTimeout(pollJobStatus, 1000);
  }
}

function updateProgress(progress) {
  $('#progress-fill').style.width = `${progress}%`;
}

async function showResults(images) {
  $('#results-loading').classList.add('hidden');
  $('#results-grid').classList.remove('hidden');
  $('#results-grid').innerHTML = '';

  images.forEach((img, idx) => {
    const card = document.createElement('div');
    card.className = 'image-card';
    // Use URL directly if absolute, otherwise prepend baseUrl
    const imageUrl = img.url.startsWith('http') ? img.url : `${API.baseUrl}${img.url}`;
    card.innerHTML = `
      <img src="${imageUrl}" alt="Generated image ${idx + 1}">
      <div class="image-overlay">
        <button class="btn btn-small btn-secondary" onclick="downloadImage('${img.url}')">Download</button>
        <button class="btn btn-small btn-secondary" onclick="favoriteImage('${state.currentJob}', ${idx})">Favorite</button>
      </div>
    `;
    $('#results-grid').appendChild(card);
  });

  // Save generation record to Convex
  if (state.pendingGeneration) {
    await saveGenerationToHistory(images);
    state.pendingGeneration = null;
  }

  // Reload history sidebar to show the new generation
  await loadHistorySidebar();
}

async function saveGenerationToHistory(images) {
  const generationData = {
    assetTypeId: state.pendingGeneration.assetTypeId,
    userPrompt: state.pendingGeneration.userPrompt,
    combinedPrompt: state.pendingGeneration.combinedPrompt,
    images: images.map((img) => ({
      url: img.url,
      width: img.width || 1024,
      height: img.height || 1024,
      seed: img.seed,
    })),
    isFavorite: false,
    createdAt: Date.now(),
  };
  console.log('[DEBUG] Saving generation to Convex:', generationData);
  const result = await API.createGeneration(generationData);
  if (result.success) {
    console.log('[DEBUG] Generation saved successfully');
  } else {
    // Don't show error to user - generation was successful, just history save failed
    console.error('[DEBUG] Failed to save generation to history:', result.error?.message);
  }
}

async function cancelGeneration() {
  if (state.currentJob) {
    const result = await API.cancelJob(state.currentJob);
    if (!result.success) {
      console.error('Cancel failed:', result.error?.message);
    }
  }
  resetGenerateUI();
}

function resetGenerateUI() {
  $('#results-loading').classList.add('hidden');
  $('#results-empty').classList.remove('hidden');
  state.currentJob = null;
  state.pendingGeneration = null;
}

function showError(title, message) {
  alert(`${title}: ${message}`);
}

function downloadImage(url) {
  const a = document.createElement('a');
  a.href = url.startsWith('http') ? url : `${API.baseUrl}${url}`;
  a.download = `noisett-${Date.now()}.png`;
  a.click();
}

async function favoriteImage(jobId, imageIndex) {
  const result = await API.addFavorite(jobId, imageIndex);
  if (result.success) {
    showError('Success', 'Added to favorites!');
  } else {
    showError('Failed to favorite', result.error?.message || 'Unknown error');
  }
}

// === LoRAs (for Generate tab selector) ===
async function loadLoras() {
  const result = await API.listLoras();
  if (result.success) {
    const loras = result.data || [];
    state.loras = Array.isArray(loras) ? loras : [];
  } else {
    console.error('Failed to load LoRAs:', result.error?.message);
    state.loras = [];
  }
  populateLoraSelector();
}

function populateLoraSelector() {
  const select = $('#lora-select');
  const activeLoras = state.loras.filter((l) => l.status === 'deployed' || l.status === 'completed');

  select.innerHTML = '<option value="">None (Default)</option>' +
    activeLoras.map((l) => `<option value="${l._id}">${l.name} (${l.triggerWord})</option>`).join('');
}
