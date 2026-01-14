/**
 * Noisett App
 * Main application logic
 */

// State
const state = {
  activeTab: 'generate',
  loras: [],
  selectedLora: null,
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
  setupLoras();
  setupHistory();
  setupFavorites();
  
  await checkHealth();
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
  if (tabName === 'loras') loadLoras();
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

// === LoRAs Tab ===
async function loadLoras() {
  try {
    // Use local API which proxies to Convex (avoids CORS)
    const result = await API.listLoras();
    const loras = result.data || result || [];
    state.loras = Array.isArray(loras) ? loras : [];
    renderLoraList();
    populateLoraSelector();
  } catch (error) {
    console.error('Failed to load LoRAs:', error);
    state.loras = [];
    renderLoraList();
    populateLoraSelector();
  }
}

function renderLoraList() {
  const list = $('#lora-list');
  
  if (state.loras.length === 0) {
    list.innerHTML = '<div class="empty-state"><span class="empty-icon">🎨</span><p>No LoRAs yet</p></div>';
    return;
  }

  list.innerHTML = state.loras.map((lora) => `
    <div class="lora-item ${state.selectedLora?._id === lora._id ? 'active' : ''}" data-id="${lora._id}">
      <div>
        <div class="lora-item-name">${lora.name}</div>
        <div class="lora-item-trigger">${lora.triggerWord}</div>
      </div>
      <span class="status-badge ${lora.status}">${lora.status}</span>
    </div>
  `).join('');

  $$('.lora-item').forEach((item) => {
    item.addEventListener('click', () => selectLora(item.dataset.id));
  });
}

function populateLoraSelector() {
  const select = $('#lora-select');
  const activeLoras = state.loras.filter((l) => l.status === 'deployed' || l.status === 'completed');
  
  select.innerHTML = '<option value="">None (Default)</option>' +
    activeLoras.map((l) => `<option value="${l._id}">${l.name} (${l.triggerWord})</option>`).join('');
}

function selectLora(id) {
  state.selectedLora = state.loras.find((l) => l._id === id);
  renderLoraList();
  showLoraDetail();
}

function showLoraDetail() {
  if (!state.selectedLora) return;

  $('#lora-empty').classList.add('hidden');
  $('#lora-create-form').classList.add('hidden');
  $('#lora-detail').classList.remove('hidden');

  const lora = state.selectedLora;
  $('#lora-detail-name').textContent = lora.name;
  $('#lora-detail-status').textContent = lora.status;
  $('#lora-detail-status').className = `status-badge ${lora.status}`;
  $('#lora-detail-trigger').textContent = lora.triggerWord;
  $('#lora-detail-model').textContent = lora.baseModel;
  $('#lora-detail-images').textContent = '0'; // TODO: fetch image count

  // Show/hide sections based on status
  const canUpload = ['created', 'uploading', 'ready_to_train'].includes(lora.status);
  const isTraining = lora.status === 'training';
  
  $('#upload-section').classList.toggle('hidden', !canUpload);
  $('#training-section').classList.toggle('hidden', !isTraining);
  $('#lora-train-btn').classList.toggle('hidden', lora.status !== 'ready_to_train');
}

function setupLoras() {
  // Create button
  $('#create-lora-btn').addEventListener('click', showCreateForm);
  $('#lora-create-cancel').addEventListener('click', hideCreateForm);
  $('#lora-create-submit').addEventListener('click', createLora);
  
  // Upload dropzone
  const dropzone = $('#upload-dropzone');
  const input = $('#upload-input');

  dropzone.addEventListener('click', () => input.click());
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
  dropzone.addEventListener('drop', handleDrop);
  input.addEventListener('change', (e) => handleFiles(e.target.files));

  // Actions
  $('#lora-train-btn').addEventListener('click', startTraining);
  $('#lora-delete-btn').addEventListener('click', deleteLora);
}

function showCreateForm() {
  $('#lora-empty').classList.add('hidden');
  $('#lora-detail').classList.add('hidden');
  $('#lora-create-form').classList.remove('hidden');
}

function hideCreateForm() {
  $('#lora-create-form').classList.add('hidden');
  $('#lora-empty').classList.remove('hidden');
  state.selectedLora = null;
  renderLoraList();
}

async function createLora() {
  const name = $('#lora-name').value.trim();
  const trigger = $('#lora-trigger').value.trim();
  const model = $('#lora-model').value;
  const steps = parseInt($('#lora-steps').value) || 1000;

  if (!name || !trigger) {
    alert('Please fill in name and trigger word');
    return;
  }

  try {
    // Use local API which proxies to Convex
    const result = await API.createLora(name, trigger, model, steps);

    await loadLoras();
    hideCreateForm();
    
    // Select the new LoRA
    const newId = result.data?.id || result.id;
    if (newId) {
      selectLora(newId);
    }
  } catch (error) {
    alert('Failed to create LoRA: ' + error.message);
  }
}

function handleDrop(e) {
  e.preventDefault();
  $('#upload-dropzone').classList.remove('dragover');
  const files = e.dataTransfer.files;
  handleFiles(files);
}

async function handleFiles(files) {
  if (!state.selectedLora) return;

  const preview = $('#upload-preview');
  preview.innerHTML = '';

  for (const file of files) {
    if (!file.type.startsWith('image/')) continue;

    // Preview
    const reader = new FileReader();
    reader.onload = (e) => {
      const div = document.createElement('div');
      div.className = 'upload-preview-item';
      div.innerHTML = `<img src="${e.target.result}">`;
      preview.appendChild(div);
    };
    reader.readAsDataURL(file);
  }
  
  // Note: Upload to Convex requires backend proxy (CORS restriction)
  // For now, previews are shown but files aren't uploaded to cloud
  console.log(`${files.length} files previewed (upload needs API proxy)`);
}

async function startTraining() {
  if (!state.selectedLora) return;
  alert('Training would start here. Requires REPLICATE_API_TOKEN to be configured.');
}

async function deleteLora() {
  if (!state.selectedLora) return;
  if (!confirm(`Delete "${state.selectedLora.name}"?`)) return;

  try {
    await API.deleteLora(state.selectedLora._id);
    state.selectedLora = null;
    await loadLoras();
    hideCreateForm();
  } catch (error) {
    alert('Failed to delete: ' + error.message);
  }
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
