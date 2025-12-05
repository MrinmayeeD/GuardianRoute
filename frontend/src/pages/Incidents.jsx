import { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import { Search, AlertCircle, Clock, MapPin, TrendingUp, Loader, XCircle, Construction, AlertTriangle } from 'lucide-react';
import { getIncidentAnalytics } from '../services/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import 'leaflet/dist/leaflet.css';
import './Incidents.css';

// Fix for default Leaflet marker icons
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

const Incidents = () => {
    const [city, setCity] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [data, setData] = useState(null);
    const [mapCenter, setMapCenter] = useState([19.0760, 72.8777]); // Default Mumbai

    const presetCities = [
        { name: 'Mumbai', lat: 19.0760, lon: 72.8777 },
        { name: 'Delhi', lat: 28.7041, lon: 77.1025 },
        { name: 'Bangalore', lat: 12.9716, lon: 77.5946 },
        { name: 'Pune', lat: 18.5204, lon: 73.8567 },
        { name: 'Chennai', lat: 13.0827, lon: 80.2707 },
    ];

    const handleCitySelect = async (cityData) => {
        setCity(cityData.name);
        setMapCenter([cityData.lat, cityData.lon]);
        await fetchIncidents(cityData.lat, cityData.lon);
    };

    const fetchIncidents = async (lat, lon, radius = 15) => {
        setLoading(true);
        setError('');

        try {
            const result = await getIncidentAnalytics(lat, lon, radius);
            setData(result);
        } catch (err) {
            setError(err.message || 'Failed to fetch incident data');
            console.error('Error fetching incidents:', err);
        } finally {
            setLoading(false);
        }
    };

    const getIncidentTypeIcon = (type) => {
        switch (type) {
            case 'Road Closed':
                return <XCircle size={16} />;
            case 'Road Works':
                return <Construction size={16} />;
            case 'Jam':
                return <AlertTriangle size={16} />;
            default:
                return <AlertCircle size={16} />;
        }
    };

    const getIncidentColor = (type) => {
        switch (type) {
            case 'Road Closed':
                return '#ef4444'; // Red
            case 'Road Works':
                return '#f97316'; // Orange
            case 'Jam':
                return '#eab308'; // Yellow
            default:
                return '#64748b'; // Gray
        }
    };

    const getSeverityColor = (severity) => {
        const colors = {
            1: '#4CAF50', // Minor - Green
            2: '#FFC107', // Moderate - Yellow
            3: '#FF9800', // Major - Orange
            4: '#F44336', // Severe - Red
            0: '#9E9E9E', // Unknown - Gray
        };
        return colors[severity] || colors[0];
    };

    return (
        <div className="incidents-page">
            <div className="container">
                {/* Header */}
                <div className="incidents-header">
                    <h1>🚨 Real-Time Traffic Incidents</h1>
                    <p className="subtitle">
                        Monitor live traffic incidents and visualize road conditions on the map
                    </p>
                </div>

                {/* City Selection */}
                <div className="city-search-card card">
                    <h3>
                        <MapPin size={20} />
                        Select City
                    </h3>
                    <div className="preset-cities">
                        {presetCities.map((cityData) => (
                            <button
                                key={cityData.name}
                                className={`preset-btn ${city === cityData.name ? 'active' : ''}`}
                                onClick={() => handleCitySelect(cityData)}
                            >
                                {cityData.name}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Loading State */}
                {loading && (
                    <div className="loading-state">
                        <Loader className="spin" size={48} />
                        <p>Fetching real-time incident data...</p>
                    </div>
                )}

                {/* Error State */}
                {error && !loading && (
                    <div className="error-state">
                        <AlertCircle size={48} />
                        <p>{error}</p>
                    </div>
                )}

                {/* Initial State */}
                {!data && !loading && !error && (
                    <div className="initial-state">
                        <MapPin size={64} />
                        <h3>Select a city to view incidents</h3>
                        <p>Choose from the cities above to see real-time traffic incident data</p>
                    </div>
                )}

                {/* Data Display with Map */}
                {data && !loading && (
                    <>
                        {/* Main Content: Map + Stats */}
                        <div className="incidents-main-content">
                            {/* Left: Stats Panel */}
                            <div className="stats-sidebar">
                                {/* Summary Stats */}
                                <div className="stats-grid">
                                    <div className="stat-card incident-icon">
                                        <AlertCircle size={24} />
                                        <div>
                                            <div className="stat-value">{data.analytics.summary.total_incidents}</div>
                                            <div className="stat-label">Total Incidents</div>
                                        </div>
                                    </div>
                                    <div className="stat-card delay-icon">
                                        <Clock size={24} />
                                        <div>
                                            <div className="stat-value">{data.analytics.summary.total_delay_hours.toFixed(1)}h</div>
                                            <div className="stat-label">Total Delay</div>
                                        </div>
                                    </div>
                                </div>

                                {/* Type Distribution Chart */}
                                <div className="chart-card">
                                    <h3>
                                        <TrendingUp size={18} />
                                        Incident Types
                                    </h3>
                                    <ResponsiveContainer width="100%" height={200}>
                                        <PieChart>
                                            <Pie
                                                data={data.analytics.type_distribution}
                                                cx="50%"
                                                cy="50%"
                                                labelLine={false}
                                                label={({ type, percentage }) => `${type}: ${percentage.toFixed(1)}%`}
                                                outerRadius={60}
                                                fill="#8884d8"
                                                dataKey="count"
                                            >
                                                {data.analytics.type_distribution.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={getIncidentColor(entry.type)} />
                                                ))}
                                            </Pie>
                                            <Tooltip />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>

                                {/* Severity Distribution */}
                                <div className="chart-card">
                                    <h3>
                                        <AlertTriangle size={18} />
                                        Severity Levels
                                    </h3>
                                    <ResponsiveContainer width="100%" height={180}>
                                        <BarChart data={data.analytics.severity_distribution}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="label" />
                                            <YAxis />
                                            <Tooltip />
                                            <Bar dataKey="count" fill="#6366f1" radius={[8, 8, 0, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            {/* Right: Map */}
                            <div className="map-container-incidents">
                                <MapContainer
                                    center={mapCenter}
                                    zoom={12}
                                    scrollWheelZoom={true}
                                    style={{ width: '100%', height: '100%' }}
                                >
                                    <TileLayer
                                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                                    />

                                    {/* Incident Markers */}
                                    {data.incidents && data.incidents.map((incident) => (
                                        <Circle
                                            key={incident.id}
                                            center={[incident.coordinates[1], incident.coordinates[0]]} // [lat, lon]
                                            radius={100}
                                            pathOptions={{
                                                color: getIncidentColor(incident.type),
                                                fillColor: getIncidentColor(incident.type),
                                                fillOpacity: 0.6
                                            }}
                                        >
                                            <Popup>
                                                <div className="incident-popup">
                                                    <div className="popup-header">
                                                        {getIncidentTypeIcon(incident.type)}
                                                        <strong>{incident.type}</strong>
                                                    </div>
                                                    <div className="popup-details">
                                                        <p><strong>ID:</strong> {incident.id}</p>
                                                        {incident.description !== 'No description' && (
                                                            <p><strong>Description:</strong> {incident.description}</p>
                                                        )}
                                                        <p><strong>Severity:</strong> {incident.severity_label}</p>
                                                        {incident.delay_minutes > 0 && (
                                                            <p><strong>Delay:</strong> {incident.delay_minutes.toFixed(1)} min</p>
                                                        )}
                                                        {incident.from_street && (
                                                            <p><strong>From:</strong> {incident.from_street}</p>
                                                        )}
                                                        {incident.to_street && (
                                                            <p><strong>To:</strong> {incident.to_street}</p>
                                                        )}
                                                    </div>
                                                </div>
                                            </Popup>
                                        </Circle>
                                    ))}
                                </MapContainer>

                                {/* Map Legend */}
                                <div className="map-legend">
                                    <h4>Incident Types</h4>
                                    <div className="legend-item">
                                        <div className="legend-color" style={{ backgroundColor: '#ef4444' }}></div>
                                        <span>Road Closed</span>
                                    </div>
                                    <div className="legend-item">
                                        <div className="legend-color" style={{ backgroundColor: '#f97316' }}></div>
                                        <span>Road Works</span>
                                    </div>
                                    <div className="legend-item">
                                        <div className="legend-color" style={{ backgroundColor: '#eab308' }}></div>
                                        <span>Traffic Jam</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default Incidents;
