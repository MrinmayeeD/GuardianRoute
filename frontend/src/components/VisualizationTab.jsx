import { useState, useEffect } from 'react';
import {
    Map,
    Loader,
    AlertCircle,
    Clock,
    MapPin,
} from 'lucide-react';
import {
    getHourlyHeatmap,
    getZoneAnalytics,
    getSimilarLocations
} from '../services/api';

const VisualizationTab = ({ selectedLocation, trafficData }) => {
    const [hourlyHeatmap, setHourlyHeatmap] = useState(null);
    const [zoneAnalytics, setZoneAnalytics] = useState(null);
    const [similarLocations, setSimilarLocations] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedHour, setSelectedHour] = useState(9); // Default to 9 AM

    useEffect(() => {
        const fetchVisualizationData = async () => {
            setLoading(true);
            setError('');

            try {
                const [heatmap, zones, similar] = await Promise.all([
                    getHourlyHeatmap(selectedHour),
                    getZoneAnalytics(),
                    getSimilarLocations(selectedLocation, 5)
                ]);

                setHourlyHeatmap(heatmap);
                setZoneAnalytics(zones);
                setSimilarLocations(similar);
            } catch (err) {
                console.error('Visualization data fetch error:', err);
                setError('Some visualization data could not be loaded. This is normal if the visualization engine is not initialized.');
            } finally {
                setLoading(false);
            }
        };

        if (selectedLocation) {
            fetchVisualizationData();
        }
    }, [selectedLocation, selectedHour]);

    const handleHourChange = async (hour) => {
        setSelectedHour(hour);
        try {
            const heatmap = await getHourlyHeatmap(hour);
            setHourlyHeatmap(heatmap);
        } catch (err) {
            console.error('Failed to load heatmap:', err);
        }
    };

    if (loading) {
        return (
            <div className="visualization-loading">
                <Loader className="spin" size={48} />
                <p>Loading visualizations...</p>
            </div>
        );
    }

    return (
        <div className="visualization-tab">
            {error && (
                <div className="alert alert-info">
                    <AlertCircle size={20} />
                    {error}
                </div>
            )}

            {/* Hourly Heatmap Section */}
            {hourlyHeatmap && (
                <div className="viz-section">
                    <h3 className="viz-section-title">
                        <Map size={24} />
                        Hourly Traffic Heatmap
                    </h3>

                    <div className="hour-selector">
                        <label>Select Hour (6 AM - 9 PM):</label>
                        <div className="hour-buttons">
                            {[...Array(16)].map((_, i) => {
                                const hour = i + 6; // 6 AM to 9 PM
                                return (
                                    <button
                                        key={hour}
                                        className={`hour-btn ${selectedHour === hour ? 'active' : ''}`}
                                        onClick={() => handleHourChange(hour)}
                                    >
                                        {hour}:00
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    <div className="heatmap-card card">
                        <h4>Traffic at {hourlyHeatmap.timestamp}</h4>
                        <p className="heatmap-count">{hourlyHeatmap.count} data points</p>

                        {hourlyHeatmap.points && hourlyHeatmap.points.length > 0 ? (
                            <div className="heatmap-points-grid">
                                {hourlyHeatmap.points.slice(0, 20).map((point, idx) => (
                                    <div key={idx} className="heatmap-point card">
                                        <div className="point-location">{point.location}</div>
                                        <div className="point-details">
                                            <span>Lat: {point.lat.toFixed(4)}</span>
                                            <span>Lon: {point.lon.toFixed(4)}</span>
                                        </div>
                                        <div className="point-severity">
                                            Severity: {point.severity.toFixed(1)}
                                            <div className="severity-bar">
                                                <div
                                                    className="severity-fill"
                                                    style={{
                                                        width: `${(point.severity / 5) * 100}%`,
                                                        backgroundColor: point.severity > 3 ? '#ef4444' : point.severity > 2 ? '#f59e0b' : '#10b981'
                                                    }}
                                                ></div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="no-data">No heatmap data available for this hour</p>
                        )}
                    </div>
                </div>
            )}

            {/* Similar Locations */}
            {similarLocations && (
                <div className="viz-section">
                    <h3 className="viz-section-title">
                        <MapPin size={24} />
                        Similar Locations
                    </h3>

                    <div className="similar-locations-card card">
                        <h4>Locations Similar to {similarLocations.input_location}</h4>
                        <p>Found {similarLocations.total_similar} similar locations</p>

                        {similarLocations.similar_locations && similarLocations.similar_locations.length > 0 ? (
                            <div className="similar-grid">
                                {similarLocations.similar_locations.map((loc, idx) => (
                                    <div key={idx} className="similar-card card">
                                        <h5>#{idx + 1}: {loc.location_name}</h5>
                                        <div className="similar-details">
                                            <p>Coordinates: {loc.latitude.toFixed(4)}, {loc.longitude.toFixed(4)}</p>
                                            <p className="similarity-score">
                                                Similarity: {loc.similarity_score.toFixed(1)}%
                                            </p>
                                            <div className="similarity-bar">
                                                <div
                                                    className="similarity-fill"
                                                    style={{ width: `${loc.similarity_score}%` }}
                                                ></div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="no-data">No similar locations found</p>
                        )}
                    </div>
                </div>
            )}

            {/* Zone Analytics Summary */}
            {zoneAnalytics && (
                <div className="viz-section">
                    <h3 className="viz-section-title">
                        <Clock size={24} />
                        All Zones Analytics
                    </h3>

                    <div className="zones-summary card">
                        <h4>Total Zones: {zoneAnalytics.count}</h4>
                        <p className="generated-at">Generated at: {new Date(zoneAnalytics.generated_at).toLocaleString()}</p>

                        {zoneAnalytics.zones && Object.keys(zoneAnalytics.zones).length > 0 ? (
                            <div className="zones-grid">
                                {Object.entries(zoneAnalytics.zones).slice(0, 10).map(([zoneName, zone]) => (
                                    <div key={zoneName} className="zone-card card">
                                        <h5>{zone.location}</h5>
                                        <div className="zone-stats">
                                            <div className="zone-stat">
                                                <span className="zone-label">Avg Severity:</span>
                                                <span className="zone-value">{zone.avg_severity.toFixed(2)}</span>
                                            </div>
                                            <div className="zone-stat">
                                                <span className="zone-label">Peak Hour:</span>
                                                <span className="zone-value">{zone.peak_hour}:00</span>
                                            </div>
                                            <div className="zone-stat">
                                                <span className="zone-label">Quiet Hour:</span>
                                                <span className="zone-value">{zone.quiet_hour}:00</span>
                                            </div>
                                            <div className="zone-recommendation">
                                                {zone.recommendation}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="no-data">No zone analytics available</p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default VisualizationTab;
