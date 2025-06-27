/**
 * Settings Management JavaScript
 * 
 * Handles the settings interface, validation, and API interactions
 */

class SettingsManager {
    constructor() {
        this.settings = {};
        this.categories = {};
        this.changedSettings = new Set();
        this.currentCategory = 'filesystem';

        this.init();
    }

    async init() {
        try {
            await this.loadSettings();
            await this.loadCategories();
            this.setupEventListeners();
            this.renderSettings();
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

        try {
            this.showLoading('Saving settings...');

            const settingsToSave = {};
            this.changedSettings.forEach(key => {
                const input = document.querySelector(`[data-key="${key}"]`);
                if (input) {
                    let value = input.value;
                    if (input.type === 'checkbox') {
                        value = input.checked.toString();
                    }
                    settingsToSave[key] = value;
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

            if (!response.ok) throw new Error('Failed to save settings');

            const result = await response.json();

            // Update status for saved settings
            Object.keys(result.updated_settings).forEach(key => {
                this.updateSettingStatus(key, 'saved');
                this.changedSettings.delete(key);
            });

            // Show errors for failed settings
            result.validation_errors?.forEach(error => {
                this.updateSettingStatus(error.key, 'error');
                Utils.showToast(`${error.key}: ${error.error}`, 'error');
            });

            if (result.success_count > 0) {
                Utils.showToast(`Saved ${result.success_count} settings`, 'success');
            }

        } catch (error) {
            console.error('Failed to save settings:', error);
            Utils.showToast('Failed to save settings', 'error');
        } finally {
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
        if (text) text.textContent = message;
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
}

// Initialize settings manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SettingsManager();
});