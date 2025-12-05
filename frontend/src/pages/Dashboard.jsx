import { useState } from 'react';
import {
    MapPin,
    TrendingUp,
    Loader,
    Activity,
    BarChart3,
    Map as MapIcon,
} from 'lucide-react';
import { predictTraffic } from '../services/api';
import AnalysisTab from '../components/AnalysisTab';
import VisualizationTab from '../components/VisualizationTab';
import Chatbot from '../components/Chatbot';
import './Dashboard.css';

const Dashboard = () => {
    const [selectedLocation, setSelectedLocation] = useState('');
    const [trafficData, setTrafficData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [activeTab, setActiveTab] = useState('analysis');

    const handlePredictTraffic = async () => {
        if (!selectedLocation) {
            setError('Please enter a city name');
            return;
        }

        setLoading(true);
        setError('');
        try {
            const data = await predictTraffic(selectedLocation);
            setTrafficData(data);
            setActiveTab('analysis');
        } catch (err) {
            setError('Failed to fetch traffic prediction: ' + (err.response?.data?.detail || err.message));
            console.error(err);
            setTrafficData(null);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handlePredictTraffic();
        }
    };

    return (
        <div className="dashboard-page">
            <div className="container">
                <div className="dashboard-header">
                    <div>
                        <h1>🌍 Know the City!</h1>
                        <p className="dashboard-subtitle">
                            Discover traffic patterns, insights, and visualizations for any city
                        </p>
                    </div>
                </div>

                <div className="city-search-container">
                    <div className="city-search-card card">
                        <div className="search-header">
                            <MapPin size={32} className="search-icon" />
                            <div>
                                <h2>Enter City Name</h2>
                                <p>Type any city to get detailed traffic analysis</p>
                            </div>
                        </div>

                        <div className="search-input-group">
                            <input
                                type="text"
                                placeholder="e.g., Koregaon Park, Pune, Maharashtra"
                                value={selectedLocation}
                                onChange={(e) => setSelectedLocation(e.target.value)}
                                onKeyPress={handleKeyPress}
                                className="city-input"
                                disabled={loading}
                            />
                            <button
                                onClick={handlePredictTraffic}
                                disabled={loading || !selectedLocation}
                                className="btn btn-primary btn-search"
                            >
                                {loading ? (
                                    <>
                                        <Loader className="spin" size={20} />
                                        Analyzing...
                                    </>
                                ) : (
                                    <>
                                        <Activity size={20} />
                                        Analyze
                                    </>
                                )}
                            </button>
                        </div>

                        {error && (
                            <div className="search-error">
                                {error}
                            </div>
                        )}
                    </div>
                </div>

                {trafficData && (
                    <div className="tabs-container">
                        <div className="tab-headers">
                            <button
                                className={`tab-header ${activeTab === 'analysis' ? 'active' : ''}`}
                                onClick={() => setActiveTab('analysis')}
                            >
                                <TrendingUp size={20} />
                                Analysis
                            </button>
                            <button
                                className={`tab-header ${activeTab === 'visualization' ? 'active' : ''}`}
                                onClick={() => setActiveTab('visualization')}
                            >
                                <BarChart3 size={20} />
                                Visualization
                            </button>
                        </div>

                        <div className="tab-content">
                            {activeTab === 'analysis' && (
                                <AnalysisTab
                                    trafficData={trafficData}
                                    selectedLocation={selectedLocation}
                                />
                            )}
                            {activeTab === 'visualization' && (
                                <VisualizationTab
                                    selectedLocation={selectedLocation}
                                    trafficData={trafficData}
                                />
                            )}
                        </div>
                    </div>
                )}

                {!trafficData && !loading && (
                    <div className="empty-state">
                        <MapIcon size={64} className="empty-icon" />
                        <h3>No City Selected Yet</h3>
                        <p>
                            Enter a city name above to get started with detailed traffic analysis and visualizations.
                        </p>
                    </div>
                )}
            </div>

            <Chatbot selectedLocation={trafficData ? selectedLocation : null} />
        </div>
    );
};

export default Dashboard;
