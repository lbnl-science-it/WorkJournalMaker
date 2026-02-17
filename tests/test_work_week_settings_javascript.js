/**
 * Comprehensive Unit Tests for Work Week Settings JavaScript
 * 
 * Tests the client-side work week configuration functionality
 * including form behavior, validation, API integration, and user experience
 */

// Mock DOM and utilities for testing
const mockDom = () => {
    global.document = {
        getElementById: jest.fn(),
        querySelector: jest.fn(),
        querySelectorAll: jest.fn(() => []),
        createElement: jest.fn(() => ({
            href: '',
            download: '',
            click: jest.fn(),
            appendChild: jest.fn(),
            parentElement: { removeChild: jest.fn() }
        })),
        body: {
            appendChild: jest.fn(),
            removeChild: jest.fn()
        },
        addEventListener: jest.fn()
    };
    
    global.fetch = jest.fn();
    global.URL = {
        createObjectURL: jest.fn(() => 'mock-url'),
        revokeObjectURL: jest.fn()
    };
    
    global.Utils = {
        showToast: jest.fn(),
        debounce: jest.fn(fn => fn)
    };
};

// Mock work week settings manager
class WorkWeekSettingsManager {
    constructor() {
        this.workWeekConfig = {
            preset: 'MONDAY_FRIDAY',
            start_day: 1,
            end_day: 5,
            timezone: 'America/New_York'
        };
        this.validationErrors = [];
        this.apiCallbacks = {};
    }

    // Initialize work week settings
    initializeWorkWeekSettings() {
        this.setupWorkWeekEventListeners();
        this.loadCurrentWorkWeekConfig();
        return Promise.resolve();
    }

    // Setup event listeners for work week controls
    setupWorkWeekEventListeners() {
        const presetSelect = document.getElementById('work-week-preset');
        const startDaySelect = document.getElementById('work-week-start-day');
        const endDaySelect = document.getElementById('work-week-end-day');
        const saveButton = document.getElementById('save-work-week-btn');

        if (presetSelect) {
            presetSelect.addEventListener('change', this.handlePresetChange.bind(this));
        }

        if (startDaySelect || endDaySelect) {
            [startDaySelect, endDaySelect].forEach(select => {
                if (select) {
                    select.addEventListener('change', this.handleCustomConfigurationChange.bind(this));
                }
            });
        }

        if (saveButton) {
            saveButton.addEventListener('click', this.saveWorkWeekConfiguration.bind(this));
        }
    }

    // Handle preset selection changes
    handlePresetChange(event) {
        const preset = event.target.value;
        this.workWeekConfig.preset = preset;

        const customFields = document.getElementById('custom-work-week-fields');
        const previewContainer = document.getElementById('work-week-preview');

        if (preset === 'CUSTOM') {
            // Show custom fields
            if (customFields) {
                customFields.style.display = 'block';
                customFields.classList.add('active');
            }
        } else {
            // Hide custom fields and set preset values
            if (customFields) {
                customFields.style.display = 'none';
                customFields.classList.remove('active');
            }

            // Set preset values
            if (preset === 'MONDAY_FRIDAY') {
                this.workWeekConfig.start_day = 1;
                this.workWeekConfig.end_day = 5;
            } else if (preset === 'SUNDAY_THURSDAY') {
                this.workWeekConfig.start_day = 7;
                this.workWeekConfig.end_day = 4;
            }
        }

        this.updateWorkWeekPreview();
        this.validateCustomConfiguration();
    }

    // Handle custom configuration changes
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

    // Validate custom work week configuration
    validateCustomConfiguration() {
        this.validationErrors = [];
        const { start_day, end_day, preset } = this.workWeekConfig;

        // Only validate custom configurations
        if (preset !== 'CUSTOM') {
            this.updateValidationDisplay();
            return true;
        }

        // Start and end day must be different
        if (start_day === end_day) {
            this.validationErrors.push({
                field: 'work-week',
                message: 'Start day and end day must be different'
            });
        }

        // Days must be 1-7
        if (start_day < 1 || start_day > 7) {
            this.validationErrors.push({
                field: 'start-day',
                message: 'Start day must be between 1-7 (1=Monday, 7=Sunday)'
            });
        }

        if (end_day < 1 || end_day > 7) {
            this.validationErrors.push({
                field: 'end-day',
                message: 'End day must be between 1-7 (1=Monday, 7=Sunday)'
            });
        }

        this.updateValidationDisplay();
        return this.validationErrors.length === 0;
    }

    // Update validation display
    updateValidationDisplay() {
        const validationContainer = document.getElementById('work-week-validation');
        const saveButton = document.getElementById('save-work-week-btn');

        if (!validationContainer) return;

        if (this.validationErrors.length > 0) {
            validationContainer.innerHTML = `
                <div class="validation-errors">
                    ${this.validationErrors.map(error => 
                        `<div class="validation-error">${error.message}</div>`
                    ).join('')}
                </div>
            `;
            validationContainer.classList.add('has-errors');
            
            if (saveButton) {
                saveButton.disabled = true;
                saveButton.classList.add('disabled');
            }
        } else {
            validationContainer.innerHTML = '';
            validationContainer.classList.remove('has-errors');
            
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.classList.remove('disabled');
            }
        }
    }

    // Update work week preview
    updateWorkWeekPreview() {
        const previewContainer = document.getElementById('work-week-preview');
        if (!previewContainer) return;

        const { preset, start_day, end_day } = this.workWeekConfig;
        const dayNames = ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

        let previewText = '';

        if (preset === 'MONDAY_FRIDAY') {
            previewText = `
                <div class="preview-header">Work Week: Monday - Friday</div>
                <div class="preview-details">
                    <p>Work days: Monday, Tuesday, Wednesday, Thursday, Friday</p>
                    <p>Weekend assignment: Saturday → Previous week, Sunday → Next week</p>
                </div>
            `;
        } else if (preset === 'SUNDAY_THURSDAY') {
            previewText = `
                <div class="preview-header">Work Week: Sunday - Thursday</div>
                <div class="preview-details">
                    <p>Work days: Sunday, Monday, Tuesday, Wednesday, Thursday</p>
                    <p>Weekend assignment: Friday & Saturday → Next week</p>
                </div>
            `;
        } else if (preset === 'CUSTOM') {
            const startDayName = dayNames[start_day] || 'Invalid';
            const endDayName = dayNames[end_day] || 'Invalid';
            
            previewText = `
                <div class="preview-header">Custom Work Week: ${startDayName} - ${endDayName}</div>
                <div class="preview-details">
                    <p>Work week starts: ${startDayName}</p>
                    <p>Work week ends: ${endDayName}</p>
                    <p>Weekend entries will be assigned to the nearest work week</p>
                </div>
            `;
        }

        previewContainer.innerHTML = previewText;
    }

    // Load current work week configuration
    async loadCurrentWorkWeekConfig() {
        try {
            const response = await fetch('/api/settings/work-week');
            if (!response.ok) throw new Error('Failed to load work week config');

            const config = await response.json();
            this.workWeekConfig = { ...this.workWeekConfig, ...config };

            // Update form fields
            this.updateFormFields();
            this.updateWorkWeekPreview();

        } catch (error) {
            console.error('Failed to load work week configuration:', error);
            Utils.showToast('Failed to load work week settings', 'error');
        }
    }

    // Update form fields with current configuration
    updateFormFields() {
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

        // Trigger preset change to show/hide custom fields
        this.handlePresetChange({ target: { value: this.workWeekConfig.preset } });
    }

    // Save work week configuration
    async saveWorkWeekConfiguration() {
        try {
            if (!this.validateCustomConfiguration()) {
                Utils.showToast('Please fix validation errors before saving', 'warning');
                return;
            }

            const response = await fetch('/api/settings/work-week', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.workWeekConfig)
            });

            if (!response.ok) throw new Error('Failed to save work week configuration');

            const result = await response.json();
            Utils.showToast('Work week configuration saved successfully', 'success');

            // Trigger callback if registered
            if (this.apiCallbacks.onSave) {
                this.apiCallbacks.onSave(result);
            }

        } catch (error) {
            console.error('Failed to save work week configuration:', error);
            Utils.showToast('Failed to save work week configuration', 'error');
        }
    }

    // Validate configuration with API
    async validateWorkWeekConfiguration(config) {
        try {
            const response = await fetch('/api/settings/work-week/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            if (!response.ok) throw new Error('Validation request failed');

            return await response.json();

        } catch (error) {
            console.error('Failed to validate work week configuration:', error);
            return { valid: false, errors: ['Failed to validate configuration'] };
        }
    }

    // Get available presets
    async getWorkWeekPresets() {
        try {
            const response = await fetch('/api/settings/work-week/presets');
            if (!response.ok) throw new Error('Failed to load presets');

            return await response.json();

        } catch (error) {
            console.error('Failed to load work week presets:', error);
            return {
                presets: [
                    { value: 'MONDAY_FRIDAY', label: 'Monday - Friday', description: 'Standard business week' },
                    { value: 'SUNDAY_THURSDAY', label: 'Sunday - Thursday', description: 'Middle East business week' },
                    { value: 'CUSTOM', label: 'Custom', description: 'Define your own work week' }
                ]
            };
        }
    }

    // Register API callbacks for testing
    registerCallback(event, callback) {
        this.apiCallbacks[event] = callback;
    }
}

// Test Suite
describe('Work Week Settings JavaScript', () => {
    let workWeekManager;

    beforeEach(() => {
        mockDom();
        workWeekManager = new WorkWeekSettingsManager();
        jest.clearAllMocks();
    });

    describe('Initialization', () => {
        test('should initialize work week settings', async () => {
            const setupSpy = jest.spyOn(workWeekManager, 'setupWorkWeekEventListeners');
            const loadSpy = jest.spyOn(workWeekManager, 'loadCurrentWorkWeekConfig');

            await workWeekManager.initializeWorkWeekSettings();

            expect(setupSpy).toHaveBeenCalled();
            expect(loadSpy).toHaveBeenCalled();
        });

        test('should have default configuration', () => {
            expect(workWeekManager.workWeekConfig).toEqual({
                preset: 'MONDAY_FRIDAY',
                start_day: 1,
                end_day: 5,
                timezone: 'America/New_York'
            });
        });
    });

    describe('Preset Selection', () => {
        test('should handle Monday-Friday preset selection', () => {
            const event = { target: { value: 'MONDAY_FRIDAY' } };
            
            workWeekManager.handlePresetChange(event);

            expect(workWeekManager.workWeekConfig.preset).toBe('MONDAY_FRIDAY');
            expect(workWeekManager.workWeekConfig.start_day).toBe(1);
            expect(workWeekManager.workWeekConfig.end_day).toBe(5);
        });

        test('should handle Sunday-Thursday preset selection', () => {
            const event = { target: { value: 'SUNDAY_THURSDAY' } };
            
            workWeekManager.handlePresetChange(event);

            expect(workWeekManager.workWeekConfig.preset).toBe('SUNDAY_THURSDAY');
            expect(workWeekManager.workWeekConfig.start_day).toBe(7);
            expect(workWeekManager.workWeekConfig.end_day).toBe(4);
        });

        test('should handle Custom preset selection', () => {
            const mockCustomFields = { 
                style: { display: 'none' }, 
                classList: { add: jest.fn(), remove: jest.fn() }
            };
            document.getElementById.mockReturnValue(mockCustomFields);

            const event = { target: { value: 'CUSTOM' } };
            
            workWeekManager.handlePresetChange(event);

            expect(workWeekManager.workWeekConfig.preset).toBe('CUSTOM');
            expect(mockCustomFields.style.display).toBe('block');
            expect(mockCustomFields.classList.add).toHaveBeenCalledWith('active');
        });
    });

    describe('Custom Configuration', () => {
        test('should handle start day changes', () => {
            const event = { target: { id: 'work-week-start-day', value: '3' } };
            
            workWeekManager.handleCustomConfigurationChange(event);

            expect(workWeekManager.workWeekConfig.start_day).toBe(3);
        });

        test('should handle end day changes', () => {
            const event = { target: { id: 'work-week-end-day', value: '6' } };
            
            workWeekManager.handleCustomConfigurationChange(event);

            expect(workWeekManager.workWeekConfig.end_day).toBe(6);
        });
    });

    describe('Validation', () => {
        beforeEach(() => {
            workWeekManager.workWeekConfig.preset = 'CUSTOM';
        });

        test('should validate valid custom configuration', () => {
            workWeekManager.workWeekConfig.start_day = 1;
            workWeekManager.workWeekConfig.end_day = 5;

            const isValid = workWeekManager.validateCustomConfiguration();

            expect(isValid).toBe(true);
            expect(workWeekManager.validationErrors).toHaveLength(0);
        });

        test('should detect same start and end day error', () => {
            workWeekManager.workWeekConfig.start_day = 3;
            workWeekManager.workWeekConfig.end_day = 3;

            const isValid = workWeekManager.validateCustomConfiguration();

            expect(isValid).toBe(false);
            expect(workWeekManager.validationErrors).toContainEqual({
                field: 'work-week',
                message: 'Start day and end day must be different'
            });
        });

        test('should detect invalid start day range', () => {
            workWeekManager.workWeekConfig.start_day = 0;
            workWeekManager.workWeekConfig.end_day = 5;

            const isValid = workWeekManager.validateCustomConfiguration();

            expect(isValid).toBe(false);
            expect(workWeekManager.validationErrors).toContainEqual({
                field: 'start-day',
                message: 'Start day must be between 1-7 (1=Monday, 7=Sunday)'
            });
        });

        test('should detect invalid end day range', () => {
            workWeekManager.workWeekConfig.start_day = 1;
            workWeekManager.workWeekConfig.end_day = 8;

            const isValid = workWeekManager.validateCustomConfiguration();

            expect(isValid).toBe(false);
            expect(workWeekManager.validationErrors).toContainEqual({
                field: 'end-day',
                message: 'End day must be between 1-7 (1=Monday, 7=Sunday)'
            });
        });

        test('should skip validation for preset configurations', () => {
            workWeekManager.workWeekConfig.preset = 'MONDAY_FRIDAY';
            workWeekManager.workWeekConfig.start_day = 3; // Invalid, but should be ignored
            workWeekManager.workWeekConfig.end_day = 3;   // Invalid, but should be ignored

            const isValid = workWeekManager.validateCustomConfiguration();

            expect(isValid).toBe(true);
            expect(workWeekManager.validationErrors).toHaveLength(0);
        });
    });

    describe('Preview Generation', () => {
        test('should generate Monday-Friday preview', () => {
            const mockPreviewContainer = { innerHTML: '' };
            document.getElementById.mockReturnValue(mockPreviewContainer);

            workWeekManager.workWeekConfig = {
                preset: 'MONDAY_FRIDAY',
                start_day: 1,
                end_day: 5
            };

            workWeekManager.updateWorkWeekPreview();

            expect(mockPreviewContainer.innerHTML).toContain('Work Week: Monday - Friday');
            expect(mockPreviewContainer.innerHTML).toContain('Saturday → Previous week, Sunday → Next week');
        });

        test('should generate Sunday-Thursday preview', () => {
            const mockPreviewContainer = { innerHTML: '' };
            document.getElementById.mockReturnValue(mockPreviewContainer);

            workWeekManager.workWeekConfig = {
                preset: 'SUNDAY_THURSDAY',
                start_day: 7,
                end_day: 4
            };

            workWeekManager.updateWorkWeekPreview();

            expect(mockPreviewContainer.innerHTML).toContain('Work Week: Sunday - Thursday');
            expect(mockPreviewContainer.innerHTML).toContain('Friday & Saturday → Next week');
        });

        test('should generate custom preview', () => {
            const mockPreviewContainer = { innerHTML: '' };
            document.getElementById.mockReturnValue(mockPreviewContainer);

            workWeekManager.workWeekConfig = {
                preset: 'CUSTOM',
                start_day: 2,
                end_day: 6
            };

            workWeekManager.updateWorkWeekPreview();

            expect(mockPreviewContainer.innerHTML).toContain('Custom Work Week: Tuesday - Saturday');
            expect(mockPreviewContainer.innerHTML).toContain('Work week starts: Tuesday');
            expect(mockPreviewContainer.innerHTML).toContain('Work week ends: Saturday');
        });
    });

    describe('API Integration', () => {
        test('should load current configuration from API', async () => {
            const mockConfig = {
                preset: 'SUNDAY_THURSDAY',
                start_day: 7,
                end_day: 4,
                timezone: 'UTC'
            };

            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockConfig
            });

            await workWeekManager.loadCurrentWorkWeekConfig();

            expect(global.fetch).toHaveBeenCalledWith('/api/settings/work-week');
            expect(workWeekManager.workWeekConfig).toEqual(expect.objectContaining(mockConfig));
        });

        test('should handle API loading errors', async () => {
            global.fetch.mockRejectedValueOnce(new Error('Network error'));

            await workWeekManager.loadCurrentWorkWeekConfig();

            expect(Utils.showToast).toHaveBeenCalledWith('Failed to load work week settings', 'error');
        });

        test('should save configuration to API', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ success: true })
            });

            workWeekManager.validationErrors = []; // Ensure validation passes

            await workWeekManager.saveWorkWeekConfiguration();

            expect(global.fetch).toHaveBeenCalledWith('/api/settings/work-week', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(workWeekManager.workWeekConfig)
            });
            expect(Utils.showToast).toHaveBeenCalledWith('Work week configuration saved successfully', 'success');
        });

        test('should handle API saving errors', async () => {
            global.fetch.mockRejectedValueOnce(new Error('Save failed'));

            workWeekManager.validationErrors = []; // Ensure validation passes

            await workWeekManager.saveWorkWeekConfiguration();

            expect(Utils.showToast).toHaveBeenCalledWith('Failed to save work week configuration', 'error');
        });

        test('should prevent saving with validation errors', async () => {
            workWeekManager.validationErrors = [{ field: 'test', message: 'Test error' }];

            await workWeekManager.saveWorkWeekConfiguration();

            expect(global.fetch).not.toHaveBeenCalled();
            expect(Utils.showToast).toHaveBeenCalledWith('Please fix validation errors before saving', 'warning');
        });

        test('should validate configuration with API', async () => {
            const mockValidationResult = { valid: true, errors: [] };
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockValidationResult
            });

            const config = { preset: 'CUSTOM', start_day: 1, end_day: 5 };
            const result = await workWeekManager.validateWorkWeekConfiguration(config);

            expect(global.fetch).toHaveBeenCalledWith('/api/settings/work-week/validate', expect.objectContaining({
                method: 'POST',
                body: JSON.stringify(config)
            }));
            expect(result).toEqual(mockValidationResult);
        });

        test('should get available presets from API', async () => {
            const mockPresets = {
                presets: [
                    { value: 'MONDAY_FRIDAY', label: 'Monday - Friday' },
                    { value: 'SUNDAY_THURSDAY', label: 'Sunday - Thursday' },
                    { value: 'CUSTOM', label: 'Custom' }
                ]
            };

            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockPresets
            });

            const result = await workWeekManager.getWorkWeekPresets();

            expect(global.fetch).toHaveBeenCalledWith('/api/settings/work-week/presets');
            expect(result).toEqual(mockPresets);
        });
    });

    describe('Error Handling', () => {
        test('should handle network errors gracefully', async () => {
            global.fetch.mockRejectedValueOnce(new Error('Network error'));

            await workWeekManager.loadCurrentWorkWeekConfig();

            expect(Utils.showToast).toHaveBeenCalledWith('Failed to load work week settings', 'error');
        });

        test('should handle API validation errors', async () => {
            global.fetch.mockResolvedValueOnce({
                ok: false,
                status: 400
            });

            const result = await workWeekManager.validateWorkWeekConfiguration({});

            expect(result.valid).toBe(false);
            expect(result.errors).toContain('Failed to validate configuration');
        });

        test('should provide fallback presets on API failure', async () => {
            global.fetch.mockRejectedValueOnce(new Error('API error'));

            const result = await workWeekManager.getWorkWeekPresets();

            expect(result.presets).toBeDefined();
            expect(result.presets.length).toBeGreaterThan(0);
            expect(result.presets[0]).toHaveProperty('value');
            expect(result.presets[0]).toHaveProperty('label');
        });
    });

    describe('User Experience', () => {
        test('should update validation display with errors', () => {
            const mockValidationContainer = {
                innerHTML: '',
                classList: { add: jest.fn(), remove: jest.fn() }
            };
            const mockSaveButton = {
                disabled: false,
                classList: { add: jest.fn(), remove: jest.fn() }
            };

            document.getElementById.mockImplementation(id => {
                if (id === 'work-week-validation') return mockValidationContainer;
                if (id === 'save-work-week-btn') return mockSaveButton;
                return null;
            });

            workWeekManager.validationErrors = [
                { field: 'test', message: 'Test error message' }
            ];

            workWeekManager.updateValidationDisplay();

            expect(mockValidationContainer.innerHTML).toContain('Test error message');
            expect(mockValidationContainer.classList.add).toHaveBeenCalledWith('has-errors');
            expect(mockSaveButton.disabled).toBe(true);
            expect(mockSaveButton.classList.add).toHaveBeenCalledWith('disabled');
        });

        test('should clear validation display when no errors', () => {
            const mockValidationContainer = {
                innerHTML: 'Previous errors',
                classList: { add: jest.fn(), remove: jest.fn() }
            };
            const mockSaveButton = {
                disabled: true,
                classList: { add: jest.fn(), remove: jest.fn() }
            };

            document.getElementById.mockImplementation(id => {
                if (id === 'work-week-validation') return mockValidationContainer;
                if (id === 'save-work-week-btn') return mockSaveButton;
                return null;
            });

            workWeekManager.validationErrors = [];

            workWeekManager.updateValidationDisplay();

            expect(mockValidationContainer.innerHTML).toBe('');
            expect(mockValidationContainer.classList.remove).toHaveBeenCalledWith('has-errors');
            expect(mockSaveButton.disabled).toBe(false);
            expect(mockSaveButton.classList.remove).toHaveBeenCalledWith('disabled');
        });

        test('should trigger callbacks on save', async () => {
            const mockCallback = jest.fn();
            const mockResult = { success: true };

            workWeekManager.registerCallback('onSave', mockCallback);
            workWeekManager.validationErrors = [];

            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockResult
            });

            await workWeekManager.saveWorkWeekConfiguration();

            expect(mockCallback).toHaveBeenCalledWith(mockResult);
        });
    });

    describe('Integration with Existing Settings', () => {
        test('should integrate with existing settings form structure', () => {
            const mockElements = {
                'work-week-preset': { addEventListener: jest.fn() },
                'work-week-start-day': { addEventListener: jest.fn() },
                'work-week-end-day': { addEventListener: jest.fn() },
                'save-work-week-btn': { addEventListener: jest.fn() }
            };

            document.getElementById.mockImplementation(id => mockElements[id] || null);

            workWeekManager.setupWorkWeekEventListeners();

            Object.values(mockElements).forEach(element => {
                expect(element.addEventListener).toHaveBeenCalled();
            });
        });

        test('should handle missing DOM elements gracefully', () => {
            document.getElementById.mockReturnValue(null);

            expect(() => {
                workWeekManager.setupWorkWeekEventListeners();
                workWeekManager.updateWorkWeekPreview();
                workWeekManager.updateValidationDisplay();
            }).not.toThrow();
        });
    });
});

// Export for use in other test files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { WorkWeekSettingsManager, mockDom };
}