/**
 * Noisett Application
 * Manages UI state and calls API. Zero business logic - just rendering and events.
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
      inputSection: document.getElementById("input-section"),
      loadingSection: document.getElementById("loading-section"),
      resultsSection: document.getElementById("results-section"),
      errorSection: document.getElementById("error-section"),

      promptInput: document.getElementById("prompt-input"),
      charCount: document.getElementById("char-count"),
      assetType: document.getElementById("asset-type"),
      quality: document.getElementById("quality"),

      generateBtn: document.getElementById("generate-btn"),
      cancelBtn: document.getElementById("cancel-btn"),
      generateMoreBtn: document.getElementById("generate-more-btn"),
      newPromptBtn: document.getElementById("new-prompt-btn"),
      retryBtn: document.getElementById("retry-btn"),
      editPromptBtn: document.getElementById("edit-prompt-btn"),

      progressFill: document.getElementById("progress-fill"),
      progressText: document.getElementById("progress-text"),
      loadingCount: document.getElementById("loading-count"),

      imageGrid: document.getElementById("image-grid"),
      resultsPrompt: document.getElementById("results-prompt"),

      errorTitle: document.getElementById("error-title"),
      errorMessage: document.getElementById("error-message"),
      errorSuggestion: document.getElementById("error-suggestion"),

      userName: document.getElementById("user-name"),
      signOutBtn: document.getElementById("sign-out-btn"),
    };

    // Set up event listeners
    this.setupEventListeners();

    // Check API health
    try {
      await API.health();
      console.log("✅ API connected");
    } catch (error) {
      console.warn("⚠️ API not available, using mock mode");
    }

    // Show input form
    this.showInput();
  },

  /**
   * Set up event listeners.
   */
  setupEventListeners() {
    // Character count
    this.elements.promptInput.addEventListener("input", () => {
      const count = this.elements.promptInput.value.length;
      this.elements.charCount.textContent = `${count}/500`;
    });

    // Generate
    this.elements.generateBtn.addEventListener("click", () => this.generate());

    // Cancel
    this.elements.cancelBtn.addEventListener("click", () => this.cancel());

    // Generate more (same prompt)
    this.elements.generateMoreBtn.addEventListener("click", () =>
      this.generate()
    );

    // New prompt
    this.elements.newPromptBtn.addEventListener("click", () => this.reset());

    // Error actions
    this.elements.retryBtn.addEventListener("click", () => this.generate());
    this.elements.editPromptBtn.addEventListener("click", () =>
      this.showInput()
    );

    // Enter to submit (Ctrl+Enter)
    this.elements.promptInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && e.ctrlKey) {
        e.preventDefault();
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

    // Update loading count
    this.elements.loadingCount.textContent = "4";
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
    // Immediately check status
    this.checkStatus();

    // Then poll every 2 seconds
    this.pollInterval = setInterval(() => {
      this.checkStatus();
    }, 2000);
  },

  /**
   * Check job status.
   */
  async checkStatus() {
    if (!this.currentJobId) return;

    try {
      const result = await API.getJobStatus(this.currentJobId);
      const job = result.data.job;

      // Update progress
      this.updateProgress(job.progress || 0);

      // Check if complete
      if (job.status === "complete") {
        this.stopPolling();
        this.showResults(job);
      } else if (job.status === "failed") {
        this.stopPolling();
        this.showError({
          message: job.error_message || "Generation failed",
          suggestion: "Try a different prompt or asset type",
        });
      } else if (job.status === "cancelled") {
        this.stopPolling();
        this.showInput();
      }
    } catch (error) {
      this.stopPolling();
      this.showError(error);
    }
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
      console.error("Failed to cancel:", error);
      // Still show input even if cancel fails
      this.stopPolling();
      this.showInput();
    }
  },

  /**
   * Reset to initial state.
   */
  reset() {
    this.currentJobId = null;
    this.elements.promptInput.value = "";
    this.elements.charCount.textContent = "0/500";
    this.showInput();
  },

  // --- UI State Management ---

  showInput() {
    this.hideAll();
    this.elements.inputSection.classList.remove("hidden");
    this.elements.promptInput.focus();
  },

  showLoading() {
    this.hideAll();
    this.elements.loadingSection.classList.remove("hidden");
    this.updateProgress(0);
  },

  showResults(job) {
    this.hideAll();
    this.elements.resultsSection.classList.remove("hidden");
    this.elements.resultsPrompt.textContent = `"${
      job.prompt || this.elements.promptInput.value
    }"`;

    // Render images
    const images = job.images || [];
    if (images.length === 0) {
      // Mock images for demo
      this.elements.imageGrid.innerHTML = `
        <div class="image-card">
          <img src="https://placehold.co/512x512/e1dfdd/605e5c?text=Image+1" alt="Generated image 1" class="image-preview">
          <div class="image-overlay">
            <a href="#" class="btn btn-small">⬇ Download</a>
          </div>
        </div>
        <div class="image-card">
          <img src="https://placehold.co/512x512/e1dfdd/605e5c?text=Image+2" alt="Generated image 2" class="image-preview">
          <div class="image-overlay">
            <a href="#" class="btn btn-small">⬇ Download</a>
          </div>
        </div>
        <div class="image-card">
          <img src="https://placehold.co/512x512/e1dfdd/605e5c?text=Image+3" alt="Generated image 3" class="image-preview">
          <div class="image-overlay">
            <a href="#" class="btn btn-small">⬇ Download</a>
          </div>
        </div>
        <div class="image-card">
          <img src="https://placehold.co/512x512/e1dfdd/605e5c?text=Image+4" alt="Generated image 4" class="image-preview">
          <div class="image-overlay">
            <a href="#" class="btn btn-small">⬇ Download</a>
          </div>
        </div>
      `;
    } else {
      this.elements.imageGrid.innerHTML = images
        .map(
          (img, i) => `
        <div class="image-card">
          <img src="${img.url}" alt="Generated image ${
            i + 1
          }" class="image-preview">
          <div class="image-overlay">
            <a href="${
              img.url
            }" download="brand-asset-${Date.now()}-${i}.png" class="btn btn-small">
              ⬇ Download
            </a>
          </div>
        </div>
      `
        )
        .join("");
    }
  },

  showError(error) {
    this.hideAll();
    this.elements.errorSection.classList.remove("hidden");
    this.elements.errorTitle.textContent = error.code || "Generation failed";
    this.elements.errorMessage.textContent =
      error.message || "An unexpected error occurred";
    this.elements.errorSuggestion.textContent =
      error.suggestion || "Please try again";
  },

  hideAll() {
    this.elements.inputSection.classList.add("hidden");
    this.elements.loadingSection.classList.add("hidden");
    this.elements.resultsSection.classList.add("hidden");
    this.elements.errorSection.classList.add("hidden");
  },

  updateProgress(percent) {
    this.elements.progressFill.style.width = `${percent}%`;
    this.elements.progressText.textContent = `${Math.round(percent)}% complete`;
  },
};

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => App.init());
