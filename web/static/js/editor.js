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

        // Fix: Parse date string as local date to avoid timezone conversion
        // Split the date string and create date with local timezone
        const [year, month, day] = this.entryDate.split('-').map(Number);
        const localDate = new Date(year, month - 1, day);

        const formattedDate = this.formatDate(localDate);
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