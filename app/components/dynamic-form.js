/**
 * Dynamic Form Component
 * Renders form inputs from model settings schema
 *
 * Supports input types: range, select, checkbox, number
 *
 * Usage:
 *   const form = new DynamicForm(containerElement, {
 *     onChange: (key, value) => console.log(key, value),
 *   });
 *   form.render(modelSettings);
 *   const values = form.getValues();
 */

class DynamicForm {
  /**
   * @param {HTMLElement} container - Container element to render form into
   * @param {Object} options - Configuration options
   * @param {Function} [options.onChange] - Callback when any value changes (key, value, allValues)
   */
  constructor(container, options = {}) {
    this.container = container;
    this.options = options;
    this.settings = [];
    this.values = {};
  }

  /**
   * Render form from settings schema
   * @param {Array} settings - Array of setting definitions from model schema
   */
  render(settings) {
    this.settings = settings || [];
    this.container.innerHTML = '';

    if (this.settings.length === 0) {
      this.container.innerHTML = '<p class="dynamic-form-empty">No configurable settings</p>';
      return;
    }

    // Initialize values with defaults
    this.values = {};
    this.settings.forEach((setting) => {
      this.values[setting.key] = setting.default;
    });

    // Create form element
    const form = document.createElement('div');
    form.className = 'dynamic-form';

    this.settings.forEach((setting) => {
      const field = this.createField(setting);
      form.appendChild(field);
    });

    this.container.appendChild(form);
  }

  /**
   * Create a form field based on setting type
   * @param {Object} setting - Setting definition
   * @returns {HTMLElement}
   */
  createField(setting) {
    const wrapper = document.createElement('div');
    wrapper.className = 'dynamic-form-field';
    wrapper.dataset.key = setting.key;

    const label = document.createElement('label');
    label.className = 'dynamic-form-label';
    label.htmlFor = `df-${setting.key}`;
    label.textContent = setting.label;
    wrapper.appendChild(label);

    let input;
    switch (setting.type) {
      case 'range':
        input = this.createRangeInput(setting);
        break;
      case 'select':
        input = this.createSelectInput(setting);
        break;
      case 'checkbox':
        input = this.createCheckboxInput(setting);
        break;
      case 'number':
        input = this.createNumberInput(setting);
        break;
      default:
        input = this.createTextInput(setting);
    }

    wrapper.appendChild(input);

    // Add hint if provided
    if (setting.hint) {
      const hint = document.createElement('span');
      hint.className = 'dynamic-form-hint';
      hint.textContent = setting.hint;
      wrapper.appendChild(hint);
    }

    return wrapper;
  }

  /**
   * Create range (slider) input with value display
   * @param {Object} setting
   * @returns {HTMLElement}
   */
  createRangeInput(setting) {
    const container = document.createElement('div');
    container.className = 'dynamic-form-range';

    const input = document.createElement('input');
    input.type = 'range';
    input.id = `df-${setting.key}`;
    input.name = setting.key;
    input.min = setting.min ?? 0;
    input.max = setting.max ?? 100;
    input.step = setting.step ?? 1;
    input.value = setting.default ?? setting.min ?? 0;
    input.className = 'dynamic-form-input dynamic-form-input-range';

    const valueDisplay = document.createElement('span');
    valueDisplay.className = 'dynamic-form-range-value';
    valueDisplay.textContent = input.value;

    input.addEventListener('input', () => {
      valueDisplay.textContent = input.value;
      this.handleChange(setting.key, parseFloat(input.value));
    });

    container.appendChild(input);
    container.appendChild(valueDisplay);

    return container;
  }

  /**
   * Create select (dropdown) input
   * @param {Object} setting
   * @returns {HTMLElement}
   */
  createSelectInput(setting) {
    const select = document.createElement('select');
    select.id = `df-${setting.key}`;
    select.name = setting.key;
    select.className = 'dynamic-form-input dynamic-form-input-select';

    const options = setting.options || [];
    options.forEach((opt) => {
      const option = document.createElement('option');
      // Support both string options and {value, label} objects
      if (typeof opt === 'object') {
        option.value = opt.value;
        option.textContent = opt.label || opt.value;
      } else {
        option.value = opt;
        option.textContent = opt;
      }
      if (option.value === setting.default) {
        option.selected = true;
      }
      select.appendChild(option);
    });

    select.addEventListener('change', () => {
      this.handleChange(setting.key, select.value);
    });

    return select;
  }

  /**
   * Create checkbox input
   * @param {Object} setting
   * @returns {HTMLElement}
   */
  createCheckboxInput(setting) {
    const container = document.createElement('div');
    container.className = 'dynamic-form-checkbox';

    const input = document.createElement('input');
    input.type = 'checkbox';
    input.id = `df-${setting.key}`;
    input.name = setting.key;
    input.checked = setting.default ?? false;
    input.className = 'dynamic-form-input dynamic-form-input-checkbox';

    const checkLabel = document.createElement('span');
    checkLabel.className = 'dynamic-form-checkbox-label';
    checkLabel.textContent = setting.checkLabel || '';

    input.addEventListener('change', () => {
      this.handleChange(setting.key, input.checked);
    });

    container.appendChild(input);
    if (setting.checkLabel) {
      container.appendChild(checkLabel);
    }

    return container;
  }

  /**
   * Create number input with optional min/max
   * @param {Object} setting
   * @returns {HTMLElement}
   */
  createNumberInput(setting) {
    const input = document.createElement('input');
    input.type = 'number';
    input.id = `df-${setting.key}`;
    input.name = setting.key;
    input.className = 'dynamic-form-input dynamic-form-input-number';
    input.value = setting.default ?? '';

    if (setting.min !== undefined) input.min = setting.min;
    if (setting.max !== undefined) input.max = setting.max;
    if (setting.step !== undefined) input.step = setting.step;

    input.addEventListener('input', () => {
      const value = input.value === '' ? null : parseFloat(input.value);
      this.handleChange(setting.key, value);
    });

    return input;
  }

  /**
   * Create text input (fallback)
   * @param {Object} setting
   * @returns {HTMLElement}
   */
  createTextInput(setting) {
    const input = document.createElement('input');
    input.type = 'text';
    input.id = `df-${setting.key}`;
    input.name = setting.key;
    input.className = 'dynamic-form-input dynamic-form-input-text';
    input.value = setting.default ?? '';

    input.addEventListener('input', () => {
      this.handleChange(setting.key, input.value);
    });

    return input;
  }

  /**
   * Handle value change
   * @param {string} key
   * @param {*} value
   */
  handleChange(key, value) {
    this.values[key] = value;
    if (this.options.onChange) {
      this.options.onChange(key, value, this.values);
    }
  }

  /**
   * Get all current form values
   * @returns {Object} Key-value pairs of all settings
   */
  getValues() {
    return { ...this.values };
  }

  /**
   * Set form values programmatically
   * @param {Object} values - Key-value pairs to set
   */
  setValues(values) {
    Object.entries(values).forEach(([key, value]) => {
      this.values[key] = value;

      // Update DOM element
      const input = this.container.querySelector(`#df-${key}`);
      if (!input) return;

      if (input.type === 'checkbox') {
        input.checked = value;
      } else if (input.type === 'range') {
        input.value = value;
        // Update value display
        const display = input.parentElement.querySelector('.dynamic-form-range-value');
        if (display) display.textContent = value;
      } else {
        input.value = value;
      }
    });
  }

  /**
   * Reset form to default values
   */
  reset() {
    this.settings.forEach((setting) => {
      this.values[setting.key] = setting.default;
    });
    this.setValues(this.values);
  }

  /**
   * Disable all form inputs
   */
  disable() {
    this.container.querySelectorAll('.dynamic-form-input').forEach((input) => {
      input.disabled = true;
    });
  }

  /**
   * Enable all form inputs
   */
  enable() {
    this.container.querySelectorAll('.dynamic-form-input').forEach((input) => {
      input.disabled = false;
    });
  }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DynamicForm;
}
