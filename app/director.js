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
  isCreating: false,
  isConnected: false,
};

// DOM Helpers
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  setupSidebarTabs();
  setupAssetTypeEditor();
  setupPromptPreview();

  await checkHealth();
  await loadModels();
  await loadLoras();
  await loadAssetTypes();
});

// === Health Check ===
async function checkHealth() {
  try {
    const health = await API.health();
    state.isConnected = health.status !== 'error';
    updateStatusIndicator(health.status === 'healthy' ? 'connected' : 'degraded');
    $('#status-text').textContent = health.status === 'healthy' ? 'Ready' : 'Degraded';
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

  // Update content
  $('#sidebar-asset-types').classList.toggle('hidden', tabName !== 'asset-types');
  $('#sidebar-loras').classList.toggle('hidden', tabName !== 'loras');

  // Update editor panel
  $('#editor-panel').classList.add('hidden');
  $('#lora-editor-panel').classList.add('hidden');
  $('#editor-empty').classList.remove('hidden');

  state.activeSidebarTab = tabName;
  state.selectedAssetType = null;
  state.isCreating = false;
}

// === Load Data ===
async function loadModels() {
  try {
    const result = await API.request('GET', '/api/models/list');
    state.models = result.data || result.models || [];
    populateModelSelector();
  } catch (error) {
    console.error('Failed to load models:', error);
    state.models = [];
  }
}

async function loadLoras() {
  try {
    const result = await API.listLoras();
    const loras = result.data || result || [];
    state.loras = Array.isArray(loras) ? loras : [];
    populateLoraSelector();
    renderLoraList();
  } catch (error) {
    console.error('Failed to load LoRAs:', error);
    state.loras = [];
  }
}

async function loadAssetTypes() {
  try {
    const result = await API.request('GET', '/api/asset-types/list');
    state.assetTypes = result.data || result.assetTypes || [];
    renderAssetTypeList();
  } catch (error) {
    console.error('Failed to load asset types:', error);
    state.assetTypes = [];
    renderAssetTypeList();
  }
}

// === Render Lists ===
function renderAssetTypeList() {
  const list = $('#asset-type-list');

  if (state.assetTypes.length === 0) {
    list.innerHTML = '<div class="empty-state"><span class="empty-icon">📦</span><p>No asset types yet</p></div>';
    return;
  }

  list.innerHTML = state.assetTypes.map((at) => `
    <div class="asset-type-item ${state.selectedAssetType?._id === at._id ? 'active' : ''}" data-id="${at._id}">
      <div class="asset-type-item-info">
        <div class="asset-type-item-name">${escapeHtml(at.name)}</div>
        <div class="asset-type-item-model">${escapeHtml(at.model || 'No model')}</div>
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
    <div class="lora-item" data-id="${lora._id}">
      <div>
        <div class="lora-item-name">${escapeHtml(lora.name)}</div>
        <div class="lora-item-trigger">${escapeHtml(lora.triggerWord)}</div>
      </div>
      <span class="status-badge ${lora.status}">${lora.status}</span>
    </div>
  `).join('');
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

  // Populate form
  $('#asset-type-name').value = at?.name || '';
  $('#asset-type-description').value = at?.description || '';
  $('#asset-type-pre-prompt').value = at?.prePrompt || '';
  $('#asset-type-post-prompt').value = at?.postPrompt || '';
  $('#asset-type-model').value = at?.model || (state.models[0]?.id || '');
  $('#asset-type-lora').value = at?.loraId || '';
  $('#asset-type-quality').value = at?.qualityPreset || '';
  $('#asset-type-active').checked = at?.isActive ?? true;

  // Update dependent UI
  updateModelSettings();
  updateLoraVisibility();
  updatePromptPreview();

  // Show/hide delete button
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
  const name = $('#asset-type-name').value.trim();
  if (!name) {
    alert('Please enter a name');
    return;
  }

  const data = {
    name,
    description: $('#asset-type-description').value.trim() || undefined,
    prePrompt: $('#asset-type-pre-prompt').value.trim(),
    postPrompt: $('#asset-type-post-prompt').value.trim(),
    model: $('#asset-type-model').value,
    modelSettings: getModelSettings(),
    loraId: $('#asset-type-lora').value || undefined,
    qualityPreset: $('#asset-type-quality').value || undefined,
    isActive: $('#asset-type-active').checked,
  };

  try {
    if (state.isCreating) {
      await API.request('POST', '/api/asset-types/create', data);
    } else {
      await API.request('POST', '/api/asset-types/update', {
        id: state.selectedAssetType._id,
        ...data,
      });
    }

    await loadAssetTypes();
    hideEditor();
  } catch (error) {
    alert('Failed to save: ' + error.message);
  }
}

async function deleteAssetType() {
  if (!state.selectedAssetType) return;
  if (!confirm(`Delete "${state.selectedAssetType.name}"? This will deactivate the asset type.`)) return;

  try {
    await API.request('DELETE', `/api/asset-types/delete?id=${state.selectedAssetType._id}`);
    await loadAssetTypes();
    hideEditor();
  } catch (error) {
    alert('Failed to delete: ' + error.message);
  }
}

// === Utilities ===
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
