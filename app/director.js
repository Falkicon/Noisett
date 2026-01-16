/**
 * Noisett Director Mode
 * Asset Type configuration interface
 */

// State
const state = {
  activeSidebarTab: 'asset-types',
  assetTypes: [],
  selectedAssetType: null,
  models: [],
  loras: [],
  selectedLora: null,
  isCreating: false,
  isConnected: false,
};

// DOM Helpers
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

/**
 * Shared dropzone utility - sets up drag/drop and file input handling
 * @param {string} dropzoneSelector - Selector for dropzone element
 * @param {string} inputSelector - Selector for file input element
 * @param {Function} onFiles - Callback receiving FileList
 */
function setupDropzone(dropzoneSelector, inputSelector, onFiles) {
  const dropzone = $(dropzoneSelector);
  const input = $(inputSelector);
  
  if (!dropzone || !input) return;
  
  dropzone.addEventListener('click', () => input.click());
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    onFiles(e.dataTransfer.files);
  });
  input.addEventListener('change', (e) => onFiles(e.target.files));
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  setupSidebarTabs();
  setupAssetTypeEditor();
  setupPromptPreview();
  setupLoraManagement();
  setupReferenceImages();

  await checkHealth();
  await loadModels();
  await loadLoras();
  await loadAssetTypes();
});

// === Health Check ===
async function checkHealth() {
  const result = await API.health();
  if (result.success) {
    const health = result.data;
    state.isConnected = health.status !== 'error';
    updateStatusIndicator(health.status === 'healthy' ? 'connected' : 'degraded');
    updateStatusText(health.status === 'healthy' ? 'Ready' : 'Degraded');
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

// === Sidebar Tabs ===
function setupSidebarTabs() {
  $$('.sidebar-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      const tabName = tab.dataset.sidebarTab;
      switchSidebarTab(tabName);
    });
  });
}

function switchSidebarTab(tabName) {
  // Update tab buttons
  $$('.sidebar-tab').forEach((t) => t.classList.remove('active'));
  $(`.sidebar-tab[data-sidebar-tab="${tabName}"]`).classList.add('active');

  // Update sidebar content visibility
  $('#sidebar-asset-types').classList.toggle('hidden', tabName !== 'asset-types');
  $('#sidebar-loras').classList.toggle('hidden', tabName !== 'loras');

  // Hide all editor panels and empty states first
  $('#editor-panel').classList.add('hidden');
  $('#editor-empty').classList.add('hidden');
  $('#lora-editor-panel').classList.add('hidden');
  $('#lora-empty').classList.add('hidden');
  $('#lora-create-form').classList.add('hidden');
  $('#lora-detail').classList.add('hidden');

  if (tabName === 'loras') {
    // Show LoRA editor panel with empty state
    $('#lora-editor-panel').classList.remove('hidden');
    $('#lora-empty').classList.remove('hidden');
  } else {
    // Show asset type empty state
    $('#editor-empty').classList.remove('hidden');
  }

  state.activeSidebarTab = tabName;
  state.selectedAssetType = null;
  state.selectedLora = null;
  state.isCreating = false;
}

// === Load Data ===
async function loadModels() {
  const result = await API.request('GET', '/api/models/list');
  if (result.success && result.data) {
    // API returns object with model IDs as keys, convert to array
    state.models = Object.entries(result.data).map(([id, model]) => ({
      id,
      ...model,
    }));
  } else {
    console.error('Failed to load models:', result.error?.message);
    state.models = [];
  }
  populateModelSelector();
}

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
  renderLoraList();
}

async function loadAssetTypes() {
  const result = await API.request('GET', '/api/asset-types');
  if (result.success && result.data) {
    // API returns array directly from Convex
    state.assetTypes = Array.isArray(result.data) ? result.data : [];
  } else {
    console.error('Failed to load asset types:', result.error?.message);
    state.assetTypes = [];
  }
  renderAssetTypeList();
}

// === Render Lists ===
function renderAssetTypeList() {
  const list = $('#asset-type-list');

  if (state.assetTypes.length === 0) {
    list.innerHTML = '<div class="empty-state"><span class="empty-icon">📦</span><p>No asset types yet</p></div>';
    return;
  }

  // Convex returns asset types with '_id' field
  list.innerHTML = state.assetTypes.map((at) => `
    <div class="asset-type-item ${state.selectedAssetType?._id === at._id ? 'active' : ''}" data-id="${at._id}">
      <div class="asset-type-item-info">
        <div class="asset-type-item-name">${escapeHtml(at.name)}</div>
        <div class="asset-type-item-model">${escapeHtml(at.description || '')}</div>
      </div>
      <span class="status-badge ${at.isActive ? 'status-active' : 'status-inactive'}">${at.isActive ? 'Active' : 'Inactive'}</span>
    </div>
  `).join('');

  $$('.asset-type-item').forEach((item) => {
    item.addEventListener('click', () => selectAssetType(item.dataset.id));
  });
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
        <div class="lora-item-name">${escapeHtml(lora.name)}</div>
        <div class="lora-item-trigger">${escapeHtml(lora.triggerWord)}</div>
      </div>
      <span class="status-badge ${lora.status}">${lora.status}</span>
    </div>
  `).join('');

  // Add click handlers
  $$('#lora-list .lora-item').forEach((item) => {
    item.addEventListener('click', () => selectLora(item.dataset.id));
  });
}

// === Populate Selectors ===
function populateModelSelector() {
  const select = $('#asset-type-model');

  if (state.models.length === 0) {
    select.innerHTML = '<option value="">No models available</option>';
    return;
  }

  select.innerHTML = state.models.map((model) =>
    `<option value="${model.id}">${escapeHtml(model.name)}</option>`
  ).join('');

  // Update model settings when selection changes
  select.addEventListener('change', () => {
    updateModelSettings();
    updateLoraVisibility();
  });
}

function populateLoraSelector() {
  const select = $('#asset-type-lora');
  const activeLoras = state.loras.filter((l) => l.status === 'deployed' || l.status === 'completed');

  select.innerHTML = '<option value="">None</option>' +
    activeLoras.map((l) => `<option value="${l._id}">${escapeHtml(l.name)} (${escapeHtml(l.triggerWord)})</option>`).join('');
}

// === Model Settings ===
function updateModelSettings() {
  const modelId = $('#asset-type-model').value;
  const model = state.models.find((m) => m.id === modelId);
  const container = $('#model-settings');

  if (!model || !model.settings || model.settings.length === 0) {
    container.innerHTML = '<p class="hint">No configurable settings for this model</p>';
    return;
  }

  container.innerHTML = model.settings.map((setting) => {
    const currentValue = state.selectedAssetType?.modelSettings?.[setting.key] ?? setting.default;

    switch (setting.type) {
      case 'range':
        return `
          <div class="form-group">
            <label for="setting-${setting.key}">${escapeHtml(setting.label)}: <span id="setting-${setting.key}-value">${currentValue}</span></label>
            <input type="range" id="setting-${setting.key}"
              data-setting="${setting.key}"
              min="${setting.min}"
              max="${setting.max}"
              step="${setting.step || 1}"
              value="${currentValue}">
          </div>
        `;
      case 'select':
        return `
          <div class="form-group">
            <label for="setting-${setting.key}">${escapeHtml(setting.label)}</label>
            <select id="setting-${setting.key}" data-setting="${setting.key}">
              ${setting.options.map((opt) =>
                `<option value="${opt}" ${opt === currentValue ? 'selected' : ''}>${opt}</option>`
              ).join('')}
            </select>
          </div>
        `;
      case 'checkbox':
        return `
          <div class="form-group">
            <label>
              <input type="checkbox" id="setting-${setting.key}"
                data-setting="${setting.key}"
                ${currentValue ? 'checked' : ''}>
              ${escapeHtml(setting.label)}
            </label>
          </div>
        `;
      case 'number':
        return `
          <div class="form-group">
            <label for="setting-${setting.key}">${escapeHtml(setting.label)}</label>
            <input type="number" id="setting-${setting.key}"
              data-setting="${setting.key}"
              min="${setting.min || ''}"
              max="${setting.max || ''}"
              value="${currentValue}">
          </div>
        `;
      default:
        return '';
    }
  }).join('');

  // Add range input listeners for live value display
  container.querySelectorAll('input[type="range"]').forEach((input) => {
    input.addEventListener('input', () => {
      const valueDisplay = $(`#${input.id}-value`);
      if (valueDisplay) {
        valueDisplay.textContent = input.value;
      }
    });
  });
}

function updateLoraVisibility() {
  const modelId = $('#asset-type-model').value;
  const model = state.models.find((m) => m.id === modelId);
  const loraGroup = $('#asset-type-lora').closest('.form-group');

  if (model?.capabilities?.supportsLora) {
    loraGroup.style.display = '';
  } else {
    loraGroup.style.display = 'none';
    $('#asset-type-lora').value = '';
  }

  // Update reference images visibility
  updateReferenceImagesVisibility();
}

function updateReferenceImagesVisibility() {
  const modelId = $('#asset-type-model').value;
  const model = state.models.find((m) => m.id === modelId);
  const section = $('#reference-images-section');
  const maxImages = model?.capabilities?.maxReferenceImages || 0;

  if (maxImages > 0) {
    section.classList.remove('hidden');
    $('#max-reference-images').textContent = maxImages;
    $('#reference-images-max').textContent = maxImages;
    renderReferenceImages();
  } else {
    section.classList.add('hidden');
  }
}

function getModelSettings() {
  const settings = {};
  $$('#model-settings [data-setting]').forEach((input) => {
    const key = input.dataset.setting;
    if (input.type === 'checkbox') {
      settings[key] = input.checked;
    } else if (input.type === 'range' || input.type === 'number') {
      settings[key] = parseFloat(input.value);
    } else {
      settings[key] = input.value;
    }
  });
  return settings;
}

// === Asset Type Editor ===
function setupAssetTypeEditor() {
  $('#new-asset-type-btn').addEventListener('click', showCreateForm);
  $('#cancel-edit-btn').addEventListener('click', hideEditor);
  $('#save-asset-type-btn').addEventListener('click', saveAssetType);
  $('#delete-asset-type-btn').addEventListener('click', deleteAssetType);
}

function selectAssetType(id) {
  state.selectedAssetType = state.assetTypes.find((at) => at._id === id);
  state.isCreating = false;
  renderAssetTypeList();
  showEditor();
}

function showCreateForm() {
  state.selectedAssetType = null;
  state.isCreating = true;
  renderAssetTypeList();
  showEditor();
}

function showEditor() {
  $('#editor-empty').classList.add('hidden');
  $('#lora-editor-panel').classList.add('hidden');
  $('#editor-panel').classList.remove('hidden');

  const at = state.selectedAssetType;

  // Populate form from Convex asset type
  $('#asset-type-name').value = at?.name || '';
  $('#asset-type-description').value = at?.description || '';
  $('#asset-type-pre-prompt').value = at?.prePrompt || '';
  $('#asset-type-post-prompt').value = at?.postPrompt || '';
  
  // AFD: Explicit precedence - asset type model overrides default
  const modelFromAssetType = at?.model ?? null;
  const defaultModel = state.models[0]?.id ?? '';
  $('#asset-type-model').value = modelFromAssetType ?? defaultModel;
  
  $('#asset-type-lora').value = at?.loraId || '';
  $('#asset-type-quality').value = at?.qualityPreset || '';
  $('#asset-type-active').checked = at?.isActive ?? true;

  // Update dependent UI
  updateModelSettings();
  updateLoraVisibility();
  updatePromptPreview();

  // All Convex asset types are editable - show save, show delete when editing
  $('#save-asset-type-btn').classList.remove('hidden');
  $('#delete-asset-type-btn').classList.toggle('hidden', state.isCreating);
}

function hideEditor() {
  $('#editor-panel').classList.add('hidden');
  $('#editor-empty').classList.remove('hidden');
  state.selectedAssetType = null;
  state.isCreating = false;
  renderAssetTypeList();
}

// === Prompt Preview ===
function setupPromptPreview() {
  $('#asset-type-pre-prompt').addEventListener('input', updatePromptPreview);
  $('#asset-type-post-prompt').addEventListener('input', updatePromptPreview);
}

function updatePromptPreview() {
  const prePrompt = $('#asset-type-pre-prompt').value.trim();
  const postPrompt = $('#asset-type-post-prompt').value.trim();

  const preview = $('#prompt-preview');
  preview.querySelector('.pre-prompt').textContent = prePrompt ? prePrompt + ' ' : '';
  preview.querySelector('.post-prompt').textContent = postPrompt ? ' ' + postPrompt : '';
}

// === Save/Delete Asset Type ===
async function saveAssetType() {
  const name = getAssetTypeFormName();
  if (!name) {
    showError('Validation', 'Please enter a name');
    return;
  }

  const data = collectAssetTypeFormData(name);

  let result;
  if (state.isCreating) {
    result = await API.request('POST', '/api/asset-types/create', data);
  } else {
    result = await API.request('POST', '/api/asset-types/update', {
      id: state.selectedAssetType._id,
      ...data,
    });
  }

  if (result.success) {
    await loadAssetTypes();
    hideEditor();
  } else {
    showError('Failed to save', result.error?.message || 'Unknown error');
  }
}

function getAssetTypeFormName() {
  return $('#asset-type-name').value.trim();
}

function collectAssetTypeFormData(name) {
  const modelId = $('#asset-type-model').value;
  const model = state.models.find((m) => m.id === modelId);
  const supportsLora = model?.capabilities?.supportsLora || false;

  return {
    name,
    description: $('#asset-type-description').value.trim() || undefined,
    prePrompt: $('#asset-type-pre-prompt').value.trim(),
    postPrompt: $('#asset-type-post-prompt').value.trim(),
    model: modelId,
    modelSettings: getModelSettings(),
    // Clear loraId if model doesn't support LoRA (use null to explicitly clear in Convex)
    loraId: supportsLora ? ($('#asset-type-lora').value || null) : null,
    qualityPreset: $('#asset-type-quality').value || undefined,
    isActive: $('#asset-type-active').checked,
  };
}

function showError(title, message) {
  alert(`${title}: ${message}`);
}

function deleteAssetType() {
  if (!state.selectedAssetType) return;
  if (!confirm(`Delete "${state.selectedAssetType.name}"? This will deactivate the asset type.`)) return;
  performDeleteAssetType();
}

async function performDeleteAssetType() {
  const result = await API.request('DELETE', `/api/asset-types/delete?id=${state.selectedAssetType._id}`);
  if (result.success) {
    await loadAssetTypes();
    hideEditor();
  } else {
    showError('Failed to delete', result.error?.message || 'Unknown error');
  }
}

// === LoRA Management ===
function setupLoraManagement() {
  // New LoRA button
  $('#new-lora-btn').addEventListener('click', showLoraCreateForm);
  $('#lora-create-cancel').addEventListener('click', hideLoraCreateForm);
  $('#lora-create-submit').addEventListener('click', createLora);

  // Upload dropzone (LoRA training images)
  setupDropzone('#upload-dropzone', '#upload-input', handleFiles);

  // Actions
  $('#lora-train-btn').addEventListener('click', startTraining);
  $('#lora-sync-btn').addEventListener('click', syncStatus);
  $('#lora-delete-btn').addEventListener('click', deleteLora);
}

function selectLora(id) {
  state.selectedLora = state.loras.find((l) => l._id === id);
  state.isCreating = false;
  renderLoraList();
  showLoraDetail();
}

function showLoraCreateForm() {
  state.selectedLora = null;
  state.isCreating = true;
  renderLoraList();

  $('#lora-empty').classList.add('hidden');
  $('#lora-detail').classList.add('hidden');
  $('#lora-create-form').classList.remove('hidden');

  // Clear form
  $('#lora-name').value = '';
  $('#lora-trigger').value = '';
  $('#lora-model').value = 'flux';
  $('#lora-steps').value = '1000';
}

function hideLoraCreateForm() {
  $('#lora-create-form').classList.add('hidden');
  $('#lora-empty').classList.remove('hidden');
  state.selectedLora = null;
  state.isCreating = false;
  renderLoraList();
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
  $('#lora-detail-images').textContent = '...'; // Loading

  // Show/hide sections based on status
  const canUpload = ['created', 'uploading', 'ready_to_train'].includes(lora.status);
  const isTraining = lora.status === 'training';

  $('#upload-section').classList.toggle('hidden', !canUpload);
  $('#training-section').classList.toggle('hidden', !isTraining);
  $('#lora-train-btn').classList.toggle('hidden', lora.status !== 'ready_to_train');

  // Fetch and display training images
  loadTrainingImages(lora._id);
}

async function loadTrainingImages(loraId) {
  const response = await API.request('GET', `/api/lora/${loraId}/training-images`);

  if (!response.success) {
    console.error('Failed to load training images:', response.error?.message);
    updateTrainingImagesCount('?');
    return;
  }

  const images = response.data || [];
  updateTrainingImagesCount(images.length);
  renderTrainingImages(images);

  // Show train button if we have enough images
  if (images.length >= 5) {
    showTrainButton();
  }
}

function updateTrainingImagesCount(count) {
  $('#lora-detail-images').textContent = count;
}

function showTrainButton() {
  $('#lora-train-btn').classList.remove('hidden');
}

function renderTrainingImages(images) {
  const preview = $('#upload-preview');
  preview.innerHTML = '';

  for (const img of images) {
    const div = document.createElement('div');
    div.className = 'upload-preview-item uploaded';

    // Use the pre-resolved URL from the API
    if (img.url) {
      div.innerHTML = `<img src="${img.url}" alt="${img.filename}" title="${img.filename}">`;
    } else {
      div.innerHTML = `<span class="error-icon">⚠️</span>`;
      div.title = 'Image not found';
    }
    preview.appendChild(div);
  }
}

async function createLora() {
  const formData = getLoraFormData();

  if (!formData.name || !formData.trigger) {
    showError('Validation', 'Please fill in name and trigger word');
    return;
  }

  const result = await API.createLora(formData.name, formData.trigger, formData.model, formData.steps);

  if (result.success) {
    await loadLoras();
    hideLoraCreateForm();

    // Select the new LoRA
    const newId = result.data?.id;
    if (newId) {
      selectLora(newId);
    }
  } else {
    showError('Failed to create LoRA', result.error?.message || 'Unknown error');
  }
}

function getLoraFormData() {
  return {
    name: $('#lora-name').value.trim(),
    trigger: $('#lora-trigger').value.trim(),
    model: $('#lora-model').value,
    steps: parseInt($('#lora-steps').value) || 1000,
  };
}

// handleDrop removed - now handled by setupDropzone utility

function handleFiles(files) {
  if (!state.selectedLora) return;

  clearUploadPreview();

  // Prepare preview items synchronously
  const uploadItems = [];
  for (const file of files) {
    if (!file.type.startsWith('image/')) continue;
    const div = createUploadPreviewItem();
    previewFile(file, div);
    uploadItems.push({ file, div });
  }

  // Process uploads asynchronously
  processFileUploads(uploadItems);
}

async function processFileUploads(uploadItems) {
  let uploadedCount = 0;
  const loraId = state.selectedLora._id;

  for (const { file, div } of uploadItems) {
    const result = await uploadFileToStorage(loraId, file);
    if (result.success) {
      uploadedCount++;
      markUploadSuccess(div);
    } else {
      console.error(`Failed to upload ${file.name}:`, result.error?.message);
      markUploadError(div, result.error?.message || 'Upload failed');
    }
  }

  console.log(`${uploadedCount}/${uploadItems.length} files uploaded to Convex`);

  // Refresh LoRA to get updated image count
  if (uploadedCount > 0) {
    await refreshSelectedLora(loraId);
  }
}

function markUploadSuccess(div) {
  div.classList.add('uploaded');
}

function markUploadError(div, message) {
  div.classList.add('upload-error');
  div.title = message;
}

function clearUploadPreview() {
  $('#upload-preview').innerHTML = '';
}

function createUploadPreviewItem() {
  const preview = $('#upload-preview');
  const div = document.createElement('div');
  div.className = 'upload-preview-item';
  div.innerHTML = '<div class="uploading-indicator">⏳</div>';
  preview.appendChild(div);
  return div;
}

function previewFile(file, div) {
  const reader = new FileReader();
  reader.onload = (e) => {
    div.innerHTML = `<img src="${e.target.result}">`;
  };
  reader.readAsDataURL(file);
}

async function uploadFileToStorage(loraId, file) {
  // 1. Get upload URL from backend
  const urlResponse = await API.getUploadUrl(loraId);
  if (!urlResponse.success) {
    return urlResponse;
  }
  const uploadUrl = urlResponse.data.uploadUrl;

  // 2. Upload file to Convex storage
  const uploadResult = await API.uploadImage(uploadUrl, file);
  if (!uploadResult.success) {
    return uploadResult;
  }

  const { storageId } = uploadResult.data;

  // 3. Register training image in Convex
  return API.request('POST', '/api/training-images', {
    lora_id: loraId,
    storage_id: storageId,
    filename: file.name,
    file_type: file.type,
    file_size: file.size,
  });
}

async function refreshSelectedLora(loraId) {
  const updatedLora = await API.getLora(loraId);
  if (updatedLora.success) {
    state.selectedLora = updatedLora.data;
    // Also update the LoRA in the list
    const idx = state.loras.findIndex(l => l._id === loraId);
    if (idx >= 0) {
      state.loras[idx] = updatedLora.data;
    }
    renderLoraList();
    showLoraDetail();
  } else {
    console.error('Failed to refresh LoRA:', updatedLora.error?.message);
  }
}

function startTraining() {
  if (!state.selectedLora) return;
  
  // Confirm before starting (costs money)
  if (!confirm(`Start training "${state.selectedLora.name}"?\n\nThis will take ~20 minutes and cost ~$2.`)) {
    return;
  }
  
  // Delegate to UI wrapper with API call
  withButtonLoading('#lora-train-btn', 'Starting...', async () => {
    const result = await startLoraTraining(state.selectedLora._id);
    if (result.success) {
      alert(`Training started!\n\nTraining ID: ${result.data.training_id}\n\nThis will take ~20 minutes. The status will update automatically.`);
      await refreshSelectedLora(state.selectedLora._id);
      return true; // Keep button in original state (via refresh)
    } else {
      showError('Training Failed', result.error?.message || 'Unknown error');
      return false; // Restore button
    }
  });
}

/**
 * Pure API call - no DOM access
 * @param {string} loraId 
 * @returns {Promise<{success: boolean, data?: object, error?: object}>}
 */
async function startLoraTraining(loraId) {
  try {
    return await API.request('POST', `/api/lora/${loraId}/train`);
  } catch (err) {
    console.error('Training error:', err);
    return { success: false, error: { message: err.message || 'Unknown error', suggestion: 'Check that the LoRA has training images uploaded' } };
  }
}

/**
 * Pure API call - no DOM access
 * @param {string} loraId 
 * @returns {Promise<{success: boolean, data?: object, error?: object}>}
 */
async function syncLoraStatus(loraId) {
  try {
    return await API.request('POST', `/api/lora/${loraId}/sync`);
  } catch (err) {
    console.error('Sync error:', err);
    return { success: false, error: { message: err.message || 'Unknown error', suggestion: 'Check that the training ID is valid on Replicate' } };
  }
}

/**
 * UI wrapper - handles button loading state (sync wrapper for async callback)
 * @param {string} selector - Button selector
 * @param {string} loadingText - Text to show while loading
 * @param {Function} asyncFn - Async function that returns success boolean
 */
function withButtonLoading(selector, loadingText, asyncFn) {
  const btn = $(selector);
  if (!btn) return;
  
  const originalText = btn.textContent;
  btn.textContent = loadingText;
  btn.disabled = true;
  
  // Call async function and restore button when done
  asyncFn().finally(() => {
    btn.textContent = originalText;
    btn.disabled = false;
  });
}

function syncStatus() {
  if (!state.selectedLora) return;
  
  withButtonLoading('#lora-sync-btn', 'Syncing...', async () => {
    const result = await syncLoraStatus(state.selectedLora._id);
    
    if (result.success) {
      alert(`Status synced!\n\nReplicate status: ${result.data.replicate_status}\nNew status: ${result.data.new_status}${result.data.lora_url ? '\n\nWeights URL saved!' : ''}`);
      await refreshSelectedLora(state.selectedLora._id);
    } else {
      showError('Sync Failed', result.error?.message || 'Unknown error');
    }
  });
}

function deleteLora() {
  if (!state.selectedLora) return;
  if (!confirm(`Delete "${state.selectedLora.name}"?`)) return;
  performDeleteLora();
}

async function performDeleteLora() {
  const result = await API.deleteLora(state.selectedLora._id);
  if (result.success) {
    state.selectedLora = null;
    await loadLoras();
    hideLoraCreateForm();
  } else {
    showError('Failed to delete', result.error?.message || 'Unknown error');
  }
}

// === Reference Images Management ===
function setupReferenceImages() {
  // Reference image dropzone (asset type editor)
  setupDropzone('#reference-dropzone', '#reference-input', handleReferenceFiles);
}

// handleReferenceDrop removed - now handled by setupDropzone utility

// AFD Pattern: Sync wrapper collects DOM, passes to async core
function handleReferenceFiles(files) {
  if (!state.selectedAssetType) return;

  // Sync: Collect all DOM values
  const modelSelect = $('#asset-type-model');
  const modelId = modelSelect ? modelSelect.value : '';
  
  // Delegate to async core with pure data
  handleReferenceFilesCore(files, modelId);
}

async function handleReferenceFilesCore(files, modelId) {
  const model = state.models.find((m) => m.id === modelId);
  const maxImages = model?.capabilities?.maxReferenceImages || 0;
  const currentCount = state.selectedAssetType.referenceImages?.length || 0;
  const remainingSlots = maxImages - currentCount;

  if (remainingSlots <= 0) {
    showError('Limit Reached', `Maximum ${maxImages} reference images allowed`);
    return;
  }

  const filesToUpload = Array.from(files).slice(0, remainingSlots);

  for (const file of filesToUpload) {
    if (!file.type.startsWith('image/')) continue;
    await uploadReferenceImage(file);
  }

  // Refresh asset type to get updated reference images
  await refreshAssetType();
}

async function uploadReferenceImage(file) {
  // 1. Get upload URL from Convex
  const urlResponse = await ConvexAPI.generateUploadUrl();
  if (!urlResponse.success) {
    console.error('Failed to get upload URL:', urlResponse.error?.message);
    return;
  }

  // 2. Upload to Convex storage
  const uploadResult = await API.uploadImage(urlResponse.data.uploadUrl, file);
  if (!uploadResult.success) {
    console.error('Failed to upload image:', uploadResult.error?.message);
    return;
  }

  // 3. Add to asset type via Convex
  const addResult = await ConvexAPI.request('POST', '/api/asset-types/add-reference-image', {
    id: state.selectedAssetType._id,
    storageId: uploadResult.data.storageId,
  });

  if (!addResult.success) {
    console.error('Failed to add reference image:', addResult.error?.message);
  }
}

async function removeReferenceImage(storageId) {
  if (!state.selectedAssetType) return;

  const result = await ConvexAPI.request('POST', '/api/asset-types/remove-reference-image', {
    id: state.selectedAssetType._id,
    storageId: storageId,
  });

  if (result.success) {
    await refreshAssetType();
  } else {
    showError('Failed to remove', result.error?.message || 'Unknown error');
  }
}

async function refreshAssetType() {
  if (!state.selectedAssetType) return;

  const result = await ConvexAPI.getAssetType(state.selectedAssetType._id);
  if (result.success) {
    state.selectedAssetType = result.data;
    renderReferenceImages();
    // Also update the list
    await loadAssetTypes();
  }
}

// AFD Pattern: Sync wrapper collects DOM, passes to async core
function renderReferenceImages() {
  // Sync: Collect DOM elements
  const preview = $('#reference-preview');
  const countDisplay = $('#reference-images-current');
  const images = state.selectedAssetType?.referenceImages || [];

  // Update count synchronously
  if (countDisplay) {
    countDisplay.textContent = images.length;
  }

  if (images.length === 0) {
    if (preview) preview.innerHTML = '';
    return;
  }

  // Delegate to async core, handle result with .then()
  fetchReferenceImageUrls(images).then((htmlContent) => {
    // Sync: DOM write happens in callback, not in async function
    if (preview) preview.innerHTML = htmlContent;
  });
}

async function fetchReferenceImageUrls(images) {
  // Pure async logic - no DOM access
  const imageElements = [];
  for (const storageId of images) {
    const urlResult = await ConvexAPI.request('GET', `/api/storage/get-url?storageId=${storageId}`);
    if (urlResult.success && urlResult.data.url) {
      imageElements.push(`
        <div class="upload-preview-item uploaded" data-storage-id="${storageId}">
          <img src="${urlResult.data.url}" alt="Reference image">
          <button class="btn-remove-ref" onclick="removeReferenceImage('${storageId}')" title="Remove">×</button>
        </div>
      `);
    }
  }
  return imageElements.join('');
}

// === Utilities ===
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
