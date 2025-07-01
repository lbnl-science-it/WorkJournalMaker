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

    // Parse date string correctly to avoid timezone issues
    static parseDate(dateStr) {
        if (!dateStr) return new Date();

        // Handle ISO date strings (YYYY-MM-DD) by parsing components
        if (typeof dateStr === 'string' && dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
            const [year, month, day] = dateStr.split('-').map(Number);
            return new Date(year, month - 1, day); // month is 0-indexed
        }

        // For other formats, use standard Date constructor
        return new Date(dateStr);
    }

    // Toast notifications
    static showToast(message, type = 'info', duration = 5000) {
        const container = document.getElementById('toast-container');
        if (!container) {
            console.warn('Toast container not found');
            return;
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icon = this.getToastIcon(type);
        toast.innerHTML = `
      <div class="toast-icon">${icon}</div>
      <div class="toast-content">${message}</div>
      <button class="toast-close" onclick="this.parentElement.remove()" aria-label="Close notification">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
          <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
        </svg>
      </button>
    `;

        container.appendChild(toast);

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.style.animation = 'slideOut 0.3s ease';
                    setTimeout(() => toast.remove(), 300);
                }
            }, duration);
        }

        return toast;
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
        if (!element) return;

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

    // Throttle function
    static throttle(func, limit) {
        let inThrottle;
        return function (...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // Local storage helpers
    static storage = {
        get(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (error) {
                console.warn('Failed to get from localStorage:', error);
                return defaultValue;
            }
        },

        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (error) {
                console.warn('Failed to set localStorage:', error);
                return false;
            }
        },

        remove(key) {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (error) {
                console.warn('Failed to remove from localStorage:', error);
                return false;
            }
        }
    };

    // URL helpers
    static url = {
        getParam(name) {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(name);
        },

        setParam(name, value) {
            const url = new URL(window.location);
            url.searchParams.set(name, value);
            window.history.pushState({}, '', url);
        },

        removeParam(name) {
            const url = new URL(window.location);
            url.searchParams.delete(name);
            window.history.pushState({}, '', url);
        }
    };

    // DOM helpers
    static dom = {
        ready(callback) {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', callback);
            } else {
                callback();
            }
        },

        createElement(tag, attributes = {}, children = []) {
            const element = document.createElement(tag);

            Object.entries(attributes).forEach(([key, value]) => {
                if (key === 'className') {
                    element.className = value;
                } else if (key === 'innerHTML') {
                    element.innerHTML = value;
                } else if (key === 'textContent') {
                    element.textContent = value;
                } else {
                    element.setAttribute(key, value);
                }
            });

            children.forEach(child => {
                if (typeof child === 'string') {
                    element.appendChild(document.createTextNode(child));
                } else {
                    element.appendChild(child);
                }
            });

            return element;
        },

        findParent(element, selector) {
            while (element && element !== document) {
                if (element.matches && element.matches(selector)) {
                    return element;
                }
                element = element.parentElement;
            }
            return null;
        }
    };

    // Validation helpers
    static validate = {
        email(email) {
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return re.test(email);
        },

        required(value) {
            return value !== null && value !== undefined && value.toString().trim() !== '';
        },

        minLength(value, min) {
            return value && value.toString().length >= min;
        },

        maxLength(value, max) {
            return !value || value.toString().length <= max;
        },

        pattern(value, pattern) {
            if (!value) return true;
            const regex = new RegExp(pattern);
            return regex.test(value.toString());
        }
    };

    // Format helpers
    static format = {
        number(num, decimals = 0) {
            return new Intl.NumberFormat('en-US', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            }).format(num);
        },

        currency(amount, currency = 'USD') {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: currency
            }).format(amount);
        },

        fileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },

        timeAgo(date) {
            const now = new Date();
            const diffInSeconds = Math.floor((now - date) / 1000);

            if (diffInSeconds < 60) return 'just now';
            if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
            if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
            if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`;
            if (diffInSeconds < 31536000) return `${Math.floor(diffInSeconds / 2592000)} months ago`;
            return `${Math.floor(diffInSeconds / 31536000)} years ago`;
        }
    };

    // Animation helpers
    static animate = {
        fadeIn(element, duration = 300) {
            element.style.opacity = '0';
            element.style.display = 'block';

            const start = performance.now();

            function fade(timestamp) {
                const elapsed = timestamp - start;
                const progress = Math.min(elapsed / duration, 1);

                element.style.opacity = progress;

                if (progress < 1) {
                    requestAnimationFrame(fade);
                }
            }

            requestAnimationFrame(fade);
        },

        fadeOut(element, duration = 300) {
            const start = performance.now();
            const startOpacity = parseFloat(getComputedStyle(element).opacity);

            function fade(timestamp) {
                const elapsed = timestamp - start;
                const progress = Math.min(elapsed / duration, 1);

                element.style.opacity = startOpacity * (1 - progress);

                if (progress < 1) {
                    requestAnimationFrame(fade);
                } else {
                    element.style.display = 'none';
                }
            }

            requestAnimationFrame(fade);
        },

        slideDown(element, duration = 300) {
            element.style.height = '0';
            element.style.overflow = 'hidden';
            element.style.display = 'block';

            const targetHeight = element.scrollHeight;
            const start = performance.now();

            function slide(timestamp) {
                const elapsed = timestamp - start;
                const progress = Math.min(elapsed / duration, 1);

                element.style.height = (targetHeight * progress) + 'px';

                if (progress < 1) {
                    requestAnimationFrame(slide);
                } else {
                    element.style.height = '';
                    element.style.overflow = '';
                }
            }

            requestAnimationFrame(slide);
        },

        slideUp(element, duration = 300) {
            const startHeight = element.offsetHeight;
            const start = performance.now();

            element.style.overflow = 'hidden';

            function slide(timestamp) {
                const elapsed = timestamp - start;
                const progress = Math.min(elapsed / duration, 1);

                element.style.height = (startHeight * (1 - progress)) + 'px';

                if (progress < 1) {
                    requestAnimationFrame(slide);
                } else {
                    element.style.display = 'none';
                    element.style.height = '';
                    element.style.overflow = '';
                }
            }

            requestAnimationFrame(slide);
        }
    };

    // Keyboard helpers
    static keyboard = {
        isKey(event, key) {
            return event.key === key || event.code === key;
        },

        isModifierKey(event, modifier) {
            switch (modifier) {
                case 'ctrl': return event.ctrlKey;
                case 'alt': return event.altKey;
                case 'shift': return event.shiftKey;
                case 'meta': return event.metaKey;
                default: return false;
            }
        },

        isCombo(event, combo) {
            const parts = combo.toLowerCase().split('+');
            const key = parts.pop();

            if (!this.isKey(event, key)) return false;

            return parts.every(modifier => this.isModifierKey(event, modifier));
        }
    };

    // Copy to clipboard
    static async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Copied to clipboard', 'success', 2000);
            return true;
        } catch (error) {
            console.warn('Failed to copy to clipboard:', error);
            this.showToast('Failed to copy to clipboard', 'error');
            return false;
        }
    }

    // Generate unique ID
    static generateId(prefix = 'id') {
        return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    // Escape HTML
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Strip HTML
    static stripHtml(html) {
        const div = document.createElement('div');
        div.innerHTML = html;
        return div.textContent || div.innerText || '';
    }
}

// Theme management
class ThemeManager {
    constructor() {
        this.init();
    }

    init() {
        // Get saved theme or default to system preference
        const savedTheme = Utils.storage.get('theme');
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        const initialTheme = savedTheme || systemTheme;

        this.setTheme(initialTheme);

        // Set up theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!Utils.storage.get('theme')) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
    }

    setTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        document.body.className = `theme-${theme}`;
        Utils.storage.set('theme', theme);

        // Update theme toggle icons
        const lightIcon = document.querySelector('.theme-icon-light');
        const darkIcon = document.querySelector('.theme-icon-dark');

        if (lightIcon && darkIcon) {
            if (theme === 'dark') {
                lightIcon.style.display = 'none';
                darkIcon.style.display = 'block';
            } else {
                lightIcon.style.display = 'block';
                darkIcon.style.display = 'none';
            }
        }

        // Dispatch theme change event
        window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
    }

    toggleTheme() {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }

    getTheme() {
        return document.body.getAttribute('data-theme');
    }
}

// Initialize theme manager when DOM is loaded
Utils.dom.ready(() => {
    window.themeManager = new ThemeManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Utils, ThemeManager };
}