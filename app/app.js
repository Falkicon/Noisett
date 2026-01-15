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
};

// DOM Elements
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
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
  try {
    const health = await API.health();
    state.isConnected = health.status !== 'error';
    updateStatusIndicator(health.status === 'healthy' ? 'connected' : 'degraded');
    $('#status-text').textContent = health.status === 'healthy' ? 'Ready' : 'Degraded (No GPU)';
  } catch (error) {
    state.isConnected = false;
    updateStatusIndicator('error');
    $('#status-text').textContent = 'Disconnected';
  }
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
  try {
    // Load from Convex generations API (Issue #21)
    const result = await API.listGenerations();
    const items = result || [];
    state.history = Array.isArray(items) ? items : [];
    renderHistorySidebar();
  } catch (error) {
    console.error('Failed to load history:', error);
    state.history = [];
    renderHistorySidebar();
  }
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

// History Actions (Issue #22)
async function toggleHistoryFavorite(id) {
  try {
    await ConvexAPI.toggleFavorite(id);
    // Update local state
    const item = state.history.find((h) => (h._id || h.id) === id);
    if (item) {
      item.isFavorite = !item.isFavorite;
    }
    renderHistorySidebar();
  } catch (error) {
    console.error('Failed to toggle favorite:', error);
    alert('Failed to toggle favorite: ' + error.message);
  }
}

async function regenerateFromHistory(id) {
  try {
    // Find the history item
    const item = state.history.find((h) => (h._id || h.id) === id);
    if (!item) {
      alert('Generation not found in history');
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
  } catch (error) {
    console.error('Failed to regenerate:', error);
    alert('Failed to regenerate: ' + error.message);
  }
}

async function deleteHistoryItem(id) {
  if (!confirm('Are you sure you want to delete this generation?')) {
    return;
  }

  try {
    await ConvexAPI.deleteGeneration(id);
    // Remove from local state
    state.history = state.history.filter((h) => (h._id || h.id) !== id);
    renderHistorySidebar();
  } catch (error) {
    console.error('Failed to delete generation:', error);
    alert('Failed to delete: ' + error.message);
  }
}

// === Asset Types & Prompt Builder ===

/**
 * Default asset types (used until API integration in Issue #12)
 * Each asset type has pre/post prompts that wrap the user's input
 */
const DEFAULT_ASSET_TYPES = [
  {
    id: 'product',
    name: 'Product Illustrations',
    prePrompt: 'A clean, modern product illustration of',
    postPrompt: ', minimalist style, white background, professional lighting',
  },
  {
    id: 'icons',
    name: 'Icons (Fluent 2)',
    prePrompt: 'A Fluent 2 design system icon of',
    postPrompt: ', simple shapes, consistent stroke width, monochrome',
  },
  {
    id: 'logo',
    name: 'Logo Illustrations',
    prePrompt: 'A modern logo design featuring',
    postPrompt: ', vector style, scalable, brand-appropriate',
  },
  {
    id: 'premium',
    name: 'Premium Illustrations',
    prePrompt: 'A premium, high-quality illustration of',
    postPrompt: ', detailed, artistic, publication-ready',
  },
];

/**
 * Load asset types from API (falls back to defaults)
 */
async function loadAssetTypes() {
  try {
    // Try to load from API
    const result = await API.getAssetTypes();
    const items = result?.data || result || [];
    // Filter to only active items if they have isActive property
    const activeItems = Array.isArray(items)
      ? items.filter((at) => at.isActive !== false)
      : [];

    if (activeItems.length > 0) {
      state.assetTypes = activeItems;
    } else {
      console.log('No active asset types from API, using defaults');
      state.assetTypes = DEFAULT_ASSET_TYPES;
    }
  } catch (error) {
    console.log('Using default asset types (API not available)');
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

  select.innerHTML = state.assetTypes
    .map((at) => `<option value="${at.id || at._id}">${at.name}</option>`)
    .join('');

  // Set initial current asset type
  if (state.assetTypes.length > 0) {
    state.currentAssetType = state.assetTypes[0];
  }
}

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
        (at) => (at.id || at._id) === selectedId
      );
      updatePromptBuilder();
    });
  }

  if (promptInput) {
    promptInput.addEventListener('input', () => {
      updateCombinedPromptPreview();
    });
  }
}

/**
 * Update the prompt builder UI with current asset type's pre/post prompts
 */
function updatePromptBuilder() {
  const preLabel = $('#pre-prompt-label');
  const postLabel = $('#post-prompt-label');

  if (!state.currentAssetType) {
    if (preLabel) preLabel.textContent = '';
    if (postLabel) postLabel.textContent = '';
    updateCombinedPromptPreview();
    return;
  }

  const prePrompt = state.currentAssetType.prePrompt || '';
  const postPrompt = state.currentAssetType.postPrompt || '';

  if (preLabel) preLabel.textContent = prePrompt;
  if (postLabel) postLabel.textContent = postPrompt;

  updateCombinedPromptPreview();
}

/**
 * Update the combined prompt preview
 */
function updateCombinedPromptPreview() {
  const preview = $('#combined-prompt-preview');
  if (!preview) return;

  const userPrompt = $('#prompt')?.value || '';
  const combined = buildCombinedPrompt(userPrompt);

  if (combined) {
    preview.textContent = combined;
  } else {
    preview.textContent = '';
  }
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

/**
 * Get the combined prompt for generation
 * @returns {string} The combined prompt ready for API
 */
function getCombinedPromptForGeneration() {
  const userPrompt = $('#prompt')?.value || '';
  return buildCombinedPrompt(userPrompt);
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

  // Get current asset type settings (Issue #21)
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
  $('#results-empty').classList.add('hidden');
  $('#results-grid').classList.add('hidden');
  $('#results-loading').classList.remove('hidden');

  try {
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

    // Extract job ID from various possible structures
    state.currentJob = result.data?.job?.id || result.data?.job_id || result.job_id || result.job?.id;
    console.log('[DEBUG] Job ID extracted:', state.currentJob);

    if (!state.currentJob) {
      throw new Error('No job ID in response');
    }
    pollJobStatus();
  } catch (error) {
    console.error('[DEBUG] Generation error:', error);
    showError('Generation failed', error.message);
    resetGenerateUI();
    state.pendingGeneration = null;
  }
}

async function pollJobStatus() {
  if (!state.currentJob) return;

  try {
    const result = await API.getJob(state.currentJob);
    console.log('[DEBUG] Job response:', JSON.stringify(result, null, 2));
    
    // Job is nested at result.data.job
    const job = result.data?.job || result.data || result;
    console.log('[DEBUG] Job object:', { status: job.status, progress: job.progress, hasImages: !!job.images });

    updateProgress(job.progress || 0);

    // Backend uses 'complete' not 'completed'
    if (job.status === 'complete') {
      console.log('[DEBUG] Job complete, images:', job.images);
      showResults(job.images);
    } else if (job.status === 'failed') {
      console.log('[DEBUG] Job failed:', job.error_message);
      showError('Generation failed', job.error_message || job.error || 'Unknown error');
      resetGenerateUI();
    } else {
      console.log('[DEBUG] Job still processing, polling again...');
      setTimeout(pollJobStatus, 1000);
    }
  } catch (error) {
    console.error('[DEBUG] Poll error:', error);
    showError('Failed to get job status', error.message);
    resetGenerateUI();
  }
}

function updateProgress(progress) {
  $('#progress-fill').style.width = `${progress}%`;
}

function showResults(images) {
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
        <button class="btn btn-small btn-secondary" onclick="downloadImage('${img.url}')">⬇️</button>
        <button class="btn btn-small btn-secondary" onclick="favoriteImage('${state.currentJob}', ${idx})">⭐</button>
      </div>
    `;
    $('#results-grid').appendChild(card);
  });

  // Reload history sidebar to show the new generation
  loadHistorySidebar();
}

async function cancelGeneration() {
  if (state.currentJob) {
    try {
      await API.cancelJob(state.currentJob);
    } catch (e) {
      console.error('Cancel failed:', e);
    }
  }
  resetGenerateUI();
}

function resetGenerateUI() {
  $('#results-loading').classList.add('hidden');
  $('#results-empty').classList.remove('hidden');
  state.currentJob = null;
}

function showError(title, message) {
  alert(`${title}: ${message}`);
}

function downloadImage(url) {
  const a = document.createElement('a');
  a.href = `${API.baseUrl}${url}`;
  a.download = `noisett-${Date.now()}.png`;
  a.click();
}

async function favoriteImage(jobId, imageIndex) {
  try {
    await API.addFavorite(jobId, imageIndex);
    alert('Added to favorites!');
  } catch (error) {
    alert('Failed to favorite: ' + error.message);
  }
}

// === LoRAs (for Generate tab selector) ===
async function loadLoras() {
  try {
    const result = await API.listLoras();
    const loras = result.data || result || [];
    state.loras = Array.isArray(loras) ? loras : [];
    populateLoraSelector();
  } catch (error) {
    console.error('Failed to load LoRAs:', error);
    state.loras = [];
    populateLoraSelector();
  }
}

function populateLoraSelector() {
  const select = $('#lora-select');
  const activeLoras = state.loras.filter((l) => l.status === 'deployed' || l.status === 'completed');

  select.innerHTML = '<option value="">None (Default)</option>' +
    activeLoras.map((l) => `<option value="${l._id}">${l.name} (${l.triggerWord})</option>`).join('');
}

