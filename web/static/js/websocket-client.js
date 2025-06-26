/**
 * WebSocket Client for Summarization Progress Tracking
 * 
 * This module provides a client for connecting to the summarization WebSocket
 * endpoints and handling real-time progress updates.
 */

class SummarizationWebSocketClient {
    constructor(baseUrl = 'ws://localhost:8000') {
        this.baseUrl = baseUrl;
        this.connections = new Map();
        this.eventHandlers = new Map();
    }

    /**
     * Connect to general summarization updates
     */
    connectGeneral() {
        const wsUrl = `${this.baseUrl}/api/summarization/ws`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = (event) => {
            console.log('Connected to general summarization WebSocket');
            this.connections.set('general', ws);
            this.emit('connected', { type: 'general' });
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage('general', data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };

        ws.onclose = (event) => {
            console.log('General WebSocket connection closed');
            this.connections.delete('general');
            this.emit('disconnected', { type: 'general' });
        };

        ws.onerror = (error) => {
            console.error('General WebSocket error:', error);
            this.emit('error', { type: 'general', error });
        };

        return ws;
    }

    /**
     * Connect to task-specific updates
     */
    connectToTask(taskId) {
        const wsUrl = `${this.baseUrl}/api/summarization/ws/${taskId}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = (event) => {
            console.log(`Connected to task ${taskId} WebSocket`);
            this.connections.set(taskId, ws);
            this.emit('connected', { type: 'task', taskId });
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(taskId, data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };

        ws.onclose = (event) => {
            console.log(`Task ${taskId} WebSocket connection closed`);
            this.connections.delete(taskId);
            this.emit('disconnected', { type: 'task', taskId });
        };

        ws.onerror = (error) => {
            console.error(`Task ${taskId} WebSocket error:`, error);
            this.emit('error', { type: 'task', taskId, error });
        };

        return ws;
    }

    /**
     * Handle incoming WebSocket messages
     */
    handleMessage(connectionId, data) {
        console.log(`Received message from ${connectionId}:`, data);

        switch (data.type) {
            case 'progress_update':
                this.emit('progress', {
                    taskId: data.task_id,
                    progress: data.data.progress,
                    currentStep: data.data.current_step,
                    status: data.data.status,
                    timestamp: data.data.timestamp
                });
                break;

            case 'task_status':
                this.emit('status', {
                    taskId: data.task_id,
                    status: data.data.status,
                    progress: data.data.progress,
                    currentStep: data.data.current_step,
                    errorMessage: data.data.error_message,
                    completedAt: data.data.completed_at,
                    timestamp: data.data.timestamp
                });
                break;

            case 'initial_status':
                this.emit('initialStatus', {
                    taskId: data.task_id,
                    status: data.data.status,
                    progress: data.data.progress,
                    currentStep: data.data.current_step,
                    createdAt: data.data.created_at,
                    startedAt: data.data.started_at,
                    completedAt: data.data.completed_at
                });
                break;

            case 'connection_status':
                this.emit('connectionStatus', {
                    taskId: data.task_id,
                    status: data.status,
                    message: data.message
                });
                break;

            case 'error':
                this.emit('error', {
                    message: data.message,
                    taskId: data.task_id
                });
                break;

            default:
                console.warn('Unknown message type:', data.type);
        }
    }

    /**
     * Add event listener
     */
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    /**
     * Remove event listener
     */
    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * Emit event to all listeners
     */
    emit(event, data) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Disconnect from a specific connection
     */
    disconnect(connectionId) {
        if (this.connections.has(connectionId)) {
            const ws = this.connections.get(connectionId);
            ws.close();
            this.connections.delete(connectionId);
        }
    }

    /**
     * Disconnect from all connections
     */
    disconnectAll() {
        this.connections.forEach((ws, connectionId) => {
            ws.close();
        });
        this.connections.clear();
    }

    /**
     * Send a test message to a connection
     */
    sendTestMessage(connectionId, message = 'test') {
        if (this.connections.has(connectionId)) {
            const ws = this.connections.get(connectionId);
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(message);
            }
        }
    }
}

// Example usage
if (typeof window !== 'undefined') {
    window.SummarizationWebSocketClient = SummarizationWebSocketClient;

    // Example initialization
    window.initializeSummarizationWebSocket = function () {
        const client = new SummarizationWebSocketClient();

        // Set up event listeners
        client.on('progress', (data) => {
            console.log('Progress update:', data);
            updateProgressUI(data);
        });

        client.on('status', (data) => {
            console.log('Status update:', data);
            updateStatusUI(data);
        });

        client.on('error', (data) => {
            console.error('WebSocket error:', data);
            showErrorMessage(data.message);
        });

        return client;
    };

    // UI update functions (to be implemented by the frontend)
    function updateProgressUI(data) {
        const progressBar = document.getElementById(`progress-${data.taskId}`);
        const statusText = document.getElementById(`status-${data.taskId}`);

        if (progressBar) {
            progressBar.style.width = `${data.progress}%`;
            progressBar.setAttribute('aria-valuenow', data.progress);
        }

        if (statusText) {
            statusText.textContent = data.currentStep;
        }
    }

    function updateStatusUI(data) {
        const statusElement = document.getElementById(`task-status-${data.taskId}`);
        if (statusElement) {
            statusElement.textContent = data.status;
            statusElement.className = `status status-${data.status}`;
        }

        if (data.status === 'completed') {
            showCompletionMessage(data.taskId);
        } else if (data.status === 'failed') {
            showErrorMessage(data.errorMessage || 'Task failed');
        }
    }

    function showErrorMessage(message) {
        // Implementation depends on your UI framework
        console.error('Error:', message);
    }

    function showCompletionMessage(taskId) {
        // Implementation depends on your UI framework
        console.log(`Task ${taskId} completed successfully`);
    }
}

// Export for Node.js environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SummarizationWebSocketClient;
}