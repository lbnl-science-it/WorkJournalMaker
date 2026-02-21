class SummarizationInterface {
    constructor() {
        this.activeTasks = new Map();
        this.websockets = new Map();
        this.summaryHistory = [];
        this.currentResult = null;
        this.currentResultData = null;

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

        // Close modals on overlay click
        document.getElementById('progress-modal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.closeProgressModal();
            }
        });

        document.getElementById('result-modal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.closeResultModal();
            }
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

            // Show loading state
            const generateBtn = document.getElementById('generate-btn');
            Utils.setLoading(generateBtn, true);

            // Create summary task
            const task = await this.createSummaryTask(formData);

            if (task) {
                // Show progress modal
                this.showProgressModal(task);

                // Start WebSocket connection for progress updates
                this.connectToTaskProgress(task.task_id);
            }

        } catch (error) {
            console.error('Failed to handle summary request:', error);
            Utils.showToast('Failed to create summary task', 'error');
        } finally {
            const generateBtn = document.getElementById('generate-btn');
            Utils.setLoading(generateBtn, false);
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

        // Check date range is reasonable (not more than 1 year)
        const daysDiff = (endDate - startDate) / (1000 * 60 * 60 * 24);
        if (daysDiff > 365) {
            Utils.showToast('Date range cannot exceed 1 year', 'warning');
            return false;
        }

        return true;
    }

    async createSummaryTask(formData) {
        try {
            const response = await fetch('/api/summarization/tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to create summary task');
            }

            const task = await response.json();
            this.activeTasks.set(task.task_id, task);

            return task;

        } catch (error) {
            console.error('Failed to create summary task:', error);
            throw error;
        }
    }

    showProgressModal(task) {
        const modal = document.getElementById('progress-modal');
        const title = document.getElementById('progress-title');
        const taskIdDisplay = document.getElementById('task-id-display');
        const startedTime = document.getElementById('started-time');
        const estimatedTime = document.getElementById('estimated-time');

        title.textContent = `Generating ${task.summary_type} Summary`;
        taskIdDisplay.textContent = task.task_id.substring(0, 8) + '...';
        startedTime.textContent = new Date().toLocaleTimeString();

        // Estimate time based on summary type
        const estimates = {
            'weekly': '2-3 minutes',
            'monthly': '5-10 minutes',
            'custom': '3-8 minutes'
        };
        estimatedTime.textContent = estimates[task.summary_type] || '3-5 minutes';

        // Reset progress and show buttons
        this.updateProgress(0, 'Initializing...');
        document.getElementById('view-result-btn').style.display = 'none';
        document.getElementById('cancel-task-btn').style.display = 'inline-flex';

        modal.style.display = 'flex';
    }

    closeProgressModal() {
        const modal = document.getElementById('progress-modal');
        modal.style.display = 'none';

        // Close WebSocket connections
        this.websockets.forEach((ws, taskId) => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        });
        this.websockets.clear();
    }

    connectToTaskProgress(taskId) {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/api/summarization/ws/${taskId}`;

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

            ws.onclose = (event) => {
                console.log(`WebSocket closed for task ${taskId}`, event.code, event.reason);
                this.websockets.delete(taskId);

                // If connection closed unexpectedly, try to get final status
                if (event.code !== 1000 && event.code !== 1001) {
                    setTimeout(() => this.checkTaskStatus(taskId), 2000);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                Utils.showToast('Connection error during summarization', 'warning');
            };

            this.websockets.set(taskId, ws);

        } catch (error) {
            console.error('Failed to connect to task progress:', error);
            // Fallback to polling
            this.startProgressPolling(taskId);
        }
    }

    startProgressPolling(taskId) {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/summarization/tasks/${taskId}`);
                if (response.ok) {
                    const data = await response.json();
                    this.handleProgressUpdate(data);

                    if (data.status === 'completed' || data.status === 'failed') {
                        clearInterval(pollInterval);
                    }
                }
            } catch (error) {
                console.error('Failed to poll task status:', error);
                clearInterval(pollInterval);
            }
        }, 2000);

        // Store interval for cleanup
        this.activeTasks.get(taskId).pollInterval = pollInterval;
    }

    async checkTaskStatus(taskId) {
        try {
            const response = await fetch(`/api/summarization/tasks/${taskId}`);
            if (response.ok) {
                const data = await response.json();
                this.handleProgressUpdate(data);
            }
        } catch (error) {
            console.error('Failed to check task status:', error);
        }
    }

    handleProgressUpdate(data) {
        // Update progress bar and status
        this.updateProgress(data.progress || 0, data.current_step || data.status);

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

        if (progressFill && progressText && progressStatus) {
            progressFill.style.width = `${Math.min(100, Math.max(0, progress))}%`;
            progressText.textContent = `${Math.round(progress)}%`;
            progressStatus.textContent = status;
        }
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

            const response = await fetch(`/api/summarization/tasks/${taskId}/cancel`, {
                method: 'POST'
            });

            if (response.ok) {
                Utils.showToast('Task cancelled successfully', 'info');
                this.closeProgressModal();
                this.activeTasks.delete(taskId);
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
            const response = await fetch(`/api/summarization/tasks/${this.currentResult.task_id}/result`);

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

        title.textContent = `${result.summary_type} Summary`;
        content.textContent = result.result || result.summary || 'No content available';

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
            const textToCopy = this.currentResultData.result || this.currentResultData.summary || '';
            await navigator.clipboard.writeText(textToCopy);
            Utils.showToast('Result copied to clipboard', 'success');
        } catch (error) {
            console.error('Failed to copy to clipboard:', error);
            Utils.showToast('Failed to copy to clipboard', 'error');
        }
    }

    async downloadResult() {
        if (!this.currentResultData) return;

        try {
            const response = await fetch(`/api/summarization/tasks/${this.currentResultData.task_id}/download`);

            if (!response.ok) {
                throw new Error('Failed to download result');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `summary_${this.currentResultData.task_id.substring(0, 8)}_${new Date().toISOString().split('T')[0]}.txt`;
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
            const container = document.getElementById('history-container');

            // Show loading state
            container.innerHTML = `
        <div class="history-loading">
          <div class="loading-spinner"></div>
          <span>Loading summary history...</span>
        </div>
      `;

            const response = await fetch('/api/summarization/tasks');

            if (!response.ok) {
                throw new Error('Failed to fetch summary history');
            }

            const data = await response.json();
            this.summaryHistory = Array.isArray(data) ? data : [];

            this.renderSummaryHistory();

        } catch (error) {
            console.error('Failed to load summary history:', error);
            const container = document.getElementById('history-container');
            container.innerHTML = `
        <div class="history-loading">
          <span>Summary history feature coming soon!</span>
        </div>
      `;
        }
    }

    renderSummaryHistory() {
        const container = document.getElementById('history-container');

        if (!this.summaryHistory.length) {
            container.innerHTML = `
        <div class="history-loading">
          <span>No summary history found. Generate your first summary to get started!</span>
        </div>
      `;
            return;
        }

        container.innerHTML = this.summaryHistory.map(summary => `
      <div class="history-item">
        <div class="history-header">
          <h3 class="history-title">${summary.summary_type} Summary</h3>
          <span class="history-status ${summary.status}">${summary.status}</span>
        </div>
        <div class="history-meta">
          ${summary.start_date} to ${summary.end_date} • ${new Date(summary.created_at).toLocaleDateString()}
        </div>
        <div class="history-preview">
          ${this.getHistoryPreview(summary)}
        </div>
        <div class="history-actions">
          <button class="btn btn-secondary btn-sm" onclick="summarizationInterface.viewHistoryItem('${summary.task_id}')">
            View
          </button>
          ${summary.status === 'completed' ? `
            <button class="btn btn-secondary btn-sm" onclick="summarizationInterface.downloadHistoryItem('${summary.task_id}')">
              Download
            </button>
          ` : ''}
        </div>
      </div>
    `).join('');
    }

    getHistoryPreview(summary) {
        if (summary.result) {
            return summary.result.substring(0, 150) + (summary.result.length > 150 ? '...' : '');
        }
        return 'No preview available';
    }

    async viewHistoryItem(taskId) {
        try {
            const response = await fetch(`/api/summarization/tasks/${taskId}/result`);
            if (response.ok) {
                const result = await response.json();
                this.showResultModal(result);
            } else {
                Utils.showToast('Failed to load summary', 'error');
            }
        } catch (error) {
            console.error('Failed to view history item:', error);
            Utils.showToast('Failed to load summary', 'error');
        }
    }

    async downloadHistoryItem(taskId) {
        try {
            const response = await fetch(`/api/summarization/tasks/${taskId}/download`);

            if (!response.ok) {
                throw new Error('Failed to download summary');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `summary_${taskId.substring(0, 8)}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            Utils.showToast('Summary downloaded successfully', 'success');

        } catch (error) {
            console.error('Failed to download summary:', error);
            Utils.showToast('Failed to download summary', 'error');
        }
    }

    // Cleanup method
    destroy() {
        // Close all WebSocket connections
        this.websockets.forEach((ws) => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        });
        this.websockets.clear();

        // Clear polling intervals
        this.activeTasks.forEach((task) => {
            if (task.pollInterval) {
                clearInterval(task.pollInterval);
            }
        });
        this.activeTasks.clear();
    }
}

// Initialize summarization interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.summarizationInterface = new SummarizationInterface();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.summarizationInterface) {
        window.summarizationInterface.destroy();
    }
});