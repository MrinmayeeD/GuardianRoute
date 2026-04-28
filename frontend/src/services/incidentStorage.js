/**
 * Incident Storage Service
 * Manages localStorage operations for reported incidents
 * Allows incidents to be shared across users/sessions
 */

const INCIDENTS_STORAGE_KEY = "reported_incidents";
const INCIDENT_ID_COUNTER = "incident_id_counter";

/**
 * Initialize storage if it doesn't exist
 */
const initializeStorage = () => {
  if (!localStorage.getItem(INCIDENTS_STORAGE_KEY)) {
    localStorage.setItem(INCIDENTS_STORAGE_KEY, JSON.stringify([]));
  }
  if (!localStorage.getItem(INCIDENT_ID_COUNTER)) {
    localStorage.setItem(INCIDENT_ID_COUNTER, "1");
  }
};

/**
 * Get all reported incidents from localStorage
 */
export const getAllIncidents = () => {
  initializeStorage();
  try {
    const incidents = localStorage.getItem(INCIDENTS_STORAGE_KEY);
    return incidents ? JSON.parse(incidents) : [];
  } catch (error) {
    console.error("Error reading incidents from storage:", error);
    return [];
  }
};

/**
 * Add a new incident to localStorage
 */
export const addIncident = (incidentData) => {
  initializeStorage();
  try {
    const incidents = getAllIncidents();

    // Generate unique ID
    const idCounter = parseInt(localStorage.getItem(INCIDENT_ID_COUNTER) || "1");
    const newIncident = {
      id: `INC-${idCounter.toString().padStart(5, "0")}`,
      ...incidentData,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    incidents.push(newIncident);
    localStorage.setItem(INCIDENTS_STORAGE_KEY, JSON.stringify(incidents));
    localStorage.setItem(INCIDENT_ID_COUNTER, (idCounter + 1).toString());

    // Trigger storage event for other tabs
    window.dispatchEvent(
      new StorageEvent("storage", {
        key: INCIDENTS_STORAGE_KEY,
        newValue: JSON.stringify(incidents),
        storageArea: localStorage,
      })
    );

    return newIncident;
  } catch (error) {
    console.error("Error adding incident to storage:", error);
    return null;
  }
};

/**
 * Update an existing incident
 */
export const updateIncident = (incidentId, updatedData) => {
  initializeStorage();
  try {
    const incidents = getAllIncidents();
    const index = incidents.findIndex((inc) => inc.id === incidentId);

    if (index !== -1) {
      incidents[index] = {
        ...incidents[index],
        ...updatedData,
        updatedAt: new Date().toISOString(),
      };
      localStorage.setItem(INCIDENTS_STORAGE_KEY, JSON.stringify(incidents));

      // Trigger storage event
      window.dispatchEvent(
        new StorageEvent("storage", {
          key: INCIDENTS_STORAGE_KEY,
          newValue: JSON.stringify(incidents),
          storageArea: localStorage,
        })
      );

      return incidents[index];
    }
    return null;
  } catch (error) {
    console.error("Error updating incident:", error);
    return null;
  }
};

/**
 * Delete an incident
 */
export const deleteIncident = (incidentId) => {
  initializeStorage();
  try {
    const incidents = getAllIncidents();
    const filteredIncidents = incidents.filter((inc) => inc.id !== incidentId);
    localStorage.setItem(INCIDENTS_STORAGE_KEY, JSON.stringify(filteredIncidents));

    // Trigger storage event
    window.dispatchEvent(
      new StorageEvent("storage", {
        key: INCIDENTS_STORAGE_KEY,
        newValue: JSON.stringify(filteredIncidents),
        storageArea: localStorage,
      })
    );

    return true;
  } catch (error) {
    console.error("Error deleting incident:", error);
    return false;
  }
};

/**
 * Get incidents by status
 */
export const getIncidentsByStatus = (status) => {
  const incidents = getAllIncidents();
  return incidents.filter((inc) => inc.status === status);
};

/**
 * Get incidents by type
 */
export const getIncidentsByType = (type) => {
  const incidents = getAllIncidents();
  return incidents.filter((inc) => inc.type === type);
};

/**
 * Get incidents by severity
 */
export const getIncidentsBySeverity = (severity) => {
  const incidents = getAllIncidents();
  return incidents.filter((inc) => inc.severity === severity);
};

/**
 * Get incidents within a location radius
 */
export const getIncidentsNearLocation = (lat, lng, radiusInKm = 5) => {
  const incidents = getAllIncidents();

  return incidents.filter((inc) => {
    if (!inc.location || !inc.location.lat || !inc.location.lng) return false;

    const distance = calculateDistance(lat, lng, inc.location.lat, inc.location.lng);
    return distance <= radiusInKm;
  });
};

/**
 * Calculate distance between two coordinates (Haversine formula)
 */
const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371; // Earth's radius in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

/**
 * Get incident statistics
 */
export const getIncidentStatistics = () => {
  const incidents = getAllIncidents();

  const stats = {
    total: incidents.length,
    byStatus: {},
    byType: {},
    bySeverity: {},
  };

  incidents.forEach((inc) => {
    // Count by status
    stats.byStatus[inc.status] = (stats.byStatus[inc.status] || 0) + 1;
    // Count by type
    stats.byType[inc.type] = (stats.byType[inc.type] || 0) + 1;
    // Count by severity
    stats.bySeverity[inc.severity] = (stats.bySeverity[inc.severity] || 0) + 1;
  });

  return stats;
};

/**
 * Clear all incidents (for testing/reset)
 */
export const clearAllIncidents = () => {
  try {
    localStorage.removeItem(INCIDENTS_STORAGE_KEY);
    localStorage.removeItem(INCIDENT_ID_COUNTER);

    // Trigger storage event
    window.dispatchEvent(
      new StorageEvent("storage", {
        key: INCIDENTS_STORAGE_KEY,
        newValue: null,
        storageArea: localStorage,
      })
    );

    return true;
  } catch (error) {
    console.error("Error clearing incidents:", error);
    return false;
  }
};

/**
 * Export incidents as JSON
 */
export const exportIncidentsAsJSON = () => {
  const incidents = getAllIncidents();
  const dataStr = JSON.stringify(incidents, null, 2);
  const dataBlob = new Blob([dataStr], { type: "application/json" });
  const url = URL.createObjectURL(dataBlob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `incidents_${new Date().toISOString().split("T")[0]}.json`;
  link.click();
  URL.revokeObjectURL(url);
};

/**
 * Import incidents from JSON
 */
export const importIncidentsFromJSON = (jsonData) => {
  try {
    const incidents = JSON.parse(jsonData);
    if (Array.isArray(incidents)) {
      localStorage.setItem(INCIDENTS_STORAGE_KEY, JSON.stringify(incidents));

      // Trigger storage event
      window.dispatchEvent(
        new StorageEvent("storage", {
          key: INCIDENTS_STORAGE_KEY,
          newValue: JSON.stringify(incidents),
          storageArea: localStorage,
        })
      );

      return true;
    }
    return false;
  } catch (error) {
    console.error("Error importing incidents:", error);
    return false;
  }
};
