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
          <div class="entry-date">${Utils.formatDate(Utils.parseDate(entry.date), 'short')}</div>
          <div class="entry-preview">${this.getEntryPreview(entry)}</div>
        </div>
        <div class="entry-meta">
          <span>${entry.metadata?.word_count || 0} words</span>
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
            const entryDate = Utils.parseDate(entry.date);
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
                const entryDate = Utils.parseDate(entry.date);
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
            // Get today's date in local timezone to avoid timezone issues
            const today = new Date();
            const year = today.getFullYear();
            const month = String(today.getMonth() + 1).padStart(2, '0');
            const day = String(today.getDate()).padStart(2, '0');
            const todayStr = `${year}-${month}-${day}`;

            const response = await fetch(`/api/entries/${todayStr}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    date: todayStr,
                    content: `${Utils.formatDate(new Date(), 'long')}\n\n`
                })
            });

            if (!response.ok) throw new Error('Failed to create entry');

            Utils.showToast('New entry created successfully!', 'success');

            // Redirect to editor
            window.location.href = `/entry/${todayStr}`;

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