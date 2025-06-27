# Daily Work Journal Web Application - Complete Implementation Blueprint

## 🎯 Project Overview

This blueprint integrates a modern web interface with the existing sophisticated CLI-based Work Journal Summarizer. The approach leverages all existing components ([`ConfigManager`](config_manager.py:71), [`FileDiscovery`](file_discovery.py:54), [`UnifiedLLMClient`](unified_llm_client.py:24), etc.) while adding web functionality through a clean integration layer.

## 🚀 Detailed Implementation Prompts

### **Step 11: Base Templates & Styling**

```
Create the foundational HTML templates and CSS styling system for the web interface. Focus on minimalistic, clean, premium, aesthetic, macOS-like styling that provides a professional and distraction-free user experience.

Requirements:
1. Create minimalistic, macOS-like base templates with clean design
2. Implement responsive CSS framework with professional typography
3. Add premium aesthetic styling with proper spacing and hierarchy
4. Create reusable UI components and design system
5. Ensure accessibility and cross-browser compatibility
6. Implement dark/light theme support

Template and Styling Implementation:

1. Base Template (web/templates/base.html):
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Daily Work Journal{% endblock %}</title>
    
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Styles -->
    <link rel="stylesheet" href="/static/css/reset.css">
    <link rel="stylesheet" href="/static/css/variables.css">
    <link rel="stylesheet" href="/static/css/base.css">
    <link rel="stylesheet" href="/static/css/components.css">
    <link rel="stylesheet" href="/static/css/utilities.css">
    {% block extra_css %}{% endblock %}
    
    <!-- Favicon -->
    <link rel="icon" type="image/svg+xml" href="/static/icons/favicon.svg">
</head>
<body class="theme-light" data-theme="light">
    <!-- Navigation -->
    <nav class="nav-main">
        <div class="nav-container">
            <div class="nav-brand">
                <svg class="nav-icon" width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
                    <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2"/>
                    <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2"/>
                </svg>
                <span class="nav-title">Daily Work Journal</span>
            </div>
            
            <div class="nav-links">
                <a href="/" class="nav-link">Dashboard</a>
                <a href="/calendar" class="nav-link">Calendar</a>
                <a href="/summarize" class="nav-link">Summarize</a>
            </div>
            
            <div class="nav-actions">
                <button class="btn-icon theme-toggle" id="theme-toggle">
                    <svg class="theme-icon-light" width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="5" stroke="currentColor" stroke-width="2"/>
                        <line x1="12" y1="1" x2="12" y2="3" stroke="currentColor" stroke-width="2"/>
                    </svg>
                </button>
            </div>
        </div>
    </nav>
    
    <!-- Main Content -->
    <main class="main-content">
        {% block content %}{% endblock %}
    </main>
    
    <!-- Toast Notifications -->
    <div id="toast-container" class="toast-container"></div>
    
    <!-- Scripts -->
    <script src="/static/js/theme.js"></script>
    <script src="/static/js/utils.js"></script>
    <script src="/static/js/api.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>

2. CSS Variables (web/static/css/variables.css):
:root {
  /* Colors - Light Theme */
  --color-primary: #007AFF;
  --color-primary-hover: #0056CC;
  --color-primary-light: #E5F2FF;
  
  --color-success: #34C759;
  --color-warning: #FF9500;
  --color-error: #FF3B30;
  
  /* Neutral Colors */
  --color-background: #FFFFFF;
  --color-surface: #F2F2F7;
  --color-surface-secondary: #FFFFFF;
  --color-border: #E5E5EA;
  
  /* Text Colors */
  --color-text-primary: #1D1D1F;
  --color-text-secondary: #86868B;
  --color-text-tertiary: #C7C7CC;
  
  /* Typography */
  --font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  
  /* Spacing */
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-12: 3rem;
  
  /* Layout */
  --nav-height: 4rem;
  --container-max-width: 1200px;
  --content-max-width: 800px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  
  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;
  
  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
}

/* Dark Theme */
[data-theme="dark"] {
  --color-background: #000000;
  --color-surface: #1C1C1E;
  --color-surface-secondary: #2C2C2E;
  --color-border: #38383A;
  
  --color-text-primary: #FFFFFF;
  --color-text-secondary: #98989D;
  --color-text-tertiary: #636366;
}

3. Component Styles (web/static/css/components.css):
/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn-primary {
  background-color: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  background-color: var(--color-primary-hover);
}

.btn-secondary {
  background-color: var(--color-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover {
  background-color: var(--color-border);
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border: none;
  border-radius: var(--radius-lg);
  background-color: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-icon:hover {
  background-color: var(--color-surface);
  color: var(--color-text-primary);
}

/* Cards */
.card {
  background-color: var(--color-surface-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
}

.card:hover {
  box-shadow: var(--shadow-md);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.card-content {
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* Forms */
.form-group {
  margin-bottom: var(--space-4);
}

.form-label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.form-input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-base);
  background-color: var(--color-surface-secondary);
  color: var(--color-text-primary);
  transition: all var(--transition-fast);
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}

.form-textarea {
  resize: vertical;
  min-height: 120px;
  font-family: var(--font-family-base);
}

/* Calendar */
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  background-color: var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.calendar-day {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-surface-secondary);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

.calendar-day:hover {
  background-color: var(--color-surface);
}

.calendar-day.today {
  background-color: var(--color-primary);
  color: white;
}

.calendar-day.has-entry::after {
  content: '';
  position: absolute;
  bottom: 4px;
  right: 4px;
  width: 6px;
  height: 6px;
  background-color: var(--color-success);
  border-radius: 50%;
}

/* Toast Notifications */
.toast-container {
  position: fixed;
  top: var(--space-6);
  right: var(--space-6);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.toast {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  background-color: var(--color-surface-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  min-width: 300px;
  animation: slideIn 0.3s ease;
}

.toast.success {
  border-color: var(--color-success);
}

.toast.error {
  border-color: var(--color-error);
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

4. Base JavaScript (web/static/js/utils.js):
// Utility functions for the web interface
class Utils {
  // Date formatting
  static formatDate(date, format = 'long') {
    const options = {
      short: { month: 'short', day: 'numeric', year: 'numeric' },
      long: { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' },
      iso: undefined
    };
    
    if (format === 'iso') {
      return date.toISOString().split('T')[0];
    }
    
    return date.toLocaleDateString('en-US', options[format] || options.long);
  }
  
  // Toast notifications
  static showToast(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = this.getToastIcon(type);
    toast.innerHTML = `
      ${icon}
      <span>${message}</span>
      <button class="btn-icon" onclick="this.parentElement.remove()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
          <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
        </svg>
      </button>
    `;
    
    container.appendChild(toast);
    
    if (duration > 0) {
      setTimeout(() => toast.remove(), duration);
    }
  }
  
  static getToastIcon(type) {
    const icons = {
      success: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2"/><polyline points="22,4 12,14.01 9,11.01" stroke="currentColor" stroke-width="2"/></svg>',
      error: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2"/><line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2"/></svg>',
      warning: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" stroke="currentColor" stroke-width="2"/><line x1="12" y1="9" x2="12" y2="13" stroke="currentColor" stroke-width="2"/><line x1="12" y1="17" x2="12.01" y2="17" stroke="currentColor" stroke-width="2"/></svg>',
      info: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><line x1="12" y1="16" x2="12" y2="12" stroke="currentColor" stroke-width="2"/><line x1="12" y1="8" x2="12.01" y2="8" stroke="currentColor" stroke-width="2"/></svg>'
    };
    return icons[type] || icons.info;
  }
  
  // Loading states
  static setLoading(element, loading = true) {
    if (loading) {
      element.disabled = true;
      element.classList.add('loading');
      const originalText = element.textContent;
      element.dataset.originalText = originalText;
      element.innerHTML = `
        <svg class="spinner" width="16" height="16" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="31.416" stroke-dashoffset="31.416">
            <animate attributeName="stroke-dasharray" dur="2s" values="0 31.416;15.708 15.708;0 31.416" repeatCount="indefinite"/>
            <animate attributeName="stroke-dashoffset" dur="2s" values="0;-15.708;-31.416" repeatCount="indefinite"/>
          </circle>
        </svg>
        Loading...
      `;
    } else {
      element.disabled = false;
      element.classList.remove('loading');
      element.textContent = element.dataset.originalText || 'Submit';
    }
  }
  
  // Debounce function
  static debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
}

// Theme management
class ThemeManager {
  constructor() {
    this.init();
  }
  
  init() {
    // Get saved theme or default to light
    const savedTheme = localStorage.getItem('theme') || 'light';
    this.setTheme(savedTheme);
    
    // Set up theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => this.toggleTheme());
    }
  }
  
  setTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    document.body.className = `theme-${theme}`;
    localStorage.setItem('theme', theme);
  }
  
  toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
  }
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new ThemeManager();
});

Testing Requirements:
1. Test responsive design across different screen sizes
2. Verify theme switching functionality works correctly
3. Test accessibility features (keyboard navigation, screen readers)
4. Validate cross-browser compatibility
5. Test component reusability and consistency
6. Verify toast notifications and loading states

Success Criteria:
- Clean, minimalistic design with macOS-like aesthetics
- Responsive layout works on all device sizes
- Theme switching provides smooth transitions
- Components are reusable and consistent
- Accessibility standards are met
- Cross-browser compatibility is maintained
- Professional typography and spacing throughout

Write production-ready code with comprehensive styling, proper accessibility features, and a cohesive design system that provides an excellent user experience.
```

---

### **Step 12: Dashboard Interface**

```
Create the main dashboard interface that serves as the primary entry point for users. Focus on today's entry, recent activity, and quick actions with a clean, minimalistic design that emphasizes productivity and ease of use.

Requirements:
1. Implement main dashboard with today's entry focus
2. Add recent entries display with quick access
3. Create quick action buttons for common tasks
4. Add status indicators and navigation elements
5. Integrate with EntryManager API for real-time data
6. Ensure responsive design and accessibility

Dashboard Implementation:

1. Dashboard Template (web/templates/dashboard.html):
{% extends "base.html" %}

{% block title %}Dashboard - Daily Work Journal{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="/static/css/dashboard.css">
{% endblock %}

{% block content %}
<div class="dashboard-container">
  <!-- Today Section -->
  <section class="today-section">
    <div class="today-header">
      <div class="today-info">
        <h1 class="today-title" id="today-title">Today</h1>
        <p class="today-date" id="today-date">Loading...</p>
      </div>
      <div class="today-actions">
        <button class="btn btn-primary" id="new-entry-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2"/>
            <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2"/>
          </svg>
          New Entry
        </button>
        <button class="btn btn-secondary" id="open-today-btn" style="display: none;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
            <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2"/>
          </svg>
          Open Today's Entry
        </button>
      </div>
    </div>
    
    <div class="today-status" id="today-status">
      <div class="status-indicator">
        <div class="status-dot" id="status-dot"></div>
        <span class="status-text" id="status-text">Loading...</span>
      </div>
      <div class="status-meta" id="status-meta"></div>
    </div>
  </section>

  <!-- Quick Stats -->
  <section class="stats-section">
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value" id="total-entries">-</div>
          <div class="stat-label">Total Entries</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M3 3h18v18H3zM8 12h8M8 16h6" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value" id="this-week-entries">-</div>
          <div class="stat-label">This Week</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <polyline points="12,6 12,12 16,14" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value" id="streak-count">-</div>
          <div class="stat-label">Day Streak</div>
        </div>
      </div>
    </div>
  </section>

  <!-- Recent Entries -->
  <section class="recent-section">
    <div class="section-header">
      <h2 class="section-title">Recent Entries</h2>
      <a href="/calendar" class="section-action">View All</a>
    </div>
    
    <div class="recent-entries" id="recent-entries">
      <div class="loading-placeholder">
        <div class="loading-spinner"></div>
        <span>Loading recent entries...</span>
      </div>
    </div>
  </section>

  <!-- Quick Actions -->
  <section class="actions-section">
    <div class="section-header">
      <h2 class="section-title">Quick Actions</h2>
    </div>
    
    <div class="actions-grid">
      <button class="action-card" id="calendar-action">
        <div class="action-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
            <line x1="16" y1="2" x2="16" y2="6" stroke="currentColor" stroke-width="2"/>
            <line x1="8" y1="2" x2="8" y2="6" stroke="currentColor" stroke-width="2"/>
            <line x1="3" y1="10" x2="21" y2="10" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <div class="action-content">
          <h3 class="action-title">Browse Calendar</h3>
          <p class="action-description">View and navigate your journal entries by date</p>
        </div>
      </button>
      
      <button class="action-card" id="summarize-action">
        <div class="action-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
            <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2"/>
            <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <div class="action-content">
          <h3 class="action-title">Generate Summary</h3>
          <p class="action-description">Create weekly or monthly summaries of your work</p>
        </div>
      </button>
      
      <button class="action-card" id="search-action">
        <div class="action-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
            <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2"/>
            <path d="m21 21-4.35-4.35" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <div class="action-content">
          <h3 class="action-title">Search Entries</h3>
          <p class="action-description">Find specific entries or content across all dates</p>
        </div>
      </button>
    </div>
  </section>
</div>
{% endblock %}

{% block extra_js %}
<script src="/static/js/dashboard.js"></script>
{% endblock %}

2. Dashboard Styles (web/static/css/dashboard.css):
.dashboard-container {
  max-width: var(--container-max-width);
  margin: 0 auto;
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

/* Today Section */
.today-section {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  border-radius: var(--radius-2xl);
  padding: var(--space-8);
  color: white;
  position: relative;
  overflow: hidden;
}

.today-section::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 200px;
  height: 200px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  transform: translate(50%, -50%);
}

.today-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-6);
  position: relative;
  z-index: 1;
}

.today-title {
  font-size: var(--font-size-3xl);
  font-weight: 700;
  margin: 0;
  margin-bottom: var(--space-2);
}

.today-date {
  font-size: var(--font-size-lg);
  opacity: 0.9;
  margin: 0;
}

.today-actions {
  display: flex;
  gap: var(--space-3);
}

.today-actions .btn {
  background-color: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255,
255, 255, 255, 0.3);
  color: white;
  backdrop-filter: blur(10px);
}

.today-actions .btn:hover {
  background-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.today-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  z-index: 1;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: var(--color-success);
  animation: pulse 2s infinite;
}

.status-dot.empty {
  background-color: var(--color-warning);
}

.status-text {
  font-size: var(--font-size-lg);
  font-weight: 500;
}

.status-meta {
  font-size: var(--font-size-sm);
  opacity: 0.8;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Stats Section */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-4);
}

.stat-card {
  background-color: var(--color-surface-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  transition: all var(--transition-normal);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background-color: var(--color-primary-light);
  border-radius: var(--radius-lg);
  color: var(--color-primary);
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-top: var(--space-1);
}

/* Recent Entries */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.section-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.section-action {
  color: var(--color-primary);
  text-decoration: none;
  font-size: var(--font-size-sm);
  font-weight: 500;
  transition: color var(--transition-fast);
}

.section-action:hover {
  color: var(--color-primary-hover);
}

.recent-entries {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.entry-item {
  background-color: var(--color-surface-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.entry-item:hover {
  background-color: var(--color-surface);
  transform: translateX(4px);
}

.entry-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.entry-date {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-primary);
}

.entry-preview {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.entry-meta {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.loading-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-8);
  color: var(--color-text-secondary);
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-border);
  border-top: 2px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Quick Actions */
.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-4);
}

.action-card {
  background-color: var(--color-surface-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  cursor: pointer;
  transition: all var(--transition-normal);
  text-align: left;
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-primary);
}

.action-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  background-color: var(--color-primary-light);
  border-radius: var(--radius-xl);
  color: var(--color-primary);
  flex-shrink: 0;
}

.action-content {
  flex: 1;
}

.action-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2) 0;
}

.action-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin: 0;
}

/* Responsive Design */
@media (max-width: 768px) {
  .dashboard-container {
    padding: var(--space-4);
    gap: var(--space-6);
  }
  
  .today-header {
    flex-direction: column;
    gap: var(--space-4);
    align-items: flex-start;
  }
  
  .today-actions {
    width: 100%;
  }
  
  .today-actions .btn {
    flex: 1;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .actions-grid {
    grid-template-columns: 1fr;
  }
  
  .entry-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-2);
  }
  
  .entry-preview {
    max-width: none;
  }
}

3. Dashboard JavaScript (web/static/js/dashboard.js):
class Dashboard {
  constructor() {
    this.todayData = null;
    this.recentEntries = [];
    this.stats = {};
    
    this.init();
  }
  
  async init() {
    try {
      await this.loadTodayInfo();
      await this.loadRecentEntries();
      await this.loadStats();
      this.setupEventListeners();
    } catch (error) {
      console.error('Failed to initialize dashboard:', error);
      Utils.showToast('Failed to load dashboard data', 'error');
    }
  }
  
  async loadTodayInfo() {
    try {
      const response = await fetch('/api/calendar/today');
      if (!response.ok) throw new Error('Failed to fetch today info');
      
      this.todayData = await response.json();
      this.updateTodaySection();
    } catch (error) {
      console.error('Failed to load today info:', error);
      this.updateTodaySection(true);
    }
  }
  
  async loadRecentEntries() {
    try {
      const response = await fetch('/api/entries/recent?limit=5');
      if (!response.ok) throw new Error('Failed to fetch recent entries');
      
      const data = await response.json();
      this.recentEntries = data.entries || [];
      this.updateRecentEntriesSection();
    } catch (error) {
      console.error('Failed to load recent entries:', error);
      this.updateRecentEntriesSection(true);
    }
  }
  
  async loadStats() {
    try {
      const response = await fetch('/api/entries/stats/database');
      if (!response.ok) throw new Error('Failed to fetch stats');
      
      this.stats = await response.json();
      this.updateStatsSection();
    } catch (error) {
      console.error('Failed to load stats:', error);
      this.updateStatsSection(true);
    }
  }
  
  updateTodaySection(error = false) {
    const titleEl = document.getElementById('today-title');
    const dateEl = document.getElementById('today-date');
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    const statusMeta = document.getElementById('status-meta');
    const newEntryBtn = document.getElementById('new-entry-btn');
    const openTodayBtn = document.getElementById('open-today-btn');
    
    if (error || !this.todayData) {
      dateEl.textContent = 'Error loading date';
      statusText.textContent = 'Unable to load status';
      return;
    }
    
    // Update date display
    dateEl.textContent = this.todayData.formatted_date;
    
    // Update status
    if (this.todayData.has_entry) {
      statusDot.className = 'status-dot';
      statusText.textContent = 'Entry exists';
      statusMeta.textContent = this.todayData.entry_metadata ? 
        `${this.todayData.entry_metadata.word_count} words` : '';
      
      // Show open button, hide new button
      newEntryBtn.style.display = 'none';
      openTodayBtn.style.display = 'flex';
    } else {
      statusDot.className = 'status-dot empty';
      statusText.textContent = 'No entry yet';
      statusMeta.textContent = 'Click "New Entry" to get started';
      
      // Show new button, hide open button
      newEntryBtn.style.display = 'flex';
      openTodayBtn.style.display = 'none';
    }
  }
  
  updateRecentEntriesSection(error = false) {
    const container = document.getElementById('recent-entries');
    
    if (error) {
      container.innerHTML = `
        <div class="loading-placeholder">
          <span>Failed to load recent entries</span>
        </div>
      `;
      return;
    }
    
    if (!this.recentEntries.length) {
      container.innerHTML = `
        <div class="loading-placeholder">
          <span>No recent entries found</span>
        </div>
      `;
      return;
    }
    
    container.innerHTML = this.recentEntries.map(entry => `
      <div class="entry-item" data-date="${entry.date}" onclick="Dashboard.openEntry('${entry.date}')">
        <div class="entry-info">
          <div class="entry-date">${Utils.formatDate(new Date(entry.date), 'short')}</div>
          <div class="entry-preview">${this.getEntryPreview(entry)}</div>
        </div>
        <div class="entry-meta">
          <span>${entry.metadata.word_count} words</span>
          <span>•</span>
          <span>${Utils.formatDate(new Date(entry.modified_at || entry.created_at), 'short')}</span>
        </div>
      </div>
    `).join('');
  }
  
  updateStatsSection(error = false) {
    const totalEl = document.getElementById('total-entries');
    const weekEl = document.getElementById('this-week-entries');
    const streakEl = document.getElementById('streak-count');
    
    if (error || !this.stats) {
      totalEl.textContent = '?';
      weekEl.textContent = '?';
      streakEl.textContent = '?';
      return;
    }
    
    totalEl.textContent = this.stats.entries_with_content || 0;
    weekEl.textContent = this.calculateWeekEntries();
    streakEl.textContent = this.calculateStreak();
  }
  
  calculateWeekEntries() {
    // This would need to be calculated based on recent entries
    // For now, return a placeholder
    return this.recentEntries.filter(entry => {
      const entryDate = new Date(entry.date);
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      return entryDate >= weekAgo;
    }).length;
  }
  
  calculateStreak() {
    // Calculate consecutive days with entries
    // This is a simplified version - real implementation would need more data
    let streak = 0;
    const today = new Date();
    
    for (let i = 0; i < 30; i++) {
      const checkDate = new Date(today);
      checkDate.setDate(today.getDate() - i);
      
      const hasEntry = this.recentEntries.some(entry => {
        const entryDate = new Date(entry.date);
        return entryDate.toDateString() === checkDate.toDateString();
      });
      
      if (hasEntry) {
        streak++;
      } else {
        break;
      }
    }
    
    return streak;
  }
  
  getEntryPreview(entry) {
    // Extract preview text from entry content
    if (entry.content) {
      return entry.content.substring(0, 100) + (entry.content.length > 100 ? '...' : '');
    }
    return 'No content preview available';
  }
  
  setupEventListeners() {
    // New entry button
    document.getElementById('new-entry-btn')?.addEventListener('click', () => {
      this.createNewEntry();
    });
    
    // Open today button
    document.getElementById('open-today-btn')?.addEventListener('click', () => {
      Dashboard.openEntry(this.todayData.today);
    });
    
    // Quick action buttons
    document.getElementById('calendar-action')?.addEventListener('click', () => {
      window.location.href = '/calendar';
    });
    
    document.getElementById('summarize-action')?.addEventListener('click', () => {
      window.location.href = '/summarize';
    });
    
    document.getElementById('search-action')?.addEventListener('click', () => {
      // Implement search functionality
      Utils.showToast('Search functionality coming soon!', 'info');
    });
  }
  
  async createNewEntry() {
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await fetch(`/api/entries/${today}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          date: today,
          content: `${Utils.formatDate(new Date(), 'long')}\n\n`
        })
      });
      
      if (!response.ok) throw new Error('Failed to create entry');
      
      Utils.showToast('New entry created successfully!', 'success');
      
      // Redirect to editor
      window.location.href = `/entry/${today}`;
      
    } catch (error) {
      console.error('Failed to create new entry:', error);
      Utils.showToast('Failed to create new entry', 'error');
    }
  }
  
  static openEntry(date) {
    window.location.href = `/entry/${date}`;
  }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new Dashboard();
});

Testing Requirements:
1. Test dashboard loading with various data states
2. Verify today's entry status updates correctly
3. Test recent entries display and interaction
4. Validate quick action buttons functionality
5. Test responsive design on different screen sizes
6. Verify error handling for API failures

Success Criteria:
- Dashboard loads quickly with accurate today's information
- Recent entries display correctly with proper previews
- Quick stats provide meaningful insights
- Action buttons navigate to correct pages
- Responsive design works on all devices
- Error states are handled gracefully
- Loading states provide good user feedback

Write production-ready code with comprehensive error handling, responsive design, and smooth user interactions that create an excellent dashboard experience.
```

---

### **Step 13: Entry Editor Interface**

```
Create a clean, distraction-free entry editor interface that provides an excellent writing experience. Focus on simplicity, auto-save functionality, and seamless integration with the EntryManager API.

Requirements:
1. Create clean, distraction-free editor with minimalistic design
2. Implement auto-save functionality with visual feedback
3. Add markdown support and live preview capabilities
4. Integrate with EntryManager API for seamless data persistence
5. Include word count, character count, and writing statistics
6. Ensure responsive design and keyboard shortcuts

Editor Implementation:

1. Entry Editor Template (web/templates/entry_editor.html):
{% extends "base.html" %}

{% block title %}{{ entry_date }} - Daily Work Journal{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="/static/css/editor.css">
{% endblock %}

{% block content %}
<div class="editor-container">
  <!-- Editor Header -->
  <header class="editor-header">
    <div class="editor-nav">
      <button class="btn-icon back-btn" id="back-btn" title="Back to Dashboard">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <path d="m12 19-7-7 7-7" stroke="currentColor" stroke-width="2"/>
          <path d="m19 12H5" stroke="currentColor" stroke-width="2"/>
        </svg>
      </button>
      
      <div class="editor-title-section">
        <h1 class="editor-title" id="editor-title">Loading...</h1>
        <div class="editor-subtitle" id="editor-subtitle">Entry for {{ entry_date }}</div>
      </div>
    </div>
    
    <div class="editor-actions">
      <button class="btn btn-secondary" id="preview-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2"/>
          <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
        </svg>
        Preview
      </button>
      
      <button class="btn btn-primary" id="save-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" stroke="currentColor" stroke-width="2"/>
          <polyline points="17,21 17,13 7,13 7,21" stroke="currentColor" stroke-width="2"/>
          <polyline points="7,3 7,8 15,8" stroke="currentColor" stroke-width="2"/>
        </svg>
        Save
      </button>
    </div>
  </header>
  
  <!-- Editor Main Content -->
  <main class="editor-main">
    <div class="editor-workspace">
      <!-- Writing Area -->
      <div class="editor-pane" id="editor-pane">
        <div class="editor-toolbar">
          <div class="toolbar-group">
            <button class="toolbar-btn" id="bold-btn" title="Bold (Ctrl+B)">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z" stroke="currentColor" stroke-width="2"/>
                <path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z" stroke="currentColor" stroke-width="2"/>
              </svg>
            </button>
            
            <button class="toolbar-btn" id="italic-btn" title="Italic (Ctrl+I)">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <line x1="19" y1="4" x2="10" y2="4" stroke="currentColor" stroke-width="2"/>
                <line x1="14" y1="20" x2="5" y2="20" stroke="currentColor" stroke-width="2"/>
                <line x1="15" y1="4" x2="9" y2="20" stroke="currentColor" stroke-width="2"/>
              </svg>
            </button>
            
            <button class="toolbar-btn" id="heading-btn" title="Heading">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M6 12h12M6 4v16M18 4v16" stroke="currentColor" stroke-width="2"/>
              </svg>
            </button>
          </div>
          
          <div class="toolbar-group">
            <button class="toolbar-btn" id="list-btn" title="Bullet List">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <line x1="8" y1="6" x2="21" y2="6" stroke="currentColor" stroke-width="2"/>
                <line x1="8" y1="12" x2="21" y2="12" stroke="currentColor" stroke-width="2"/>
                <line x1="8" y1="18" x2="21" y2="18" stroke="currentColor" stroke-width="2"/>
                <line x1="3" y1="6" x2="3.01" y2="6" stroke="currentColor" stroke-width="2"/>
                <line x1="3" y1="12" x2="3.01" y2="12" stroke="currentColor" stroke-width="2"/>
                <line x1="3" y1="18" x2="3.01" y2="18" stroke="currentColor" stroke-width="2"/>
              </svg>
            </button>
            
            <button class="toolbar-btn" id="link-btn" title="Link">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" stroke="currentColor" stroke-width="2"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" stroke="currentColor" stroke-width="2"/>
              </svg>
            </button>
          </div>
          
          <div class="toolbar-spacer"></div>
          
          <div class="toolbar-group">
            <button class="toolbar-btn" id="fullscreen-btn" title="Focus Mode (F11)">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" stroke="currentColor" stroke-width="2"/>
              </svg>
            </button>
          </div>
        </div>
        
        <div class="editor-content">
          <textarea 
            class="editor-textarea" 
            id="editor-textarea" 
            placeholder="Start writing your journal entry..."
            spellcheck="true"
            autocomplete="off"
          ></textarea>
        </div>
      </div>
      
      <!-- Preview Pane -->
      <div class="preview-pane" id="preview-pane" style="display: none;">
        <div class="preview-header">
          <h3>Preview</h3>
          <button class="btn-icon" id="close-preview-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
            </svg>
          </button>
        </div>
        <div class="preview-content" id="preview-content">
          <p class="preview-placeholder">Start writing to see preview...</p>
        </div>
      </div>
    </div>
  </main>
  
  <!-- Editor Footer -->
  <footer class="editor-footer">
    <div class="editor-stats">
      <div class="stat-item">
        <span class="stat-label">Words:</span>
        <span class="stat-value" id="word-count">0</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Characters:</span>
        <span class="stat-value" id="char-count">0</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Lines:</span>
        <span class="stat-value" id="line-count">1</span>
      </div>
    </div>
    
    <div class="editor-status">
      <div class="save-status" id="save-status">
        <svg class="save-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" stroke="currentColor" stroke-width="2"/>
        </svg>
        <span id="save-text">All changes saved</span>
      </div>
    </div>
  </footer>
</div>

<!-- Keyboard Shortcuts Help -->
<div class="shortcuts-help" id="shortcuts-help" style="display: none;">
  <div class="shortcuts-content">
    <h3>Keyboard Shortcuts</h3>
    <div class="shortcuts-list">
      <div class="shortcut-item">
        <kbd>Ctrl</kbd> + <kbd>S</kbd>
        <span>Save</span>
      </div>
      <div class="shortcut-item">
        <kbd>Ctrl</kbd> + <kbd>B</kbd>
        <span>Bold</span>
      </div>
      <div class="shortcut-item">
        <kbd>Ctrl</kbd> + <kbd>I</kbd>
        <span>Italic</span>
      </div>
      <div class="shortcut-item">
        <kbd>F11</kbd>
        <span>Focus Mode</span>
      </div>
      <div class="shortcut-item">
        <kbd>Ctrl</kbd> + <kbd>P</kbd>
        <span>Preview</span>
      </div>
    </div>
    <button class="btn btn-secondary" onclick="document.getElementById('shortcuts-help').style.display='none'">Close</button>
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="/static/js/editor.js"></script>
{% endblock %}

2. Editor Styles (web/static/css/editor.css):
.editor-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--color-background);
}

/* Editor Header */
.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  background-color: var(--color-surface-secondary);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.editor-nav {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.back-btn {
  color: var(--color-text-secondary);
}

.back-btn:hover {
  color: var(--color-text-primary);
}

.editor-title-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.editor-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.editor-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.editor-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

/* Editor Main */
.editor-main {
  flex: 1
; 
  display: flex;
  overflow: hidden;
}

.editor-workspace {
  display: flex;
  width: 100%;
  height: 100%;
}

.editor-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--color-surface-secondary);
}

.preview-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--color-background);
  border-left: 1px solid var(--color-border);
}

/* Editor Toolbar */
.editor-toolbar {
  display: flex;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  gap: var(--space-2);
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-md);
  background-color: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toolbar-btn:hover {
  background-color: var(--color-border);
  color: var(--color-text-primary);
}

.toolbar-btn.active {
  background-color: var(--color-primary);
  color: white;
}

.toolbar-spacer {
  flex: 1;
}

/* Editor Content */
.editor-content {
  flex: 1;
  display: flex;
  position: relative;
}

.editor-textarea {
  width: 100%;
  height: 100%;
  border: none;
  outline: none;
  resize: none;
  padding: var(--space-6);
  font-family: var(--font-family-base);
  font-size: var(--font-size-base);
  line-height: 1.7;
  color: var(--color-text-primary);
  background-color: transparent;
  tab-size: 2;
}

.editor-textarea::placeholder {
  color: var(--color-text-tertiary);
}

/* Preview Pane */
.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.preview-header h3 {
  margin: 0;
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--color-text-primary);
}

.preview-content {
  flex: 1;
  padding: var(--space-6);
  overflow-y: auto;
  line-height: 1.7;
}

.preview-content h1,
.preview-content h2,
.preview-content h3,
.preview-content h4,
.preview-content h5,
.preview-content h6 {
  color: var(--color-text-primary);
  margin-top: var(--space-6);
  margin-bottom: var(--space-3);
}

.preview-content h1 { font-size: var(--font-size-2xl); }
.preview-content h2 { font-size: var(--font-size-xl); }
.preview-content h3 { font-size: var(--font-size-lg); }

.preview-content p {
  margin-bottom: var(--space-4);
  color: var(--color-text-primary);
}

.preview-content ul,
.preview-content ol {
  margin-bottom: var(--space-4);
  padding-left: var(--space-6);
}

.preview-content li {
  margin-bottom: var(--space-2);
  color: var(--color-text-primary);
}

.preview-content code {
  background-color: var(--color-surface);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-family: var(--font-family-mono);
  font-size: 0.9em;
}

.preview-content pre {
  background-color: var(--color-surface);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  overflow-x: auto;
  margin-bottom: var(--space-4);
}

.preview-placeholder {
  color: var(--color-text-tertiary);
  font-style: italic;
}

/* Editor Footer */
.editor-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-6);
  background-color: var(--color-surface-secondary);
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
}

.editor-stats {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
}

.stat-label {
  color: var(--color-text-secondary);
}

.stat-value {
  color: var(--color-text-primary);
  font-weight: 500;
}

.save-status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.save-status.saving {
  color: var(--color-warning);
}

.save-status.saved {
  color: var(--color-success);
}

.save-status.error {
  color: var(--color-error);
}

/* Focus Mode */
.editor-container.focus-mode {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background-color: var(--color-background);
}

.editor-container.focus-mode .editor-header,
.editor-container.focus-mode .editor-footer {
  display: none;
}

.editor-container.focus-mode .editor-toolbar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1;
  opacity: 0;
  transition: opacity var(--transition-normal);
}

.editor-container.focus-mode:hover .editor-toolbar {
  opacity: 1;
}

/* Keyboard Shortcuts Help */
.shortcuts-help {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.shortcuts-content {
  background-color: var(--color-surface-secondary);
  border-radius: var(--radius-xl);
  padding: var(--space-8);
  max-width: 400px;
  width: 90%;
}

.shortcuts-content h3 {
  margin: 0 0 var(--space-6) 0;
  color: var(--color-text-primary);
}

.shortcuts-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}

.shortcut-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.shortcut-item kbd {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-1) var(--space-2);
  font-size: var(--font-size-xs);
  font-family: var(--font-family-mono);
}

/* Responsive Design */
@media (max-width: 768px) {
  .editor-header {
    flex-direction: column;
    gap: var(--space-3);
    align-items: stretch;
  }
  
  .editor-nav {
    justify-content: space-between;
  }
  
  .editor-actions {
    justify-content: center;
  }
  
  .editor-workspace {
    flex-direction: column;
  }
  
  .preview-pane {
    border-left: none;
    border-top: 1px solid var(--color-border);
  }
  
  .editor-stats {
    gap: var(--space-4);
  }
  
  .editor-footer {
    flex-direction: column;
    gap: var(--space-2);
    align-items: stretch;
  }
}

3. Editor JavaScript (web/static/js/editor.js):
class JournalEditor {
  constructor(entryDate) {
    this.entryDate = entryDate;
    this.content = '';
    this.isPreviewMode = false;
    this.isFocusMode = false;
    this.autoSaveInterval = null;
    this.lastSaved = null;
    this.hasUnsavedChanges = false;
    
    this.init();
  }
  
  async init() {
    try {
      await this.loadEntry();
      this.setupEventListeners();
      this.setupAutoSave();
      this.updateStats();
      this.updateTitle();
    } catch (error) {
      console.error('Failed to initialize editor:', error);
      Utils.showToast('Failed to load entry', 'error');
    }
  }
  
  async loadEntry() {
    try {
      const response = await fetch(`/api/entries/${this.entryDate}?include_content=true`);
      
      if (response.ok) {
        const entry = await response.json();
        this.content = entry.content || '';
        document.getElementById('editor-textarea').value = this.content;
        this.lastSaved = new Date(entry.modified_at || entry.created_at);
      } else if (response.status === 404) {
        // Entry doesn't exist yet, start with empty content
        this.content = `${this.formatDate(new Date(this.entryDate))}\n\n`;
        document.getElementById('editor-textarea').value = this.content;
      } else {
        throw new Error('Failed to load entry');
      }
    } catch (error) {
      console.error('Failed to load entry:', error);
      throw error;
    }
  }
  
  setupEventListeners() {
    const textarea = document.getElementById('editor-textarea');
    const saveBtn = document.getElementById('save-btn');
    const backBtn = document.getElementById('back-btn');
    const previewBtn = document.getElementById('preview-btn');
    const closePreviewBtn = document.getElementById('close-preview-btn');
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    
    // Content change events
    textarea.addEventListener('input', () => {
      this.content = textarea.value;
      this.hasUnsavedChanges = true;
      this.updateStats();
      this.updateSaveStatus('unsaved');
      
      if (this.isPreviewMode) {
        this.updatePreview();
      }
    });
    
    // Save button
    saveBtn.addEventListener('click', () => this.saveEntry());
    
    // Back button
    backBtn.addEventListener('click', () => this.handleBack());
    
    // Preview toggle
    previewBtn.addEventListener('click', () => this.togglePreview());
    closePreviewBtn.addEventListener('click', () => this.togglePreview());
    
    // Focus mode
    fullscreenBtn.addEventListener('click', () => this.toggleFocusMode());
    
    // Toolbar buttons
    this.setupToolbarButtons();
    
    // Keyboard shortcuts
    this.setupKeyboardShortcuts();
    
    // Prevent accidental navigation
    window.addEventListener('beforeunload', (e) => {
      if (this.hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    });
  }
  
  setupToolbarButtons() {
    document.getElementById('bold-btn').addEventListener('click', () => {
      this.insertMarkdown('**', '**', 'bold text');
    });
    
    document.getElementById('italic-btn').addEventListener('click', () => {
      this.insertMarkdown('*', '*', 'italic text');
    });
    
    document.getElementById('heading-btn').addEventListener('click', () => {
      this.insertMarkdown('## ', '', 'Heading');
    });
    
    document.getElementById('list-btn').addEventListener('click', () => {
      this.insertMarkdown('- ', '', 'List item');
    });
    
    document.getElementById('link-btn').addEventListener('click', () => {
      this.insertMarkdown('[', '](url)', 'link text');
    });
  }
  
  setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Save: Ctrl+S
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        this.saveEntry();
      }
      
      // Bold: Ctrl+B
      if (e.ctrlKey && e.key === 'b') {
        e.preventDefault();
        this.insertMarkdown('**', '**', 'bold text');
      }
      
      // Italic: Ctrl+I
      if (e.ctrlKey && e.key === 'i') {
        e.preventDefault();
        this.insertMarkdown('*', '*', 'italic text');
      }
      
      // Preview: Ctrl+P
      if (e.ctrlKey && e.key === 'p') {
        e.preventDefault();
        this.togglePreview();
      }
      
      // Focus mode: F11
      if (e.key === 'F11') {
        e.preventDefault();
        this.toggleFocusMode();
      }
      
      // Help: Ctrl+?
      if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        this.showKeyboardShortcuts();
      }
    });
  }
  
  setupAutoSave() {
    this.autoSaveInterval = setInterval(() => {
      if (this.hasUnsavedChanges) {
        this.saveEntry(true); // Silent save
      }
    }, 30000); // Auto-save every 30 seconds
  }
  
  async saveEntry(silent = false) {
    try {
      if (!silent) {
        this.updateSaveStatus('saving');
        Utils.setLoading(document.getElementById('save-btn'), true);
      }
      
      const response = await fetch(`/api/entries/${this.entryDate}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          date: this.entryDate,
          content: this.content
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to save entry');
      }
      
      this.hasUnsavedChanges = false;
      this.lastSaved = new Date();
      this.updateSaveStatus('saved');
      
      if (!silent) {
        Utils.showToast('Entry saved successfully', 'success');
      }
      
    } catch (error) {
      console.error('Failed to save entry:', error);
      this.updateSaveStatus('error');
      
      if (!silent) {
        Utils.showToast('Failed to save entry', 'error');
      }
    } finally {
      if (!silent) {
        Utils.setLoading(document.getElementById('save-btn'), false);
      }
    }
  }
  
  togglePreview() {
    this.isPreviewMode = !this.isPreviewMode;
    const previewPane = document.getElementById('preview-pane');
    const previewBtn = document.getElementById('preview-btn');
    
    if (this.isPreviewMode) {
      previewPane.style.display = 'flex';
      previewBtn.classList.add('active');
      this.updatePreview();
    } else {
      previewPane.style.display = 'none';
      previewBtn.classList.remove('active');
    }
  }
  
  updatePreview() {
    const previewContent = document.getElementById('preview-content');
    
    if (this.content.trim()) {
      previewContent.innerHTML = marked.parse(this.content);
    } else {
      previewContent.innerHTML = '<p class="preview-placeholder">Start writing to see preview...</p>';
    }
  }
  
  toggleFocusMode() {
    this.isFocusMode = !this.isFocusMode;
    const container = document.querySelector('.editor-container');
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    
    if (this.isFocusMode) {
      container.classList.add('focus-mode');
      fullscreenBtn.classList.add('active');
      document.getElementById('editor-textarea').focus();
    } else {
      container.classList.remove('focus-mode');
      fullscreenBtn.classList.remove('active');
    }
  }
  
  insertMarkdown(before, after, placeholder) {
    const textarea = document.getElementById('editor-textarea');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    
    const insertText = selectedText || placeholder;
    const newText = before + insertText + after;
    
    textarea.value = textarea.value.substring(0, start) + newText + textarea.value.substring(end);
    
    // Set cursor position
    const newCursorPos = start + before.length + insertText.length;
    textarea.setSelectionRange(newCursorPos, newCursorPos);
    textarea.focus();
    
    // Update content and trigger change
    this.content = textarea.value;
    this.hasUnsavedChanges = true;
    this.updateStats();
    this.updateSaveStatus('unsaved');
  }
  
  updateStats() {
    const words = this.content.trim() ? this.content.trim().split(/\s+/).length : 0;
    const chars = this.content.length;
    const lines = this.content.split('\n').length;
    
    document.getElementById('word-count').textContent = words;
    document.getElementById('char-count').textContent = chars;
    document.getElementById('line-count').textContent = lines;
  }
  
  updateSaveStatus(status) {
    const saveStatus = document.getElementById('save-status');
    const saveText = document.getElementById('save-text');
    
    saveStatus.className = `save-status ${status}`;
    
    switch (status) {
      case 'saving':
        saveText.textContent = 'Saving...';
        break;
      case 'saved':
        saveText.textContent = this.lastSaved ? 
          `Saved ${this.formatTime(this.lastSaved)}` : 'All changes saved';
        break;
      case 'unsaved':
        saveText.textContent = 'Unsaved changes';
        break;
      case 'error':
        saveText.textContent = 'Save failed';
        break;
    }
  }
  
  updateTitle() {
    const title = document.getElementById('editor-title');
    const formattedDate = this.formatDate(new Date(this.entryDate));
    title.textContent = formattedDate;
  }
  
  async handleBack() {
    if (this.hasUnsavedChanges) {
      const shouldSave = confirm('You have unsaved changes. Save before leaving?');
      if (shouldSave) {
        await this.saveEntry();
      }
    }
    
    window.location.href = '/';
  }
  
  showKeyboardShortcuts() {
    document.getElementById('shortcuts-help').style.display = 'flex';
  }
  
  formatDate(date) {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }
  
  formatTime(date) {
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) { // Less than 1 minute
      return 'just now';
    } else if (diff < 3600000) { // Less than 1 hour
      const minutes = Math.floor(diff / 60000);
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit'
      });
    }
  }
  
  destroy() {
    if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval);
    }
  }
}

// Initialize editor when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  const entryDate = window.location.pathname.split('/').pop();
  window.journalEditor = new JournalEditor(entryDate);
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (window.journalEditor) {
    window.journalEditor.destroy();
  }
});

Testing Requirements:
1. Test editor loading with existing and new entries
2. Verify auto-save functionality works correctly
3. Test markdown preview and toolbar buttons
4. Validate keyboard shortcuts and focus mode
5. Test responsive design on different screen sizes
6. Verify data persistence and error handling

Success Criteria:
- Editor provides distraction-free writing experience
- Auto-save prevents data loss
- Markdown preview works accurately
- Keyboard shortcuts enhance productivity
- Responsive design works on all devices
- Error handling provides meaningful feedback
- Performance is smooth during typing and editing

Write production-ready code with comprehensive functionality, excellent user experience, and robust error handling for a professional journal editing interface.
```

---

### **Step 14: Calendar View Interface**

```
Create an interactive calendar view interface that provides intuitive navigation and clear visual indicators for journal entries. Focus on clean design, smooth interactions, and seamless integration with the CalendarService.

Requirements:
1. Implement interactive calendar grid with entry indicators
2. Add smooth month navigation and transitions
3. Create entry preview and quick access functionality
4. Integrate with CalendarService for real-time data
5. Ensure responsive design and touch-friendly interactions
6. Add keyboard navigation and accessibility features

Calendar Interface Implementation:

1. Calendar View Template (web/templates/calendar.html):
{% extends "base.html" %}

{% block title %}Calendar - Daily Work Journal{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="/static/css/calendar.css">
{% endblock %}

{% block content %}
<div class="calendar-container">
  <!-- Calendar Header -->
  <header class="calendar-header">
    <div class="calendar-nav">
      <button class="btn-icon nav-btn" id="prev-month-btn" title="Previous Month">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <path d="m15 18-6-6 6-6" stroke="currentColor" stroke-width="2"/>
        </svg>
      </button>
      
      <div class="calendar-title-section">
        <h1 class="calendar-title" id="calendar-title">Loading...</h1>
        <div class="calendar-subtitle" id="calendar-subtitle">Navigate your journal entries</div>
      </div>
      
      <button class="btn-icon nav-btn" id="next-month-btn" title="Next Month">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <path d="m9 18 6-6-6-6" stroke="currentColor" stroke-width="2"/>
        </svg>
      </button>
    </div>
    
    <div class="calendar-actions">
      <button class="btn btn-secondary" id="today-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <polyline points="12,6 12,12 16,14" stroke="currentColor" stroke-width="2"/>
        </svg>
        Today
      </button>
      
      <button class="btn btn-primary" id="new-entry-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2"/>
          <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2"/>
        </svg>
        New Entry
      </button>
    </div>
  </header>
  
  <!-- Calendar Grid -->
  <main class="calendar-main">
    <div class="calendar-wrapper">
      <!-- Calendar Legend -->
      <div class="calendar-legend">
        <div class="legend-item">
          <div class="legend-dot today"></div>
          <span>Today</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot has-entry"></div>
          <span>Has Entry</span>
        </div>
        <div class="legend-item">
          <div class="legend-dot selected"></div>
          <span>Selected</span>
        </div>
      </div>
      
      <!-- Calendar Grid -->
      <div class="calendar-grid-container">
        <div class="calendar-weekdays">
          <div class="weekday">Sun</div>
          <div class="weekday">Mon</div>
          <div class="weekday">Tue</div>
          <div class="weekday">Wed</div>
          <div class="weekday">Thu</div>
          <div class="weekday">Fri</div>
          <div class="weekday">Sat</div>
        </div>
        
        <div class="calendar-grid" id="calendar-grid">
          <!-- Calendar days will be populated by JavaScript -->
          <div class="calendar-loading">
            <div class="loading-spinner"></div>
            <span>Loading calendar...</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Entry Preview Panel -->
    <div class="entry-preview-panel" id="entry-preview-panel" style="display: none;">
      <div class="preview-header">
        <h3 class="preview-title" id="preview-title">Entry Preview</h3>
        <button class="btn-icon" id="close-preview-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
            <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
          </svg>
        </button>
      </div>
      
      <div class="preview-content" id="preview-content">
        <div class="preview-loading">
          <div class="loading-spinner"></div>
          <span>Loading entry...</span>
        </div>
      </div>
      
      <div class="preview-actions">
        <button class="btn btn-secondary" id="preview-edit-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2"/>
          </svg>
          Edit Entry
        </button>
      </div>
    </div>
  </main>
  
  <!-- Quick Stats -->
  <aside class="calendar-sidebar">
    <div class="stats-card">
      <h3 class="stats-title">This Month</h3>
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value" id="month-entries">-</div>
          <div class="stat-label">Entries</div>
        </div>
        <div class="stat-item">
          <div class="stat-value" id="month-words">-</div>
          <div class="stat-label">Words</div>
        </div>
        <div class="stat-item">
          <div class="stat-value" id="month-streak">-</div>
          <div class="stat-label">Streak</div>
        </div>
      </div>
    </div>
    
    <div class="recent-card">
      <h3 class="recent-title">Recent Entries</h3>
      <div class="recent-list" id="recent-list">
        <div class="recent-loading">
          <div class="loading-spinner"></div>
          <span>Loading...</span>
        </div>
      </div>
    </div>
  </aside>
</div>
{% endblock %}

{% block extra_js %}
<script src="/static/js/calendar.js"></script>
{% endblock %}

2. Calendar Styles (web/static/css/calendar.css):
.calendar-container {
  max-width: var(--container-max-width);
  margin: 0 auto;
  padding: var(--space-6);
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: var(--space-8);
  min-height: calc(100vh - var(--nav-height));
}

/* Calendar Header */
.calendar-header {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-6);
}

.calendar-nav {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.nav-btn {
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
}

.nav-btn:hover {
  color: var(--color-primary);
  transform: scale(1.1);
}

.calendar-title-section {
  text-align: center;
  min-width: 200px;
}

.calendar-title
{
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
  transition: all var(--transition-normal);
}

.calendar-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0;
}

.calendar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

/* Calendar Main */
.calendar-main {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.calendar-wrapper {
  background-color: var(--color-surface-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2xl);
  padding: var(--space-6);
}

.calendar-legend {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--color-border);
}

.legend-dot.today {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
}

.legend-dot.has-entry {
  background-color: var(--color-success);
  border-color: var(--color-success);
}

.legend-dot.selected {
  background-color: var(--color-warning);
  border-color: var(--color-warning);
}

/* Calendar Grid */
.calendar-grid-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.calendar-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  margin-bottom: var(--space-2);
}

.weekday {
  padding: var(--space-3);
  text-align: center;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
  background-color: var(--color-surface);
  border-radius: var(--radius-md);
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  background-color: var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  min-height: 300px;
}

.calendar-day {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
  font-weight: 500;
  border: 2px solid transparent;
}

.calendar-day:hover {
  background-color: var(--color-surface);
  transform: scale(1.05);
  z-index: 1;
  border-radius: var(--radius-md);
}

.calendar-day.other-month {
  color: var(--color-text-tertiary);
  background-color: var(--color-surface);
}

.calendar-day.today {
  background-color: var(--color-primary);
  color: white;
  font-weight: 700;
}

.calendar-day.today:hover {
  background-color: var(--color-primary-hover);
}

.calendar-day.has-entry::after {
  content: '';
  position: absolute;
  bottom: 4px;
  right: 4px;
  width: 8px;
  height: 8px;
  background-color: var(--color-success);
  border-radius: 50%;
  border: 2px solid var(--color-background);
}

.calendar-day.selected {
  border-color: var(--color-warning);
  background-color: var(--color-warning);
  color: white;
}

.calendar-loading {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-8);
  color: var(--color-text-secondary);
}

/* Entry Preview Panel */
.entry-preview-panel {
  background-color: var(--color-surface-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  display: flex;
  flex-direction: column;
  max-height: 400px;
  margin-top: var(--space-4);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-border);
}

.preview-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.preview-content {
  flex: 1;
  padding: var(--space-6);
  overflow-y: auto;
  line-height: 1.6;
  color: var(--color-text-primary);
}

.preview-content p {
  margin-bottom: var(--space-3);
}

.preview-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-8);
  color: var(--color-text-secondary);
}

.preview-actions {
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
}

/* Calendar Sidebar */
.calendar-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.stats-card,
.recent-card {
  background-color: var(--color-surface-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
}

.stats-title,
.recent-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--space-4) 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-top: var(--space-1);
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.recent-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-3);
  background-color: var(--color-surface);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.recent-item:hover {
  background-color: var(--color-border);
  transform: translateX(4px);
}

.recent-date {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-primary);
}

.recent-preview {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-4);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

/* Responsive Design */
@media (max-width: 1024px) {
  .calendar-container {
    grid-template-columns: 1fr;
    gap: var(--space-6);
  }
  
  .calendar-sidebar {
    order: -1;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-4);
  }
}

@media (max-width: 768px) {
  .calendar-container {
    padding: var(--space-4);
  }
  
  .calendar-header {
    flex-direction: column;
    gap: var(--space-4);
    align-items: stretch;
  }
  
  .calendar-nav {
    justify-content: center;
  }
  
  .calendar-actions {
    justify-content: center;
  }
  
  .calendar-sidebar {
    grid-template-columns: 1fr;
  }
  
  .calendar-legend {
    flex-wrap: wrap;
    gap: var(--space-3);
  }
  
  .calendar-day {
    font-size: var(--font-size-sm);
  }
  
  .weekday {
    padding: var(--space-2);
    font-size: var(--font-size-xs);
  }
}

3. Calendar JavaScript (web/static/js/calendar.js):
class CalendarView {
  constructor() {
    this.currentYear = new Date().getFullYear();
    this.currentMonth = new Date().getMonth() + 1;
    this.selectedDate = null;
    this.calendarData = null;
    this.recentEntries = [];
    
    this.init();
  }
  
  async init() {
    try {
      await this.loadCalendarData();
      await this.loadRecentEntries();
      this.setupEventListeners();
      this.updateStats();
    } catch (error) {
      console.error('Failed to initialize calendar:', error);
      Utils.showToast('Failed to load calendar', 'error');
    }
  }
  
  async loadCalendarData() {
    try {
      const response = await fetch(`/api/calendar/${this.currentYear}/${this.currentMonth}`);
      if (!response.ok) throw new Error('Failed to fetch calendar data');
      
      this.calendarData = await response.json();
      this.renderCalendar();
      this.updateTitle();
    } catch (error) {
      console.error('Failed to load calendar data:', error);
      this.renderCalendarError();
    }
  }
  
  async loadRecentEntries() {
    try {
      const response = await fetch('/api/entries/recent?limit=5');
      if (!response.ok) throw new Error('Failed to fetch recent entries');
      
      const data = await response.json();
      this.recentEntries = data.entries || [];
      this.renderRecentEntries();
    } catch (error) {
      console.error('Failed to load recent entries:', error);
      this.renderRecentEntriesError();
    }
  }
  
  renderCalendar() {
    const grid = document.getElementById('calendar-grid');
    
    if (!this.calendarData) {
      this.renderCalendarError();
      return;
    }
    
    // Create calendar grid
    const today = new Date();
    const currentDate = new Date(this.currentYear, this.currentMonth - 1, 1);
    const firstDay = currentDate.getDay();
    const daysInMonth = new Date(this.currentYear, this.currentMonth, 0).getDate();
    const daysInPrevMonth = new Date(this.currentYear, this.currentMonth - 1, 0).getDate();
    
    let html = '';
    let dayCount = 1;
    
    // Create entry lookup for fast access
    const entryLookup = {};
    this.calendarData.entries.forEach(entry => {
      entryLookup[entry.date] = entry;
    });
    
    // Generate calendar days
    for (let week = 0; week < 6; week++) {
      for (let day = 0; day < 7; day++) {
        const cellIndex = week * 7 + day;
        let dayNumber, cellDate, isCurrentMonth = true, cssClasses = ['calendar-day'];
        
        if (cellIndex < firstDay) {
          // Previous month days
          dayNumber = daysInPrevMonth - (firstDay - cellIndex - 1);
          cellDate = new Date(this.currentYear, this.currentMonth - 2, dayNumber);
          cssClasses.push('other-month');
          isCurrentMonth = false;
        } else if (dayCount <= daysInMonth) {
          // Current month days
          dayNumber = dayCount++;
          cellDate = new Date(this.currentYear, this.currentMonth - 1, dayNumber);
        } else {
          // Next month days
          dayNumber = dayCount++ - daysInMonth;
          cellDate = new Date(this.currentYear, this.currentMonth, dayNumber);
          cssClasses.push('other-month');
          isCurrentMonth = false;
        }
        
        // Check if it's today
        if (cellDate.toDateString() === today.toDateString()) {
          cssClasses.push('today');
        }
        
        // Check if it has an entry
        const dateStr = cellDate.toISOString().split('T')[0];
        const entry = entryLookup[dateStr];
        if (entry && entry.has_content) {
          cssClasses.push('has-entry');
        }
        
        // Check if it's selected
        if (this.selectedDate === dateStr) {
          cssClasses.push('selected');
        }
        
        html += `
          <div class="${cssClasses.join(' ')}" 
               data-date="${dateStr}"
               data-day="${dayNumber}"
               onclick="calendar.selectDate('${dateStr}')">
            ${dayNumber}
          </div>
        `;
      }
      
      // Break if we've filled the month
      if (dayCount > daysInMonth) break;
    }
    
    grid.innerHTML = html;
  }
  
  renderCalendarError() {
    const grid = document.getElementById('calendar-grid');
    grid.innerHTML = `
      <div class="calendar-loading">
        <span>Failed to load calendar</span>
      </div>
    `;
  }
  
  renderRecentEntries() {
    const container = document.getElementById('recent-list');
    
    if (!this.recentEntries.length) {
      container.innerHTML = `
        <div class="recent-loading">
          <span>No recent entries</span>
        </div>
      `;
      return;
    }
    
    container.innerHTML = this.recentEntries.map(entry => `
      <div class="recent-item" onclick="calendar.selectDate('${entry.date}')">
        <div class="recent-date">${Utils.formatDate(new Date(entry.date), 'short')}</div>
        <div class="recent-preview">${this.getEntryPreview(entry)}</div>
      </div>
    `).join('');
  }
  
  renderRecentEntriesError() {
    const container = document.getElementById('recent-list');
    container.innerHTML = `
      <div class="recent-loading">
        <span>Failed to load entries</span>
      </div>
    `;
  }
  
  updateTitle() {
    const title = document.getElementById('calendar-title');
    if (this.calendarData) {
      title.textContent = `${this.calendarData.month_name} ${this.calendarData.year}`;
    }
  }
  
  updateStats() {
    if (!this.calendarData) return;
    
    const entriesWithContent = this.calendarData.entries.filter(e => e.has_content);
    const totalWords = entriesWithContent.reduce((sum, e) => sum + e.word_count, 0);
    
    document.getElementById('month-entries').textContent = entriesWithContent.length;
    document.getElementById('month-words').textContent = totalWords.toLocaleString();
    document.getElementById('month-streak').textContent = this.calculateMonthStreak();
  }
  
  calculateMonthStreak() {
    if (!this.calendarData) return 0;
    
    const entriesWithContent = this.calendarData.entries
      .filter(e => e.has_content)
      .map(e => new Date(e.date))
      .sort((a, b) => b - a);
    
    if (!entriesWithContent.length) return 0;
    
    let streak = 1;
    for (let i = 1; i < entriesWithContent.length; i++) {
      const current = entriesWithContent[i];
      const previous = entriesWithContent[i - 1];
      const dayDiff = (previous - current) / (1000 * 60 * 60 * 24);
      
      if (dayDiff === 1) {
        streak++;
      } else {
        break;
      }
    }
    
    return streak;
  }
  
  setupEventListeners() {
    // Navigation buttons
    document.getElementById('prev-month-btn').addEventListener('click', () => {
      this.navigateMonth(-1);
    });
    
    document.getElementById('next-month-btn').addEventListener('click', () => {
      this.navigateMonth(1);
    });
    
    // Today button
    document.getElementById('today-btn').addEventListener('click', () => {
      this.goToToday();
    });
    
    // New entry button
    document.getElementById('new-entry-btn').addEventListener('click', () => {
      this.createNewEntry();
    });
    
    // Close preview button
    document.getElementById('close-preview-btn').addEventListener('click', () => {
      this.closePreview();
    });
    
    // Edit entry button
    document.getElementById('preview-edit-btn').addEventListener('click', () => {
      if (this.selectedDate) {
        window.location.href = `/entry/${this.selectedDate}`;
      }
    });
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      
      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          this.navigateMonth(-1);
          break;
        case 'ArrowRight':
          e.preventDefault();
          this.navigateMonth(1);
          break;
        case 't':
        case 'T':
          e.preventDefault();
          this.goToToday();
          break;
        case 'n':
        case 'N':
          e.preventDefault();
          this.createNewEntry();
          break;
        case 'Escape':
          this.closePreview();
          break;
      }
    });
  }
  
  async navigateMonth(direction) {
    this.currentMonth += direction;
    
    if (this.currentMonth > 12) {
      this.currentMonth = 1;
      this.currentYear++;
    } else if (this.currentMonth < 1) {
      this.currentMonth = 12;
      this.currentYear--;
    }
    
    await this.loadCalendarData();
  }
  
  async goToToday() {
    const today = new Date();
    this.currentYear = today.getFullYear();
    this.currentMonth = today.getMonth() + 1;
    
    await this.loadCalendarData();
    
    // Select today's date
    const todayStr = today.toISOString().split('T')[0];
    this.selectDate(todayStr);
  }
  
  async selectDate(dateStr) {
    // Remove previous selection
    document.querySelectorAll('.calendar-day.selected').forEach(el => {
      el.classList.remove('selected');
    });
    
    // Add selection to clicked date
    const dayEl = document.querySelector(`[data-date="${dateStr}"]`);
    if (dayEl) {
      dayEl.classList.add('selected');
    }
    
    this.selectedDate = dateStr;
    
    // Load and show entry preview
    await this.showEntryPreview(dateStr);
  }
  
  async showEntryPreview(dateStr) {
    const panel = document.getElementById('entry-preview-panel');
    const title = document.getElementById('preview-title');
    const content = document.getElementById('preview-content');
    
    // Show panel
    panel.style.display = 'flex';
    
    // Update title
    const date = new Date(dateStr);
    title.textContent = Utils.formatDate(date, 'long');
    
    // Show loading
    content.innerHTML = `
      <div class="preview-loading">
        <div class="loading-spinner"></div>
        <span>Loading entry...</span>
      </div>
    `;
    
    try {
      const response = await fetch(`/api/entries/${dateStr}?include_content=true`);
      
      if (response.ok) {
        const entry = await response.json();
        if (entry.content && entry.content.trim()) {
          // Show entry content (first 500 characters)
          const preview = entry.content.length > 500 ? 
            entry.content.substring(0, 500) + '...' : 
            entry.content;
          
          content.innerHTML = `
            <div class="entry-meta">
              <small>${entry.metadata.word_count} words • ${Utils.formatDate(new Date(entry.modified_at || entry.created_at), 'short')}</small>
            </div>
            <div class="entry-text">${preview.replace(/\n/g, '<br>')}</div>
          `;
        } else {
          content.innerHTML = '<p><em>This entry is empty. Click "Edit Entry" to add content.</em></p>';
        }
      } else if (response.status === 404) {
        content.innerHTML = '<p><em>No entry exists for this date. Click "New Entry" to create one.</em></p>';
      } else {
        throw new Error('Failed to load entry');
      }
    } catch (error) {
      console.error('Failed to load entry preview:', error);
      content.innerHTML = '<p><em>Failed to load entry preview.</em></p>';
    }
  }
  
  closePreview() {
    const panel = document.getElementById('entry-preview-panel');
    panel.style.display = 'none';
    
    // Remove selection
    document.querySelectorAll('.calendar-day.selected').forEach(el => {
      el.classList.remove('selected');
    });
    
    this.selectedDate = null;
  }
  
  async createNewEntry() {
    const today = new Date().toISOString().split('T')[0];
    
    try {
      const response = await fetch(`/api/entries/${today}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          date: today,
          content: `${Utils.formatDate(new Date(), 'long')}\n\n`
        })
      });
      
      if (!response.ok) throw new Error('Failed to create entry');
      
      Utils.showToast('New entry created!', 'success');
      window.location.href = `/entry/${today}`;
      
    } catch (error) {
      console.error('Failed to create new entry:', error);
      Utils.showToast('Failed to create new entry', 'error');
    }
  }
  
  getEntryPreview(entry) {
    if (entry.content) {
      return entry.content.substring(0, 60) + (entry.content.length > 60 ? '...' : '');
    }
    return 'No content preview';
  }
}

// Initialize calendar when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.calendar = new CalendarView();
});

Testing Requirements:
1. Test calendar navigation and month transitions
2. Verify entry indicators display correctly
3. Test date selection and preview functionality
4. Validate responsive design on different screen sizes
5. Test keyboard navigation and accessibility
6. Verify integration with CalendarService API

Success Criteria:
- Calendar displays correctly with proper entry indicators
- Month navigation is smooth and responsive
- Entry preview provides useful information
- Responsive design works on all devices
- Keyboard navigation enhances accessibility
- Performance is smooth during interactions
- Integration with API provides real-time data

Write production-ready code with smooth animations, excellent user experience, and comprehensive functionality for calendar-based journal navigation.
```

---

### **Step 15: Settings Management**

```
Create a comprehensive settings management system that extends the existing ConfigManager while adding web-specific configuration options. Provide an intuitive interface for users to customize their journal experience.

Requirements:
1. Create SettingsService extending existing ConfigManager
2. Implement web-specific settings and preferences. 
3. Add settings UI with validation and real-time updates
4. Maintain CLI configuration compatibility
5. Include import/export functionality for settings
6. Add settings backup and restore capabilities

Settings Implementation:

1. Settings Service (web/services/settings_service.py):
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import sys
from dataclasses import dataclass

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from config_manager import ConfigManager, AppConfig
from logger import JournalSummarizerLogger, ErrorCategory
from web.database import DatabaseManager, WebSettings
from web.services.base_service import BaseService
from web.models.settings import (
    WebSettingResponse, WebSettingCreate, WebSettingUpdate, 
    SettingsCollection, SettingsExport
)
from sqlalchemy import select, update, delete

@dataclass
class SettingDefinition:
    """Definition of a web setting."""
    key: str
    default_value: Any
    value_type: str
    description: str
    category: str
    validation_rules: Dict[str, Any] = None
    requires_restart: bool = False

class SettingsService(BaseService):
    """
    Manages web-specific settings while maintaining compatibility
    with existing CLI configuration system.
    """
    
    def __init__(self, config: AppConfig, logger: JournalSummarizerLogger, 
                 db_manager: DatabaseManager):
        """Initialize SettingsService with core dependencies."""
        super().__init__(config, logger)
        self.db_manager = db_manager
        self.config_manager = ConfigManager()
        
        # Define web-specific settings
        self.setting_definitions = {
            # Editor Settings
            'editor.auto_save_interval': SettingDefinition(
                key='editor.auto_save_interval',
                default_value=30,
                value_type='integer',
                description='Auto-save interval in seconds',
                category='editor',
                validation_rules={'min': 10, 'max': 300}
            ),
            'editor.font_size': SettingDefinition(
                key='editor.font_size',
                default_value=16,
                value_type='integer',
                description='Editor font size in pixels',
                category='editor',
                validation_rules={'min': 12, 'max': 24}
            ),
            'editor.font_family': SettingDefinition(
                key='editor.font_family',
                default_value='Inter',
                value_type='string',
                description='Editor font family',
                category='editor'
            ),
            'editor.line_height': SettingDefinition(
                key='editor.line_height',
                default_value=1.6,
                value_type='float',
                description='Editor line height',
                category='editor',
                validation_rules={'min': 1.2, 'max': 2.0}
            ),
            'editor.show_word_count': SettingDefinition(
                key='editor.show_word_count',
                default_value=True,
                value_type='boolean',
                description='Show word count in editor',
                category='editor'
            ),
            'editor.markdown_preview': SettingDefinition(
                key='editor.markdown_preview',
                default_value=True,
                value_type='boolean',
                description='Enable markdown preview',
                category='editor'
            ),
            
            # UI Settings
            'ui.theme': SettingDefinition(
                key='ui.theme',
                default_value='light',
                value_type='string',
                description='UI theme preference',
                category='ui',
                validation_rules={'options': ['light', 'dark', 'auto']}
            ),
            'ui.compact_mode': SettingDefinition(
                key='ui.compact_mode',
                default_value=False,
                value_type='boolean',
                description='Use compact UI layout',
                category='ui'
            ),
            'ui.animations_enabled': SettingDefinition(
                key='ui.animations_enabled',
                default_value=True,
                value_type='boolean',
                description='Enable UI animations',
                category='ui'
            ),
            
            # Calendar Settings
            'calendar.start_week_on': SettingDefinition(
                key='calendar.start_week_on',
                default_value=0,
                value_type='integer',
                description='First day of week (0=Sunday, 1=Monday)',
                category='calendar',
                validation_rules={'min': 0, 'max': 6}
            ),
            'calendar.show_week_numbers': SettingDefinition(
                key='calendar.show_week_numbers',
                default_value=False,
                value_type='boolean',
                description='Show week numbers in calendar',
                category='calendar'
            ),
            
            # Backup Settings
            'backup.auto_backup': SettingDefinition(
                key='backup.auto_backup',
                default_value=True,
                value_type='boolean',
                description='Enable automatic backups',
                category='backup'
            ),
            'backup.backup_interval_days': SettingDefinition(
                key='backup.backup_interval_days',
                default_value=7,
                value_type='integer',
                description='Backup interval in days',
                category='backup',
                validation_rules={'min': 1, 'max': 30}
            ),
            'backup.max_backups': SettingDefinition(
                key='backup.max_backups',
                default_value=10,
                value_type='integer',
                description='Maximum number of
backups to keep',
                category='backup',
                validation_rules={'min': 5, 'max': 50}
            )
        }
    
    async def get_all_settings(self) -> Dict[str, WebSettingResponse]:
        """Get all web settings with their current values."""
        try:
            settings = {}
            
            async with self.db_manager.get_session() as session:
                # Get all settings from database
                stmt = select(WebSettings)
                result = await session.execute(stmt)
                db_settings = result.scalars().all()
                
                # Create lookup for existing settings
                db_lookup = {setting.key: setting for setting in db_settings}
                
                # Process all defined settings
                for key, definition in self.setting_definitions.items():
                    if key in db_lookup:
                        # Use database value
                        db_setting = db_lookup[key]
                        parsed_value = self._parse_setting_value(
                            db_setting.value, db_setting.value_type
                        )
                        
                        settings[key] = WebSettingResponse(
                            id=db_setting.id,
                            key=db_setting.key,
                            value=db_setting.value,
                            value_type=db_setting.value_type,
                            description=db_setting.description or definition.description,
                            parsed_value=parsed_value,
                            created_at=db_setting.created_at,
                            modified_at=db_setting.modified_at
                        )
                    else:
                        # Use default value and create database entry
                        await self._create_default_setting(session, definition)
                        
                        settings[key] = WebSettingResponse(
                            id=0,  # Will be updated after creation
                            key=definition.key,
                            value=str(definition.default_value),
                            value_type=definition.value_type,
                            description=definition.description,
                            parsed_value=definition.default_value,
                            created_at=datetime.utcnow(),
                            modified_at=datetime.utcnow()
                        )
                
                await session.commit()
            
            return settings
            
        except Exception as e:
            self.logger.error(f"Failed to get all settings: {str(e)}", ErrorCategory.DATABASE_ERROR)
            raise
    
    async def get_setting(self, key: str) -> Optional[WebSettingResponse]:
        """Get a specific setting by key."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(WebSettings).where(WebSettings.key == key)
                result = await session.execute(stmt)
                db_setting = result.scalar_one_or_none()
                
                if db_setting:
                    parsed_value = self._parse_setting_value(
                        db_setting.value, db_setting.value_type
                    )
                    
                    return WebSettingResponse(
                        id=db_setting.id,
                        key=db_setting.key,
                        value=db_setting.value,
                        value_type=db_setting.value_type,
                        description=db_setting.description,
                        parsed_value=parsed_value,
                        created_at=db_setting.created_at,
                        modified_at=db_setting.modified_at
                    )
                
                # Return default if not found
                if key in self.setting_definitions:
                    definition = self.setting_definitions[key]
                    return WebSettingResponse(
                        id=0,
                        key=definition.key,
                        value=str(definition.default_value),
                        value_type=definition.value_type,
                        description=definition.description,
                        parsed_value=definition.default_value,
                        created_at=datetime.utcnow(),
                        modified_at=datetime.utcnow()
                    )
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get setting {key}: {str(e)}")
            return None
    
    async def update_setting(self, key: str, value: str) -> Optional[WebSettingResponse]:
        """Update a setting value."""
        try:
            # Validate setting exists and value is valid
            if key not in self.setting_definitions:
                raise ValueError(f"Unknown setting: {key}")
            
            definition = self.setting_definitions[key]
            parsed_value = self._parse_setting_value(value, definition.value_type)
            
            # Validate value
            if not self._validate_setting_value(parsed_value, definition):
                raise ValueError(f"Invalid value for setting {key}")
            
            async with self.db_manager.get_session() as session:
                # Check if setting exists
                stmt = select(WebSettings).where(WebSettings.key == key)
                result = await session.execute(stmt)
                existing_setting = result.scalar_one_or_none()
                
                if existing_setting:
                    # Update existing setting
                    update_stmt = (
                        update(WebSettings)
                        .where(WebSettings.key == key)
                        .values(
                            value=value,
                            modified_at=datetime.utcnow()
                        )
                    )
                    await session.execute(update_stmt)
                    
                    # Return updated setting
                    updated_setting = await session.scalar(
                        select(WebSettings).where(WebSettings.key == key)
                    )
                    
                else:
                    # Create new setting
                    new_setting = WebSettings(
                        key=key,
                        value=value,
                        value_type=definition.value_type,
                        description=definition.description,
                        created_at=datetime.utcnow(),
                        modified_at=datetime.utcnow()
                    )
                    session.add(new_setting)
                    await session.flush()
                    updated_setting = new_setting
                
                await session.commit()
                
                return WebSettingResponse(
                    id=updated_setting.id,
                    key=updated_setting.key,
                    value=updated_setting.value,
                    value_type=updated_setting.value_type,
                    description=updated_setting.description,
                    parsed_value=parsed_value,
                    created_at=updated_setting.created_at,
                    modified_at=updated_setting.modified_at
                )
                
        except Exception as e:
            self.logger.error(f"Failed to update setting {key}: {str(e)}")
            raise
    
    async def bulk_update_settings(self, settings: Dict[str, Any]) -> Dict[str, WebSettingResponse]:
        """Update multiple settings at once."""
        try:
            updated_settings = {}
            
            for key, value in settings.items():
                try:
                    updated_setting = await self.update_setting(key, str(value))
                    if updated_setting:
                        updated_settings[key] = updated_setting
                except Exception as e:
                    self.logger.error(f"Failed to update setting {key}: {str(e)}")
                    # Continue with other settings
            
            return updated_settings
            
        except Exception as e:
            self.logger.error(f"Failed to bulk update settings: {str(e)}")
            raise
    
    async def reset_setting(self, key: str) -> Optional[WebSettingResponse]:
        """Reset a setting to its default value."""
        if key not in self.setting_definitions:
            raise ValueError(f"Unknown setting: {key}")
        
        definition = self.setting_definitions[key]
        return await self.update_setting(key, str(definition.default_value))
    
    async def reset_all_settings(self) -> Dict[str, WebSettingResponse]:
        """Reset all settings to their default values."""
        try:
            reset_settings = {}
            
            for key, definition in self.setting_definitions.items():
                try:
                    reset_setting = await self.reset_setting(key)
                    if reset_setting:
                        reset_settings[key] = reset_setting
                except Exception as e:
                    self.logger.error(f"Failed to reset setting {key}: {str(e)}")
            
            return reset_settings
            
        except Exception as e:
            self.logger.error(f"Failed to reset all settings: {str(e)}")
            raise
    
    async def export_settings(self) -> SettingsExport:
        """Export all settings for backup or transfer."""
        try:
            settings = await self.get_all_settings()
            
            export_data = {
                'version': '1.0',
                'exported_at': datetime.utcnow().isoformat(),
                'settings': {
                    key: {
                        'value': setting.parsed_value,
                        'type': setting.value_type,
                        'description': setting.description
                    }
                    for key, setting in settings.items()
                }
            }
            
            return SettingsExport(
                version=export_data['version'],
                exported_at=export_data['exported_at'],
                settings=export_data['settings']
            )
            
        except Exception as e:
            self.logger.error(f"Failed to export settings: {str(e)}")
            raise
    
    async def import_settings(self, settings_data: Dict[str, Any]) -> Dict[str, WebSettingResponse]:
        """Import settings from exported data."""
        try:
            imported_settings = {}
            
            if 'settings' not in settings_data:
                raise ValueError("Invalid settings export format")
            
            for key, setting_data in settings_data['settings'].items():
                try:
                    if key in self.setting_definitions:
                        value = setting_data.get('value')
                        if value is not None:
                            imported_setting = await self.update_setting(key, str(value))
                            if imported_setting:
                                imported_settings[key] = imported_setting
                except Exception as e:
                    self.logger.error(f"Failed to import setting {key}: {str(e)}")
            
            return imported_settings
            
        except Exception as e:
            self.logger.error(f"Failed to import settings: {str(e)}")
            raise
    
    def get_setting_categories(self) -> Dict[str, List[str]]:
        """Get settings organized by category."""
        categories = {}
        
        for key, definition in self.setting_definitions.items():
            category = definition.category
            if category not in categories:
                categories[category] = []
            categories[category].append(key)
        
        return categories
    
    def _parse_setting_value(self, value: str, value_type: str) -> Any:
        """Parse string value to appropriate type."""
        try:
            if value_type == 'boolean':
                return value.lower() in ('true', '1', 'yes', 'on')
            elif value_type == 'integer':
                return int(value)
            elif value_type == 'float':
                return float(value)
            elif value_type == 'json':
                return json.loads(value)
            else:  # string
                return value
        except Exception:
            # Return original value if parsing fails
            return value
    
    def _validate_setting_value(self, value: Any, definition: SettingDefinition) -> bool:
        """Validate a setting value against its definition."""
        if not definition.validation_rules:
            return True
        
        rules = definition.validation_rules
        
        # Check minimum value
        if 'min' in rules and isinstance(value, (int, float)):
            if value < rules['min']:
                return False
        
        # Check maximum value
        if 'max' in rules and isinstance(value, (int, float)):
            if value > rules['max']:
                return False
        
        # Check allowed options
        if 'options' in rules:
            if value not in rules['options']:
                return False
        
        # Check string length
        if 'max_length' in rules and isinstance(value, str):
            if len(value) > rules['max_length']:
                return False
        
        return True
    
    async def _create_default_setting(self, session, definition: SettingDefinition):
        """Create a default setting in the database."""
        try:
            new_setting = WebSettings(
                key=definition.key,
                value=str(definition.default_value),
                value_type=definition.value_type,
                description=definition.description,
                created_at=datetime.utcnow(),
                modified_at=datetime.utcnow()
            )
            session.add(new_setting)
            
        except Exception as e:
            self.logger.error(f"Failed to create default setting {definition.key}: {str(e)}")

2. Settings Models (web/models/settings.py):
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Any, Dict, Optional, Union

class SettingsExport(BaseModel):
    """Model for settings export data."""
    version: str = Field(..., description="Export format version")
    exported_at: str = Field(..., description="Export timestamp")
    settings: Dict[str, Dict[str, Any]] = Field(..., description="Settings data")

class SettingsImport(BaseModel):
    """Model for settings import data."""
    settings: Dict[str, Any] = Field(..., description="Settings to import")
    
    @field_validator('settings')
    def validate_settings_format(cls, v):
        """Validate settings import format."""
        if not isinstance(v, dict):
            raise ValueError('Settings must be a dictionary')
        return v

class SettingsCategoryResponse(BaseModel):
    """Response model for settings organized by category."""
    categories: Dict[str, List[str]] = Field(..., description="Settings by category")

Testing Requirements:
1. Test settings CRUD operations
2. Verify validation rules work correctly
3. Test bulk update and reset functionality
4. Validate import/export functionality
5. Test integration with existing ConfigManager
6. Verify settings persistence across restarts

Success Criteria:
- Settings service integrates seamlessly with existing configuration
- Web-specific settings are properly validated and stored
- Import/export functionality works reliably
- Settings changes are applied immediately where possible
- CLI compatibility is maintained
- Comprehensive error handling and logging

Write production-ready code with robust validation, comprehensive error handling, and seamless integration with existing configuration systems.
```

---

### **Step 16: Summarization Interface**

```
Create a comprehensive summarization interface that provides an intuitive way to generate, track, and manage journal summaries. Focus on progress visualization, result presentation, and seamless integration with the WebSummarizationService.

Requirements:
1. Create summarization request interface with date range selection
2. Add real-time progress tracking with WebSocket integration
3. Implement result display with download and sharing options
4. Integrate with WebSummarizationService for task management
5. Add summary history and management features
6. Ensure responsive design and excellent user experience

Summarization Interface Implementation:

1. Summarization Template (web/templates/summarization.html):
{% extends "base.html" %}

{% block title %}Summarization - Daily Work Journal{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="/static/css/summarization.css">
{% endblock %}

{% block content %}
<div class="summarization-container">
  <!-- Header -->
  <header class="summarization-header">
    <div class="header-content">
      <h1 class="page-title">Generate Summary</h1>
      <p class="page-subtitle">Create AI-powered summaries of your journal entries</p>
    </div>
  </header>
  
  <!-- Summary Request Form -->
  <section class="request-section">
    <div class="request-card">
      <h2 class="card-title">New Summary Request</h2>
      
      <form class="summary-form" id="summary-form">
        <div class="form-row">
          <div class="form-group">
            <label class="form-label" for="start-date">Start Date</label>
            <input type="date" class="form-input" id="start-date" required>
          </div>
          
          <div class="form-group">
            <label class="form-label" for="end-date">End Date</label>
            <input type="date" class="form-input" id="end-date" required>
          </div>
        </div>
        
        <div class="form-group">
          <label class="form-label" for="summary-type">Summary Type</label>
          <select class="form-input" id="summary-type" required>
            <option value="">Select summary type...</option>
            <option value="weekly">Weekly Summary</option>
            <option value="monthly">Monthly Summary</option>
            <option value="custom">Custom Range Summary</option>
          </select>
        </div>
        
        <div class="form-actions">
          <button type="submit" class="btn btn-primary" id="generate-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke="currentColor" stroke-width="2"/>
            </svg>
            Generate Summary
          </button>
        </div>
      </form>
    </div>
  </section>
  
  <!-- Active Tasks -->
  <section class="tasks-section" id="tasks-section" style="display: none;">
    <h2 class="section-title">Active Tasks</h2>
    <div class="tasks-container" id="tasks-container">
      <!-- Active tasks will be populated here -->
    </div>
  </section>
  
  <!-- Summary History -->
  <section class="history-section">
    <div class="section-header">
      <h2 class="section-title">Recent Summaries</h2>
      <button class="btn btn-secondary" id="refresh-history-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <polyline points="23,4 23,10 17,10" stroke="currentColor" stroke-width="2"/>
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" stroke="currentColor" stroke-width="2"/>
        </svg>
        Refresh
      </button>
    </div>
    
    <div class="history-container" id="history-container">
      <div class="history-loading">
        <div class="loading-spinner"></div>
        <span>Loading summary history...</span>
      </div>
    </div>
  </section>
</div>

<!-- Task Progress Modal -->
<div class="modal-overlay" id="progress-modal" style="display: none;">
  <div class="modal-content progress-modal">
    <div class="modal-header">
      <h3 class="modal-title" id="progress-title">Generating Summary</h3>
      <button class="btn-icon" id="close-progress-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
          <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
        </svg>
      </button>
    </div>
    
    <div class="modal-body">
      <div class="progress-container">
        <div class="progress-bar-container">
          <div class="progress-bar" id="progress-bar">
            <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
          </div>
          <div class="progress-text" id="progress-text">0%</div>
        </div>
        
        <div class="progress-status" id="progress-status">Initializing...</div>
        
        <div class="progress-details" id="progress-details">
          <div class="detail-item">
            <span class="detail-label">Task ID:</span>
            <span class="detail-value" id="task-id-display">-</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Started:</span>
            <span class="detail-value" id="started-time">-</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Estimated Time:</span>
            <span class="detail-value" id="estimated-time">-</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="modal-footer">
      <button class="btn btn-secondary" id="cancel-task-btn">Cancel Task</button>
      <button class="btn btn-primary" id="view-result-btn" style="display: none;">View Result</button>
    </div>
  </div>
</div>

<!-- Summary Result Modal -->
<div class="modal-overlay" id="result-modal" style="display: none;">
  <div class="modal-content result-modal">
    <div class="modal-header">
      <h3 class="modal-title" id="result-title">Summary Result</h3>
      <button class="btn-icon" id="close-result-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
          <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
        </svg>
      </button>
    </div>
    
    <div class="modal-body">
      <div class="result-content" id="result-content">
        <!-- Summary result will be displayed here -->
      </div>
    </div>
    
    <div class="modal-footer">
      <button class="btn btn-secondary" id="copy-result-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke="currentColor" stroke-width="2"/>
        </svg>
        Copy to Clipboard
      </button>
      <button class="btn btn-primary" id="download-result-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2"/>
          <polyline points="7,10 12,15 17,10" stroke="currentColor" stroke-width="2"/>
          <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2"/>
        </svg>
        Download
      </button>
    </div>
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="/static/js/summarization.js"></script>
{% endblock %}

2. Summarization Styles (web/static/css/summarization.css):
.summarization-container {
  max-width: var(--container-max-width);
  margin: 0 auto;
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

/* Header */
.summarization-header {
  text-align: center;
  padding: var(--space-8) 0;
}

.page-title {
  font-size: var(--font-size-3xl);
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2) 0;
}

.page-subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
  margin: 0;
}

/* Request Section */
.request-card {
  background-color: var(--color-surface-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-2xl);
  padding: var(--space-8);
  max-width: 600px;
  margin: 0 auto;
}

.card-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 var(--space-6) 0;
  text-align: center;
}

.summary-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.form-actions {
  display: flex;
  justify-content: center;
  margin-top: var(--space-4);
}

/* Tasks Section */
.tasks-section {
  background-color: var(--color-surface-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.section-title {
  font-size: var(--font-size-xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.tasks-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.task-item {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.task-info {
  flex: 1;
}

.task-title {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 0 0 var(--space-1) 0;
}

.task-meta {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.task-progress {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.task-progress-bar {
  width: 100px;
  height: 8px;
  background-color: var(--color-border);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.task-progress-fill {
  height: 100%;
  background-color: var(--color-primary);
  transition: width var(--transition-normal);
}

.task-actions {
  display: flex;
  gap: var(--space-2);
}

/* History Section */
.history-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--space-4);
}

.history-item {
  background-color: var(--color-surface-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  transition: all var(--transition-normal);
}

.history-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.history-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-3);
}

.history-title {
  font-size: var(--font-size-base);
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 0;
}

.history-status {
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: 500;
  text-transform: uppercase;
}

.history-status.completed {
  background-color: var(--color-success);
  color: white;
}

.history-status.failed {
  background-color: var(--color-error);
  color: white;
}

.history-meta {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-3);
}

.history-preview {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  line-height: 1.5;
  margin-bottom: var(--space-3);
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.history-actions {
  display: flex;
  gap: var(--space-2);
}

.history-loading {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-8);
  color: var(--color-text-secondary);
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background-color: var(--color-surface-secondary);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-xl);
  max-width: 90vw;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.progress-modal {
  width: 500px;
}

.result-modal {
  width: 800px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-6);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.modal-body {
  flex: 1;
  padding: var(--space-6);
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap:
var(--space-3);
  padding: var(--space-6);
  border-top: 1px solid var(--color-border);
}

/* Progress Components */
.progress-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.progress-bar-container {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.progress-bar {
  flex: 1;
  height: 12px;
  background-color: var(--color-border);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
  transition: width var(--transition-normal);
  border-radius: var(--radius-full);
}

.progress-text {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
  min-width: 40px;
  text-align: right;
}

.progress-status {
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  text-align: center;
  padding: var(--space-2);
  background-color: var(--color-surface);
  border-radius: var(--radius-lg);
}

.progress-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4);
  background-color: var(--color-surface);
  border-radius: var(--radius-lg);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-sm);
}

.detail-label {
  color: var(--color-text-secondary);
}

.detail-value {
  color: var(--color-text-primary);
  font-weight: 500;
}

/* Result Content */
.result-content {
  background-color: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  line-height: 1.7;
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  white-space: pre-wrap;
  max-height: 400px;
  overflow-y: auto;
}

/* Responsive Design */
@media (max-width: 768px) {
  .summarization-container {
    padding: var(--space-4);
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .progress-modal,
  .result-modal {
    width: 95vw;
    margin: var(--space-4);
  }
  
  .history-container {
    grid-template-columns: 1fr;
  }
  
  .task-item {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-3);
  }
  
  .task-progress {
    justify-content: space-between;
  }
  
  .modal-footer {
    flex-direction: column;
    gap: var(--space-2);
  }
  
  .modal-footer .btn {
    width: 100%;
  }
}

3. Summarization JavaScript (web/static/js/summarization.js):
class SummarizationInterface {
  constructor() {
    this.activeTasks = new Map();
    this.websockets = new Map();
    this.summaryHistory = [];
    
    this.init();
  }
  
  async init() {
    try {
      this.setupEventListeners();
      this.setDefaultDates();
      await this.loadSummaryHistory();
    } catch (error) {
      console.error('Failed to initialize summarization interface:', error);
      Utils.showToast('Failed to initialize interface', 'error');
    }
  }
  
  setupEventListeners() {
    // Form submission
    document.getElementById('summary-form').addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleSummaryRequest();
    });
    
    // Modal controls
    document.getElementById('close-progress-btn').addEventListener('click', () => {
      this.closeProgressModal();
    });
    
    document.getElementById('close-result-btn').addEventListener('click', () => {
      this.closeResultModal();
    });
    
    document.getElementById('cancel-task-btn').addEventListener('click', () => {
      this.cancelCurrentTask();
    });
    
    document.getElementById('view-result-btn').addEventListener('click', () => {
      this.viewTaskResult();
    });
    
    document.getElementById('copy-result-btn').addEventListener('click', () => {
      this.copyResultToClipboard();
    });
    
    document.getElementById('download-result-btn').addEventListener('click', () => {
      this.downloadResult();
    });
    
    document.getElementById('refresh-history-btn').addEventListener('click', () => {
      this.loadSummaryHistory();
    });
  }
  
  setDefaultDates() {
    const today = new Date();
    const weekAgo = new Date(today);
    weekAgo.setDate(today.getDate() - 7);
    
    document.getElementById('start-date').value = weekAgo.toISOString().split('T')[0];
    document.getElementById('end-date').value = today.toISOString().split('T')[0];
    document.getElementById('summary-type').value = 'weekly';
  }
  
  async handleSummaryRequest() {
    try {
      const formData = this.getFormData();
      
      // Validate form data
      if (!this.validateFormData(formData)) {
        return;
      }
      
      // Create summary task
      const task = await this.createSummaryTask(formData);
      
      if (task) {
        // Start the task
        await this.startSummaryTask(task.task_id);
        
        // Show progress modal
        this.showProgressModal(task);
        
        // Start WebSocket connection for progress updates
        this.connectToTaskProgress(task.task_id);
      }
      
    } catch (error) {
      console.error('Failed to handle summary request:', error);
      Utils.showToast('Failed to create summary task', 'error');
    }
  }
  
  getFormData() {
    return {
      start_date: document.getElementById('start-date').value,
      end_date: document.getElementById('end-date').value,
      summary_type: document.getElementById('summary-type').value
    };
  }
  
  validateFormData(data) {
    if (!data.start_date || !data.end_date || !data.summary_type) {
      Utils.showToast('Please fill in all required fields', 'warning');
      return false;
    }
    
    const startDate = new Date(data.start_date);
    const endDate = new Date(data.end_date);
    
    if (startDate > endDate) {
      Utils.showToast('Start date must be before end date', 'warning');
      return false;
    }
    
    if (startDate > new Date()) {
      Utils.showToast('Start date cannot be in the future', 'warning');
      return false;
    }
    
    return true;
  }
  
  async createSummaryTask(formData) {
    try {
      const response = await fetch('/api/summarization/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      
      if (!response.ok) {
        throw new Error('Failed to create summary task');
      }
      
      const task = await response.json();
      this.activeTasks.set(task.task_id, task);
      
      return task;
      
    } catch (error) {
      console.error('Failed to create summary task:', error);
      throw error;
    }
  }
  
  async startSummaryTask(taskId) {
    try {
      const response = await fetch(`/api/summarization/${taskId}/start`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error('Failed to start summary task');
      }
      
      Utils.showToast('Summary task started successfully', 'success');
      
    } catch (error) {
      console.error('Failed to start summary task:', error);
      throw error;
    }
  }
  
  showProgressModal(task) {
    const modal = document.getElementById('progress-modal');
    const title = document.getElementById('progress-title');
    const taskIdDisplay = document.getElementById('task-id-display');
    const startedTime = document.getElementById('started-time');
    
    title.textContent = `Generating ${task.summary_type} Summary`;
    taskIdDisplay.textContent = task.task_id.substring(0, 8) + '...';
    startedTime.textContent = new Date().toLocaleTimeString();
    
    // Reset progress
    this.updateProgress(0, 'Initializing...');
    
    modal.style.display = 'flex';
  }
  
  closeProgressModal() {
    const modal = document.getElementById('progress-modal');
    modal.style.display = 'none';
    
    // Close WebSocket connections
    this.websockets.forEach((ws, taskId) => {
      ws.close();
    });
    this.websockets.clear();
  }
  
  connectToTaskProgress(taskId) {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/summarization/${taskId}/progress`;
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log(`WebSocket connected for task ${taskId}`);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleProgressUpdate(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      ws.onclose = () => {
        console.log(`WebSocket closed for task ${taskId}`);
        this.websockets.delete(taskId);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        Utils.showToast('Connection error during summarization', 'warning');
      };
      
      this.websockets.set(taskId, ws);
      
    } catch (error) {
      console.error('Failed to connect to task progress:', error);
    }
  }
  
  handleProgressUpdate(data) {
    // Update progress bar and status
    this.updateProgress(data.progress, data.current_step);
    
    // Handle task completion
    if (data.status === 'completed') {
      this.handleTaskCompletion(data);
    } else if (data.status === 'failed') {
      this.handleTaskFailure(data);
    }
  }
  
  updateProgress(progress, status) {
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressStatus = document.getElementById('progress-status');
    
    progressFill.style.width = `${progress}%`;
    progressText.textContent = `${Math.round(progress)}%`;
    progressStatus.textContent = status;
  }
  
  handleTaskCompletion(data) {
    // Update UI
    this.updateProgress(100, 'Completed successfully!');
    
    // Show view result button
    document.getElementById('view-result-btn').style.display = 'inline-flex';
    document.getElementById('cancel-task-btn').style.display = 'none';
    
    // Store result data
    this.currentResult = data;
    
    Utils.showToast('Summary generated successfully!', 'success');
    
    // Refresh history
    setTimeout(() => {
      this.loadSummaryHistory();
    }, 1000);
  }
  
  handleTaskFailure(data) {
    this.updateProgress(0, 'Task failed');
    
    Utils.showToast(`Summary generation failed: ${data.error_message || 'Unknown error'}`, 'error');
    
    // Hide progress modal after a delay
    setTimeout(() => {
      this.closeProgressModal();
    }, 3000);
  }
  
  async cancelCurrentTask() {
    try {
      const taskIds = Array.from(this.activeTasks.keys());
      if (taskIds.length === 0) return;
      
      const taskId = taskIds[0]; // Cancel the first active task
      
      const response = await fetch(`/api/summarization/${taskId}/cancel`, {
        method: 'POST'
      });
      
      if (response.ok) {
        Utils.showToast('Task cancelled successfully', 'info');
        this.closeProgressModal();
      } else {
        throw new Error('Failed to cancel task');
      }
      
    } catch (error) {
      console.error('Failed to cancel task:', error);
      Utils.showToast('Failed to cancel task', 'error');
    }
  }
  
  async viewTaskResult() {
    if (!this.currentResult) return;
    
    try {
      // Get full result from API
      const response = await fetch(`/api/summarization/${this.currentResult.task_id}/result`);
      
      if (!response.ok) {
        throw new Error('Failed to get task result');
      }
      
      const result = await response.json();
      
      // Show result modal
      this.showResultModal(result);
      
      // Close progress modal
      this.closeProgressModal();
      
    } catch (error) {
      console.error('Failed to view task result:', error);
      Utils.showToast('Failed to load result', 'error');
    }
  }
  
  showResultModal(result) {
    const modal = document.getElementById('result-modal');
    const title = document.getElementById('result-title');
    const content = document.getElementById('result-content');
    
    title.textContent = 'Summary Result';
    content.textContent = result.result;
    
    // Store result for download/copy
    this.currentResultData = result;
    
    modal.style.display = 'flex';
  }
  
  closeResultModal() {
    const modal = document.getElementById('result-modal');
    modal.style.display = 'none';
  }
  
  async copyResultToClipboard() {
    if (!this.currentResultData) return;
    
    try {
      await navigator.clipboard.writeText(this.currentResultData.result);
      Utils.showToast('Result copied to clipboard', 'success');
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      Utils.showToast('Failed to copy to clipboard', 'error');
    }
  }
  
  async downloadResult() {
    if (!this.currentResultData) return;
    
    try {
      const response = await fetch(`/api/summarization/${this.currentResultData.task_id}/download`);
      
      if (!response.ok) {
        throw new Error('Failed to download result');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `summary_${this.currentResultData.task_id.substring(0, 8)}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      Utils.showToast('Summary downloaded successfully', 'success');
      
    } catch (error) {
      console.error('Failed to download result:', error);
      Utils.showToast('Failed to download result', 'error');
    }
  }
  
  async loadSummaryHistory() {
    try {
      // This would need to be implemented as an API endpoint
      // For now, show placeholder
      const container = document.getElementById('history-container');
      container.innerHTML = `
        <div class="history-loading">
          <span>Summary history feature coming soon!</span>
        </div>
      `;
      
    } catch (error) {
      console.error('Failed to load summary history:', error);
      const container = document.getElementById('history-container');
      container.innerHTML = `
        <div class="history-loading">
          <span>Failed to load summary history</span>
        </div>
      `;
    }
  }
}

// Initialize summarization interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.summarizationInterface = new SummarizationInterface();
});

Testing Requirements:
1. Test summarization request creation and validation
2. Verify WebSocket progress tracking works correctly
3. Test task cancellation and error handling
4. Validate result display and download functionality
5. Test responsive design on different screen sizes
6. Verify integration with WebSummarizationService

Success Criteria:
- Summarization requests are created and processed correctly
- Real-time progress tracking provides accurate updates
- Results are displayed clearly with download options
- Error handling provides meaningful feedback
- Responsive design works on all devices
- Integration with backend services is seamless

Write production-ready code with comprehensive error handling, excellent user experience, and robust WebSocket integration for real-time progress tracking.
```

---

### **Step 17: Comprehensive Testing**

```
Create a comprehensive testing strategy that ensures web-CLI compatibility, API reliability, UI functionality, and production readiness. Focus on integration testing, performance validation, and user acceptance testing.

Requirements:
1. Create integration tests for web-CLI compatibility
2. Add comprehensive API endpoint testing
3. Implement UI testing with automated browser testing
4. Test concurrent access scenarios and data consistency
5. Add performance testing and load validation
6. Create user acceptance testing procedures

Testing Implementation:

1. Integration Test Suite (tests/test_web_integration.py):
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
import sys

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

from web.app import app
from web.database import DatabaseManager, init_database
from config_manager import ConfigManager
from file_discovery import FileDiscovery
from work_journal_summarizer import WorkJournalSummarizer

class TestWebCLIIntegration:
    """Test integration between web interface and CLI functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_config(self, temp_workspace):
        """Create test configuration."""
        config_path = temp_workspace / "config.yaml"
        config_content = f"""
processing:
  base_path: "{temp_workspace / 'worklogs'}"
  output_path: "{temp_workspace / 'output'}"
  max_file_size_mb: 10

llm:
  provider: "mock"

logging:
  level: "INFO"
  file_enabled: false
"""
        config_path.write_text(config_content)
        return config_path
    
    @pytest.fixture
    def test_client(self, test_config):
        """Create test client with temporary configuration."""
        # Override config path
        import os
        os.environ['CONFIG_PATH'] = str(test_config)
        
        with TestClient(app) as client:
            yield client
    
    @pytest.fixture
    async def sample_entries(self, temp_workspace):
        """Create sample journal entries."""
        base_path = temp_workspace / "worklogs"
        
        # Create entries for the past week
        entries = []
        for i in range(7):
            entry_date = date.today() - timedelta(days=i)
            
            # Use FileDiscovery to create proper structure
            file_discovery = FileDiscovery(str(base_path))
            file_path = file_discovery._construct_file_path(entry_date)
            
            # Create directory structure
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write sample content
            content = f"""
{entry_date.strftime('%A, %B %d, %Y')}

Sample journal entry for {entry_date}.
This is test content with multiple lines.
Word count should be calculated correctly.

Tasks completed:
- Task 1
- Task 2
- Task 3

Notes:
This is a sample entry for testing purposes.
"""
            file_path.write_text(content.strip())
            entries.append({
                'date': entry_date,
                'path': file_path,
                'content': content.strip()
            })
        
        return entries
    
    def test_health_check(self, test_client):
        """Test basic health check endpoint."""
        response = test_client.get("/api/health/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    def test_web_cli_file_compatibility(self, sample_entries, temp_workspace):
        """Test that web interface can read CLI-created files."""
        # Files created by sample_entries fixture should be readable
        base_path = temp_workspace / "worklogs"
        file_discovery = FileDiscovery(str(base_path))
        
        # Test file discovery
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        result = file_discovery.discover_files(start_date, end_date)
        assert len(result.found_files) == 7
        
        # Test file reading
        for entry in sample_entries:
            content = entry['path'].read_text()
            assert len(content) > 0
            assert entry['date'].strftime('%A, %B %d, %Y') in content
    
    def test_cli_web_file_compatibility(self, test_client, temp_workspace):
        """Test that CLI can read web-created files."""
        # Create entry via web API
        today = date.today().isoformat()
        entry_data = {
            "date": today,
            "content": "Test entry created via web interface"
        }
        
        response = test_client.post(f"/api/entries/{today}", json=entry_data)
        assert response.status_code == 200
        
        # Verify CLI can read the file
        base_path = temp_workspace / "worklogs"
        file_discovery = FileDiscovery(str(base_path))
        file_path = file_discovery._construct_file_path(date.today())
        
        assert file_path.exists()
        content = file_path.read_text()
        assert "Test entry created via web interface" in content
    
    def test_concurrent_access(self, test_client, sample_entries):
        """Test concurrent access between web and CLI operations."""
        today = date.today().isoformat()
        
        # Simulate concurrent reads
        responses = []
        for _ in range(5):
            response = test_client.get(f"/api/entries/{today}?include_content=true")
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code in [200, 404]  # 404 if entry doesn't exist
    
    def test_database_sync_accuracy(self, test_client, sample_entries):
        """Test that database sync accurately reflects file system."""
        # Trigger database sync
        response = test_client.get("/api/entries/recent?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        entries = data.get("entries", [])
        
        # Should have entries from sample data
        assert len(entries) > 0
        
        # Verify entry data accuracy
        for entry in entries:
            assert "date" in entry
            assert "metadata" in entry
            assert entry["metadata"]["word_count"] > 0
    
    def test_summarization_integration(self, test_client, sample_entries):
        """Test summarization integration with existing CLI components."""
        # Create summarization request
        summary_request = {
            "summary_type": "weekly",
            "start_date": (date.today() - timedelta(days=6)).isoformat(),
            "end_date": date.today().isoformat()
        }
        
        response = test_client.post("/api/summarization/create", json=summary_request)
        assert response.status_code == 200
        
        task_data = response.json()
        assert "task_id" in task_data
        assert task_data["summary_type"] == "weekly"

2. API Testing Suite (tests/test_api_endpoints.py):
import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
import json

class TestAPIEndpoints:
    """Comprehensive API endpoint testing."""
    
    @pytest.fixture
    def client(self):
        from web.app import app
        with TestClient(app) as client:
            yield client
    
    def test_entry_crud_operations(self, client):
        """Test complete CRUD operations for entries."""
        today = date.today().isoformat()
        
        # Create entry
        entry_data = {
            "date": today,
            "content": "Test entry content for CRUD testing"
        }
        
        response = client.post(f"/api/entries/{today}", json=entry_data)
        assert response.status_code == 200
        
        created_entry = response.json()
        assert created_entry["date"] == today
        assert "Test entry content" in created_entry.get("content", "")
        
        # Read entry
        response = client.get(f"/api/entries/{today}?include_content=true")
        assert response.status_code == 200
        
        retrieved_entry = response.json()
        assert retrieved_entry["date"] == today
        
        # Update entry
        updated_data = {
            "content": "Updated test entry content"
        }
        
        response = client.put(f"/api/entries/{today}", json=updated_data)
        assert response.status_code == 200
        
        updated_entry = response.json()
        assert "Updated test entry content" in updated_entry.get("content", "")
        
        # Delete entry (if implemented)
        # response = client.delete(f"/api/entries/{today}")
        # assert response.status_code == 200
    
    def test_entry_validation(self, client):
        """Test entry data validation."""
        # Test invalid date format
        response = client.post("/api/entries/invalid-date", json={
            "date": "invalid-date",
            "content": "Test content"
        })
        assert response.status_code == 422
        
        # Test future date
        future_date = (date.today() + timedelta(days=1)).isoformat()
        response = client.post(f"/api/entries/{future_date}", json={
            "date": future_date,
            "content": "Test content"
        })
        assert response.status_code == 400
    
    def test_calendar_endpoints(self, client):
        """Test calendar-related endpoints."""
        # Test today info
        response = client.get("/api/calendar/today")
        assert response.status_code == 200
        
        today_data = response.json()
        assert "today" in today_data
        assert "formatted_date" in today_data
        assert "has_entry" in today_data
        
        # Test calendar month data
        today = date.today()
        response = client.get(f"/api/calendar/{today.year}/{today.month}")
        assert response.status_code == 200
        
        calendar_data = response.json()
        assert calendar_data["year"] == today.year
        assert calendar_data["month"] == today.month
        assert "entries" in calendar_data
    
    def test_pagination(self, client):
        """Test API pagination functionality."""
        response = client.get("/api/entries/?limit=5&offset=0")
        assert response.status_code == 200
        
        data = response.json()
        assert "entries" in data
        assert "total_count" in data
        assert "has_more" in data
        assert "pagination" in data
        
        # Test pagination parameters
        assert len(data["entries"]) <= 5
    
    def test_error_handling(self, client):
        """Test API error handling."""
        # Test non-existent entry
        response = client.get("/api/entries/1900-01-01")
        assert response.status_code == 404
        
        # Test invalid parameters
        response = client.get("/api/entries/?limit=invalid")
        assert response.status_code == 422
    
    def test_rate_limiting(self, client):
        """Test API rate limiting (if implemented)."""
        # Make multiple rapid requests
        responses = []
        for _ in range(100):
            response = client.get("/api/health/")
            responses.append(response.status_code)
        
        # Should not have too many failures
        success_rate = sum(1 for code in responses if code == 200) / len(responses)
        assert success_rate > 0.9  # At least 90% success rate

3. UI Testing Suite (tests/test_ui_functionality.py):
import pytest
from playwright.async_api import async_playwright
import asyncio

class TestUIFunctionality:
    """UI testing with Playwright."""
    
    @pytest.fixture
    async def browser_context(self):
        """Create browser context for testing."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            yield context
            await browser.close()
    
    @pytest.fixture
    async def page(self, browser_context):
        """Create page for testing."""
        page = await browser_context.new_page()
        yield page
        await page.close()
    
    async def test_dashboard_loading(self, page):
        """Test dashboard page loading."""
        await page.goto("http://localhost:8000/")
        
        # Wait for page to load
        await page.wait_for_selector(".dashboard-container")
        
        # Check for key elements
        assert await page.is_visible(".today-section")
        assert await page.is_visible(".stats-section")
        assert await page.is_visible(".recent-section")
        
        # Check for today's date
        today_title = await page.text_content(".today-title")
        assert "Today" in today_title
    
    async def test_calendar_navigation(self, page):
        """Test calendar navigation functionality."""
        await page.goto("http://localhost:8000/calendar")
        
        # Wait for calendar to load
        await page.wait_for_selector(".calendar-grid")
        
        # Test month navigation
        await page.click("#prev-month-btn")
        await page.wait_for_timeout(500)  # Wait for transition
        
        await page.click("#next-month-btn")
        await page.wait_for_timeout(500)
        
        # Test today button
        await page.click("#today-btn")
        await page.wait_for_timeout(500)
        
        # Should highlight today
        today_cell = await page.query_selector(".calendar-day.today")
        assert
today_cell is not None
    
    async def test_entry_editor(self, page):
        """Test entry editor functionality."""
        await page.goto("http://localhost:8000/entry/2025-01-01")
        
        # Wait for editor to load
        await page.wait_for_selector(".editor-textarea")
        
        # Test typing
        await page.fill(".editor-textarea", "Test entry content")
        
        # Check word count updates
        word_count = await page.text_content("#word-count")
        assert int(word_count) > 0
        
        # Test save functionality
        await page.click("#save-btn")
        
        # Should show success message
        await page.wait_for_selector(".toast.success", timeout=5000)
    
    async def test_responsive_design(self, page):
        """Test responsive design on different screen sizes."""
        # Test desktop
        await page.set_viewport_size({"width": 1200, "height": 800})
        await page.goto("http://localhost:8000/")
        
        # Test tablet
        await page.set_viewport_size({"width": 768, "height": 1024})
        await page.reload()
        
        # Test mobile
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.reload()
        
        # Should still be functional
        assert await page.is_visible(".nav-main")
        assert await page.is_visible(".main-content")
    
    async def test_theme_switching(self, page):
        """Test theme switching functionality."""
        await page.goto("http://localhost:8000/")
        
        # Test theme toggle
        await page.click("#theme-toggle")
        
        # Check if theme changed
        body_class = await page.get_attribute("body", "class")
        assert "theme-dark" in body_class or "theme-light" in body_class

4. Performance Testing (tests/test_performance.py):
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

class TestPerformance:
    """Performance and load testing."""
    
    @pytest.fixture
    def client(self):
        from web.app import app
        with TestClient(app) as client:
            yield client
    
    def test_response_times(self, client):
        """Test API response times."""
        endpoints = [
            "/api/health/",
            "/api/calendar/today",
            "/api/entries/recent?limit=10"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Response should be under 1 second
            assert response_time < 1.0
            assert response.status_code == 200
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        def make_request():
            response = client.get("/api/health/")
            return response.status_code
        
        # Make 50 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        success_count = sum(1 for status in results if status == 200)
        assert success_count >= 45  # At least 90% success rate
    
    def test_memory_usage(self, client):
        """Test memory usage under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make many requests
        for _ in range(100):
            client.get("/api/health/")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50

5. User Acceptance Testing Procedures (tests/user_acceptance_tests.md):
# User Acceptance Testing Procedures

## Test Environment Setup

1. **Prerequisites**
   - Clean installation of the application
   - Sample journal data for testing
   - Multiple browsers (Chrome, Firefox, Safari)
   - Different devices (desktop, tablet, mobile)

2. **Test Data Preparation**
   - Create journal entries for the past 30 days
   - Include entries with varying content lengths
   - Create entries with special characters and formatting

## Core Functionality Tests

### Dashboard Tests
- [ ] Dashboard loads within 3 seconds
- [ ] Today's entry status displays correctly
- [ ] Recent entries show with proper previews
- [ ] Quick action buttons work correctly
- [ ] Statistics display accurate information

### Entry Management Tests
- [ ] Can create new entry with auto-generated header
- [ ] Can edit existing entries without data loss
- [ ] Auto-save works every 30 seconds
- [ ] Manual save provides immediate feedback
- [ ] Word count updates in real-time
- [ ] Can navigate between entries seamlessly

### Calendar Tests
- [ ] Calendar displays current month correctly
- [ ] Can navigate between months smoothly
- [ ] Entry indicators show on correct dates
- [ ] Can click dates to view/edit entries
- [ ] Today's date is clearly highlighted
- [ ] Responsive design works on all screen sizes

### Summarization Tests
- [ ] Can create summarization requests
- [ ] Progress tracking works accurately
- [ ] Can cancel running tasks
- [ ] Results display clearly
- [ ] Can download summary files
- [ ] Error handling works properly

## Usability Tests

### Navigation Tests
- [ ] Maximum 2 clicks to reach any feature
- [ ] Back button works consistently
- [ ] Breadcrumbs show current location
- [ ] Keyboard shortcuts work as expected

### Accessibility Tests
- [ ] Screen reader compatibility
- [ ] Keyboard-only navigation
- [ ] High contrast mode support
- [ ] Text scaling works properly
- [ ] Focus indicators are visible

### Performance Tests
- [ ] Pages load within acceptable time limits
- [ ] No noticeable lag during typing
- [ ] Smooth animations and transitions
- [ ] Works well on slower devices

## Cross-Platform Tests

### Browser Compatibility
- [ ] Chrome (latest version)
- [ ] Firefox (latest version)
- [ ] Safari (latest version)
- [ ] Edge (latest version)

### Device Compatibility
- [ ] Desktop (1920x1080 and higher)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667 and similar)

### Operating System Tests
- [ ] Windows 10/11
- [ ] macOS (latest version)
- [ ] Linux (Ubuntu/similar)

## Integration Tests

### CLI Compatibility
- [ ] Files created via web are readable by CLI
- [ ] Files created via CLI are readable by web
- [ ] No data corruption during concurrent access
- [ ] Configuration changes apply to both interfaces

### Data Integrity Tests
- [ ] No data loss during auto-save
- [ ] Concurrent editing handled properly
- [ ] Database sync maintains accuracy
- [ ] Backup and restore functions work

## Error Handling Tests

### Network Issues
- [ ] Graceful handling of connection loss
- [ ] Proper error messages for failed requests
- [ ] Retry mechanisms work correctly
- [ ] Offline functionality (if applicable)

### Input Validation
- [ ] Invalid dates rejected properly
- [ ] Large content handled correctly
- [ ] Special characters don't break functionality
- [ ] XSS protection works

### Recovery Tests
- [ ] Application recovers from crashes
- [ ] Unsaved changes are preserved
- [ ] Database corruption is handled
- [ ] Configuration errors are reported

## Acceptance Criteria

### Performance Criteria
- [ ] Dashboard loads in < 3 seconds
- [ ] Entry editor responds in < 500ms
- [ ] Calendar navigation in < 1 second
- [ ] Memory usage < 100MB baseline

### Usability Criteria
- [ ] New users can create entry in < 2 minutes
- [ ] All features accessible within 2 clicks
- [ ] Error messages are clear and actionable
- [ ] No training required for basic usage

### Reliability Criteria
- [ ] < 1% error rate in normal usage
- [ ] No data loss under normal conditions
- [ ] Graceful degradation when services unavailable
- [ ] Consistent behavior across all platforms

Testing Requirements:
1. Test web-CLI compatibility thoroughly
2. Verify all API endpoints work correctly
3. Test UI functionality across browsers and devices
4. Validate performance under various load conditions
5. Ensure accessibility standards are met
6. Test error handling and recovery scenarios

Success Criteria:
- All integration tests pass consistently
- API endpoints respond within acceptable time limits
- UI works correctly across all target browsers and devices
- Performance meets specified benchmarks
- User acceptance tests achieve 95% pass rate
- No critical bugs or data integrity issues

Write comprehensive tests with proper setup, teardown, and clear assertions that validate both functional and non-functional requirements.
```

---

### **Step 18: Production Deployment**

```
Create a comprehensive production deployment strategy that includes unified entry points, security measures, performance optimization, and operational procedures. Ensure the application is ready for real-world usage.

Requirements:
1. Create unified entry point for CLI and web modes
2. Add production configuration and environment management
3. Implement security measures and hardening
4. Add monitoring, logging, and health checks
5. Create deployment documentation and procedures
6. Include backup, recovery, and maintenance procedures

Production Deployment Implementation:

1. Unified Entry Point (main.py):
#!/usr/bin/env python3
"""
Daily Work Journal - Unified Entry Point

This script provides a unified entry point for both CLI and web modes
of the Daily Work Journal application.
"""

import sys
import argparse
import asyncio
import signal
import os
from pathlib import Path
from typing import Optional

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config_manager import ConfigManager
from logger import create_logger_with_config
from work_journal_summarizer import WorkJournalSummarizer

class ApplicationManager:
    """Manages the application lifecycle for both CLI and web modes."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.logger = create_logger_with_config(self.config.logging)
        self.web_server_process = None
        self.shutdown_requested = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
        
        if self.web_server_process:
            self.web_server_process.terminate()
    
    def run_cli_mode(self, args):
        """Run the application in CLI mode."""
        try:
            self.logger.info("Starting Daily Work Journal in CLI mode")
            
            # Create and run CLI summarizer
            summarizer = WorkJournalSummarizer(self.config, self.logger)
            
            if args.start_date and args.end_date:
                # Run summarization
                result = summarizer.run_summarization(
                    start_date=args.start_date,
                    end_date=args.end_date,
                    summary_type=args.summary_type or 'weekly'
                )
                
                if result:
                    self.logger.info("Summarization completed successfully")
                    print(f"Summary saved to: {result}")
                else:
                    self.logger.error("Summarization failed")
                    sys.exit(1)
            else:
                # Interactive mode
                self._run_interactive_cli()
                
        except KeyboardInterrupt:
            self.logger.info("CLI mode interrupted by user")
        except Exception as e:
            self.logger.error(f"CLI mode failed: {str(e)}")
            sys.exit(1)
    
    def run_web_mode(self, args):
        """Run the application in web mode."""
        try:
            self.logger.info("Starting Daily Work Journal in web mode")
            
            # Import web components
            import uvicorn
            from web.app import app
            
            # Configure web server
            host = args.host or "127.0.0.1"
            port = args.port or 8000
            
            # Production vs development configuration
            if args.production:
                # Production configuration
                uvicorn_config = {
                    "app": app,
                    "host": host,
                    "port": port,
                    "log_level": "info",
                    "access_log": True,
                    "workers": args.workers or 1,
                    "loop": "uvloop",
                    "http": "httptools"
                }
            else:
                # Development configuration
                uvicorn_config = {
                    "app": app,
                    "host": host,
                    "port": port,
                    "log_level": "debug",
                    "reload": args.reload,
                    "access_log": True
                }
            
            self.logger.info(f"Starting web server on {host}:{port}")
            
            # Start the server
            uvicorn.run(**uvicorn_config)
            
        except KeyboardInterrupt:
            self.logger.info("Web server interrupted by user")
        except Exception as e:
            self.logger.error(f"Web server failed: {str(e)}")
            sys.exit(1)
    
    def run_hybrid_mode(self, args):
        """Run both CLI and web modes simultaneously."""
        try:
            self.logger.info("Starting Daily Work Journal in hybrid mode")
            
            # Start web server in background
            import multiprocessing
            from web.app import app
            import uvicorn
            
            def start_web_server():
                uvicorn.run(
                    app,
                    host=args.host or "127.0.0.1",
                    port=args.port or 8000,
                    log_level="info"
                )
            
            # Start web server process
            self.web_server_process = multiprocessing.Process(target=start_web_server)
            self.web_server_process.start()
            
            self.logger.info(f"Web server started on {args.host or '127.0.0.1'}:{args.port or 8000}")
            self.logger.info("CLI mode available for direct operations")
            
            # Keep main process alive
            while not self.shutdown_requested:
                try:
                    asyncio.sleep(1)
                except KeyboardInterrupt:
                    break
            
            # Cleanup
            if self.web_server_process:
                self.web_server_process.terminate()
                self.web_server_process.join(timeout=10)
                
        except Exception as e:
            self.logger.error(f"Hybrid mode failed: {str(e)}")
            sys.exit(1)
    
    def _run_interactive_cli(self):
        """Run interactive CLI mode."""
        print("\n=== Daily Work Journal - Interactive Mode ===")
        print("Available commands:")
        print("1. Generate summary")
        print("2. View recent entries")
        print("3. Check configuration")
        print("4. Exit")
        
        while not self.shutdown_requested:
            try:
                choice = input("\nEnter your choice (1-4): ").strip()
                
                if choice == '1':
                    self._interactive_summarize()
                elif choice == '2':
                    self._interactive_view_entries()
                elif choice == '3':
                    self._interactive_show_config()
                elif choice == '4':
                    break
                else:
                    print("Invalid choice. Please enter 1-4.")
                    
            except (EOFError, KeyboardInterrupt):
                break
        
        print("\nGoodbye!")
    
    def _interactive_summarize(self):
        """Interactive summarization."""
        try:
            print("\n--- Generate Summary ---")
            start_date = input("Start date (YYYY-MM-DD): ").strip()
            end_date = input("End date (YYYY-MM-DD): ").strip()
            summary_type = input("Summary type (weekly/monthly) [weekly]: ").strip() or "weekly"
            
            # Validate dates
            from datetime import datetime
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # Run summarization
            summarizer = WorkJournalSummarizer(self.config, self.logger)
            result = summarizer.run_summarization(start_dt, end_dt, summary_type)
            
            if result:
                print(f"Summary generated successfully: {result}")
            else:
                print("Summary generation failed")
                
        except ValueError as e:
            print(f"Invalid date format: {e}")
        except Exception as e:
            print(f"Error generating summary: {e}")
    
    def _interactive_view_entries(self):
        """Interactive entry viewing."""
        try:
            from file_discovery import FileDiscovery
            from datetime import date, timedelta
            
            print("\n--- Recent Entries ---")
            
            # Show entries from last 7 days
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            
            file_discovery = FileDiscovery(self.config.processing.base_path)
            result = file_discovery.discover_files(start_date, end_date)
            
            if result.found_files:
                print(f"Found {len(result.found_files)} entries:")
                for file_path in sorted(result.found_files):
                    print(f"  - {file_path.name}")
            else:
                print("No recent entries found")
                
        except Exception as e:
            print(f"Error viewing entries: {e}")
    
    def _interactive_show_config(self):
        """Show current configuration."""
        print("\n--- Current Configuration ---")
        print(f"Base path: {self.config.processing.base_path}")
        print(f"Output path: {self.config.processing.output_path}")
        print(f"LLM provider: {self.config.llm.provider}")
        print(f"Log level: {self.config.logging.level}")

def create_argument_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Daily Work Journal - Unified CLI and Web Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s web                          # Start web interface
  %(prog)s web --port 8080             # Start web on custom port
  %(prog)s cli --start-date 2025-01-01 --end-date 2025-01-07  # CLI summarization
  %(prog)s cli                         # Interactive CLI mode
  %(prog)s hybrid                      # Both web and CLI modes
        """
    )
    
    # Mode selection
    parser.add_argument(
        'mode',
        choices=['web', 'cli', 'hybrid'],
        help='Application mode: web interface, CLI, or both'
    )
    
    # Web mode options
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Web server host (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Web server port (default: 8000)'
    )
    
    parser.add_argument(
        '--production',
        action='store_true',
        help='Run in production mode with optimizations'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        help='Number of worker processes for production'
    )
    
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable auto-reload for development'
    )
    
    # CLI mode options
    parser.add_argument(
        '--start-date',
        type=lambda s: datetime.strptime(s, '%Y-%m-%d').date(),
        help='Start date for summarization (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        type=lambda s: datetime.strptime(s, '%Y-%m-%d').date(),
        help='End date for summarization (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--summary-type',
        choices=['weekly', 'monthly', 'custom'],
        default='weekly',
        help='Type of summary to generate'
    )
    
    # General options
    parser.add_argument(
        '--config',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Daily Work Journal 1.0.0'
    )
    
    return parser

def main():
    """Main entry point."""
    # Parse command line arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Set config path if provided
    if args.config:
        os.environ['CONFIG_PATH'] = args.config
    
    # Create application manager
    app_manager = ApplicationManager()
    
    # Run in selected mode
    if args.mode == 'web':
        app_manager.run_web_mode(args)
    elif args.mode == 'cli':
        app_manager.run_cli_mode(args)
    elif args.mode == 'hybrid':
        app_manager.run_hybrid_mode(args)

if __name__ == '__main__':
    main()

2. Production Configuration (config/production.yaml):
# Production Configuration for Daily Work Journal

processing:
  base_path: "${JOURNAL_BASE_PATH:-/data/worklogs}"
  output_path: "${JOURNAL_OUTPUT_PATH:-/data/output}"
  max_file_size_mb: 50
  backup_enabled: true
  backup_path: "${JOURNAL_BACKUP_PATH:-/data/backups}"

llm:
  provider: "${LLM_PROVIDER:-bedrock}"
  timeout_seconds: 120
  max_retries: 3

bedrock:
  region: "${AWS_REGION:-us-east-1}"
  model_id: "${BEDROCK_MODEL_ID:-anthropic.claude-3-sonnet-20240229-v1:0}"
  max_tokens: 4000

openai:
  api_key: "${OPENAI_API_KEY}"
  model: "${OPENAI_MODEL:-gpt-4}"
  max_tokens: 4000

google_genai:
  api_key: "${GOOGLE_GENAI_API_KEY}"
  model: "${GOOGLE_GENAI_MODEL:-gemini-pro}"

logging:
  level: "${LOG_LEVEL:-INFO}"
  file_enabled: true
  file_path: "${LOG_FILE_PATH:-/var/log/work-journal/app.log}"
  max_file_size_mb: 100
  backup_count: 5
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

web:
  host: "${WEB_HOST:-0.0.0.0}"
  port: "${WEB_PORT:-8000}"
  workers: "${WEB_WORKERS:-4}"
  max_connections: 1000
  keepalive_timeout: 5
  
security:
  allowed_hosts: 
    - "${ALLOWED_HOST:-localhost}"
    - "127.0.0.1"
  cors_origins:
    - "${CORS_ORIGIN:-http://localhost:3000}"
  rate_limit_per_minute: 60
  max_request_size_mb: 10

database:
  path: "${DATABASE_PATH:-/data/journal_index.db}"
  backup_enabled: true
  backup_interval_hours: 24
  connection_pool_size: 10
  query_timeout_seconds: 30

monitoring:
  health_check_enabled: true
  metrics_enabled: true
  metrics_port: "${METRICS_PORT:-9090}"
  
maintenance:
  auto_cleanup_enabled: true
  cleanup_interval_days: 30
  max_log_age_days: 90
  max_backup_age_days: 365

3. Docker Configuration (Dockerfile):
# Multi-stage Docker build for Daily Work Journal
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r journal && useradd -r -g journal journal

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/journal/.local

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /data/worklogs /data/output /data/backups /var/log/work-journal \
    && chown -R journal:journal /data /var/log/work-journal /app

# Set environment variables
ENV PATH=/home/journal/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV CONFIG_PATH=/app/config/production.yaml

# Switch to non-root user
USER journal

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "main.py", "web", "--production", "--host", "0.0.0.0"]

4. Docker Compose (docker-compose.yml):
version: '3.8'

services:
  work-journal:
    build: .
    container_name: work-journal-app
    restart: unless-stopped
    ports:
      - "${WEB_PORT:-8000}:8000"
      - "${METRICS_PORT:-9090}:9090"
    environment:
      - JOURNAL_BASE_PATH=/data/worklogs
      - JOURNAL_OUTPUT_PATH=/data/output
      - JOURNAL_BACKUP_PATH=/data/backups
      - DATABASE_PATH=/data/journal_index.db
      - LOG_FILE_PATH=/var/log/work-journal/app.log
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - LLM_PROVIDER=${LLM_PROVIDER:-bedrock}
      - AWS_REGION=${AWS_REGION:-us-east-1}
      - BEDROCK_MODEL_ID=${BEDROCK_MODEL_ID}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_GENAI_API_KEY=${GOOGLE_GENAI_API_KEY}
    volumes:
      - journal_data:/data
      - journal_logs:/var/log/work-journal
      - ./config/production.yaml:/app/config/production.yaml:ro
    networks:
      - journal_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Reverse proxy with SSL
  nginx:
    image: nginx:alpine
    container_name: work-journal-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - work-journal
    networks:
      - journal_network

  # Optional: Log aggregation
  fluentd:
    image: fluentd:latest
    container_name: work-journal-logs
    restart: unless-stopped
    volumes:
      - journal_logs:/var/log/work-journal:ro
      - ./fluentd.conf:/fluentd/etc/fluent.conf:ro
    networks:
      - journal_network

volumes:
  journal_data:
    driver: local
  journal_logs:
    driver: local

networks:
  journal_network:
    driver: bridge

5. Deployment Scripts (scripts/deploy.sh):
#!/bin/bash
set -e

# Daily Work Journal Deployment Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
ENVIRONMENT="${1:-production}"
VERSION="${2:-latest}"

echo "=== Daily Work Journal Deployment ==="
echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"
echo "Project Directory: $PROJECT_DIR"

# Load environment-specific configuration
if [ -f "$PROJECT_DIR/config/$ENVIRONMENT.env" ]; then
    echo "Loading environment configuration..."
    source "$PROJECT_DIR/config/$ENVIRONMENT.env"
else
    echo "Warning: No environment configuration found for $ENVIRONMENT"
fi

# Pre-deployment checks
echo "Running pre-deployment checks..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    exit 1
fi

# Check required environment variables
REQUIRED_VARS=("LLM_PROVIDER")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set"
        exit 1
    fi
done

# Create necessary directories
echo "Creating directories..."
mkdir -p /data/worklogs /data/output /data/backups /var/log/work-journal

# Backup existing data (if exists)
if [ -d "/data/worklogs" ] && [ "$(ls -A /data/worklogs)" ]; then
    echo "Backing up existing data..."
    BACKUP_DIR="/data/backups/deployment-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    cp -r /data/worklogs "$BACKUP_DIR/"
    cp -r /data/output "$BACKUP_DIR/" 2>/dev/null || true
    echo "Backup created at: $BACKUP_DIR"
fi

# Build and deploy
echo "Building application..."
cd "$PROJECT_DIR"

# Build Docker image
docker-compose build

# Stop existing services
echo "Stopping existing services..."
docker-compose down

# Start new services
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Health check
echo "Performing health check..."
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:${WEB_PORT:-8000}/api/health/ > /dev/null 2>&1; then
        echo "Health check passed!"
        break
    else
        echo "Health check failed, retrying in 10 seconds..."
        sleep 10
        RETRY_COUNT=$((RETRY_COUNT + 1))
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Error: Health check failed after $MAX_RETRIES attempts"
    echo "Checking logs..."
    docker-compose logs work
-journal
    exit 1
fi

# Post-deployment tasks
echo "Running post-deployment tasks..."

# Database migration/sync (if needed)
docker-compose exec work-journal python -c "
import asyncio
from web.database import DatabaseManager
from web.services.sync_service import DatabaseSyncService
from config_manager import ConfigManager
from logger import create_logger_with_config

async def sync_database():
    config_manager = ConfigManager()
    config = config_manager.get_config()
    logger = create_logger_with_config(config.logging)
    db_manager = DatabaseManager()
    
    await db_manager.initialize()
    
    sync_service = DatabaseSyncService(config, logger, db_manager)
    result = await sync_service.full_sync()
    
    print(f'Database sync completed: {result.entries_processed} entries processed')

asyncio.run(sync_database())
"

echo "=== Deployment Completed Successfully ==="
echo "Application is running at: http://localhost:${WEB_PORT:-8000}"
echo "Health check: http://localhost:${WEB_PORT:-8000}/api/health/"
echo "API documentation: http://localhost:${WEB_PORT:-8000}/api/docs"

# Show running services
echo ""
echo "Running services:"
docker-compose ps

6. Monitoring and Maintenance (scripts/maintenance.sh):
#!/bin/bash
set -e

# Daily Work Journal Maintenance Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Daily Work Journal Maintenance ==="

# Function to show usage
show_usage() {
    echo "Usage: $0 [backup|cleanup|logs|status|update]"
    echo ""
    echo "Commands:"
    echo "  backup  - Create backup of data and database"
    echo "  cleanup - Clean up old logs and temporary files"
    echo "  logs    - Show application logs"
    echo "  status  - Show system status and health"
    echo "  update  - Update application to latest version"
    exit 1
}

# Backup function
backup_data() {
    echo "Creating backup..."
    
    BACKUP_DIR="/data/backups/manual-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup journal data
    if [ -d "/data/worklogs" ]; then
        echo "Backing up journal entries..."
        cp -r /data/worklogs "$BACKUP_DIR/"
    fi
    
    # Backup output files
    if [ -d "/data/output" ]; then
        echo "Backing up output files..."
        cp -r /data/output "$BACKUP_DIR/"
    fi
    
    # Backup database
    if [ -f "/data/journal_index.db" ]; then
        echo "Backing up database..."
        cp /data/journal_index.db "$BACKUP_DIR/"
    fi
    
    # Backup configuration
    if [ -f "$PROJECT_DIR/config/production.yaml" ]; then
        echo "Backing up configuration..."
        cp "$PROJECT_DIR/config/production.yaml" "$BACKUP_DIR/"
    fi
    
    # Create backup info file
    cat > "$BACKUP_DIR/backup_info.txt" << EOF
Backup created: $(date)
Backup type: Manual
Application version: $(docker-compose exec work-journal python -c "print('1.0.0')" 2>/dev/null || echo "Unknown")
System: $(uname -a)
EOF
    
    echo "Backup completed: $BACKUP_DIR"
    
    # Compress backup
    cd "$(dirname "$BACKUP_DIR")"
    tar -czf "$(basename "$BACKUP_DIR").tar.gz" "$(basename "$BACKUP_DIR")"
    rm -rf "$BACKUP_DIR"
    
    echo "Compressed backup: $(dirname "$BACKUP_DIR")/$(basename "$BACKUP_DIR").tar.gz"
}

# Cleanup function
cleanup_old_files() {
    echo "Cleaning up old files..."
    
    # Clean old log files (older than 90 days)
    find /var/log/work-journal -name "*.log*" -mtime +90 -delete 2>/dev/null || true
    
    # Clean old backups (older than 365 days)
    find /data/backups -name "*.tar.gz" -mtime +365 -delete 2>/dev/null || true
    
    # Clean Docker images and containers
    docker system prune -f
    
    echo "Cleanup completed"
}

# Show logs function
show_logs() {
    echo "=== Application Logs ==="
    docker-compose logs --tail=100 work-journal
}

# Show status function
show_status() {
    echo "=== System Status ==="
    
    # Docker services status
    echo "Docker Services:"
    docker-compose ps
    echo ""
    
    # Health check
    echo "Health Check:"
    if curl -f http://localhost:${WEB_PORT:-8000}/api/health/ 2>/dev/null; then
        echo "✓ Application is healthy"
    else
        echo "✗ Application health check failed"
    fi
    echo ""
    
    # Disk usage
    echo "Disk Usage:"
    df -h /data 2>/dev/null || df -h /
    echo ""
    
    # Memory usage
    echo "Memory Usage:"
    free -h
    echo ""
    
    # Database stats
    echo "Database Statistics:"
    docker-compose exec work-journal python -c "
import asyncio
from web.database import DatabaseManager
from web.api.entries import get_database_stats

async def show_stats():
    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        async with db_manager.get_session() as session:
            from sqlalchemy import select, func
            from web.database import JournalEntryIndex
            
            total_result = await session.execute(select(func.count(JournalEntryIndex.id)))
            total_count = total_result.scalar()
            
            content_result = await session.execute(
                select(func.count(JournalEntryIndex.id))
                .where(JournalEntryIndex.has_content == True)
            )
            content_count = content_result.scalar()
            
            print(f'Total entries: {total_count}')
            print(f'Entries with content: {content_count}')
            
    except Exception as e:
        print(f'Error getting database stats: {e}')

asyncio.run(show_stats())
" 2>/dev/null || echo "Could not retrieve database statistics"
}

# Update function
update_application() {
    echo "Updating application..."
    
    cd "$PROJECT_DIR"
    
    # Pull latest changes
    git pull origin main
    
    # Rebuild and restart
    docker-compose build
    docker-compose down
    docker-compose up -d
    
    # Wait for startup
    sleep 30
    
    # Health check
    if curl -f http://localhost:${WEB_PORT:-8000}/api/health/ 2>/dev/null; then
        echo "✓ Update completed successfully"
    else
        echo "✗ Update failed - application not responding"
        exit 1
    fi
}

# Main script logic
case "${1:-}" in
    backup)
        backup_data
        ;;
    cleanup)
        cleanup_old_files
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    update)
        update_application
        ;;
    *)
        show_usage
        ;;
esac

7. Production Deployment Documentation (docs/DEPLOYMENT.md):
# Daily Work Journal - Production Deployment Guide

## Overview

This guide covers the complete production deployment of the Daily Work Journal application, including both CLI and web interfaces.

## Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **Memory**: Minimum 2GB RAM, 4GB+ recommended
- **Storage**: Minimum 10GB free space, SSD recommended
- **Network**: Internet access for LLM API calls

### Software Dependencies
- Docker 20.10+
- Docker Compose 2.0+
- Git
- curl (for health checks)

### Environment Setup
1. **Create deployment user**:
   ```bash
   sudo useradd -m -s /bin/bash journal
   sudo usermod -aG docker journal
   ```

2. **Create data directories**:
   ```bash
   sudo mkdir -p /data/{worklogs,output,backups}
   sudo mkdir -p /var/log/work-journal
   sudo chown -R journal:journal /data /var/log/work-journal
   ```

## Configuration

### Environment Variables
Create `/home/journal/.env` with required variables:

```bash
# LLM Configuration
LLM_PROVIDER=bedrock
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Alternative LLM providers
# OPENAI_API_KEY=your_openai_key
# GOOGLE_GENAI_API_KEY=your_google_key

# Web Server
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_WORKERS=4

# Security
ALLOWED_HOST=your-domain.com
CORS_ORIGIN=https://your-domain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=/var/log/work-journal/app.log

# Database
DATABASE_PATH=/data/journal_index.db

# Paths
JOURNAL_BASE_PATH=/data/worklogs
JOURNAL_OUTPUT_PATH=/data/output
JOURNAL_BACKUP_PATH=/data/backups
```

### SSL Configuration (Optional)
For HTTPS deployment, create SSL certificates:

```bash
# Using Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /home/journal/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /home/journal/ssl/
sudo chown journal:journal /home/journal/ssl/*
```

## Deployment Steps

### 1. Clone Repository
```bash
su - journal
git clone https://github.com/your-org/work-journal-maker.git
cd work-journal-maker
```

### 2. Configure Environment
```bash
cp config/production.yaml.example config/production.yaml
# Edit configuration as needed
```

### 3. Deploy Application
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh production
```

### 4. Verify Deployment
```bash
# Check services
docker-compose ps

# Health check
curl http://localhost:8000/api/health/

# View logs
docker-compose logs -f work-journal
```

## Monitoring and Maintenance

### Health Monitoring
Set up automated health checks:

```bash
# Add to crontab
*/5 * * * * curl -f http://localhost:8000/api/health/ || echo "Health check failed" | mail -s "Work Journal Alert" admin@your-domain.com
```

### Log Rotation
Configure logrotate:

```bash
sudo tee /etc/logrotate.d/work-journal << EOF
/var/log/work-journal/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 journal journal
    postrotate
        docker-compose restart work-journal
    endscript
}
EOF
```

### Backup Schedule
Set up automated backups:

```bash
# Add to crontab
0 2 * * * /home/journal/work-journal-maker/scripts/maintenance.sh backup
0 3 * * 0 /home/journal/work-journal-maker/scripts/maintenance.sh cleanup
```

## Security Considerations

### Network Security
- Use firewall to restrict access
- Enable HTTPS in production
- Use reverse proxy (nginx) for additional security

### Application Security
- Keep dependencies updated
- Use non-root containers
- Implement rate limiting
- Regular security audits

### Data Security
- Encrypt data at rest
- Secure backup storage
- Implement access controls
- Regular backup testing

## Troubleshooting

### Common Issues

1. **Application won't start**
   - Check Docker logs: `docker-compose logs work-journal`
   - Verify environment variables
   - Check disk space and permissions

2. **Database connection errors**
   - Verify database file permissions
   - Check disk space
   - Review database logs

3. **LLM API errors**
   - Verify API credentials
   - Check network connectivity
   - Review rate limits

4. **Performance issues**
   - Monitor resource usage
   - Check database performance
   - Review log files for errors

### Log Analysis
```bash
# View recent errors
docker-compose logs work-journal | grep ERROR

# Monitor real-time logs
docker-compose logs -f work-journal

# Check system resources
docker stats work-journal-app
```

## Scaling Considerations

### Horizontal Scaling
- Use load balancer for multiple instances
- Implement session affinity
- Consider database replication

### Performance Optimization
- Enable caching
- Optimize database queries
- Use CDN for static assets
- Implement connection pooling

## Backup and Recovery

### Backup Strategy
- Daily automated backups
- Weekly full system backups
- Monthly offsite backups
- Test restore procedures regularly

### Recovery Procedures
1. **Data Recovery**:
   ```bash
   # Stop application
   docker-compose down
   
   # Restore from backup
   tar -xzf backup-20250101-120000.tar.gz
   cp -r backup-20250101-120000/* /data/
   
   # Restart application
   docker-compose up -d
   ```

2. **Database Recovery**:
   ```bash
   # Stop application
   docker-compose down
   
   # Restore database
   cp backup-20250101-120000/journal_index.db /data/
   
   # Restart and verify
   docker-compose up -d
   ./scripts/maintenance.sh status
   ```

Testing Requirements:
1. Test production deployment in staging environment
2. Verify all security measures are in place
3. Test backup and recovery procedures
4. Validate monitoring and alerting
5. Perform load testing
6. Test disaster recovery scenarios

Success Criteria:
- Application deploys successfully in production environment
- All security measures are implemented and tested
- Monitoring and alerting systems are functional
- Backup and recovery procedures are validated
- Performance meets production requirements
- Documentation is complete and accurate

Write production-ready deployment procedures with comprehensive security, monitoring, and maintenance capabilities for enterprise-grade operation.
```

---

## 🎯 Implementation Summary

This comprehensive blueprint provides detailed, step-by-step implementation prompts for transforming the existing CLI-based Work Journal Summarizer into a full-featured web application. The 18-step implementation plan ensures:

### ✅ **Complete Feature Set**
- **Modern Web Interface**: Clean, minimalistic, macOS-like design
- **Full CLI Compatibility**: Seamless integration with existing functionality
- **Real-time Features**: Auto-save, progress tracking, live updates
- **Comprehensive APIs**: RESTful endpoints with WebSocket support
- **Production Ready**: Security, monitoring, deployment procedures

### 🏗️ **Architecture Highlights**
- **Hybrid Storage**: File system primary + SQLite index for performance
- **Async Integration**: Non-blocking web operations with existing sync CLI
- **Service Layer**: Clean separation between web and business logic
- **Unified Entry Point**: Single application supporting both CLI and web modes

### 🚀 **Key Benefits**
- **Zero Breaking Changes**: Existing CLI functionality remains unchanged
- **Incremental Implementation**: Each step builds on previous work
- **Production Grade**: Comprehensive testing, security, and deployment
- **Maintainable**: Clean architecture with proper separation of concerns

### 📋 **Implementation Order**
1. **Foundation** (Steps 1-3): Core infrastructure and FastAPI setup
2. **Data Layer** (Steps 4-6): Entry management and API endpoints  
3. **Calendar** (Steps 7-8): Calendar service and navigation
4. **Summarization** (Steps 9-10): Web summarization with progress tracking
5. **User Interface** (Steps 11-16): Complete web interface implementation
6. **Quality Assurance** (Step 17): Comprehensive testing strategy
7. **Production** (Step 18): Deployment and operational procedures

Each prompt is designed to be self-contained with clear requirements, detailed implementation code, testing procedures, and success criteria. The implementation maintains full backward compatibility while adding powerful web capabilities that enhance the user experience without compromising the robust CLI functionality.

The result is a professional, production-ready application that serves both power users who prefer CLI interfaces and users who want the convenience and visual appeal of a modern web interface.