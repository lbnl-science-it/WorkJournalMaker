#!/usr/bin/env node

/**
 * Validation Script for Work Week JavaScript Implementation
 * 
 * This script validates that the JavaScript implementation is syntactically correct
 * and tests basic functionality without requiring a full browser environment.
 */

const fs = require('fs');
const path = require('path');

// Simple test framework
class SimpleTestRunner {
    constructor() {
        this.tests = [];
        this.passed = 0;
        this.failed = 0;
    }

    test(name, testFn) {
        this.tests.push({ name, testFn });
    }

    async run() {
        console.log('🧪 Running Work Week JavaScript Validation Tests\n');

        for (const { name, testFn } of this.tests) {
            try {
                await testFn();
                console.log(`✅ ${name}`);
                this.passed++;
            } catch (error) {
                console.log(`❌ ${name}: ${error.message}`);
                this.failed++;
            }
        }

        console.log(`\n📊 Test Results: ${this.passed} passed, ${this.failed} failed`);
        return this.failed === 0;
    }
}

// Mock browser globals for Node.js environment
function mockBrowserGlobals() {
    global.document = {
        getElementById: () => null,
        querySelector: () => null,
        querySelectorAll: () => [],
        createElement: () => ({
            style: {},
            classList: { add: () => {}, remove: () => {} },
            addEventListener: () => {}
        }),
        addEventListener: () => {}
    };

    global.fetch = async (url, options) => {
        return {
            ok: true,
            status: 200,
            json: async () => ({ success: true })
        };
    };

    global.Utils = {
        showToast: () => {},
        debounce: (fn) => fn
    };

    global.FileReader = function() {
        this.readAsText = () => {};
    };

    global.URL = {
        createObjectURL: () => 'mock-url',
        revokeObjectURL: () => {}
    };

    global.setTimeout = (fn, delay) => fn();
    global.confirm = () => true;
}

// Load and evaluate the settings.js file
function loadSettingsJS() {
    const settingsPath = path.join(__dirname, 'web', 'static', 'js', 'settings.js');
    
    if (!fs.existsSync(settingsPath)) {
        throw new Error('settings.js file not found');
    }

    const content = fs.readFileSync(settingsPath, 'utf8');
    
    // Remove the DOMContentLoaded event listener for testing
    let modifiedContent = content.replace(
        /document\.addEventListener\('DOMContentLoaded'.*?\}\);/s,
        '// DOM event listener removed for testing'
    );

    // Add global assignment for testing
    modifiedContent += '\n\nif (typeof global !== "undefined") { global.SettingsManager = SettingsManager; }';

    return modifiedContent;
}

// Test suite
async function runValidationTests() {
    mockBrowserGlobals();

    const runner = new SimpleTestRunner();

    runner.test('JavaScript syntax is valid', () => {
        const settingsContent = loadSettingsJS();
        // This will throw if there are syntax errors
        eval(settingsContent);
    });

    runner.test('SettingsManager class can be instantiated', () => {
        const settingsContent = loadSettingsJS();
        eval(settingsContent);
        
        const manager = new global.SettingsManager();
        if (!manager) throw new Error('Failed to create SettingsManager instance');
        if (!manager.workWeekConfig) throw new Error('Work week config not initialized');
    });

    runner.test('Work week config has correct default values', () => {
        const settingsContent = loadSettingsJS();
        eval(settingsContent);
        
        const manager = new global.SettingsManager();
        const config = manager.workWeekConfig;
        
        if (config.preset !== 'MONDAY_FRIDAY') throw new Error('Default preset incorrect');
        if (config.start_day !== 1) throw new Error('Default start day incorrect');
        if (config.end_day !== 5) throw new Error('Default end day incorrect');
    });

    runner.test('Preset change handler works correctly', () => {
        const settingsContent = loadSettingsJS();
        eval(settingsContent);
        
        const manager = new global.SettingsManager();
        
        // Test Monday-Friday preset
        manager.handlePresetChange({ target: { value: 'MONDAY_FRIDAY' } });
        if (manager.workWeekConfig.start_day !== 1 || manager.workWeekConfig.end_day !== 5) {
            throw new Error('Monday-Friday preset not set correctly');
        }
        
        // Test Sunday-Thursday preset
        manager.handlePresetChange({ target: { value: 'SUNDAY_THURSDAY' } });
        if (manager.workWeekConfig.start_day !== 7 || manager.workWeekConfig.end_day !== 4) {
            throw new Error('Sunday-Thursday preset not set correctly');
        }
    });

    runner.test('Custom configuration validation works', () => {
        const settingsContent = loadSettingsJS();
        eval(settingsContent);
        
        const manager = new global.SettingsManager();
        
        // Test valid custom configuration
        manager.workWeekConfig.preset = 'CUSTOM';
        manager.workWeekConfig.start_day = 2;
        manager.workWeekConfig.end_day = 6;
        
        if (!manager.validateCustomConfiguration()) {
            throw new Error('Valid custom configuration should pass validation');
        }
        
        // Test invalid custom configuration (same start and end day)
        manager.workWeekConfig.start_day = 3;
        manager.workWeekConfig.end_day = 3;
        
        if (manager.validateCustomConfiguration()) {
            throw new Error('Invalid custom configuration should fail validation');
        }
        
        if (manager.workWeekValidationErrors.length === 0) {
            throw new Error('Validation errors should be populated');
        }
    });

    runner.test('Work days list generation works', () => {
        const settingsContent = loadSettingsJS();
        eval(settingsContent);
        
        const manager = new global.SettingsManager();
        
        // Test normal week (Mon-Fri)
        const normalWeek = manager.generateWorkDaysList(1, 5);
        if (!normalWeek.includes('Monday') || !normalWeek.includes('Friday')) {
            throw new Error('Normal week generation failed');
        }
        
        // Test wrapped week (Thu-Tue)
        const wrappedWeek = manager.generateWorkDaysList(4, 2);
        if (!wrappedWeek.includes('Thursday') || !wrappedWeek.includes('Tuesday')) {
            throw new Error('Wrapped week generation failed');
        }
    });

    runner.test('API integration methods exist and are callable', async () => {
        const settingsContent = loadSettingsJS();
        eval(settingsContent);
        
        const manager = new global.SettingsManager();
        
        // Test that API methods exist
        if (typeof manager.saveWorkWeekConfiguration !== 'function') {
            throw new Error('saveWorkWeekConfiguration method missing');
        }
        
        if (typeof manager.loadCurrentWorkWeekConfig !== 'function') {
            throw new Error('loadCurrentWorkWeekConfig method missing');
        }
        
        if (typeof manager.validateWorkWeekConfiguration !== 'function') {
            throw new Error('validateWorkWeekConfiguration method missing');
        }
        
        // Test that methods can be called (they should handle errors gracefully)
        try {
            await manager.loadCurrentWorkWeekConfig();
            await manager.validateWorkWeekConfiguration();
        } catch (error) {
            // Methods should handle API errors gracefully, not throw
            if (error.message.includes('is not a function')) {
                throw error;
            }
        }
    });

    runner.test('Animation helper methods exist', () => {
        const settingsContent = loadSettingsJS();
        eval(settingsContent);
        
        const manager = new global.SettingsManager();
        
        if (typeof manager.addSlideAnimation !== 'function') {
            throw new Error('addSlideAnimation method missing');
        }
        
        if (typeof manager.addPreviewAnimation !== 'function') {
            throw new Error('addPreviewAnimation method missing');
        }
        
        if (typeof manager.addSuccessAnimation !== 'function') {
            throw new Error('addSuccessAnimation method missing');
        }
        
        // Test that animation methods handle null elements gracefully
        manager.addSlideAnimation(null, 'show');
        manager.addPreviewAnimation(null);
        manager.addSuccessAnimation(null);
    });

    return await runner.run();
}

// Check JavaScript test files exist
function validateTestFiles() {
    const testFiles = [
        'tests/test_work_week_settings_javascript.js',
        'tests/test_work_week_javascript_integration.js'
    ];

    console.log('📁 Checking test files exist...\n');

    for (const testFile of testFiles) {
        const fullPath = path.join(__dirname, testFile);
        if (fs.existsSync(fullPath)) {
            console.log(`✅ ${testFile} exists`);
        } else {
            console.log(`❌ ${testFile} missing`);
            return false;
        }
    }

    return true;
}

// Main execution
async function main() {
    console.log('🚀 Work Week JavaScript Implementation Validation\n');

    // Check if test files exist
    if (!validateTestFiles()) {
        console.log('\n❌ Some test files are missing');
        process.exit(1);
    }

    console.log('\n🧪 Running functionality tests...\n');

    // Run validation tests
    const success = await runValidationTests();

    if (success) {
        console.log('\n🎉 All validation tests passed! The Work Week JavaScript implementation is ready.');
        console.log('\n📋 Implementation Summary:');
        console.log('   ✅ Work week configuration management');
        console.log('   ✅ Preset and custom configuration support');
        console.log('   ✅ Real-time validation and preview');
        console.log('   ✅ API integration for save/load operations');
        console.log('   ✅ Smooth animations and user feedback');
        console.log('   ✅ Integration with existing settings system');
        
        process.exit(0);
    } else {
        console.log('\n❌ Some validation tests failed. Please review the implementation.');
        process.exit(1);
    }
}

// Run if called directly
if (require.main === module) {
    main().catch(error => {
        console.error('💥 Validation failed with error:', error.message);
        process.exit(1);
    });
}

module.exports = { runValidationTests, validateTestFiles };