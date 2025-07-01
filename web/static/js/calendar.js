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
                <div class="recent-date">${Utils.formatDate(Utils.parseDate(entry.date), 'short')}</div>
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

        // Update title - fix timezone issue by parsing date components
        const [year, month, day] = dateStr.split('-').map(Number);
        const date = new Date(year, month - 1, day); // month is 0-indexed
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