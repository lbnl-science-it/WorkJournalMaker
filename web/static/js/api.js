// API client for the Daily Work Journal web interface
class ApiClient {
    constructor() {
        this.baseUrl = '';
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            const response = await fetch(url, config);

            // Handle different response types
            const contentType = response.headers.get('content-type');
            let data;

            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }

            if (!response.ok) {
                throw new ApiError(response.status, data.message || data || 'Request failed', data);
            }

            return data;
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }

            // Network or other errors
            throw new ApiError(0, error.message || 'Network error', null);
        }
    }

    // GET request
    async get(endpoint, params = {}) {
        const url = new URL(`${this.baseUrl}${endpoint}`, window.location.origin);
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                url.searchParams.append(key, value);
            }
        });

        return this.request(url.pathname + url.search, { method: 'GET' });
    }

    // POST request
    async post(endpoint, data = null) {
        const options = { method: 'POST' };
        if (data) {
            options.body = JSON.stringify(data);
        }
        return this.request(endpoint, options);
    }

    // PUT request
    async put(endpoint, data = null) {
        const options = { method: 'PUT' };
        if (data) {
            options.body = JSON.stringify(data);
        }
        return this.request(endpoint, options);
    }

    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // Health check
    async health() {
        return this.get('/api/health');
    }

    // Calendar API methods
    calendar = {
        // Get today's information
        getToday: () => this.get('/api/calendar/today'),

        // Get calendar data for a specific month
        getMonth: (year, month) => this.get('/api/calendar/month', { year, month }),

        // Get entries for a date range
        getDateRange: (startDate, endDate) => this.get('/api/calendar/range', {
            start_date: startDate,
            end_date: endDate
        })
    };

    // Entry API methods
    entries = {
        // Get recent entries
        getRecent: (limit = 10) => this.get('/api/entries/recent', { limit }),

        // Get entry by date
        getByDate: (date) => this.get(`/api/entries/${date}`),

        // Create or update entry
        save: (date, content) => this.put(`/api/entries/${date}`, {
            date,
            content
        }),

        // Create new entry
        create: (date, content) => this.post(`/api/entries/${date}`, {
            date,
            content
        }),

        // Delete entry
        delete: (date) => this.delete(`/api/entries/${date}`),

        // Get entry statistics
        getStats: () => this.get('/api/entries/stats/database'),

        // Search entries
        search: (query, options = {}) => this.get('/api/entries/search', {
            q: query,
            ...options
        })
    };

    // Sync API methods
    sync = {
        // Get sync status
        getStatus: () => this.get('/api/sync/status'),

        // Trigger full sync
        triggerFull: (dateRangeDays = null) => {
            const params = dateRangeDays ? { date_range_days: dateRangeDays } : {};
            return this.post('/api/sync/full', params);
        },

        // Trigger incremental sync
        triggerIncremental: (sinceDays = 7) => {
            const params = { since_days: sinceDays };
            return this.post('/api/sync/incremental', params);
        },

        // Sync single entry
        syncEntry: (entryDate) => this.post(`/api/sync/entry/${entryDate}`),

        // Get sync history
        getHistory: (limit = 10, syncType = null) => {
            const params = { limit };
            if (syncType) params.sync_type = syncType;
            return this.get('/api/sync/history', params);
        },

        // Get scheduler status
        getSchedulerStatus: () => this.get('/api/sync/scheduler/status'),

        // Start scheduler
        startScheduler: () => this.post('/api/sync/scheduler/start'),

        // Stop scheduler
        stopScheduler: () => this.post('/api/sync/scheduler/stop'),

        // Trigger scheduler full sync
        triggerSchedulerFull: () => this.post('/api/sync/scheduler/trigger/full'),

        // Trigger scheduler incremental sync
        triggerSchedulerIncremental: () => this.post('/api/sync/scheduler/trigger/incremental'),

        // Update scheduler configuration
        updateSchedulerConfig: (incrementalSeconds = null, fullHours = null) => {
            const params = {};
            if (incrementalSeconds !== null) params.incremental_seconds = incrementalSeconds;
            if (fullHours !== null) params.full_hours = fullHours;
            return this.put('/api/sync/scheduler/config', params);
        }
    };

    // Summarization API methods
    summarization = {
        // Generate summary
        generate: (options = {}) => this.post('/api/summarization/generate', options),

        // Get summary status
        getStatus: (taskId) => this.get(`/api/summarization/status/${taskId}`),

        // Get summary result
        getResult: (taskId) => this.get(`/api/summarization/result/${taskId}`),

        // Get recent summaries
        getRecent: (limit = 10) => this.get('/api/summarization/recent', { limit })
    };
}

// Custom error class for API errors
class ApiError extends Error {
    constructor(status, message, data = null) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.data = data;
    }

    get isNetworkError() {
        return this.status === 0;
    }

    get isClientError() {
        return this.status >= 400 && this.status < 500;
    }

    get isServerError() {
        return this.status >= 500;
    }
}

// Request interceptor for loading states and error handling
class ApiInterceptor {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.activeRequests = new Set();
        this.setupInterceptors();
    }

    setupInterceptors() {
        const originalRequest = this.apiClient.request.bind(this.apiClient);

        this.apiClient.request = async (endpoint, options = {}) => {
            const requestId = Utils.generateId('req');
            this.activeRequests.add(requestId);

            // Show global loading indicator if needed
            this.updateLoadingState();

            try {
                const result = await originalRequest(endpoint, options);
                return result;
            } catch (error) {
                // Handle common errors
                this.handleError(error, endpoint);
                throw error;
            } finally {
                this.activeRequests.delete(requestId);
                this.updateLoadingState();
            }
        };
    }

    updateLoadingState() {
        const isLoading = this.activeRequests.size > 0;
        document.body.classList.toggle('api-loading', isLoading);

        // Dispatch loading state change event
        window.dispatchEvent(new CustomEvent('apiloadingchange', {
            detail: { isLoading, activeRequests: this.activeRequests.size }
        }));
    }

    handleError(error, endpoint) {
        console.error(`API Error for ${endpoint}:`, error);

        if (error.isNetworkError) {
            Utils.showToast('Network error. Please check your connection.', 'error');
        } else if (error.status === 401) {
            Utils.showToast('Authentication required. Please refresh the page.', 'error');
        } else if (error.status === 403) {
            Utils.showToast('Access denied.', 'error');
        } else if (error.status === 404) {
            Utils.showToast('Resource not found.', 'error');
        } else if (error.isServerError) {
            Utils.showToast('Server error. Please try again later.', 'error');
        } else if (error.isClientError) {
            Utils.showToast(error.message || 'Request failed.', 'error');
        }
    }
}

// WebSocket client for real-time updates
class WebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.listeners = new Map();
    }

    connect() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.emit('connected');
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.emit('message', data);

                    // Emit specific event types
                    if (data.type) {
                        this.emit(data.type, data);
                    }
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.emit('disconnected');
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.emit('error', error);
            };

        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected');
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

            console.log(`Attempting to reconnect WebSocket in ${delay}ms (attempt ${this.reconnectAttempts})`);

            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.error('Max WebSocket reconnection attempts reached');
        }
    }

    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in WebSocket event handler for ${event}:`, error);
                }
            });
        }
    }
}

// Initialize API client and interceptor
const api = new ApiClient();
const apiInterceptor = new ApiInterceptor(api);

// Initialize WebSocket client
const ws = new WebSocketClient();

// Auto-connect WebSocket when page loads - DISABLED until summarization service is configured
// Utils.dom.ready(() => {
//     ws.connect();
// });

// Export for global use
window.api = api;
window.ws = ws;
window.ApiError = ApiError;

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ApiClient, ApiError, ApiInterceptor, WebSocketClient };
}