/**
 * Settings Management JavaScript
 * 
 * Handles the settings interface, validation, and API interactions
 * Includes comprehensive work week configuration functionality
 */

class SettingsManager {
    constructor() {
        this.settings = {};
        this.categories = {};
        this.changedSettings = new Set();
        this.currentCategory = 'filesystem';
        this.syncManager = new SyncManager();
        this.init();
    }

    async init() {
        try {
            await this.loadSettings();
            await this.loadCategories();
            this.setupEventListeners();
            this.renderSettings();
            await this.initializeWorkWeekSettings();
            this.showCategory(this.currentCategory);
        } catch (error) {
            console.error('Failed to initialize settings:', error);
            Utils.showToast('Failed to load settings', 'error');
        }
    }

    async loadSettings() {
        try {
            const response = await fetch('/api/settings/');
            if (!response.ok) throw new Error('Failed to fetch settings');

            this.settings = await response.json();
        } catch (error) {
            console.error('Failed to load settings:', error);
            throw error;
        }
    }

    async loadCategories() {
        try {
            const response = await fetch('/api/settings/categories');
            if (!response.ok) throw new Error('Failed to fetch categories');

            const data = await response.json();
            this.categories = data.categories;
        } catch (error) {
            console.error('Failed to load categories:', error);
            throw error;
        }
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item[data-category]').forEach(item => {
            item.addEventListener('click', (e) => {
                const category = e.currentTarget.dataset.category;
                this.showCategory(category);
            });
        });

        // Back button
        document.getElementById('back-btn')?.addEventListener('click', () => {
            window.location.href = '/';
        });

        // Action buttons
        document.getElementById('save-all-btn')?.addEventListener('click', () => {
            this.saveAllChanges();
        });

        document.getElementById('export-btn')?.addEventListener('click', () => {
            this.exportSettings();
        });

        document.getElementById('import-btn')?.addEventListener('click', () => {
            this.showImportModal();
        });

        document.getElementById('reset-all-btn')?.addEventListener('click', () => {
            this.showResetModal();
        });

        // Modal handlers
        this.setupModalHandlers();
    }

    setupModalHandlers() {
        // Import modal
        document.getElementById('close-import-modal')?.addEventListener('click', () => {
            this.hideImportModal();
        });

        document.getElementById('cancel-import')?.addEventListener('click', () => {
            this.hideImportModal();
        });

        document.getElementById('confirm-import')?.addEventListener('click', () => {
            this.importSettings();
        });

        // Reset modal
        document.getElementById('close-reset-modal')?.addEventListener('click', () => {
            this.hideResetModal();
        });

        document.getElementById('cancel-reset')?.addEventListener('click', () => {
            this.hideResetModal();
        });

        document.getElementById('confirm-reset')?.addEventListener('click', () => {
            this.resetAllSettings();
        });

        // Close modals on backdrop click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        });
    }

    showCategory(category) {
        // Update navigation
        document.querySelectorAll('.nav-item[data-category]').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-category="${category}"]`)?.classList.add('active');

        // Update panels
        document.querySelectorAll('.settings-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        document.getElementById(`${category}-panel`)?.classList.add('active');

        this.currentCategory = category;

        // Initialize sync panel if selected
        if (category === 'sync') {
            this.syncManager.init();
        }
    }

    renderSettings() {
        Object.keys(this.categories).forEach(category => {
            this.renderCategorySettings(category);
        });
    }

    renderCategorySettings(category) {
        const container = document.getElementById(`${category}-settings`);
        if (!container) return;

        const categorySettings = this.categories[category] || [];

        container.innerHTML = categorySettings.map(settingKey => {
            const setting = this.settings[settingKey];
            if (!setting) return '';

            return this.renderSettingItem(setting);
        }).join('');

        // Add event listeners to the rendered settings
        this.addSettingEventListeners(container);
    }

    renderSettingItem(setting) {
        const isReadonly = this.isReadonlySetting(setting.key);
        const inputHtml = this.renderSettingInput(setting, isReadonly);

        return `
      <div class="setting-item" data-key="${setting.key}">
        <div class="setting-header">
          <div class="setting-info">
            <h3 class="setting-label">${this.formatSettingLabel(setting.key)}</h3>
            <p class="setting-description">${setting.description || ''}</p>
          </div>
          <div class="setting-actions">
            ${!isReadonly ? `
              <button class="btn-icon reset-setting-btn" title="Reset to default" data-key="${setting.key}">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <polyline points="23,4 23,10 17,10" stroke="currentColor" stroke-width="2"/>
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" stroke="currentColor" stroke-width="2"/>
                </svg>
              </button>
            ` : ''}
          </div>
        </div>
        
        <div class="setting-control">
          ${inputHtml}
        </div>
        
        <div class="setting-status">
          <div class="status-indicator ${isReadonly ? 'readonly' : ''}" data-key="${setting.key}"></div>
          <span class="status-text">${isReadonly ? 'Read-only' : 'Default'}</span>
        </div>
        
        ${setting.key.includes('_path') ? '<div class="path-validation" data-key="' + setting.key + '"></div>' : ''}
      </div>
    `;
    }

    renderSettingInput(setting, isReadonly) {
        const value = setting.parsed_value;
        const key = setting.key;

        switch (setting.value_type) {
            case 'boolean':
                return `
          <label class="setting-control">
            <input type="checkbox" class="setting-checkbox" data-key="${key}" 
                   ${value ? 'checked' : ''} ${isReadonly ? 'disabled' : ''}>
            <span>${value ? 'Enabled' : 'Disabled'}</span>
          </label>
        `;

            case 'integer':
                if (this.hasValidationRule(setting, 'min') && this.hasValidationRule(setting, 'max')) {
                    const min = this.getValidationRule(setting, 'min');
                    const max = this.getValidationRule(setting, 'max');
                    return `
            <input type="range" class="setting-range" data-key="${key}" 
                   min="${min}" max="${max}" value="${value}" ${isReadonly ? 'disabled' : ''}>
            <span class="range-value">${value}</span>
          `;
                } else {
                    return `
            <input type="number" class="setting-input" data-key="${key}" 
                   value="${value}" ${isReadonly ? 'disabled' : ''}>
          `;
                }

            case 'float':
                if (this.hasValidationRule(setting, 'min') && this.hasValidationRule(setting, 'max')) {
                    const min = this.getValidationRule(setting, 'min');
                    const max = this.getValidationRule(setting, 'max');
                    const step = (max - min) / 100;
                    return `
            <input type="range" class="setting-range" data-key="${key}" 
                   min="${min}" max="${max}" step="${step}" value="${value}" ${isReadonly ? 'disabled' : ''}>
            <span class="range-value">${value}</span>
          `;
                } else {
                    return `
            <input type="number" class="setting-input" data-key="${key}" 
                   step="0.1" value="${value}" ${isReadonly ? 'disabled' : ''}>
          `;
                }

            case 'string':
                if (this.hasValidationRule(setting, 'options')) {
                    const options = this.getValidationRule(setting, 'options');
                    return `
            <select class="setting-select" data-key="${key}" ${isReadonly ? 'disabled' : ''}>
              ${options.map(option =>
                        `<option value="${option}" ${option === value ? 'selected' : ''}>${option}</option>`
                    ).join('')}
            </select>
          `;
                } else if (key.includes('template')) {
                    return `
            <textarea class="setting-input form-textarea" data-key="${key}" 
                      rows="4" ${isReadonly ? 'disabled' : ''}>${value}</textarea>
          `;
                } else {
                    return `
            <input type="text" class="setting-input" data-key="${key}" 
                   value="${value}" ${isReadonly ? 'disabled' : ''}>
          `;
                }

            default:
                return `
          <input type="text" class="setting-input" data-key="${key}" 
                 value="${value}" ${isReadonly ? 'disabled' : ''}>
        `;
        }
    }

    addSettingEventListeners(container) {
        // Input change listeners
        container.querySelectorAll('.setting-input, .setting-select, .setting-checkbox, .setting-range').forEach(input => {
            const eventType = input.type === 'checkbox' ? 'change' : 'input';

            input.addEventListener(eventType, (e) => {
                const key = e.target.dataset.key;
                let value = e.target.value;

                if (e.target.type === 'checkbox') {
                    value = e.target.checked.toString();
                }

                this.handleSettingChange(key, value, e.target);
            });
        });

        // Reset button listeners
        container.querySelectorAll('.reset-setting-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const key = e.currentTarget.dataset.key;
                this.resetSetting(key);
            });
        });
    }

    async handleSettingChange(key, value, inputElement) {
        try {
            // Update range value display
            if (inputElement.type === 'range') {
                const valueSpan = inputElement.parentElement.querySelector('.range-value');
                if (valueSpan) {
                    valueSpan.textContent = value;
                }
            }

            // Update checkbox label
            if (inputElement.type === 'checkbox') {
                const label = inputElement.parentElement.querySelector('span');
                if (label) {
                    label.textContent = inputElement.checked ? 'Enabled' : 'Disabled';
                }
            }

            // Mark as changed
            this.changedSettings.add(key);
            this.updateSettingStatus(key, 'changed');

            // Validate path settings
            if (key.includes('_path')) {
                await this.validatePath(key, value);
            }

            // Auto-save after delay
            this.debouncedSave = this.debouncedSave || Utils.debounce(() => {
                this.saveChangedSettings();
            }, 2000);

            this.debouncedSave();

        } catch (error) {
            console.error(`Failed to handle setting change for ${key}:`, error);
            this.updateSettingStatus(key, 'error');
        }
    }

    async validatePath(key, path) {
        try {
            const response = await fetch(`/api/settings/filesystem/validate-path?path=${encodeURIComponent(path)}`);
            const result = await response.json();

            const validationEl = document.querySelector(`.path-validation[data-key="${key}"]`);
            if (!validationEl) return;

            validationEl.className = 'path-validation';

            if (result.exists && result.is_writable) {
                validationEl.classList.add('valid');
                validationEl.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <polyline points="20,6 9,17 4,12" stroke="currentColor" stroke-width="2"/>
          </svg>
          Path is valid and writable
        `;
            } else if (result.exists && !result.is_writable) {
                validationEl.classList.add('warning');
                validationEl.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" stroke="currentColor" stroke-width="2"/>
          </svg>
          Path exists but may not be writable
        `;
            } else {
                validationEl.classList.add('invalid');
                validationEl.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2"/>
          </svg>
          Path does not exist
        `;
            }

        } catch (error) {
            console.error(`Failed to validate path ${key}:`, error);
        }
    }

    updateSettingStatus(key, status) {
        const indicator = document.querySelector(`.status-indicator[data-key="${key}"]`);
        const statusText = indicator?.parentElement.querySelector('.status-text');

        if (indicator) {
            indicator.className = `status-indicator ${status}`;
        }

        if (statusText) {
            const statusMessages = {
                'changed': 'Modified',
                'saved': 'Saved',
                'error': 'Error',
                'readonly': 'Read-only'
            };
            statusText.textContent = statusMessages[status] || 'Default';
        }
    }

    async saveChangedSettings() {
        if (this.changedSettings.size === 0) return;
        
        // Prevent multiple concurrent save operations
        if (this.saveInProgress) {
            Utils.showToast('Save operation already in progress', 'warning');
            return;
        }

        try {
            this.saveInProgress = true;
            this.saveStartTime = Date.now();
            this.showLoading('Saving settings...');

            const settingsToSave = {};
            this.changedSettings.forEach(key => {
                // Look for the actual input element within the setting item
                const settingItem = document.querySelector(`[data-key="${key}"]`);
                if (settingItem) {
                    // Find the input element within this setting item
                    const input = settingItem.querySelector('.setting-input, .setting-select, .setting-checkbox, .setting-range');
                    if (input) {
                        let value = input.value;
                        if (input.type === 'checkbox') {
                            value = input.checked.toString();
                        }
                        settingsToSave[key] = value;
                    } else {
                        console.warn(`No input element found within setting item for key: ${key}`);
                    }
                } else {
                    console.warn(`No setting item found for key: ${key}`);
                }
            });

            const response = await fetch('/api/settings/bulk-update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    settings: settingsToSave
                })
            });

            const result = this.handleApiResponse(response);
            await this.processSettingsSaveResult(await result, response.status);

        } catch (error) {
            this.handleSaveError(error);
        } finally {
            this.saveInProgress = false;
            this.saveStartTime = null;
            this.hideLoading();
        }
    }

    async saveAllChanges() {
        await this.saveChangedSettings();
    }

    async resetSetting(key) {
        try {
            const response = await fetch(`/api/settings/${key}/reset`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Failed to reset setting');

            const updatedSetting = await response.json();

            // Update the input with the reset value
            const input = document.querySelector(`[data-key="${key}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = updatedSetting.parsed_value;
                    const label = input.parentElement.querySelector('span');
                    if (label) {
                        label.textContent = input.checked ? 'Enabled' : 'Disabled';
                    }
                } else {
                    input.value = updatedSetting.parsed_value;

                    // Update range display
                    if (input.type === 'range') {
                        const valueSpan = input.parentElement.querySelector('.range-value');
                        if (valueSpan) {
                            valueSpan.textContent = updatedSetting.parsed_value;
                        }
                    }
                }
            }

            // Update status and remove from changed set
            this.updateSettingStatus(key, 'saved');
            this.changedSettings.delete(key);

            Utils.showToast(`Reset ${this.formatSettingLabel(key)}`, 'success');

        } catch (error) {
            console.error(`Failed to reset setting ${key}:`, error);
            Utils.showToast('Failed to reset setting', 'error');
        }
    }

    async exportSettings() {
        try {
            this.showLoading('Exporting settings...');

            const response = await fetch('/api/settings/export/current');
            if (!response.ok) throw new Error('Failed to export settings');

            const exportData = await response.json();

            // Create and download file
            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `journal-settings-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            Utils.showToast('Settings exported successfully', 'success');

        } catch (error) {
            console.error('Failed to export settings:', error);
            Utils.showToast('Failed to export settings', 'error');
        } finally {
            this.hideLoading();
        }
    }

    showImportModal() {
        document.getElementById('import-modal').classList.add('active');
    }

    hideImportModal() {
        document.getElementById('import-modal').classList.remove('active');
        document.getElementById('import-file').value = '';
    }

    async importSettings() {
        try {
            const fileInput = document.getElementById('import-file');
            const mergeMode = document.getElementById('import-merge').checked;

            if (!fileInput.files[0]) {
                Utils.showToast('Please select a file to import', 'warning');
                return;
            }

            this.showLoading('Importing settings...');

            const fileContent = await this.readFileAsText(fileInput.files[0]);
            const importData = JSON.parse(fileContent);

            const response = await fetch('/api/settings/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    settings: importData
                })
            });

            if (!response.ok) throw new Error('Failed to import settings');

            const result = await response.json();
            const importCount = Object.keys(result).length;

            Utils.showToast(`Imported ${importCount} settings`, 'success');

            // Reload settings and re-render
            await this.loadSettings();
            this.renderSettings();

            this.hideImportModal();

        } catch (error) {
            console.error('Failed to import settings:', error);
            Utils.showToast('Failed to import settings', 'error');
        } finally {
            this.hideLoading();
        }
    }

    showResetModal() {
        document.getElementById('reset-modal').classList.add('active');
    }

    hideResetModal() {
        document.getElementById('reset-modal').classList.remove('active');
    }

    async resetAllSettings() {
        try {
            this.showLoading('Resetting all settings...');

            const response = await fetch('/api/settings/reset-all', {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Failed to reset settings');

            const result = await response.json();
            const resetCount = Object.keys(result).length;

            Utils.showToast(`Reset ${resetCount} settings to defaults`, 'success');

            // Reload settings and re-render
            await this.loadSettings();
            this.renderSettings();
            this.changedSettings.clear();

            this.hideResetModal();

        } catch (error) {
            console.error('Failed to reset all settings:', error);
            Utils.showToast('Failed to reset settings', 'error');
        } finally {
            this.hideLoading();
        }
    }

    // Utility methods
    formatSettingLabel(key) {
        return key.split('.').pop().replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    isReadonlySetting(key) {
        const setting = this.settings[key];
        return setting && setting.key.startsWith('llm.') && setting.key !== 'llm.timeout_seconds';
    }

    hasValidationRule(setting, rule) {
        // This would need to be implemented based on setting definitions
        // For now, return false as validation rules aren't exposed in the API response
        return false;
    }

    getValidationRule(setting, rule) {
        // This would need to be implemented based on setting definitions
        return null;
    }

    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        const text = overlay.querySelector('.loading-text');
        if (text) {
            text.textContent = message;
            
            // Add timing information for save operations
            if (this.saveStartTime && message.includes('Saving')) {
                const elapsed = Date.now() - this.saveStartTime;
                if (elapsed > 1000) {
                    text.textContent += ` (${Math.round(elapsed / 1000)}s)`;
                }
            }
        }
        overlay.classList.add('active');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.remove('active');
    }

    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = e => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsText(file);
        });
    }

    // ==========================================
    // WORK WEEK CONFIGURATION FUNCTIONALITY
    // ==========================================

    /**
     * Initialize work week settings functionality
     */
    async initializeWorkWeekSettings() {
        try {
            await this.loadCurrentWorkWeekConfig();
            this.setupWorkWeekEventListeners();
            this.updateWorkWeekPreview();
        } catch (error) {
            console.error('Failed to initialize work week settings:', error);
        }
    }

    /**
     * Setup event listeners for work week controls
     */
    setupWorkWeekEventListeners() {
        // Preset selection
        const presetSelect = document.getElementById('work-week-preset');
        if (presetSelect) {
            presetSelect.addEventListener('change', this.handlePresetChange.bind(this));
        }

        // Custom day selectors
        const startDaySelect = document.getElementById('work-week-start-day');
        const endDaySelect = document.getElementById('work-week-end-day');
        
        [startDaySelect, endDaySelect].forEach(select => {
            if (select) {
                select.addEventListener('change', this.handleCustomConfigurationChange.bind(this));
            }
        });

        // Save button
        const saveButton = document.getElementById('save-work-week-btn');
        if (saveButton) {
            saveButton.addEventListener('click', this.saveWorkWeekConfiguration.bind(this));
        }

        // Reset button
        const resetButton = document.getElementById('reset-work-week-btn');
        if (resetButton) {
            resetButton.addEventListener('click', this.resetWorkWeekConfiguration.bind(this));
        }
    }

    /**
     * Handle preset selection changes
     */
    handlePresetChange(event) {
        const preset = event.target.value;
        this.workWeekConfig.preset = preset;

        const customFields = document.getElementById('custom-work-week-fields');
        
        if (preset === 'CUSTOM') {
            // Show custom fields
            if (customFields) {
                customFields.style.display = 'block';
                customFields.classList.add('active');
                this.addSlideAnimation(customFields, 'show');
            }
        } else {
            // Hide custom fields and set preset values
            if (customFields) {
                this.addSlideAnimation(customFields, 'hide');
                setTimeout(() => {
                    customFields.style.display = 'none';
                    customFields.classList.remove('active');
                }, 300);
            }

            // Set preset values
            if (preset === 'MONDAY_FRIDAY') {
                this.workWeekConfig.start_day = 1;
                this.workWeekConfig.end_day = 5;
            } else if (preset === 'SUNDAY_THURSDAY') {
                this.workWeekConfig.start_day = 7;
                this.workWeekConfig.end_day = 4;
            }

            // Update custom selectors
            this.updateCustomDaySelectors();
        }

        this.updateWorkWeekPreview();
        this.validateCustomConfiguration();
    }

    /**
     * Handle custom configuration changes
     */
    handleCustomConfigurationChange(event) {
        const field = event.target.id;
        const value = parseInt(event.target.value);

        if (field === 'work-week-start-day') {
            this.workWeekConfig.start_day = value;
        } else if (field === 'work-week-end-day') {
            this.workWeekConfig.end_day = value;
        }

        this.updateWorkWeekPreview();
        this.validateCustomConfiguration();
    }

    /**
     * Validate custom work week configuration
     */
    validateCustomConfiguration() {
        this.workWeekValidationErrors = [];
        const { start_day, end_day, preset } = this.workWeekConfig;

        // Only validate custom configurations
        if (preset !== 'CUSTOM') {
            this.updateWorkWeekValidationDisplay();
            return true;
        }

        // Start and end day must be different
        if (start_day === end_day) {
            this.workWeekValidationErrors.push({
                field: 'work-week',
                message: 'Start day and end day must be different',
                suggestion: 'Choose different days for your work week'
            });
        }

        // Days must be 1-7
        if (start_day < 1 || start_day > 7) {
            this.workWeekValidationErrors.push({
                field: 'start-day',
                message: 'Start day must be between 1-7 (1=Monday, 7=Sunday)'
            });
        }

        if (end_day < 1 || end_day > 7) {
            this.workWeekValidationErrors.push({
                field: 'end-day',
                message: 'End day must be between 1-7 (1=Monday, 7=Sunday)'
            });
        }

        this.updateWorkWeekValidationDisplay();
        return this.workWeekValidationErrors.length === 0;
    }

    /**
     * Update validation display for work week settings
     */
    updateWorkWeekValidationDisplay() {
        const validationContainer = document.getElementById('work-week-validation');
        const saveButton = document.getElementById('save-work-week-btn');

        if (!validationContainer) return;

        if (this.workWeekValidationErrors.length > 0) {
            validationContainer.innerHTML = `
                <div class="validation-errors">
                    <div class="validation-header">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        Please fix the following issues:
                    </div>
                    ${this.workWeekValidationErrors.map(error => 
                        `<div class="validation-error">
                            <span class="error-message">${error.message}</span>
                            ${error.suggestion ? `<span class="error-suggestion">${error.suggestion}</span>` : ''}
                        </div>`
                    ).join('')}
                </div>
            `;
            validationContainer.classList.add('has-errors');
            
            if (saveButton) {
                saveButton.disabled = true;
                saveButton.classList.add('disabled');
            }
        } else {
            validationContainer.innerHTML = `
                <div class="validation-success">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <polyline points="20,6 9,17 4,12" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    Work week configuration is valid
                </div>
            `;
            validationContainer.classList.remove('has-errors');
            validationContainer.classList.add('has-success');
            
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.classList.remove('disabled');
            }
        }
    }

    /**
     * Update work week preview
     */
    updateWorkWeekPreview() {
        const previewContainer = document.getElementById('work-week-preview');
        if (!previewContainer) return;

        const { preset, start_day, end_day } = this.workWeekConfig;
        const dayNames = ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

        let previewHtml = '';

        if (preset === 'MONDAY_FRIDAY') {
            previewHtml = `
                <div class="preview-header">
                    <h4>Work Week: Monday - Friday</h4>
                    <span class="preset-badge">Standard</span>
                </div>
                <div class="preview-details">
                    <div class="work-days">
                        <strong>Work days:</strong> Monday, Tuesday, Wednesday, Thursday, Friday
                    </div>
                    <div class="weekend-assignment">
                        <strong>Weekend assignment:</strong>
                        <ul>
                            <li>Saturday entries → Previous week</li>
                            <li>Sunday entries → Next week</li>
                        </ul>
                    </div>
                </div>
                <div class="preview-example">
                    <strong>Example:</strong> An entry created on Saturday Nov 16 will be saved to the Nov 8-15 work week directory.
                </div>
            `;
        } else if (preset === 'SUNDAY_THURSDAY') {
            previewHtml = `
                <div class="preview-header">
                    <h4>Work Week: Sunday - Thursday</h4>
                    <span class="preset-badge">Middle East</span>
                </div>
                <div class="preview-details">
                    <div class="work-days">
                        <strong>Work days:</strong> Sunday, Monday, Tuesday, Wednesday, Thursday
                    </div>
                    <div class="weekend-assignment">
                        <strong>Weekend assignment:</strong>
                        <ul>
                            <li>Friday entries → Next week</li>
                            <li>Saturday entries → Next week</li>
                        </ul>
                    </div>
                </div>
                <div class="preview-example">
                    <strong>Example:</strong> An entry created on Friday Nov 15 will be saved to the Nov 17-21 work week directory.
                </div>
            `;
        } else if (preset === 'CUSTOM') {
            const startDayName = dayNames[start_day] || 'Invalid';
            const endDayName = dayNames[end_day] || 'Invalid';
            
            // Generate work days list
            const workDays = this.generateWorkDaysList(start_day, end_day);
            const weekendDays = this.generateWeekendAssignmentLogic(start_day, end_day);
            
            previewHtml = `
                <div class="preview-header">
                    <h4>Custom Work Week: ${startDayName} - ${endDayName}</h4>
                    <span class="preset-badge">Custom</span>
                </div>
                <div class="preview-details">
                    <div class="work-days">
                        <strong>Work days:</strong> ${workDays}
                    </div>
                    <div class="weekend-assignment">
                        <strong>Weekend assignment:</strong>
                        <ul>
                            ${weekendDays}
                        </ul>
                    </div>
                </div>
                <div class="preview-example">
                    <strong>Note:</strong> Weekend entries will be assigned to the nearest work week based on your custom schedule.
                </div>
            `;
        }

        previewContainer.innerHTML = previewHtml;
        this.addPreviewAnimation(previewContainer);
    }

    /**
     * Generate work days list for custom configurations
     */
    generateWorkDaysList(startDay, endDay) {
        const dayNames = ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        const workDays = [];

        if (startDay <= endDay) {
            // Normal week (e.g., Mon-Fri)
            for (let i = startDay; i <= endDay; i++) {
                workDays.push(dayNames[i]);
            }
        } else {
            // Week wraps around (e.g., Thu-Tue)
            for (let i = startDay; i <= 7; i++) {
                workDays.push(dayNames[i]);
            }
            for (let i = 1; i <= endDay; i++) {
                workDays.push(dayNames[i]);
            }
        }

        return workDays.join(', ');
    }

    /**
     * Generate weekend assignment logic for custom configurations
     */
    generateWeekendAssignmentLogic(startDay, endDay) {
        const dayNames = ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        const weekendAssignments = [];

        for (let day = 1; day <= 7; day++) {
            const isWorkDay = (startDay <= endDay) ? 
                (day >= startDay && day <= endDay) : 
                (day >= startDay || day <= endDay);

            if (!isWorkDay) {
                const dayName = dayNames[day];
                // Simplified logic: days before work week go to previous, days after go to next
                const assignment = (day < startDay) ? 'Previous week' : 'Next week';
                weekendAssignments.push(`<li>${dayName} entries → ${assignment}</li>`);
            }
        }

        return weekendAssignments.join('');
    }

    /**
     * Load current work week configuration from API
     */
    async loadCurrentWorkWeekConfig() {
        try {
            const response = await fetch('/api/settings/work-week');
            if (!response.ok) {
                // If endpoint doesn't exist yet, use defaults
                if (response.status === 404) {
                    console.info('Work week settings not yet configured, using defaults');
                    return;
                }
                throw new Error('Failed to load work week config');
            }

            const config = await response.json();
            this.workWeekConfig = { ...this.workWeekConfig, ...config };

            // Update form fields
            this.updateWorkWeekFormFields();

        } catch (error) {
            console.error('Failed to load work week configuration:', error);
            // Use defaults on error
        }
    }

    /**
     * Update form fields with current configuration
     */
    updateWorkWeekFormFields() {
        const presetSelect = document.getElementById('work-week-preset');
        const startDaySelect = document.getElementById('work-week-start-day');
        const endDaySelect = document.getElementById('work-week-end-day');

        if (presetSelect) {
            presetSelect.value = this.workWeekConfig.preset;
        }

        if (startDaySelect) {
            startDaySelect.value = this.workWeekConfig.start_day;
        }

        if (endDaySelect) {
            endDaySelect.value = this.workWeekConfig.end_day;
        }

        // Update custom day selectors
        this.updateCustomDaySelectors();

        // Trigger preset change to show/hide custom fields
        if (presetSelect) {
            this.handlePresetChange({ target: { value: this.workWeekConfig.preset } });
        }
    }

    /**
     * Update custom day selectors values
     */
    updateCustomDaySelectors() {
        const startDaySelect = document.getElementById('work-week-start-day');
        const endDaySelect = document.getElementById('work-week-end-day');

        if (startDaySelect) {
            startDaySelect.value = this.workWeekConfig.start_day;
        }

        if (endDaySelect) {
            endDaySelect.value = this.workWeekConfig.end_day;
        }
    }

    /**
     * Save work week configuration with enhanced error handling
     */
    async saveWorkWeekConfiguration() {
        try {
            if (!this.validateCustomConfiguration()) {
                Utils.showToast('Please fix validation errors before saving', 'warning');
                return;
            }

            const saveStartTime = Date.now();
            this.showLoading('Saving work week configuration...');

            const response = await fetch('/api/settings/work-week', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.workWeekConfig)
            });

            const result = await this.handleApiResponse(response);
            const processingTime = result.processing_time_ms || (Date.now() - saveStartTime);
            const timingInfo = processingTime < 1000 ? 
                `${Math.round(processingTime)}ms` : 
                `${(processingTime / 1000).toFixed(1)}s`;

            if (response.ok) {
                Utils.showToast(`Work week configuration saved successfully (${timingInfo})`, 'success');
                
                // Update local config with server response
                if (result.current_config) {
                    this.workWeekConfig = { ...this.workWeekConfig, ...result.current_config };
                }

                // Add success animation
                this.addSuccessAnimation(document.getElementById('work-week-settings'));
                
                if (result.request_id) {
                    console.log(`Work week save completed - Request ID: ${result.request_id}`);
                }
            } else {
                // Handle API error responses
                const errorMsg = result.detail?.message || result.message || 'Failed to save work week configuration';
                throw new Error(errorMsg);
            }

        } catch (error) {
            console.error('Failed to save work week configuration:', error);
            
            let errorMessage = 'Failed to save work week configuration';
            if (error.message.includes('HTTP 400')) {
                errorMessage = 'Invalid work week configuration. Please check your settings.';
            } else if (error.message.includes('HTTP 503')) {
                errorMessage = 'Service temporarily unavailable. Please try again.';
            } else if (error.message.includes('Network') || error.name === 'TypeError') {
                errorMessage = 'Network error: Could not connect to server';
            } else if (error.message !== 'Failed to save work week configuration') {
                errorMessage = `Save failed: ${error.message}`;
            }
            
            Utils.showToast(errorMessage, 'error', { duration: 5000 });
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Reset work week configuration to defaults
     */
    async resetWorkWeekConfiguration() {
        try {
            const confirmed = confirm('Are you sure you want to reset the work week configuration to defaults?');
            if (!confirmed) return;

            this.showLoading('Resetting work week configuration...');

            const response = await fetch('/api/settings/work-week/reset', {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Failed to reset work week configuration');

            const defaultConfig = await response.json();
            this.workWeekConfig = { ...this.workWeekConfig, ...defaultConfig };

            // Update form fields
            this.updateWorkWeekFormFields();
            this.updateWorkWeekPreview();
            this.validateCustomConfiguration();

            Utils.showToast('Work week configuration reset to defaults', 'success');

        } catch (error) {
            console.error('Failed to reset work week configuration:', error);
            Utils.showToast('Failed to reset work week configuration', 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Validate configuration with API
     */
    async validateWorkWeekConfiguration(config = null) {
        try {
            const configToValidate = config || this.workWeekConfig;

            const response = await fetch('/api/settings/work-week/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(configToValidate)
            });

            if (!response.ok) throw new Error('Validation request failed');

            return await response.json();

        } catch (error) {
            console.error('Failed to validate work week configuration:', error);
            return { 
                valid: false, 
                errors: ['Failed to validate configuration'],
                suggestions: []
            };
        }
    }

    /**
     * Get available work week presets
     */
    async getWorkWeekPresets() {
        try {
            const response = await fetch('/api/settings/work-week/presets');
            if (!response.ok) throw new Error('Failed to load presets');

            return await response.json();

        } catch (error) {
            console.error('Failed to load work week presets:', error);
            // Return fallback presets
            return {
                presets: [
                    { 
                        value: 'MONDAY_FRIDAY', 
                        label: 'Monday - Friday', 
                        description: 'Standard business week (5 days)',
                        start_day: 1,
                        end_day: 5
                    },
                    { 
                        value: 'SUNDAY_THURSDAY', 
                        label: 'Sunday - Thursday', 
                        description: 'Middle East business week (5 days)',
                        start_day: 7,
                        end_day: 4
                    },
                    { 
                        value: 'CUSTOM', 
                        label: 'Custom', 
                        description: 'Define your own work week schedule',
                        start_day: null,
                        end_day: null
                    }
                ]
            };
        }
    }

    // ==========================================
    // ANIMATION AND UI HELPERS
    // ==========================================

    /**
     * Add slide animation to elements
     */
    addSlideAnimation(element, direction) {
        if (!element) return;

        element.style.transition = 'all 0.3s ease-in-out';
        
        if (direction === 'show') {
            element.style.maxHeight = '0';
            element.style.opacity = '0';
            element.style.overflow = 'hidden';
            
            setTimeout(() => {
                element.style.maxHeight = '500px';
                element.style.opacity = '1';
            }, 10);
        } else if (direction === 'hide') {
            element.style.maxHeight = element.scrollHeight + 'px';
            element.style.opacity = '1';
            
            setTimeout(() => {
                element.style.maxHeight = '0';
                element.style.opacity = '0';
            }, 10);
        }
    }

    /**
     * Add preview animation
     */
    addPreviewAnimation(element) {
        if (!element) return;

        element.style.transition = 'all 0.2s ease-in-out';
        element.style.transform = 'scale(0.98)';
        element.style.opacity = '0.7';

        setTimeout(() => {
            element.style.transform = 'scale(1)';
            element.style.opacity = '1';
        }, 50);
    }

    /**
     * Add success animation
     */
    addSuccessAnimation(element) {
        if (!element) return;

        element.style.transition = 'all 0.3s ease-in-out';
        element.style.transform = 'scale(1.02)';
        element.style.backgroundColor = 'var(--success-bg, #d4edda)';

        setTimeout(() => {
            element.style.transform = 'scale(1)';
            element.style.backgroundColor = '';
        }, 500);
    }

    // ==========================================
    // ENHANCED API RESPONSE HANDLING
    // ==========================================

    /**
     * Handle API response with enhanced error handling
     */
    async handleApiResponse(response) {
        try {
            const result = await response.json();
            
            // Store request metadata
            this.lastRequestId = result.request_id;
            
            return result;
        } catch (parseError) {
            // Handle cases where response isn't JSON
            if (response.status >= 400) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            throw new Error('Invalid response format');
        }
    }

    /**
     * Process settings save result with enhanced feedback
     */
    async processSettingsSaveResult(result, statusCode) {
        const processingTime = result.processing_time_ms || (Date.now() - this.saveStartTime);
        
        // Update status for saved settings
        if (result.updated_settings) {
            Object.keys(result.updated_settings).forEach(key => {
                this.updateSettingStatus(key, 'saved');
                this.changedSettings.delete(key);
            });
        }

        // Handle validation errors with detailed feedback
        if (result.validation_errors && result.validation_errors.length > 0) {
            this.handleValidationErrors(result.validation_errors);
        }

        // Show appropriate success/error messages based on status code
        this.showSaveResultMessage(result, statusCode, processingTime);
    }

    /**
     * Handle validation errors with detailed feedback
     */
    handleValidationErrors(validationErrors) {
        validationErrors.forEach(error => {
            this.updateSettingStatus(error.key, 'error');
            
            // Show detailed error message
            const errorMsg = this.formatErrorMessage(error);
            Utils.showToast(errorMsg, 'error', { duration: 5000 });
        });
    }

    /**
     * Format error message with additional context
     */
    formatErrorMessage(error) {
        const settingLabel = this.formatSettingLabel(error.key);
        let message = `${settingLabel}: ${error.error || error.message}`;
        
        // Add validation details if available
        if (error.details) {
            message += ` (${error.details})`;
        }
        
        // Add suggestion if available
        if (error.suggestion) {
            message += `. Suggestion: ${error.suggestion}`;
        }
        
        return message;
    }

    /**
     * Show save result message with operation details
     */
    showSaveResultMessage(result, statusCode, processingTime) {
        const timingInfo = processingTime < 1000 ? 
            `${Math.round(processingTime)}ms` : 
            `${(processingTime / 1000).toFixed(1)}s`;

        if (statusCode === 200) {
            // Complete success
            const message = `Successfully saved ${result.success_count} setting${result.success_count !== 1 ? 's' : ''} (${timingInfo})`;
            Utils.showToast(message, 'success', { duration: 3000 });
        } else if (statusCode === 207) {
            // Partial success
            const successMsg = `Saved ${result.success_count} setting${result.success_count !== 1 ? 's' : ''}`;
            const errorMsg = `${result.error_count} failed`;
            const message = `${successMsg}, ${errorMsg} (${timingInfo})`;
            Utils.showToast(message, 'warning', { duration: 4000 });
        } else if (statusCode === 400) {
            // Complete failure
            Utils.showToast(`Failed to save settings: Validation errors (${timingInfo})`, 'error', { duration: 4000 });
        }

        // Add request ID to console for debugging
        if (result.request_id) {
            console.log(`Settings save operation completed - Request ID: ${result.request_id}`);
        }
    }

    /**
     * Handle save errors with network/timeout scenarios
     */
    handleSaveError(error) {
        console.error('Failed to save settings:', error);
        
        let errorMessage = 'Failed to save settings';
        let toastType = 'error';
        let duration = 4000;
        
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            // Network error
            errorMessage = 'Network error: Could not connect to server';
            duration = 6000;
        } else if (error.name === 'AbortError') {
            // Timeout error
            errorMessage = 'Request timed out: Settings save took too long';
            duration = 6000;
        } else if (error.message.includes('HTTP 503')) {
            // Service unavailable
            errorMessage = 'Database temporarily unavailable. Please try again in a moment.';
            toastType = 'warning';
            duration = 6000;
        } else if (error.message.includes('HTTP 408')) {
            // Request timeout
            errorMessage = 'Save operation timed out. Please try again.';
            duration = 6000;
        } else if (error.message.includes('HTTP')) {
            // Other HTTP errors
            errorMessage = `Server error: ${error.message}`;
        }
        
        // Add timing information if available
        if (this.saveStartTime) {
            const elapsed = Date.now() - this.saveStartTime;
            errorMessage += ` (after ${Math.round(elapsed / 1000)}s)`;
        }
        
        Utils.showToast(errorMessage, toastType, { duration });
        
        // Mark all changed settings as error state
        this.changedSettings.forEach(key => {
            this.updateSettingStatus(key, 'error');
        });
    }
}

// Enhanced Utils.showToast to support duration options
if (typeof Utils !== 'undefined' && Utils.showToast) {
    const originalShowToast = Utils.showToast;
    Utils.showToast = function(message, type = 'info', options = {}) {
        if (typeof options === 'number') {
            // Backward compatibility: if options is a number, treat as duration
            options = { duration: options };
        }
        return originalShowToast.call(this, message, type, options);
    };
}

/**
 * Sync Management Class
 * 
 * Handles database synchronization interface and operations
 */
class SyncManager {
    constructor() {
        this.syncInProgress = false;
        this.refreshInterval = null;
        this.initialized = false;
    }

    async init() {
        if (this.initialized) return;

        try {
            this.setupEventListeners();
            await this.loadSyncStatus();
            await this.loadSyncHistory();
            await this.loadSchedulerStatus();

            // Auto-refresh sync status every 5 seconds when sync is in progress
            this.startAutoRefresh();
            this.initialized = true;
        } catch (error) {
            console.error('Failed to initialize sync manager:', error);
            this.showError('Failed to load sync interface');
        }
    }

    setupEventListeners() {
        // Sync control buttons
        document.getElementById('trigger-incremental-sync')?.addEventListener('click', () => {
            this.triggerIncrementalSync();
        });

        document.getElementById('trigger-full-sync')?.addEventListener('click', () => {
            this.triggerFullSync();
        });

        // Refresh buttons
        document.getElementById('refresh-sync-status')?.addEventListener('click', () => {
            this.loadSyncStatus();
        });

        document.getElementById('refresh-sync-history')?.addEventListener('click', () => {
            this.loadSyncHistory();
        });

        // Input validation
        document.getElementById('incremental-days')?.addEventListener('input', (e) => {
            this.validateDaysInput(e.target, 1, 30);
        });

        document.getElementById('full-sync-days')?.addEventListener('input', (e) => {
            this.validateDaysInput(e.target, 30, 3650);
        });
    }

    validateDaysInput(input, min, max) {
        let value = parseInt(input.value);
        if (isNaN(value) || value < min) {
            input.value = min;
        } else if (value > max) {
            input.value = max;
        }
    }

    async triggerIncrementalSync() {
        try {
            const days = parseInt(document.getElementById('incremental-days').value) || 7;
            const button = document.getElementById('trigger-incremental-sync');
            
            this.setButtonLoading(button, true);
            
            const result = await api.sync.triggerIncremental(days);
            
            this.syncInProgress = true;
            this.setSyncButtonsDisabled(true);
            this.startAutoRefresh();
            
            // Refresh status immediately
            await this.loadSyncStatus();
            
        } catch (error) {
            console.error('Failed to trigger incremental sync:', error);
            Utils.showToast('Failed to start incremental sync', 'error');
            this.setSyncButtonsDisabled(false);
        } finally {
            this.setButtonLoading(document.getElementById('trigger-incremental-sync'), false);
        }
    }

    async triggerFullSync() {
        try {
            const days = parseInt(document.getElementById('full-sync-days').value) || 730;
            const button = document.getElementById('trigger-full-sync');
            
            this.setButtonLoading(button, true);
            
            const result = await api.sync.triggerFull(days);
            
            this.syncInProgress = true;
            this.setSyncButtonsDisabled(true);
            this.startAutoRefresh();
            
            // Refresh status immediately
            await this.loadSyncStatus();
            
        } catch (error) {
            console.error('Failed to trigger full sync:', error);
            Utils.showToast('Failed to start full sync', 'error');
            this.setSyncButtonsDisabled(false);
        } finally {
            this.setButtonLoading(document.getElementById('trigger-full-sync'), false);
        }
    }

    async loadSyncStatus() {
        try {
            const status = await api.sync.getStatus();
            this.renderSyncStatus(status);
            
            // Update sync in progress flag and button states
            const newSyncInProgress = status.sync_status?.sync_in_progress || false;
            
            // Re-enable buttons if sync completed
            if (this.syncInProgress && !newSyncInProgress) {
                this.setSyncButtonsDisabled(false);
            }
            
            this.syncInProgress = newSyncInProgress;
            
        } catch (error) {
            console.error('Failed to load sync status:', error);
            this.showSyncStatusError();
        }
    }

    async loadSyncHistory() {
        try {
            const history = await api.sync.getHistory(10);
            this.renderSyncHistory(history);
        } catch (error) {
            console.error('Failed to load sync history:', error);
            this.showSyncHistoryError();
        }
    }

    async loadSchedulerStatus() {
        try {
            const status = await api.sync.getSchedulerStatus();
            this.renderSchedulerStatus(status);
        } catch (error) {
            console.error('Failed to load scheduler status:', error);
            this.showSchedulerStatusError();
        }
    }

    renderSyncStatus(data) {
        const container = document.getElementById('sync-status-content');
        if (!container) return;

        const syncStatus = data.sync_status || {};
        const dbStats = data.database_stats || {};

        container.innerHTML = `
            <div class="sync-status-item">
                <span class="status-label">Sync Status</span>
                <span class="status-value ${syncStatus.sync_in_progress ? 'in-progress' : 'success'}">
                    ${syncStatus.sync_in_progress ? 'In Progress' : 'Idle'}
                </span>
            </div>
            
            <div class="sync-status-item">
                <span class="status-label">Total Entries</span>
                <span class="status-value">${dbStats.total_entries || 0}</span>
            </div>
            
            <div class="sync-status-item">
                <span class="status-label">Last Sync</span>
                <span class="status-value">
                    ${syncStatus.last_sync ? new Date(syncStatus.last_sync).toLocaleString() : 'Never'}
                </span>
            </div>
            
            <div class="sync-status-item">
                <span class="status-label">Database Size</span>
                <span class="status-value">${this.formatFileSize(dbStats.database_size_bytes || 0)}</span>
            </div>
            
            ${syncStatus.sync_in_progress ? `
                <div class="sync-progress">
                    <div class="sync-progress-spinner"></div>
                    <span class="sync-progress-text">Synchronization in progress...</span>
                </div>
            ` : ''}
        `;
    }

    renderSyncHistory(data) {
        const container = document.getElementById('sync-history-content');
        if (!container) return;

        const history = data.history || [];

        if (history.length === 0) {
            container.innerHTML = `
                <div class="loading-placeholder">
                    <span>No sync history available</span>
                </div>
            `;
            return;
        }

        container.innerHTML = history.map(record => {
            const statusClass = record.status === 'running' ? 'running' : 
                              record.status === 'completed' ? 'completed' : 'failed';
            
            return `
                <div class="sync-history-item">
                    <div class="history-status ${statusClass}"></div>
                    <div class="history-info">
                        <div class="history-type">${this.formatSyncType(record.sync_type)}</div>
                        <div class="history-details">
                            ${record.entries_processed || 0} processed, 
                            ${record.entries_added || 0} added, 
                            ${record.entries_updated || 0} updated
                            ${record.error_message ? ` - ${record.error_message}` : ''}
                        </div>
                    </div>
                    <div class="history-timestamp">
                        ${new Date(record.started_at).toLocaleString()}
                    </div>
                    <div class="history-stats">
                        ${record.duration_seconds ? `${record.duration_seconds.toFixed(1)}s` : 'Running'}
                    </div>
                </div>
            `;
        }).join('');
    }

    renderSchedulerStatus(data) {
        const container = document.getElementById('sync-scheduler-content');
        if (!container) return;

        const isRunning = data.is_running || false;

        container.innerHTML = `
            <div class="scheduler-status">
                <div class="scheduler-info">
                    <div class="scheduler-state">
                        Scheduler: ${isRunning ? 'Running' : 'Stopped'}
                    </div>
                    <div class="scheduler-details">
                        ${data.next_incremental ? `Next incremental: ${new Date(data.next_incremental).toLocaleString()}` : 'No scheduled incremental sync'}
                        <br>
                        ${data.next_full ? `Next full sync: ${new Date(data.next_full).toLocaleString()}` : 'No scheduled full sync'}
                    </div>
                </div>
                <div class="scheduler-controls">
                    <button class="btn btn-${isRunning ? 'secondary' : 'primary'} btn-small" 
                            onclick="syncManager.${isRunning ? 'stopScheduler' : 'startScheduler'}()">
                        ${isRunning ? 'Stop' : 'Start'} Scheduler
                    </button>
                    ${isRunning ? `
                        <button class="btn btn-secondary btn-small" onclick="syncManager.triggerSchedulerSync('incremental')">
                            Trigger Incremental
                        </button>
                        <button class="btn btn-secondary btn-small" onclick="syncManager.triggerSchedulerSync('full')">
                            Trigger Full
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    async startScheduler() {
        try {
            await api.sync.startScheduler();
            Utils.showToast('Scheduler started', 'success');
            await this.loadSchedulerStatus();
        } catch (error) {
            console.error('Failed to start scheduler:', error);
            Utils.showToast('Failed to start scheduler', 'error');
        }
    }

    async stopScheduler() {
        try {
            await api.sync.stopScheduler();
            Utils.showToast('Scheduler stopped', 'success');
            await this.loadSchedulerStatus();
        } catch (error) {
            console.error('Failed to stop scheduler:', error);
            Utils.showToast('Failed to stop scheduler', 'error');
        }
    }

    async triggerSchedulerSync(type) {
        try {
            if (type === 'incremental') {
                await api.sync.triggerSchedulerIncremental();
            } else {
                await api.sync.triggerSchedulerFull();
            }
            
            this.syncInProgress = true;
            this.setSyncButtonsDisabled(true);
            this.startAutoRefresh();
            await this.loadSyncStatus();
            
        } catch (error) {
            console.error(`Failed to trigger scheduler ${type} sync:`, error);
            Utils.showToast(`Failed to trigger scheduler ${type} sync`, 'error');
            this.setSyncButtonsDisabled(false);
        }
    }

    startAutoRefresh() {
        if (this.refreshInterval) return;

        this.refreshInterval = setInterval(async () => {
            if (this.syncInProgress) {
                await this.loadSyncStatus();
                await this.loadSyncHistory();
                
                // Stop auto-refresh if sync is no longer in progress
                if (!this.syncInProgress) {
                    this.stopAutoRefresh();
                }
            } else {
                this.stopAutoRefresh();
            }
        }, 5000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    setSyncButtonsDisabled(disabled) {
        const syncButtons = [
            'trigger-incremental-sync',
            'trigger-full-sync'
        ];
        
        syncButtons.forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button) {
                button.disabled = disabled;
            }
        });
        
        // Also disable scheduler sync buttons if they exist
        const schedulerButtons = document.querySelectorAll('button[onclick*="triggerSchedulerSync"]');
        schedulerButtons.forEach(button => {
            button.disabled = disabled;
        });
    }

    setButtonLoading(button, loading) {
        if (!button) return;

        if (loading) {
            button.disabled = true;
            button.innerHTML = `
                <div class="sync-progress-spinner" style="width: 16px; height: 16px; margin-right: 8px;"></div>
                Syncing...
            `;
        } else {
            button.disabled = false;
            // Restore original content based on button ID
            if (button.id === 'trigger-incremental-sync') {
                button.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <polyline points="23,4 23,10 17,10" stroke="currentColor" stroke-width="2" />
                        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" stroke="currentColor" stroke-width="2" />
                    </svg>
                    Start Incremental Sync
                `;
            } else if (button.id === 'trigger-full-sync') {
                button.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" stroke="currentColor" stroke-width="2" />
                        <polyline points="16,6 12,2 8,6" stroke="currentColor" stroke-width="2" />
                        <line x1="12" y1="2" x2="12" y2="15" stroke="currentColor" stroke-width="2" />
                    </svg>
                    Start Full Sync
                `;
            }
        }
    }

    showSyncStatusError() {
        const container = document.getElementById('sync-status-content');
        if (container) {
            container.innerHTML = '<div class="loading-placeholder"><span>Failed to load sync status</span></div>';
        }
    }

    showSyncHistoryError() {
        const container = document.getElementById('sync-history-content');
        if (container) {
            container.innerHTML = '<div class="loading-placeholder"><span>Failed to load sync history</span></div>';
        }
    }

    showSchedulerStatusError() {
        const container = document.getElementById('sync-scheduler-content');
        if (container) {
            container.innerHTML = '<div class="loading-placeholder"><span>Failed to load scheduler status</span></div>';
        }
    }

    showError(message) {
        Utils.showToast(message, 'error');
    }

    formatSyncType(type) {
        switch (type) {
            case 'full': return 'Full Sync';
            case 'incremental': return 'Incremental Sync';
            case 'single_entry': return 'Single Entry';
            default: return type;
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    destroy() {
        this.stopAutoRefresh();
        this.initialized = false;
    }
}

// Initialize settings manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.settingsManager = new SettingsManager();
    window.syncManager = new SyncManager();
});