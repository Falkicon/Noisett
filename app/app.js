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
};

// DOM Elements
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  setupTabs();
  setupGenerate();
  setupHistory();
  setupFavorites();

  await checkHealth();
  await loadLoras(); // Still needed for LoRA selector in Generate tab
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
  const prompt = $('#prompt').value.trim();
  if (!prompt) {
    alert('Please enter a prompt');
    return;
  }

  const assetType = $('#asset-type').value;
  const quality = $('#quality').value;
  const lora = $('#lora-select').value || null;

  // Show loading
  $('#results-empty').classList.add('hidden');
  $('#results-grid').classList.add('hidden');
  $('#results-loading').classList.remove('hidden');

  try {
    console.log('[DEBUG] Starting generation:', { prompt, assetType, quality, lora });
    const result = await API.generate(prompt, assetType, quality, 1, lora);
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
