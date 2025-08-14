"""
Work Week CSS Validation Tests

This module provides comprehensive tests for the work week CSS styling components.
Tests validate CSS class definitions, responsive design, accessibility features,
and design system consistency.
"""

import os
import re
import pytest
from pathlib import Path


class TestWorkWeekCSSValidation:
    """Test suite for work week CSS styling components."""
    
    @classmethod
    def setup_class(cls):
        """Set up test fixtures and CSS content."""
        cls.css_file_path = Path(__file__).parent.parent / "web" / "static" / "css" / "settings.css"
        cls.test_css_path = Path(__file__).parent / "test_work_week_css.html"
        
        # Read CSS content
        if cls.css_file_path.exists():
            with open(cls.css_file_path, 'r', encoding='utf-8') as f:
                cls.css_content = f.read()
        else:
            cls.css_content = ""
        
        # Read test HTML content (contains work week CSS)
        if cls.test_css_path.exists():
            with open(cls.test_css_path, 'r', encoding='utf-8') as f:
                cls.test_css_content = f.read()
        else:
            cls.test_css_content = ""
    
    def test_css_files_exist(self):
        """Test that required CSS files exist."""
        assert self.css_file_path.exists(), f"Settings CSS file not found: {self.css_file_path}"
        assert self.test_css_path.exists(), f"Test CSS file not found: {self.test_css_path}"
    
    def test_work_week_main_classes_defined(self):
        """Test that main work week CSS classes are defined."""
        required_classes = [
            'work-week-settings',
            'work-week-preset',
            'work-week-preview',
            'custom-schedule',
            'validation-feedback'
        ]
        
        for class_name in required_classes:
            pattern = rf'\.{re.escape(class_name)}\s*\{{'
            assert re.search(pattern, self.test_css_content), f"CSS class '{class_name}' not found"
    
    def test_work_week_component_classes_defined(self):
        """Test that component-specific CSS classes are defined."""
        component_classes = [
            'work-week-preset-select',
            'work-week-preview-title',
            'work-week-preview-content',
            'work-week-preview-schedule',
            'work-week-day',
            'custom-schedule-row',
            'custom-schedule-field',
            'custom-schedule-label',
            'custom-schedule-select'
        ]
        
        for class_name in component_classes:
            pattern = rf'\.{re.escape(class_name)}\s*\{{'
            assert re.search(pattern, self.test_css_content), f"Component class '{class_name}' not found"
    
    def test_validation_state_classes_defined(self):
        """Test that validation state CSS classes are defined."""
        validation_classes = [
            'validation-feedback.success',
            'validation-feedback.warning',
            'validation-feedback.error'
        ]
        
        for class_name in validation_classes:
            # Handle compound selectors
            escaped_class = class_name.replace('.', r'\.')
            pattern = rf'\.{escaped_class}\s*\{{'
            assert re.search(pattern, self.test_css_content), f"Validation class '{class_name}' not found"
    
    def test_help_and_loading_classes_defined(self):
        """Test that help text and loading state classes are defined."""
        support_classes = [
            'work-week-help',
            'work-week-help-title',
            'work-week-help-content',
            'work-week-loading',
            'work-week-spinner'
        ]
        
        for class_name in support_classes:
            pattern = rf'\.{re.escape(class_name)}\s*\{{'
            assert re.search(pattern, self.test_css_content), f"Support class '{class_name}' not found"
    
    def test_css_variables_usage(self):
        """Test that CSS custom properties (variables) are used correctly."""
        required_variables = [
            '--color-primary',
            '--color-background',
            '--color-surface',
            '--color-border',
            '--color-text-primary',
            '--color-success',
            '--color-warning',
            '--color-error',
            '--space-',  # Any spacing variable
            '--font-size-',  # Any font size variable
            '--radius-',  # Any radius variable
            '--transition-'  # Any transition variable
        ]
        
        for var_name in required_variables:
            pattern = rf'var\({re.escape(var_name)}'
            assert re.search(pattern, self.test_css_content), f"CSS variable pattern '{var_name}' not used"
    
    def test_responsive_design_media_queries(self):
        """Test that responsive design media queries are present."""
        # Check for mobile breakpoint
        mobile_query = r'@media\s*\([^)]*max-width:\s*768px[^)]*\)'
        assert re.search(mobile_query, self.test_css_content), "Mobile media query not found"
        
        # Check that responsive classes are defined within media queries
        responsive_patterns = [
            r'\.custom-schedule-row\s*\{[^}]*flex-direction:\s*column',
            r'\.work-week-preview-schedule\s*\{[^}]*justify-content:\s*center'
        ]
        
        for pattern in responsive_patterns:
            assert re.search(pattern, self.test_css_content, re.DOTALL), f"Responsive pattern not found: {pattern[:30]}..."
    
    def test_accessibility_features(self):
        """Test that accessibility features are implemented."""
        # Test for high contrast media query
        high_contrast_query = r'@media\s*\([^)]*prefers-contrast:\s*high[^)]*\)'
        assert re.search(high_contrast_query, self.test_css_content), "High contrast media query not found"
        
        # Test for reduced motion media query
        reduced_motion_query = r'@media\s*\([^)]*prefers-reduced-motion:\s*reduce[^)]*\)'
        assert re.search(reduced_motion_query, self.test_css_content), "Reduced motion media query not found"
        
        # Test for focus states
        focus_patterns = [
            r'\.work-week-preset-select:focus\s*\{',
            r'\.custom-schedule-select:focus\s*\{'
        ]
        
        for pattern in focus_patterns:
            assert re.search(pattern, self.test_css_content), f"Focus state not found: {pattern[:30]}..."
    
    def test_dark_theme_support(self):
        """Test that dark theme styling is implemented."""
        # Check for dark theme attribute selector
        dark_theme_pattern = r'\[data-theme="dark"\]'
        assert re.search(dark_theme_pattern, self.test_css_content), "Dark theme selector not found"
        
        # Check that dark theme affects work week components
        dark_theme_work_week_patterns = [
            r'\[data-theme="dark"\].*\.work-week-preview',
            r'\[data-theme="dark"\].*\.work-week-day'
        ]
        
        for pattern in dark_theme_work_week_patterns:
            assert re.search(pattern, self.test_css_content, re.DOTALL), f"Dark theme work week pattern not found: {pattern[:30]}..."
    
    def test_animation_keyframes_defined(self):
        """Test that required animations and keyframes are defined."""
        required_animations = [
            'slideDown',
            'spin'
        ]
        
        for animation in required_animations:
            keyframe_pattern = rf'@keyframes\s+{re.escape(animation)}\s*\{{'
            assert re.search(keyframe_pattern, self.test_css_content), f"Keyframe animation '{animation}' not found"
    
    def test_color_consistency(self):
        """Test that colors are used consistently throughout the work week CSS."""
        # Test that validation colors match the defined color variables
        validation_color_patterns = [
            r'rgba\(52,\s*199,\s*89',  # Success color pattern
            r'rgba\(255,\s*149,\s*0',  # Warning color pattern
            r'rgba\(255,\s*59,\s*48'   # Error color pattern
        ]
        
        for pattern in validation_color_patterns:
            assert re.search(pattern, self.test_css_content), f"Validation color pattern not found: {pattern}"
    
    def test_layout_properties(self):
        """Test that layout properties are properly defined."""
        layout_patterns = [
            r'display:\s*flex',
            r'gap:\s*var\(--space-\d+\)',
            r'padding:\s*var\(--space-\d+\)',
            r'margin:\s*var\(--space-\d+\)'
        ]
        
        for pattern in layout_patterns:
            assert re.search(pattern, self.test_css_content), f"Layout property pattern not found: {pattern}"
    
    def test_transition_properties(self):
        """Test that transition properties are defined for interactive elements."""
        transition_selectors = [
            'work-week-settings',
            'work-week-preset-select',
            'custom-schedule',
            'validation-feedback'
        ]
        
        for selector in transition_selectors:
            # Look for transition property in the selector block
            selector_pattern = rf'\.{re.escape(selector)}\s*\{{[^}}]*transition:[^;]*;[^}}]*\}}'
            assert re.search(selector_pattern, self.test_css_content, re.DOTALL), f"Transition not found for '{selector}'"
    
    def test_font_properties(self):
        """Test that font properties use design system variables."""
        font_patterns = [
            r'font-size:\s*var\(--font-size-\w+\)',
            r'font-weight:\s*\d+',
            r'line-height:\s*[\d.]+',
        ]
        
        for pattern in font_patterns:
            assert re.search(pattern, self.test_css_content), f"Font property pattern not found: {pattern}"
    
    def test_interactive_states(self):
        """Test that interactive states (hover, focus, active) are defined."""
        interactive_states = [
            ':hover',
            ':focus',
            '.active'
        ]
        
        for state in interactive_states:
            pattern = rf'{re.escape(state)}\s*\{{'
            assert re.search(pattern, self.test_css_content), f"Interactive state '{state}' not found"


class TestWorkWeekCSSStructure:
    """Test suite for CSS structure and organization."""
    
    def test_css_syntax_validity(self):
        """Test that CSS syntax is valid (basic check)."""
        test_css_path = Path(__file__).parent / "test_work_week_css.html"
        if test_css_path.exists():
            with open(test_css_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract CSS from style blocks
            css_blocks = re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
            
            for css_block in css_blocks:
                # Basic syntax checks
                open_braces = css_block.count('{')
                close_braces = css_block.count('}')
                assert open_braces == close_braces, f"Mismatched braces in CSS block: {open_braces} != {close_braces}"
    
    def test_css_organization(self):
        """Test that CSS is well-organized with proper comments and sections."""
        test_css_path = Path(__file__).parent / "test_work_week_css.html"
        if test_css_path.exists():
            with open(test_css_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for section comments
            section_comments = [
                'Work Week Settings Section',
                'Work Week Preset Selector',
                'Custom Schedule Configuration',
                'Work Week Preview',
                'Validation Feedback',
                'Help Text',
                'Loading States',
                'Animations',
                'Responsive Design',
                'High Contrast Mode',
                'Reduced Motion',
                'Dark Theme Adjustments'
            ]
            
            for comment in section_comments:
                pattern = rf'/\*.*{re.escape(comment)}.*\*/'
                assert re.search(pattern, content, re.DOTALL), f"Section comment not found: {comment}"
    
    def test_css_specificity_management(self):
        """Test that CSS specificity is managed appropriately."""
        test_css_path = Path(__file__).parent / "test_work_week_css.html"
        if test_css_path.exists():
            with open(test_css_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check that we're not using overly specific selectors (no more than 3 levels deep)
            overly_specific_pattern = r'\.[a-zA-Z-]+\s+\.[a-zA-Z-]+\s+\.[a-zA-Z-]+\s+\.[a-zA-Z-]+'
            matches = re.findall(overly_specific_pattern, content)
            
            # Allow some exceptions for complex state selectors
            acceptable_exceptions = ['data-theme', 'prefers-contrast', 'prefers-reduced-motion']
            problematic_matches = []
            
            for match in matches:
                is_exception = any(exception in match for exception in acceptable_exceptions)
                if not is_exception:
                    problematic_matches.append(match)
            
            assert len(problematic_matches) == 0, f"Overly specific selectors found: {problematic_matches}"


def run_css_tests():
    """Run all CSS validation tests."""
    # Run the tests programmatically
    pytest.main([__file__, '-v'])


if __name__ == "__main__":
    run_css_tests()