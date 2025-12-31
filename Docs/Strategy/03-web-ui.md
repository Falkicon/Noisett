# Web UI Implementation

The web UI is a **thin vanilla JS wrapper** over the REST API. Following AFD principles, it contains zero business logic—all functionality comes from commands exposed via FastAPI.

---

## Philosophy

> "The best UI is no UI" — AFD inverts traditional development by making commands the application and UI just one possible surface.

### Why Vanilla JS?

| Reason | Explanation |
|--------|-------------|
| **Small surface** | ~3 screens total, no complex state management needed |
| **Easy to swap** | AFD makes the UI disposable—can replace with React/Vue/FAST Element later |
| **Fast iteration** | No build step during development, instant reload |
| **Team accessibility** | Any developer can modify without framework knowledge |
| **Proves AFD** | Demonstrates that commands are truly the source of truth |

### UI Responsibilities

The UI is responsible for:
- Rendering state received from API
- Capturing user input
- Calling REST endpoints
- Showing loading/error states

The UI is **NOT** responsible for:
- Business logic
- Validation (server validates)
- Data transformation
- State management beyond current view

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser (Vanilla JS)                                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  index.html          │  styles.css         │  app.js        ││
│  │  - Structure         │  - Design tokens    │  - API calls   ││
│  │  - Semantic HTML     │  - Components       │  - DOM updates ││
│  │  - Accessibility     │  - Responsive       │  - Events      ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│                              │ fetch()                           │
│                              ▼                                   │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI REST Server                                             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  POST /api/generate   │  GET /api/jobs/{id}  │  GET /api/... ││
│  │       │                      │                               ││
│  │       ▼                      ▼                               ││
│  │  Commands (same as MCP/CLI)                                  ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
web/
├── index.html          # Single page app shell
├── styles.css          # All styles (design tokens + components)
├── app.js              # Application logic
├── api.js              # API client (thin wrapper over fetch)
└── auth.js             # Entra ID authentication (MSAL)
```

---

## HTML Structure

```html
<!-- web/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Brand Asset Generator</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <!-- Header -->
  <header class="header">
    <div class="header-brand">
      <span class="header-logo">🎨</span>
      <h1 class="header-title">Brand Asset Generator</h1>
    </div>
    <div class="header-user">
      <span id="user-name"></span>
      <button id="sign-out-btn" class="btn btn-text">Sign out</button>
    </div>
  </header>

  <!-- Main Content -->
  <main class="main">
    <!-- Input Section -->
    <section id="input-section" class="section section-input">
      <h2 class="section-title">Describe what you need</h2>
      
      <div class="form-group">
        <label for="prompt-input" class="label">Prompt</label>
        <textarea 
          id="prompt-input" 
          class="input input-textarea"
          placeholder="e.g., A person collaborating with AI on a creative project"
          maxlength="500"
          rows="3"
        ></textarea>
        <span id="char-count" class="char-count">0/500</span>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label for="asset-type" class="label">Asset type</label>
          <select id="asset-type" class="input input-select">
            <option value="product">Product Illustrations</option>
            <option value="icons">Icons (Fluent 2)</option>
            <option value="logo">Logo Illustrations</option>
            <option value="premium">Premium Illustrations</option>
          </select>
        </div>

        <div class="form-group">
          <label for="quality" class="label">Quality</label>
          <select id="quality" class="input input-select">
            <option value="draft">Draft (~10 sec)</option>
            <option value="standard" selected>Standard (~25 sec)</option>
            <option value="high">High (~45 sec)</option>
          </select>
        </div>
      </div>

      <button id="generate-btn" class="btn btn-primary btn-large">
        Generate
      </button>

      <p class="tip">
        💡 <strong>Tip:</strong> Be specific about the subject, composition, and style you want.
      </p>
    </section>

    <!-- Loading Section (hidden by default) -->
    <section id="loading-section" class="section section-loading hidden">
      <div class="loading-content">
        <div class="spinner"></div>
        <h2 class="loading-title">Generating...</h2>
        <p class="loading-subtitle">Creating <span id="loading-count">4</span> variations</p>
        <div class="progress-bar">
          <div id="progress-fill" class="progress-fill" style="width: 0%"></div>
        </div>
        <p id="progress-text" class="progress-text">0% complete</p>
        <button id="cancel-btn" class="btn btn-secondary">Cancel</button>
      </div>
    </section>

    <!-- Results Section (hidden by default) -->
    <section id="results-section" class="section section-results hidden">
      <div class="results-header">
        <h2 class="section-title">Results</h2>
        <p id="results-prompt" class="results-prompt"></p>
      </div>

      <div id="image-grid" class="image-grid">
        <!-- Images injected by JS -->
      </div>

      <div class="results-actions">
        <button id="generate-more-btn" class="btn btn-primary">Generate More</button>
        <button id="new-prompt-btn" class="btn btn-secondary">New Prompt</button>
      </div>
    </section>

    <!-- Error Section (hidden by default) -->
    <section id="error-section" class="section section-error hidden">
      <div class="error-content">
        <span class="error-icon">⚠️</span>
        <h2 id="error-title" class="error-title">Generation failed</h2>
        <p id="error-message" class="error-message"></p>
        <p id="error-suggestion" class="error-suggestion"></p>
        <div class="error-actions">
          <button id="retry-btn" class="btn btn-primary">Try Again</button>
          <button id="edit-prompt-btn" class="btn btn-secondary">Edit Prompt</button>
        </div>
      </div>
    </section>
  </main>

  <!-- Auth (hidden login screen) -->
  <div id="auth-screen" class="auth-screen hidden">
    <div class="auth-content">
      <span class="auth-icon">🔐</span>
      <h1 class="auth-title">Sign in to continue</h1>
      <p class="auth-hint">Use your work account to access Brand Asset Generator</p>
      <button id="sign-in-btn" class="btn btn-primary btn-large">Sign in with SSO</button>
    </div>
  </div>

  <!-- Scripts -->
  <script src="https://alcdn.msauth.net/browser/2.38.0/js/msal-browser.min.js"></script>
  <script src="auth.js"></script>
  <script src="api.js"></script>
  <script src="app.js"></script>
</body>
</html>
```

---

## API Client

```javascript
// web/api.js

/**
 * Thin API client - just wraps fetch with auth token.
 * All business logic is on the server.
 */
const API = {
  baseUrl: '/api',

  /**
   * Make authenticated API request.
   */
  async request(method, path, body = null) {
    const token = await Auth.getToken();
    
    const options = {
      method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${this.baseUrl}${path}`, options);
    const data = await response.json();

    // Server returns CommandResult format
    if (!data.success && data.error) {
      const error = new Error(data.error.message);
      error.code = data.error.code;
      error.suggestion = data.error.suggestion;
      throw error;
    }

    return data;
  },

  // --- Commands (mirror server commands) ---

  async generate(prompt, assetType, quality, count = 4) {
    return this.request('POST', '/generate', {
      prompt,
      asset_type: assetType,
      quality,
      count,
    });
  },

  async getJobStatus(jobId) {
    return this.request('GET', `/jobs/${jobId}`);
  },

  async cancelJob(jobId) {
    return this.request('DELETE', `/jobs/${jobId}`);
  },

  async getAssetTypes() {
    return this.request('GET', '/asset-types');
  },

  async getModels() {
    return this.request('GET', '/models');
  },
};
```

---

## Application Logic

```javascript
// web/app.js

/**
 * Main application logic.
 * Manages UI state and calls API.
 */
const App = {
  // Current state
  currentJobId: null,
  pollInterval: null,

  // DOM elements (cached on init)
  elements: {},

  /**
   * Initialize application.
   */
  async init() {
    // Cache DOM elements
    this.elements = {
      inputSection: document.getElementById('input-section'),
      loadingSection: document.getElementById('loading-section'),
      resultsSection: document.getElementById('results-section'),
      errorSection: document.getElementById('error-section'),
      authScreen: document.getElementById('auth-screen'),
      
      promptInput: document.getElementById('prompt-input'),
      charCount: document.getElementById('char-count'),
      assetType: document.getElementById('asset-type'),
      quality: document.getElementById('quality'),
      
      generateBtn: document.getElementById('generate-btn'),
      cancelBtn: document.getElementById('cancel-btn'),
      generateMoreBtn: document.getElementById('generate-more-btn'),
      newPromptBtn: document.getElementById('new-prompt-btn'),
      retryBtn: document.getElementById('retry-btn'),
      editPromptBtn: document.getElementById('edit-prompt-btn'),
      
      progressFill: document.getElementById('progress-fill'),
      progressText: document.getElementById('progress-text'),
      loadingCount: document.getElementById('loading-count'),
      
      imageGrid: document.getElementById('image-grid'),
      resultsPrompt: document.getElementById('results-prompt'),
      
      errorTitle: document.getElementById('error-title'),
      errorMessage: document.getElementById('error-message'),
      errorSuggestion: document.getElementById('error-suggestion'),
      
      userName: document.getElementById('user-name'),
      signOutBtn: document.getElementById('sign-out-btn'),
      signInBtn: document.getElementById('sign-in-btn'),
    };

    // Set up event listeners
    this.setupEventListeners();

    // Check authentication
    const user = await Auth.init();
    if (user) {
      this.showApp(user);
    } else {
      this.showAuthScreen();
    }
  },

  /**
   * Set up event listeners.
   */
  setupEventListeners() {
    // Character count
    this.elements.promptInput.addEventListener('input', () => {
      const count = this.elements.promptInput.value.length;
      this.elements.charCount.textContent = `${count}/500`;
    });

    // Generate
    this.elements.generateBtn.addEventListener('click', () => this.generate());
    
    // Cancel
    this.elements.cancelBtn.addEventListener('click', () => this.cancel());
    
    // Generate more (same prompt)
    this.elements.generateMoreBtn.addEventListener('click', () => this.generate());
    
    // New prompt
    this.elements.newPromptBtn.addEventListener('click', () => this.reset());
    
    // Error actions
    this.elements.retryBtn.addEventListener('click', () => this.generate());
    this.elements.editPromptBtn.addEventListener('click', () => this.showInput());
    
    // Auth
    this.elements.signInBtn.addEventListener('click', () => Auth.signIn());
    this.elements.signOutBtn.addEventListener('click', () => Auth.signOut());

    // Enter to submit
    this.elements.promptInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && e.ctrlKey) {
        this.generate();
      }
    });
  },

  /**
   * Generate images.
   */
  async generate() {
    const prompt = this.elements.promptInput.value.trim();
    if (!prompt) {
      this.elements.promptInput.focus();
      return;
    }

    const assetType = this.elements.assetType.value;
    const quality = this.elements.quality.value;

    this.showLoading();

    try {
      // Start generation
      const result = await API.generate(prompt, assetType, quality);
      this.currentJobId = result.data.job.id;
      
      // Poll for status
      this.startPolling();
    } catch (error) {
      this.showError(error);
    }
  },

  /**
   * Start polling for job status.
   */
  startPolling() {
    this.pollInterval = setInterval(async () => {
      try {
        const result = await API.getJobStatus(this.currentJobId);
        const job = result.data.job;

        // Update progress
        this.updateProgress(job.progress);

        // Check if complete
        if (job.status === 'complete') {
          this.stopPolling();
          this.showResults(job);
        } else if (job.status === 'failed') {
          this.stopPolling();
          this.showError({
            message: job.error_message || 'Generation failed',
            suggestion: 'Try a different prompt or asset type',
          });
        } else if (job.status === 'cancelled') {
          this.stopPolling();
          this.showInput();
        }
      } catch (error) {
        this.stopPolling();
        this.showError(error);
      }
    }, 2000); // Poll every 2 seconds
  },

  /**
   * Stop polling.
   */
  stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  },

  /**
   * Cancel current job.
   */
  async cancel() {
    if (!this.currentJobId) return;

    try {
      await API.cancelJob(this.currentJobId);
      this.stopPolling();
      this.showInput();
    } catch (error) {
      console.error('Failed to cancel:', error);
    }
  },

  /**
   * Reset to initial state.
   */
  reset() {
    this.currentJobId = null;
    this.elements.promptInput.value = '';
    this.elements.charCount.textContent = '0/500';
    this.showInput();
  },

  // --- UI State Management ---

  showApp(user) {
    this.elements.authScreen.classList.add('hidden');
    this.elements.userName.textContent = user.name || user.email;
    this.showInput();
  },

  showAuthScreen() {
    this.elements.authScreen.classList.remove('hidden');
    this.hideAll();
  },

  showInput() {
    this.hideAll();
    this.elements.inputSection.classList.remove('hidden');
    this.elements.promptInput.focus();
  },

  showLoading() {
    this.hideAll();
    this.elements.loadingSection.classList.remove('hidden');
    this.updateProgress(0);
  },

  showResults(job) {
    this.hideAll();
    this.elements.resultsSection.classList.remove('hidden');
    this.elements.resultsPrompt.textContent = `"${job.prompt}"`;
    
    // Render images
    this.elements.imageGrid.innerHTML = job.images.map((img, i) => `
      <div class="image-card">
        <img src="${img.url}" alt="Generated image ${i + 1}" class="image-preview">
        <div class="image-overlay">
          <a href="${img.url}" download="brand-asset-${Date.now()}-${i}.png" class="btn btn-small">
            ⬇ Download
          </a>
        </div>
      </div>
    `).join('');
  },

  showError(error) {
    this.hideAll();
    this.elements.errorSection.classList.remove('hidden');
    this.elements.errorTitle.textContent = error.code || 'Generation failed';
    this.elements.errorMessage.textContent = error.message;
    this.elements.errorSuggestion.textContent = error.suggestion || '';
  },

  hideAll() {
    this.elements.inputSection.classList.add('hidden');
    this.elements.loadingSection.classList.add('hidden');
    this.elements.resultsSection.classList.add('hidden');
    this.elements.errorSection.classList.add('hidden');
  },

  updateProgress(percent) {
    this.elements.progressFill.style.width = `${percent}%`;
    this.elements.progressText.textContent = `${Math.round(percent)}% complete`;
  },
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => App.init());
```

---

## Authentication

```javascript
// web/auth.js

/**
 * Microsoft Entra ID authentication using MSAL.
 */
const Auth = {
  msalInstance: null,
  account: null,

  /**
   * Initialize MSAL and check for existing session.
   */
  async init() {
    const msalConfig = {
      auth: {
        clientId: window.NOISETT_CONFIG?.clientId || '',
        authority: `https://login.microsoftonline.com/${window.NOISETT_CONFIG?.tenantId || ''}`,
        redirectUri: window.location.origin,
      },
      cache: {
        cacheLocation: 'sessionStorage',
      },
    };

    this.msalInstance = new msal.PublicClientApplication(msalConfig);
    
    // Handle redirect response
    const response = await this.msalInstance.handleRedirectPromise();
    if (response) {
      this.account = response.account;
    } else {
      const accounts = this.msalInstance.getAllAccounts();
      if (accounts.length > 0) {
        this.account = accounts[0];
      }
    }

    return this.account;
  },

  /**
   * Start sign-in flow.
   */
  async signIn() {
    const loginRequest = {
      scopes: [`api://${window.NOISETT_CONFIG?.clientId}/access_as_user`],
    };

    try {
      await this.msalInstance.loginRedirect(loginRequest);
    } catch (error) {
      console.error('Sign in failed:', error);
    }
  },

  /**
   * Sign out.
   */
  async signOut() {
    await this.msalInstance.logoutRedirect();
  },

  /**
   * Get access token for API calls.
   */
  async getToken() {
    if (!this.account) {
      throw new Error('Not authenticated');
    }

    const tokenRequest = {
      scopes: [`api://${window.NOISETT_CONFIG?.clientId}/access_as_user`],
      account: this.account,
    };

    try {
      const response = await this.msalInstance.acquireTokenSilent(tokenRequest);
      return response.accessToken;
    } catch (error) {
      // Silent token acquisition failed, try redirect
      await this.msalInstance.acquireTokenRedirect(tokenRequest);
    }
  },
};
```

---

## CSS (Design Tokens)

The styles use design tokens from the existing `specs-design/04-Design-Tokens-and-Visual-Language.spec.md`:

```css
/* web/styles.css */

/* === Design Tokens === */
:root {
  /* Colors */
  --color-primary: #0078D4;
  --color-primary-hover: #106EBE;
  --color-primary-active: #005A9E;
  --color-error: #D13438;
  --color-gray-900: #201F1E;
  --color-gray-700: #605E5C;
  --color-gray-500: #8A8886;
  --color-gray-300: #C8C6C4;
  --color-gray-200: #E1DFDD;
  --color-gray-100: #F3F2F1;
  --color-gray-50: #FAF9F8;
  --color-white: #FFFFFF;

  /* Typography */
  --font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-size-base: 15px;
  --font-size-lg: 20px;
  --font-size-xl: 24px;

  /* Spacing */
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;

  /* Borders */
  --radius-md: 8px;
  --radius-lg: 12px;

  /* Shadows */
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
  --shadow-lg: 0 8px 16px rgba(0,0,0,0.1);
}

/* === Base === */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  color: var(--color-gray-900);
  background: var(--color-gray-50);
  min-height: 100vh;
}

/* === Layout === */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-6);
  background: var(--color-white);
  border-bottom: 1px solid var(--color-gray-200);
  height: 64px;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.header-logo {
  font-size: 24px;
}

.header-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.main {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--space-8) var(--space-4);
}

/* === Sections === */
.section {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-md);
}

.section-title {
  font-size: var(--font-size-xl);
  margin-bottom: var(--space-4);
}

/* === Form Elements === */
.form-group {
  margin-bottom: var(--space-4);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.label {
  display: block;
  font-weight: 600;
  margin-bottom: var(--space-2);
  color: var(--color-gray-700);
}

.input {
  width: 100%;
  padding: var(--space-3);
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  font-family: inherit;
}

.input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(0, 120, 212, 0.2);
}

.input-textarea {
  resize: vertical;
  min-height: 80px;
}

.char-count {
  display: block;
  text-align: right;
  font-size: 13px;
  color: var(--color-gray-500);
  margin-top: var(--space-2);
}

/* === Buttons === */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: background-color 0.2s;
}

.btn-primary {
  background: var(--color-primary);
  color: var(--color-white);
}

.btn-primary:hover {
  background: var(--color-primary-hover);
}

.btn-secondary {
  background: var(--color-gray-100);
  color: var(--color-gray-900);
}

.btn-secondary:hover {
  background: var(--color-gray-200);
}

.btn-text {
  background: transparent;
  color: var(--color-gray-700);
}

.btn-large {
  padding: var(--space-4) var(--space-6);
  font-size: 16px;
  min-width: 160px;
}

.btn-small {
  padding: var(--space-2) var(--space-3);
  font-size: 13px;
}

/* === Loading === */
.section-loading {
  text-align: center;
  padding: var(--space-8);
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--color-gray-200);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto var(--space-4);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.progress-bar {
  height: 4px;
  background: var(--color-gray-200);
  border-radius: 2px;
  margin: var(--space-4) 0;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  transition: width 0.3s ease;
}

/* === Results === */
.image-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
  margin: var(--space-4) 0;
}

.image-card {
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
  aspect-ratio: 1;
}

.image-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: var(--space-3);
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
  opacity: 0;
  transition: opacity 0.2s;
}

.image-card:hover .image-overlay {
  opacity: 1;
}

.results-actions {
  display: flex;
  gap: var(--space-3);
  margin-top: var(--space-4);
}

/* === Error === */
.section-error {
  text-align: center;
}

.error-icon {
  font-size: 48px;
  margin-bottom: var(--space-4);
}

.error-suggestion {
  color: var(--color-gray-700);
  margin-top: var(--space-2);
}

.error-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: center;
  margin-top: var(--space-4);
}

/* === Auth === */
.auth-screen {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-gray-50);
}

.auth-content {
  text-align: center;
  background: var(--color-white);
  padding: var(--space-8);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

.auth-icon {
  font-size: 48px;
  margin-bottom: var(--space-4);
}

/* === Utilities === */
.hidden {
  display: none !important;
}

.tip {
  margin-top: var(--space-4);
  padding: var(--space-3);
  background: var(--color-gray-100);
  border-radius: var(--radius-md);
  color: var(--color-gray-700);
  font-size: 14px;
}

/* === Responsive === */
@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .image-grid {
    grid-template-columns: 1fr;
  }
  
  .image-overlay {
    opacity: 1;
  }
}

/* === Reduced Motion === */
@media (prefers-reduced-motion: reduce) {
  .spinner {
    animation: none;
  }
  
  * {
    transition-duration: 0.01ms !important;
  }
}
```

---

## Serving the UI

The FastAPI server serves the static files:

```python
# In src/server/api.py
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="web", html=True), name="static")
```

Or for development, use any static file server:

```bash
# Python
python -m http.server 8080 --directory web

# Node
npx serve web
```

---

## Key Principles Maintained

1. **Zero business logic in UI** — All validation, generation, and state management happens server-side
2. **Commands as source of truth** — UI just renders what commands return
3. **Swappable** — Can replace vanilla JS with React/Vue/FAST Element without changing server
4. **Progressive enhancement** — Works with JavaScript disabled (shows auth screen)
5. **Accessible** — Semantic HTML, focus management, screen reader support
