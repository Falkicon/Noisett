/**
 * Noisett App
 * Main application logic
 */

// State
const state = {
  activeTab: 'generate',
  loras: [],
  currentJob: null,
  history: [],
  favorites: [],
  isConnected: false,
  assetTypes: [], // Loaded from API or defaults
  currentAssetType: null, // Currently selected asset type with pre/post prompts
};

// DOM Elements
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  setupTabs();
  setupGenerate();
  setupPromptBuilder();
  setupHistory();
  setupFavorites();

  await checkHealth();
  await loadAssetTypes();
  await loadLoras();
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

// === Tab Navigation ===
function setupTabs() {
  $$('.nav-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      const tabName = tab.dataset.tab;
      switchTab(tabName);
    });
  });
}

function switchTab(tabName) {
  // Update nav
  $$('.nav-tab').forEach((t) => t.classList.remove('active'));
  $(`.nav-tab[data-tab="${tabName}"]`).classList.add('active');

  // Update content
  $$('.tab-content').forEach((c) => c.classList.add('hidden'));
  $(`#tab-${tabName}`).classList.remove('hidden');

  state.activeTab = tabName;

  // Load data for tab
  if (tabName === 'history') loadHistory();
  if (tabName === 'favorites') loadFavorites();
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

  // Validation per spec 3.2: userPrompt required, min 1 char, max 500 chars
  if (!userPrompt) {
    alert('Please enter a prompt');
    return;
  }
  if (userPrompt.length > 500) {
    alert('Prompt must be 500 characters or less');
    return;
  }

  // Build combined prompt using pre + user + post
  const combinedPrompt = getCombinedPromptForGeneration();

  const assetType = $('#asset-type').value;
  const quality = $('#quality').value;
  const lora = $('#lora-select').value || null;

  // Show loading
  $('#results-empty').classList.add('hidden');
  $('#results-grid').classList.add('hidden');
  $('#results-loading').classList.remove('hidden');

  try {
    console.log('[DEBUG] Starting generation:', {
      userPrompt,
      combinedPrompt,
      assetType,
      quality,
      lora,
    });
    const result = await API.generate(combinedPrompt, assetType, quality, 1, lora);
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
    // Try to load from API (Issue #12 will implement this)
    const result = await API.listAssetTypes?.();
    if (result?.data && Array.isArray(result.data) && result.data.length > 0) {
      state.assetTypes = result.data;
    } else {
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

// === History Tab ===
async function loadHistory() {
  try {
    const result = await API.getHistory();
    const items = result.data || result.items || result || [];
    state.history = Array.isArray(items) ? items : [];
    renderHistory();
  } catch (error) {
    console.error('Failed to load history:', error);
    state.history = [];
    renderHistory();
  }
}

function renderHistory() {
  const list = $('#history-list');
  
  if (state.history.length === 0) {
    list.innerHTML = '<div class="empty-state"><span class="empty-icon">📜</span><p>No generation history yet</p></div>';
    return;
  }

  list.innerHTML = state.history.map((item) => `
    <div class="history-item">
      <img class="history-item-thumb" src="${item.thumbnail || 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg"></svg>'}" alt="">
      <div class="history-item-content">
        <div class="history-item-prompt">${item.prompt}</div>
        <div class="history-item-meta">${new Date(item.created_at).toLocaleString()} • ${item.status}</div>
      </div>
      <span class="status-badge ${item.status}">${item.status}</span>
    </div>
  `).join('');
}

function setupHistory() {
  $('#history-filter').addEventListener('change', async (e) => {
    const status = e.target.value || null;
    try {
      const result = await API.getHistory(50, status);
      state.history = result.data || result.items || [];
      renderHistory();
    } catch (error) {
      console.error('Filter failed:', error);
    }
  });
}

// === Favorites Tab ===
async function loadFavorites() {
  try {
    const result = await API.getFavorites();
    const items = result.data || result.items || result || [];
    state.favorites = Array.isArray(items) ? items : [];
    renderFavorites();
  } catch (error) {
    console.error('Failed to load favorites:', error);
    state.favorites = [];
    renderFavorites();
  }
}

function renderFavorites() {
  const grid = $('#favorites-grid');
  const empty = $('#favorites-empty');

  if (state.favorites.length === 0) {
    grid.classList.add('hidden');
    empty.classList.remove('hidden');
    return;
  }

  empty.classList.add('hidden');
  grid.classList.remove('hidden');
  grid.innerHTML = state.favorites.map((fav) => `
    <div class="image-card">
      <img src="${API.baseUrl}${fav.image_url}" alt="">
      <div class="image-overlay">
        <button class="btn btn-small btn-secondary" onclick="downloadImage('${fav.image_url}')">⬇️</button>
        <button class="btn btn-small btn-danger" onclick="removeFavorite('${fav.job_id}', ${fav.image_index})">❌</button>
      </div>
    </div>
  `).join('');
}

async function removeFavorite(jobId, imageIndex) {
  try {
    await API.removeFavorite(jobId, imageIndex);
    await loadFavorites();
  } catch (error) {
    alert('Failed to remove: ' + error.message);
  }
}

function setupFavorites() {
  // No additional setup needed
}
