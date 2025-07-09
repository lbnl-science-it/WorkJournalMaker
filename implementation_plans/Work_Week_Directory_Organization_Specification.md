# Work Week Directory Organization - Complete Developer Specification

## Executive Summary

This specification addresses the current issue where journal entries create individual daily "week ending" directories instead of properly grouping entries into weekly directories based on configurable work schedules.

## Problem Statement

**Current Behavior**: Each journal entry creates its own "week ending" directory (e.g., `week_ending_2025-06-02`, `week_ending_2025-06-03`), resulting in fragmented daily directories.

**Desired Behavior**: Journal entries should be grouped into proper weekly directories based on user-configurable work week settings, with intelligent weekend handling.

## Requirements

### Functional Requirements

#### FR-1: Work Week Configuration System
- **FR-1.1**: System provides Monday-Friday as default work week
- **FR-1.2**: Users can override default with custom work week settings
- **FR-1.3**: Configuration supports preset options: "Monday-Friday", "Sunday-Thursday"
- **FR-1.4**: Configuration supports custom start/end day selection
- **FR-1.5**: Invalid configurations are auto-corrected (e.g., Monday start + Sunday end = following Sunday)

#### FR-2: Weekend Day Assignment Logic
- **FR-2.1**: Saturday entries assigned to previous work week (week ending Friday before)
- **FR-2.2**: Sunday entries assigned to next work week (week ending Friday after)
- **FR-2.3**: Weekend assignment logic applies consistently regardless of user's work week configuration

#### FR-3: Directory Organization
- **FR-3.1**: Maintain existing `week_ending_YYYY-MM-DD` naming convention
- **FR-3.2**: Directory date represents the end date of the work week
- **FR-3.3**: New entries use corrected weekly grouping logic
- **FR-3.4**: Existing entries remain in current locations (no migration)

#### FR-4: User Interface
- **FR-4.1**: Work week settings integrated into existing settings page
- **FR-4.2**: Dropdown selection for preset work weeks
- **FR-4.3**: Custom option reveals start/end day selectors
- **FR-4.4**: Help text explains weekend handling logic
- **FR-4.5**: Real-time preview of selected work week configuration

### Non-Functional Requirements

#### NFR-1: Performance
- **NFR-1.1**: Work week calculation adds <10ms to journal entry creation
- **NFR-1.2**: Settings page loads within 2 seconds
- **NFR-1.3**: Configuration changes take effect immediately

#### NFR-2: Compatibility
- **NFR-2.1**: Backward compatible - existing users get Monday-Friday default
- **NFR-2.2**: System handles mixed directory structure (old daily + new weekly)
- **NFR-2.3**: No breaking changes to existing API endpoints

#### NFR-3: Reliability
- **NFR-3.1**: Work week calculation is deterministic and consistent
- **NFR-3.2**: Timezone handling prevents date boundary issues
- **NFR-3.3**: Configuration validation prevents invalid states

## Architecture Design

### Data Model Changes

#### User Settings Extension
```sql
-- Add to existing user settings table
ALTER TABLE user_settings ADD COLUMN work_week_start_day INTEGER DEFAULT 1; -- 1=Monday
ALTER TABLE user_settings ADD COLUMN work_week_end_day INTEGER DEFAULT 5;   -- 5=Friday
ALTER TABLE user_settings ADD COLUMN work_week_preset VARCHAR(20) DEFAULT 'monday-friday';
```

#### Configuration Schema
```json
{
  "workWeek": {
    "preset": "monday-friday" | "sunday-thursday" | "custom",
    "startDay": 1-7, // 1=Monday, 7=Sunday
    "endDay": 1-7,
    "timezone": "user_local"
  }
}
```

### Core Algorithm

#### Week Ending Date Calculation
```python
def calculate_week_ending_date(entry_date, work_week_config, user_timezone):
    """
    Calculate the appropriate week ending date for a journal entry.
    
    Args:
        entry_date: Date of journal entry (in user's timezone)
        work_week_config: User's work week configuration
        user_timezone: User's timezone for date calculations
    
    Returns:
        Date representing the end of the work week for this entry
    """
    
    # Convert entry date to user's timezone
    local_entry_date = entry_date.astimezone(user_timezone).date()
    
    # Get work week boundaries
    start_day = work_week_config['startDay']  # 1=Monday
    end_day = work_week_config['endDay']      # 5=Friday
    
    # Calculate days from start of week
    entry_weekday = local_entry_date.weekday() + 1  # Convert to 1-7 format
    
    # Determine if entry falls within work week or weekend
    if is_within_work_week(entry_weekday, start_day, end_day):
        # Entry is within work week - find the end date of this work week
        return find_work_week_end(local_entry_date, start_day, end_day)
    else:
        # Entry is on weekend - apply nearest work week logic
        return assign_weekend_to_work_week(local_entry_date, start_day, end_day)

def is_within_work_week(entry_day, start_day, end_day):
    """Check if entry day falls within the work week."""
    if start_day <= end_day:
        # Normal week (e.g., Mon-Fri)
        return start_day <= entry_day <= end_day
    else:
        # Week spans weekend (e.g., Fri-Thu)
        return entry_day >= start_day or entry_day <= end_day

def assign_weekend_to_work_week(entry_date, start_day, end_day):
    """Assign weekend entries to nearest work week."""
    entry_weekday = entry_date.weekday() + 1
    
    if entry_weekday == 6:  # Saturday
        # Assign to previous work week
        return find_previous_work_week_end(entry_date, start_day, end_day)
    elif entry_weekday == 7:  # Sunday
        # Assign to next work week
        return find_next_work_week_end(entry_date, start_day, end_day)
```

### Component Integration

#### Settings Service Extension
```python
class WorkWeekService:
    def get_user_work_week_config(self, user_id):
        """Retrieve user's work week configuration."""
        
    def update_work_week_config(self, user_id, config):
        """Update user's work week configuration with validation."""
        
    def validate_work_week_config(self, config):
        """Validate and auto-correct work week configuration."""
        
    def get_default_work_week_config(self):
        """Return system default work week configuration."""
```

#### Entry Manager Integration
```python
class EntryManager:
    def create_entry(self, user_id, entry_data):
        # Get user's work week configuration
        work_week_config = self.work_week_service.get_user_work_week_config(user_id)
        
        # Calculate correct week ending date
        week_ending_date = calculate_week_ending_date(
            entry_data['date'], 
            work_week_config, 
            user_timezone
        )
        
        # Create directory path
        directory_path = f"week_ending_{week_ending_date.strftime('%Y-%m-%d')}"
        
        # Save entry to correct directory
        return self.save_entry(directory_path, entry_data)
```

## User Interface Specification

### Settings Page Integration

#### Work Week Section Layout
```html
<section class="work-week-settings">
    <h3>Work Week Configuration</h3>
    <p class="help-text">Configure your work week to properly organize journal entries. Weekend entries are automatically assigned to the nearest work week.</p>
    
    <div class="form-group">
        <label for="work-week-preset">Work Week Schedule</label>
        <select id="work-week-preset" name="workWeekPreset">
            <option value="monday-friday" selected>Monday - Friday</option>
            <option value="sunday-thursday">Sunday - Thursday</option>
            <option value="custom">Custom Schedule</option>
        </select>
    </div>
    
    <div class="custom-schedule" style="display: none;">
        <div class="form-row">
            <div class="form-group">
                <label for="start-day">Start Day</label>
                <select id="start-day" name="startDay">
                    <option value="1">Monday</option>
                    <option value="2">Tuesday</option>
                    <!-- ... other days ... -->
                    <option value="7">Sunday</option>
                </select>
            </div>
            <div class="form-group">
                <label for="end-day">End Day</label>
                <select id="end-day" name="endDay">
                    <option value="1">Monday</option>
                    <!-- ... other days ... -->
                    <option value="7">Sunday</option>
                </select>
            </div>
        </div>
    </div>
    
    <div class="preview-section">
        <h4>Preview</h4>
        <p class="preview-text">Your work week: <span id="work-week-preview">Monday - Friday</span></p>
        <p class="weekend-text">Weekend handling: Saturday → Previous week, Sunday → Next week</p>
    </div>
</section>
```

#### JavaScript Behavior
```javascript
class WorkWeekSettings {
    constructor() {
        this.initializeEventListeners();
        this.loadCurrentSettings();
    }
    
    initializeEventListeners() {
        document.getElementById('work-week-preset').addEventListener('change', this.handlePresetChange.bind(this));
        document.getElementById('start-day').addEventListener('change', this.updatePreview.bind(this));
        document.getElementById('end-day').addEventListener('change', this.validateAndUpdatePreview.bind(this));
    }
    
    handlePresetChange(event) {
        const preset = event.target.value;
        const customSection = document.querySelector('.custom-schedule');
        
        if (preset === 'custom') {
            customSection.style.display = 'block';
        } else {
            customSection.style.display = 'none';
            this.applyPreset(preset);
        }
        this.updatePreview();
    }
    
    validateAndUpdatePreview() {
        const config = this.getCurrentConfig();
        const validatedConfig = this.validateConfig(config);
        
        if (validatedConfig !== config) {
            this.applyConfig(validatedConfig);
            this.showValidationMessage('Configuration adjusted for valid work week');
        }
        
        this.updatePreview();
    }
    
    validateConfig(config) {
        // Auto-correct invalid configurations
        if (config.startDay === config.endDay) {
            // Single day work week - extend to next day
            config.endDay = (config.endDay % 7) + 1;
        }
        
        return config;
    }
}
```

## Error Handling Strategy

### Validation Errors
- **Invalid Work Week Configuration**: Auto-correct and notify user
- **Timezone Conversion Errors**: Fall back to server timezone with warning
- **Date Calculation Errors**: Use current date as fallback

### Runtime Errors
- **Directory Creation Failures**: Retry with fallback directory structure
- **Database Update Failures**: Maintain previous configuration, log error
- **Configuration Load Failures**: Use system default configuration

### User Experience Errors
- **Settings Save Failures**: Show error message, maintain form state
- **Preview Generation Errors**: Show generic preview text
- **Validation Message Display**: Clear, actionable error messages

## Testing Plan

### Unit Tests

#### Work Week Calculation Tests
```python
class TestWorkWeekCalculation(unittest.TestCase):
    def test_monday_friday_work_week(self):
        """Test standard Monday-Friday work week calculations."""
        config = {'startDay': 1, 'endDay': 5}  # Mon-Fri
        
        # Test weekday entries
        monday_entry = date(2025, 6, 2)  # Monday
        self.assertEqual(
            calculate_week_ending_date(monday_entry, config, timezone.utc),
            date(2025, 6, 6)  # Friday
        )
        
        # Test weekend entries
        saturday_entry = date(2025, 6, 7)  # Saturday
        self.assertEqual(
            calculate_week_ending_date(saturday_entry, config, timezone.utc),
            date(2025, 6, 6)  # Previous Friday
        )
        
        sunday_entry = date(2025, 6, 8)  # Sunday
        self.assertEqual(
            calculate_week_ending_date(sunday_entry, config, timezone.utc),
            date(2025, 6, 13)  # Next Friday
        )
    
    def test_sunday_thursday_work_week(self):
        """Test Sunday-Thursday work week calculations."""
        config = {'startDay': 7, 'endDay': 4}  # Sun-Thu
        
        # Test various scenarios
        # ... additional test cases
    
    def test_custom_work_week_configurations(self):
        """Test various custom work week configurations."""
        # Test edge cases and unusual configurations
        # ... additional test cases
    
    def test_timezone_handling(self):
        """Test timezone-aware date calculations."""
        # Test entries created in different timezones
        # ... additional test cases
```

#### Configuration Validation Tests
```python
class TestConfigurationValidation(unittest.TestCase):
    def test_auto_correction_same_start_end_day(self):
        """Test auto-correction when start and end day are the same."""
        
    def test_auto_correction_invalid_day_range(self):
        """Test auto-correction for invalid day ranges."""
        
    def test_preset_configuration_loading(self):
        """Test loading of preset configurations."""
```

### Integration Tests

#### Settings Service Integration
```python
class TestWorkWeekSettingsIntegration(unittest.TestCase):
    def test_user_configuration_persistence(self):
        """Test saving and loading user work week configurations."""
        
    def test_default_configuration_for_new_users(self):
        """Test that new users get Monday-Friday default."""
        
    def test_configuration_migration_for_existing_users(self):
        """Test that existing users get appropriate defaults."""
```

#### Entry Creation Integration
```python
class TestEntryCreationWithWorkWeeks(unittest.TestCase):
    def test_entry_directory_assignment(self):
        """Test that entries are saved to correct weekly directories."""
        
    def test_mixed_directory_structure_handling(self):
        """Test system handling both old daily and new weekly directories."""
        
    def test_timezone_aware_entry_creation(self):
        """Test entry creation across different timezones."""
```

### User Interface Tests

#### Settings Page Tests
```javascript
describe('Work Week Settings UI', () => {
    test('preset selection updates configuration', () => {
        // Test preset dropdown functionality
    });
    
    test('custom configuration validation', () => {
        // Test custom start/end day validation
    });
    
    test('preview updates correctly', () => {
        // Test preview text updates
    });
    
    test('configuration persistence', () => {
        // Test saving and loading settings
    });
});
```

### End-to-End Tests

#### Complete Workflow Tests
```python
class TestWorkWeekEndToEnd(unittest.TestCase):
    def test_complete_user_workflow(self):
        """Test complete workflow: configure work week → create entries → verify organization."""
        
    def test_configuration_change_impact(self):
        """Test that changing work week configuration affects new entries only."""
        
    def test_weekend_entry_scenarios(self):
        """Test various weekend entry creation scenarios."""
```

## Implementation Phases

### Phase 1: Core Algorithm Implementation (Week 1)
- Implement work week calculation logic
- Create unit tests for calculation functions
- Implement configuration validation

### Phase 2: Data Model and Services (Week 1-2)
- Update database schema for work week settings
- Implement WorkWeekService class
- Integrate with existing SettingsService
- Create integration tests

### Phase 3: Entry Manager Integration (Week 2)
- Update EntryManager to use work week calculations
- Implement directory path generation logic
- Test entry creation with new logic
- Ensure backward compatibility

### Phase 4: User Interface Implementation (Week 2-3)
- Add work week section to settings page
- Implement JavaScript for configuration management
- Add preview functionality
- Create UI tests

### Phase 5: Testing and Validation (Week 3)
- Complete comprehensive testing
- Performance testing
- User acceptance testing
- Bug fixes and optimization

### Phase 6: Deployment and Monitoring (Week 3-4)
- Deploy with feature flags
- Monitor for issues
- Gradual rollout to all users
- Documentation updates

## Success Criteria

### Functional Success
- [ ] New journal entries are grouped into proper weekly directories
- [ ] Weekend entries are correctly assigned to nearest work weeks
- [ ] Users can configure custom work week schedules
- [ ] Existing entries remain accessible in their current locations
- [ ] Configuration changes take effect immediately for new entries

### Technical Success
- [ ] Work week calculation adds <10ms to entry creation time
- [ ] Settings page loads within 2 seconds
- [ ] Zero data loss during implementation
- [ ] Backward compatibility maintained
- [ ] All tests pass with >95% code coverage

### User Experience Success
- [ ] Settings interface is intuitive and self-explanatory
- [ ] Configuration validation provides helpful feedback
- [ ] Preview functionality accurately represents user's work week
- [ ] No breaking changes to existing user workflows
- [ ] Help documentation is clear and comprehensive

## Risk Mitigation

### Technical Risks
- **Risk**: Timezone calculation errors
  - **Mitigation**: Comprehensive timezone testing, fallback mechanisms
- **Risk**: Performance impact on entry creation
  - **Mitigation**: Algorithm optimization, caching strategies
- **Risk**: Database migration issues
  - **Mitigation**: Backward-compatible schema changes, rollback plan

### User Experience Risks
- **Risk**: User confusion about new directory structure
  - **Mitigation**: Clear documentation, gradual rollout, support resources
- **Risk**: Configuration complexity
  - **Mitigation**: Sensible defaults, preset options, validation assistance

### Business Risks
- **Risk**: User resistance to change
  - **Mitigation**: Backward compatibility, optional migration tools
- **Risk**: Support burden increase
  - **Mitigation**: Comprehensive testing, clear documentation, FAQ preparation

## Appendices

### Appendix A: Configuration Examples
```json
// Monday-Friday (Default)
{
  "preset": "monday-friday",
  "startDay": 1,
  "endDay": 5
}

// Sunday-Thursday
{
  "preset": "sunday-thursday", 
  "startDay": 7,
  "endDay": 4
}

// Custom: Tuesday-Saturday
{
  "preset": "custom",
  "startDay": 2,
  "endDay": 6
}
```

### Appendix B: Directory Structure Examples
```
Before (Current):
├── week_ending_2025-06-02/  # Monday entry
├── week_ending_2025-06-03/  # Tuesday entry  
├── week_ending_2025-06-04/  # Wednesday entry
└── week_ending_2025-06-05/  # Thursday entry

After (Fixed):
├── week_ending_2025-06-06/  # Monday-Friday entries + Saturday
└── week_ending_2025-06-13/  # Sunday entry + next week's entries
```

### Appendix C: API Endpoints

#### Settings API Extension
```
GET /api/settings/work-week
POST /api/settings/work-week
PUT /api/settings/work-week
```

#### Response Format
```json
{
  "workWeek": {
    "preset": "monday-friday",
    "startDay": 1,
    "endDay": 5,
    "isDefault": true
  }
}
```

This specification provides complete implementation guidance for the Work Week Directory Organization feature, ensuring proper weekly grouping of journal entries while maintaining backward compatibility and user flexibility.