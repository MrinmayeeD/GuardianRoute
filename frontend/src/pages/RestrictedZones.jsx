import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import { AlertTriangle, MapPin, Lock } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import './RestrictedZones.css';

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

const RestrictedZones = () => {
    const [selectedCountry, setSelectedCountry] = useState('all');
    const [mapCenter, setMapCenter] = useState([24.5, 92.5]); // Center of Northeast India

    // Restricted zones data organized by country
    const restrictedZones = {
        'Assam': [
            {
                id: 'assam-1',
                place: 'Haflong',
                district: 'North Cachar Hills District (Dima Hasao)',
                lat: 25.1640,
                lng: 93.0174,
                color: '#ef4444'
            },
            {
                id: 'assam-2',
                place: 'Diphu',
                district: 'Karbi Anglong District',
                lat: 25.8430,
                lng: 93.4316,
                color: '#ef4444'
            },
            {
                id: 'assam-3',
                place: 'Kokrajhar',
                district: 'Bodoland Territorial Areas District (BTAD)',
                lat: 26.4014,
                lng: 90.2720,
                color: '#ef4444'
            }
        ],
        'Meghalaya': [
            {
                id: 'meghalaya-1',
                place: 'Shillong',
                district: 'Khasi Hills District',
                lat: 25.5788,
                lng: 91.8933,
                color: '#f97316'
            },
            {
                id: 'meghalaya-2',
                place: 'Jowai',
                district: 'Jaintia Hills District',
                lat: 25.4500,
                lng: 92.2000,
                color: '#f97316'
            },
            {
                id: 'meghalaya-3',
                place: 'Tura',
                district: 'Garo Hills District',
                lat: 25.5142,
                lng: 90.2021,
                color: '#f97316'
            }
        ],
        'Tripura': [
            {
                id: 'tripura-1',
                place: 'Khumulwng',
                district: 'Tripura Tribal Areas District (TTAADC)',
                lat: 23.8406,
                lng: 91.3803,
                color: '#eab308'
            }
        ],
        'Mizoram': [
            {
                id: 'mizoram-1',
                place: 'Chawngte',
                district: 'Chakma District',
                lat: 22.5330,
                lng: 92.9000,
                color: '#06b6d4'
            },
            {
                id: 'mizoram-2',
                place: 'Siaha',
                district: 'Mara District',
                lat: 22.4883,
                lng: 92.9814,
                color: '#06b6d4'
            },
            {
                id: 'mizoram-3',
                place: 'Lawngtlai',
                district: 'Lai District',
                lat: 22.5300,
                lng: 92.9000,
                color: '#06b6d4'
            }
        ]
    };

    // Get all zones or filtered zones
    const getAllZones = () => {
        if (selectedCountry === 'all') {
            let allZones = [];
            Object.values(restrictedZones).forEach(zones => {
                allZones = [...allZones, ...zones];
            });
            return allZones;
        }
        return restrictedZones[selectedCountry] || [];
    };

    const displayZones = getAllZones();

    const getCountryColor = (country) => {
        const colors = {
            'Assam': '#ef4444',
            'Meghalaya': '#f97316',
            'Tripura': '#eab308',
            'Mizoram': '#06b6d4'
        };
        return colors[country] || '#6b7280';
    };

    return (
        <div className="restricted-zones-page">
            {/* Header */}
            <div className="page-header">
                <div className="header-icon">
                    <AlertTriangle size={32} />
                </div>
                <h1>Restricted Zones</h1>
                <p className="subtitle">Monitor and understand restricted areas across Northeast India</p>
            </div>

            <div className="zones-container">
                {/* Left side: Map (70%) */}
                <div className="map-section">
                    <div className="map-header">
                        <h2>Restricted Zone Map</h2>
                        <div className="legend">
                            <div className="legend-item">
                                <div className="legend-color" style={{ backgroundColor: '#ef4444' }}></div>
                                <span>Assam</span>
                            </div>
                            <div className="legend-item">
                                <div className="legend-color" style={{ backgroundColor: '#f97316' }}></div>
                                <span>Meghalaya</span>
                            </div>
                            <div className="legend-item">
                                <div className="legend-color" style={{ backgroundColor: '#eab308' }}></div>
                                <span>Tripura</span>
                            </div>
                            <div className="legend-item">
                                <div className="legend-color" style={{ backgroundColor: '#06b6d4' }}></div>
                                <span>Mizoram</span>
                            </div>
                        </div>
                    </div>
                    {/* <MapContainer
                        center={mapCenter}
                        zoom={7}
                        scrollWheelZoom={true}
                        style={{ width: '100%', height: '70vh' }}
                    > */}
                    <div className="map-wrapper">
                        <MapContainer
                            center={mapCenter}
                            zoom={7}
                            scrollWheelZoom={true}
                        >
                            <TileLayer
                                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                            />

                            {/* Display zones on map */}
                            {displayZones.map((zone) => (
                                <Circle
                                    key={zone.id}
                                    center={[zone.lat, zone.lng]}
                                    radius={15000}
                                    pathOptions={{
                                        color: zone.color,
                                        fillColor: zone.color,
                                        fillOpacity: 0.5,
                                        weight: 2
                                    }}
                                >
                                    <Popup>
                                        <div className="zone-popup">
                                            <h4>{zone.place}</h4>
                                            <p><strong>District:</strong> {zone.district}</p>
                                            <p className="zone-notice">⚠️ Restricted Zone - Entry Restricted</p>
                                        </div>
                                    </Popup>
                                </Circle>
                            ))}
                        </MapContainer>
                        </div>
                    </div>

                    {/* Right side: Zone List (30%) */}
                    <div className="zones-list-section">
                        <div className="list-header">
                            <h2>Zones by Country</h2>
                            <select
                                value={selectedCountry}
                                onChange={(e) => setSelectedCountry(e.target.value)}
                                className="country-filter"
                            >
                                <option value="all">All Countries</option>
                                <option value="Assam">Assam</option>
                                <option value="Meghalaya">Meghalaya</option>
                                <option value="Tripura">Tripura</option>
                                <option value="Mizoram">Mizoram</option>
                            </select>
                        </div>

                        <div className="zones-list">
                            {displayZones.length === 0 ? (
                                <div className="no-zones">
                                    <MapPin size={32} />
                                    <p>No zones found</p>
                                </div>
                            ) : (
                                Object.entries(restrictedZones).map(([country, zones]) => {
                                    // Filter zones based on selection and country
                                    const filteredZones = selectedCountry === 'all'
                                        ? zones
                                        : selectedCountry === country ? zones : [];

                                    if (filteredZones.length === 0) return null;

                                    return (
                                        <div key={country} className="country-group">
                                            <div className="country-header">
                                                <div className="country-color" style={{ backgroundColor: getCountryColor(country) }}></div>
                                                <h3>{country}</h3>
                                            </div>
                                            <div className="zones-items">
                                                {filteredZones.map((zone) => (
                                                    <div key={zone.id} className="zone-card">
                                                        <div className="zone-card-header">
                                                            <Lock size={16} className="lock-icon" />
                                                            <span className="zone-place">{zone.place}</span>
                                                        </div>
                                                        <p className="zone-district">{zone.district}</p>
                                                        <p className="zone-coords">
                                                            {zone.lat.toFixed(4)}° N, {zone.lng.toFixed(4)}° E
                                                        </p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    );
                                })
                            )}
                        </div>
                    </div>
                </div>
            </div>
            );
};

            export default RestrictedZones;
