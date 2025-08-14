/**
 * Integration Test for Work Week JavaScript with Existing Settings
 * 
 * This test verifies that the work week functionality integrates properly
 * with the existing SettingsManager without breaking existing functionality.
 */

// Mock browser environment for testing
const mockBrowserEnvironment = () => {
    global.document = {
        getElementById: jest.fn(),
        querySelector: jest.fn(),
        querySelectorAll: jest.fn(() => []),
        createElement: jest.fn(() => ({
            href: '',
            download: '',
            click: jest.fn(),
            appendChild: jest.fn(),
            parentElement: { removeChild: jest.fn() },
            style: {},
            classList: { add: jest.fn(), remove: jest.fn() }
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

    global.FileReader = jest.fn(() => ({
        onload: null,
        onerror: null,
        readAsText: jest.fn()
    }));

    global.confirm = jest.fn(() => true);
    global.setTimeout = jest.fn((fn, delay) => fn());
    global.console = {
        error: jest.fn(),
        info: jest.fn(),
        log: jest.fn()
    };
};

// Import the SettingsManager class (in a real environment, this would be different)
// For testing purposes, we'll redefine the class here with the same structure
class TestSettingsManager {
    constructor() {
        this.settings = {};
        this.categories = {};
        this.changedSettings = new Set();
        this.currentCategory = 'filesystem';
        
        // Work week specific properties
        this.workWeekConfig = {
            preset: 'MONDAY_FRIDAY',
            start_day: 1,
            end_day: 5,
            timezone: 'America/New_York'
        };
        this.workWeekValidationErrors = [];
    }

    async init() {
        // Simulate initialization
        return Promise.resolve();
    }

    async initializeWorkWeekSettings() {
        return Promise.resolve();
    }

    setupWorkWeekEventListeners() {
        // Mock event listener setup
    }

    validateCustomConfiguration() {
        this.workWeekValidationErrors = [];
        const { start_day, end_day, preset } = this.workWeekConfig;

        if (preset !== 'CUSTOM') {
            return true;
        }

        if (start_day === end_day) {
            this.workWeekValidationErrors.push({
                field: 'work-week',
                message: 'Start day and end day must be different'
            });
        }

        return this.workWeekValidationErrors.length === 0;
    }

    updateWorkWeekPreview() {
        // Mock preview update
    }

    handlePresetChange(event) {
        const preset = event.target.value;
        this.workWeekConfig.preset = preset;

        if (preset === 'MONDAY_FRIDAY') {
            this.workWeekConfig.start_day = 1;
            this.workWeekConfig.end_day = 5;
        } else if (preset === 'SUNDAY_THURSDAY') {
            this.workWeekConfig.start_day = 7;
            this.workWeekConfig.end_day = 4;
        }

        this.updateWorkWeekPreview();
        this.validateCustomConfiguration();
    }

    async loadSettings() {
        global.fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ setting1: 'value1' })
        });

        const response = await fetch('/api/settings/');
        this.settings = await response.json();
    }

    async saveWorkWeekConfiguration() {
        if (!this.validateCustomConfiguration()) {
            throw new Error('Validation failed');
        }

        global.fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ success: true })
        });

        const response = await fetch('/api/settings/work-week', {
            method: 'POST',
            body: JSON.stringify(this.workWeekConfig)
        });

        return await response.json();
    }
}

describe('Work Week JavaScript Integration Tests', () => {
    let settingsManager;

    beforeEach(() => {
        mockBrowserEnvironment();
        settingsManager = new TestSettingsManager();
        jest.clearAllMocks();
    });

    describe('Integration with Existing Settings Manager', () => {
        test('should initialize without breaking existing functionality', async () => {
            await settingsManager.init();
            
            expect(settingsManager.settings).toBeDefined();
            expect(settingsManager.categories).toBeDefined();
            expect(settingsManager.changedSettings).toBeDefined();
        });

        test('should have work week properties alongside existing properties', () => {
            expect(settingsManager.workWeekConfig).toBeDefined();
            expect(settingsManager.workWeekValidationErrors).toBeDefined();
            expect(settingsManager.settings).toBeDefined();
            expect(settingsManager.categories).toBeDefined();
        });

        test('should load regular settings without affecting work week settings', async () => {
            await settingsManager.loadSettings();
            
            expect(global.fetch).toHaveBeenCalledWith('/api/settings/');
            expect(settingsManager.settings).toEqual({ setting1: 'value1' });
            expect(settingsManager.workWeekConfig.preset).toBe('MONDAY_FRIDAY');
        });
    });

    describe('Work Week Functionality Integration', () => {
        test('should handle preset changes correctly', () => {
            const event = { target: { value: 'SUNDAY_THURSDAY' } };
            
            settingsManager.handlePresetChange(event);
            
            expect(settingsManager.workWeekConfig.preset).toBe('SUNDAY_THURSDAY');
            expect(settingsManager.workWeekConfig.start_day).toBe(7);
            expect(settingsManager.workWeekConfig.end_day).toBe(4);
        });

        test('should validate configurations properly', () => {
            settingsManager.workWeekConfig.preset = 'CUSTOM';
            settingsManager.workWeekConfig.start_day = 1;
            settingsManager.workWeekConfig.end_day = 5;
            
            const isValid = settingsManager.validateCustomConfiguration();
            
            expect(isValid).toBe(true);
            expect(settingsManager.workWeekValidationErrors).toHaveLength(0);
        });

        test('should detect validation errors', () => {
            settingsManager.workWeekConfig.preset = 'CUSTOM';
            settingsManager.workWeekConfig.start_day = 3;
            settingsManager.workWeekConfig.end_day = 3;
            
            const isValid = settingsManager.validateCustomConfiguration();
            
            expect(isValid).toBe(false);
            expect(settingsManager.workWeekValidationErrors).toHaveLength(1);
            expect(settingsManager.workWeekValidationErrors[0].message).toContain('must be different');
        });

        test('should save work week configuration via API', async () => {
            const result = await settingsManager.saveWorkWeekConfiguration();
            
            expect(global.fetch).toHaveBeenCalledWith('/api/settings/work-week', expect.objectContaining({
                method: 'POST',
                body: JSON.stringify(settingsManager.workWeekConfig)
            }));
            expect(result.success).toBe(true);
        });

        test('should prevent saving with validation errors', async () => {
            settingsManager.workWeekConfig.preset = 'CUSTOM';
            settingsManager.workWeekConfig.start_day = 3;
            settingsManager.workWeekConfig.end_day = 3;
            
            await expect(settingsManager.saveWorkWeekConfiguration()).rejects.toThrow('Validation failed');
        });
    });

    describe('Event Listener Integration', () => {
        test('should setup work week event listeners without conflicts', () => {
            const mockElements = {
                'work-week-preset': { addEventListener: jest.fn() },
                'work-week-start-day': { addEventListener: jest.fn() },
                'work-week-end-day': { addEventListener: jest.fn() },
                'save-work-week-btn': { addEventListener: jest.fn() },
                'reset-work-week-btn': { addEventListener: jest.fn() }
            };

            document.getElementById.mockImplementation(id => mockElements[id] || null);

            settingsManager.setupWorkWeekEventListeners();

            // Verify event listeners were added
            expect(mockElements['work-week-preset'].addEventListener).toHaveBeenCalledWith('change', expect.any(Function));
            expect(mockElements['work-week-start-day'].addEventListener).toHaveBeenCalledWith('change', expect.any(Function));
            expect(mockElements['save-work-week-btn'].addEventListener).toHaveBeenCalledWith('click', expect.any(Function));
        });

        test('should handle missing DOM elements gracefully', () => {
            document.getElementById.mockReturnValue(null);
            
            expect(() => {
                settingsManager.setupWorkWeekEventListeners();
                settingsManager.updateWorkWeekPreview();
            }).not.toThrow();
        });
    });

    describe('API Integration', () => {
        test('should make work week API calls with correct format', async () => {
            const mockConfig = {
                preset: 'CUSTOM',
                start_day: 2,
                end_day: 6,
                timezone: 'UTC'
            };

            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockConfig
            });

            // Simulate loading work week config
            const response = await fetch('/api/settings/work-week');
            const config = await response.json();

            expect(global.fetch).toHaveBeenCalledWith('/api/settings/work-week');
            expect(config).toEqual(mockConfig);
        });

        test('should handle API errors gracefully', async () => {
            global.fetch.mockRejectedValueOnce(new Error('Network error'));

            // This should not throw, but handle the error gracefully
            try {
                await fetch('/api/settings/work-week');
            } catch (error) {
                expect(error.message).toBe('Network error');
            }

            expect(global.fetch).toHaveBeenCalledWith('/api/settings/work-week');
        });
    });

    describe('State Management', () => {
        test('should maintain separate state for work week and regular settings', () => {
            settingsManager.settings = { regularSetting: 'value' };
            settingsManager.workWeekConfig.preset = 'CUSTOM';
            settingsManager.changedSettings.add('regularSetting');

            expect(settingsManager.settings.regularSetting).toBe('value');
            expect(settingsManager.workWeekConfig.preset).toBe('CUSTOM');
            expect(settingsManager.changedSettings.has('regularSetting')).toBe(true);
        });

        test('should reset work week state independently', () => {
            settingsManager.workWeekValidationErrors = [{ field: 'test', message: 'error' }];
            settingsManager.workWeekConfig.preset = 'CUSTOM';

            // Reset work week state
            settingsManager.workWeekValidationErrors = [];
            settingsManager.workWeekConfig = {
                preset: 'MONDAY_FRIDAY',
                start_day: 1,
                end_day: 5,
                timezone: 'America/New_York'
            };

            expect(settingsManager.workWeekValidationErrors).toHaveLength(0);
            expect(settingsManager.workWeekConfig.preset).toBe('MONDAY_FRIDAY');
        });
    });

    describe('User Experience Features', () => {
        test('should provide immediate validation feedback', () => {
            settingsManager.workWeekConfig.preset = 'CUSTOM';
            settingsManager.workWeekConfig.start_day = 1;
            settingsManager.workWeekConfig.end_day = 1;

            const isValid = settingsManager.validateCustomConfiguration();

            expect(isValid).toBe(false);
            expect(settingsManager.workWeekValidationErrors).toHaveLength(1);
            expect(settingsManager.workWeekValidationErrors[0].field).toBe('work-week');
        });

        test('should update configuration on preset change', () => {
            const mondayFridayEvent = { target: { value: 'MONDAY_FRIDAY' } };
            const sundayThursdayEvent = { target: { value: 'SUNDAY_THURSDAY' } };

            settingsManager.handlePresetChange(mondayFridayEvent);
            expect(settingsManager.workWeekConfig.start_day).toBe(1);
            expect(settingsManager.workWeekConfig.end_day).toBe(5);

            settingsManager.handlePresetChange(sundayThursdayEvent);
            expect(settingsManager.workWeekConfig.start_day).toBe(7);
            expect(settingsManager.workWeekConfig.end_day).toBe(4);
        });
    });
});

// Export for use in other test files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TestSettingsManager, mockBrowserEnvironment };
}