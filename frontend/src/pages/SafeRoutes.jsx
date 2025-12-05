import { useState } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, useMapEvents } from 'react-leaflet';
import { Navigation, Clock, MapPin, Search } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import './SafeRoutes.css';
import { calculateSafeRoutes } from '../services/api';

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

const SafeRoutes = () => {
    const [source, setSource] = useState(null);
    const [destination, setDestination] = useState(null);
    const [routes, setRoutes] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedRoute, setSelectedRoute] = useState(null);
    const [inputMode, setInputMode] = useState('source');

    // Default center (Pune)
    const defaultCenter = [18.5204, 73.8567];

    const handleMapClick = (e) => {
        const { lat, lng } = e.latlng;
        if (inputMode === 'source') {
            setSource({ latitude: lat, longitude: lng });
            setInputMode('destination');
        } else {
            setDestination({ latitude: lat, longitude: lng });
        }
    };

    const MapEvents = () => {
        useMapEvents({
            click: handleMapClick,
        });
        return null;
    };

    const handleSearch = async () => {
        if (!source || !destination) {
            setError("Please select both source and destination");
            return;
        }

        setLoading(true);
        setError(null);
        setRoutes([]);
        try {
            const data = await calculateSafeRoutes(source, destination);
            setRoutes(data.routes);
            if (data.routes.length > 0) {
                setSelectedRoute(data.routes[0]);
            }
        } catch (err) {
            console.error(err);
            setError("Failed to calculate routes. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const getDangerColor = (level) => {
        switch (level?.toLowerCase()) {
            case 'green': return '#10b981';
            case 'yellow': return '#f59e0b';
            case 'red': return '#ef4444';
            default: return '#64748b';
        }
    };

    const getDangerLabel = (level) => {
        switch (level?.toLowerCase()) {
            case 'green': return 'Low Risk';
            case 'yellow': return 'Moderate';
            case 'red': return 'High Risk';
            default: return 'Unknown';
        }
    };

    const resetSelection = () => {
        setSource(null);
        setDestination(null);
        setRoutes([]);
        setSelectedRoute(null);
        setError(null);
        setInputMode('source');
    };

    return (
        <div className="safe-routes-page">
            {/* Header */}
            <div className="safe-routes-header">
                <h1>🛡️ Safe Route Finder</h1>
                <p>Navigate with confidence using AI-powered safety analysis</p>
            </div>

            {/* Main Content */}
            <div className="safe-routes-main">
                {/* Left Sidebar - Controls */}
                <div className="controls-sidebar">
                    <div className="control-card">
                        <div className="control-section">
                            <label className="control-label">
                                <MapPin size={16} color="#10b981" />
                                <span>SOURCE</span>
                            </label>
                            <div
                                className={`coord-input ${inputMode === 'source' ? 'active' : ''}`}
                                onClick={() => setInputMode('source')}
                            >
                                {source ? `${source.latitude.toFixed(4)}, ${source.longitude.toFixed(4)}` : 'Click on map to set source'}
                            </div>
                        </div>

                        <div className="control-section">
                            <label className="control-label">
                                <MapPin size={16} color="#ef4444" />
                                <span>DESTINATION</span>
                            </label>
                            <div
                                className={`coord-input ${inputMode === 'destination' ? 'active' : ''}`}
                                onClick={() => setInputMode('destination')}
                            >
                                {destination ? `${destination.latitude.toFixed(4)}, ${destination.longitude.toFixed(4)}` : 'Click on map to set destination'}
                            </div>
                        </div>

                        <button
                            className="find-btn"
                            onClick={handleSearch}
                            disabled={!source || !destination || loading}
                        >
                            <Search size={18} />
                            {loading ? 'Calculating...' : 'Find Safe Routes'}
                        </button>

                        {error && <div className="error-msg">{error}</div>}

                        {(source || destination) && (
                            <button className="reset-btn" onClick={resetSelection}>
                                Reset Selection
                            </button>
                        )}
                    </div>

                    {/* Routes List */}
                    {routes.length > 0 && (
                        <div className="routes-panel">
                            <h3>Available Routes ({routes.length})</h3>
                            {routes.map((route) => (
                                <div
                                    key={route.route_id}
                                    className={`mini-route-card ${selectedRoute?.route_id === route.route_id ? 'selected' : ''}`}
                                    onClick={() => setSelectedRoute(route)}
                                >
                                    <div className="route-top">
                                        <span className="route-num">{route.route_name}</span>
                                        <span
                                            className="risk-badge"
                                            style={{
                                                backgroundColor: `${getDangerColor(route.danger_level)}20`,
                                                color: getDangerColor(route.danger_level)
                                            }}
                                        >
                                            {getDangerLabel(route.danger_level)}
                                        </span>
                                    </div>
                                    <div className="route-info">
                                        <span><Navigation size={12} /> {route.distance.toFixed(1)} km</span>
                                        <span><Clock size={12} /> {Math.round(route.duration)} min</span>
                                    </div>
                                    <div className="risk-bar">
                                        <div
                                            className="risk-fill"
                                            style={{
                                                width: `${Math.min(100, route.danger_index * 10)}%`,
                                                backgroundColor: getDangerColor(route.danger_level)
                                            }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Right Side - Full Width Map */}
                <div className="map-section">
                    <div className="map-overlay">
                        <div className="map-hint">
                            Click to set <strong>{inputMode}</strong>
                        </div>
                    </div>
                    <MapContainer
                        center={defaultCenter}
                        zoom={13}
                        scrollWheelZoom={true}
                        style={{ width: '100%', height: '100%' }}
                    >
                        <TileLayer
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        />
                        <MapEvents />

                        {source && (
                            <Marker position={[source.latitude, source.longitude]}>
                            </Marker>
                        )}
                        {destination && (
                            <Marker position={[destination.latitude, destination.longitude]}>
                            </Marker>
                        )}

                        {selectedRoute && (
                            <Polyline
                                positions={selectedRoute.points.map(p => [p.latitude, p.longitude])}
                                color={getDangerColor(selectedRoute.danger_level)}
                                weight={5}
                                opacity={0.8}
                            />
                        )}

                        {routes.filter(r => r.route_id !== selectedRoute?.route_id).map(route => (
                            <Polyline
                                key={route.route_id}
                                positions={route.points.map(p => [p.latitude, p.longitude])}
                                color={getDangerColor(route.danger_level)}
                                weight={3}
                                opacity={0.3}
                            />
                        ))}
                    </MapContainer>
                </div>
            </div>
        </div>
    );
};

export default SafeRoutes;
