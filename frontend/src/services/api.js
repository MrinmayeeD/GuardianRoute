const API_URL = "http://127.0.0.1:8000";

// Traffic Prediction API
export const predictTraffic = async (location) => {
    const response = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ location })
    });
    if (!response.ok) throw new Error('Failed to predict traffic');
    return response.json();
};

// Chatbot API
export const chatWithBot = async (location, question, mode = 'drive', time = 'now') => {
    const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, location, mode, time })
    });
    if (!response.ok) throw new Error('Failed to chat with bot');
    return response.json();
};

// Safe Route APIs
export const calculateSafeRoutes = async (source, destination, travelMode = 'car') => {
    const response = await fetch(`${API_URL}/api/routes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source, destination, travel_mode: travelMode })
    });
    if (!response.ok) throw new Error('Failed to calculate safe routes');
    return response.json();
};

// Visualization APIs
export const getHourlyHeatmap = async (hour) => {
    const response = await fetch(`${API_URL}/api/viz/heatmap/hourly/${hour}`);
    if (!response.ok) throw new Error('Failed to fetch hourly heatmap');
    return response.json();
};

export const getZoneAnalytics = async () => {
    const response = await fetch(`${API_URL}/api/viz/zones/analytics`);
    if (!response.ok) throw new Error('Failed to fetch zone analytics');
    return response.json();
};

export const getPredictiveHeatmap = async (hoursAhead = 3) => {
    const response = await fetch(`${API_URL}/api/viz/predict/heatmap?hours_ahead=${hoursAhead}`);
    if (!response.ok) throw new Error('Failed to fetch predictive heatmap');
    return response.json();
};

export const getSimilarLocations = async (locationName, topN = 5) => {
    const response = await fetch(`${API_URL}/api/viz/similar-locations/${encodeURIComponent(locationName)}?top_n=${topN}`);
    if (!response.ok) throw new Error('Failed to fetch similar locations');
    return response.json();
};

// Incident Analytics API
export const getIncidentAnalytics = async (latitude, longitude, radiusKm = 10) => {
    const response = await fetch(`${API_URL}/api/incidents/analytics`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ latitude, longitude, radius_km: radiusKm })
    });
    if (!response.ok) throw new Error('Failed to fetch incident analytics');
    return response.json();
};

// Health Check
export const healthCheck = async () => {
    const response = await fetch(`${API_URL}/health`);
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
};

// SOS Alert API
export const sendSOSAlert = async (sosData) => {
    const response = await fetch(`${API_URL}/sos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sosData)
    });
    if (!response.ok) throw new Error('Failed to send SOS alert');
    return response.json();
};

// Reminders API
export const createReminder = async (reminderData) => {
    // Convert datetime-local format to ISO format
    const scheduledTime = new Date(reminderData.scheduled_time).toISOString();

    const response = await fetch(`${API_URL}/reminders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            ...reminderData,
            scheduled_time: scheduledTime
        })
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create reminder');
    }
    return response.json();
};

export const listReminders = async (status = '', reminderType = '') => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (reminderType) params.append('reminder_type', reminderType);

    const response = await fetch(`${API_URL}/reminders?${params.toString()}`);
    if (!response.ok) throw new Error('Failed to fetch reminders');
    return response.json();
};

export const getReminderStats = async () => {
    const response = await fetch(`${API_URL}/reminders/stats`);
    if (!response.ok) throw new Error('Failed to fetch reminder stats');
    return response.json();
};

export const getReminder = async (reminderId) => {
    const response = await fetch(`${API_URL}/reminders/${reminderId}`);
    if (!response.ok) throw new Error('Failed to fetch reminder');
    return response.json();
};

export const deleteReminder = async (reminderId) => {
    const response = await fetch(`${API_URL}/reminders/${reminderId}`, {
        method: 'DELETE'
    });
    if (!response.ok) throw new Error('Failed to delete reminder');
    return response.json();
};
