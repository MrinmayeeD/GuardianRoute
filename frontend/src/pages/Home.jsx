import { Link } from 'react-router-dom';
import {
    MapPin,
    Shield,
    TrendingUp,
    AlertTriangle,
    Navigation,
    Clock,
    BarChart,
    CheckCircle,
    MessageSquare,
    Map,
    Bell
} from 'lucide-react';
import './Home.css';

const Home = () => {
    return (
        <div className="home-page">
            {/* Hero Section */}
            <section className="hero-section">
                <div className="container">
                    <div className="hero-content animate-fade-in">
                        <h1 className="hero-title">
                            Navigate Safely with
                            <span className="gradient-text"> AI-Powered Intelligence</span>
                        </h1>
                        <p className="hero-subtitle">
                            Hybrid ML models (KNN + Random Forest) combined with real-time APIs and conversational AI.
                            Get traffic predictions, safe routes, emergency SOS, and intelligent insights—all in natural language.
                        </p>
                        <div className="hero-buttons">
                            <Link to="/dashboard" className="btn btn-primary btn-large">
                                <MapPin size={24} />
                                Start Planning
                            </Link>
                            <Link to="/about" className="btn btn-secondary btn-large">
                                Learn More
                            </Link>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="features-section section">
                <div className="container">
                    <div className="section-header text-center">
                        <h2>Powerful AI Features for Intelligent Navigation</h2>
                        <p className="section-description">
                            Advanced technology combining machine learning, real-time data, and conversational AI
                        </p>
                    </div>

                    <div className="features-grid">
                        <div className="feature-card card animate-fade-in">
                            <div className="feature-icon primary">
                                <TrendingUp size={32} />
                            </div>
                            <h3>Traffic Prediction</h3>
                            <p>
                                18-hour forecast (6 AM - 12 AM) using hybrid KNN + Random Forest models trained
                                on POI data and historical patterns.
                            </p>
                        </div>

                        <div className="feature-card card animate-fade-in">
                            <div className="feature-icon accent">
                                <Shield size={32} />
                            </div>
                            <h3>Safe Route Planning</h3>
                            <p>
                                A* pathfinding algorithm with custom safety scoring. Avoid danger zones and
                                get safest, fastest, and balanced route options.
                            </p>
                        </div>

                        <div className="feature-card card animate-fade-in">
                            <div className="feature-icon warning">
                                <MessageSquare size={32} />
                            </div>
                            <h3>Conversational AI</h3>
                            <p>
                                Groq's Llama 3.3 70B LLM analyzes traffic data and answers questions in
                                natural language via REST API or WhatsApp.
                            </p>
                        </div>

                        <div className="feature-card card animate-fade-in">
                            <div className="feature-icon success">
                                <Map size={32} />
                            </div>
                            <h3>Real-time Data</h3>
                            <p>
                                Live traffic flow, weather conditions, and incident reports from TomTom Traffic
                                APIs and OpenWeatherMap.
                            </p>
                        </div>

                        <div className="feature-card card animate-fade-in">
                            <div className="feature-icon info">
                                <BarChart size={32} />
                            </div>
                            <h3>POI Analysis</h3>
                            <p>
                                96 POI categories analyzed via TomTom Places API for area characterization,
                                walkability, and lifestyle insights.
                            </p>
                        </div>

                        <div className="feature-card card animate-fade-in">
                            <div className="feature-icon primary">
                                <Bell size={32} />
                            </div>
                            <h3>Smart Reminders</h3>
                            <p>
                                Schedule traffic alerts via WhatsApp/Email. Get notified about congestion,
                                optimal departure times, and more.
                            </p>
                        </div>

                        <div className="feature-card card animate-fade-in">
                            <div className="feature-icon warning">
                                <AlertTriangle size={32} />
                            </div>
                            <h3>SOS Emergency Alerts</h3>
                            <p>
                                Send emergency location alerts to contacts via WhatsApp with live tracking
                                link and route information.
                            </p>
                        </div>

                        <div className="feature-card card animate-fade-in">
                            <div className="feature-icon success">
                                <Clock size={32} />
                            </div>
                            <h3>Incident Analytics</h3>
                            <p>
                                Real-time traffic incidents with heatmaps, severity levels, and interactive
                                Leaflet.js visualizations.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* How It Works Section */}
            <section className="how-it-works-section section">
                <div className="container">
                    <div className="section-header text-center">
                        <h2>How It Works</h2>
                        <p className="section-description">
                            Hybrid ML → Real-time APIs → LLM Analysis → Intelligent Response
                        </p>
                    </div>

                    <div className="steps-container">
                        <div className="step animate-slide-left">
                            <div className="step-number">1</div>
                            <div className="step-content">
                                <h3>KNN + Random Forest Prediction</h3>
                                <p>
                                    KNN finds 5 most similar locations based on 96 POI categories. Random Forest
                                    uses 5 regressors and 1 classifier to predict speed, congestion, and severity.
                                </p>
                            </div>
                        </div>

                        <div className="step animate-slide-right">
                            <div className="step-number">2</div>
                            <div className="step-content">
                                <h3>Real-time Data Enrichment</h3>
                                <p>
                                    Model predictions are enriched with live data from TomTom Traffic Flow,
                                    OpenWeatherMap, and TomTom Incidents API.
                                </p>
                            </div>
                        </div>

                        <div className="step animate-slide-left">
                            <div className="step-number">3</div>
                            <div className="step-content">
                                <h3>LLM Analysis & Response</h3>
                                <p>
                                    All data combined into knowledge base, fed to Groq's Llama 3.3 70B which
                                    generates natural language explanations and recommendations.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Stats Section */}
            <section className="stats-section section">
                <div className="container">
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-value">96</div>
                            <div className="stat-label">POI Categories</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">18hr</div>
                            <div className="stat-label">Traffic Forecast</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">3</div>
                            <div className="stat-label">Route Options</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">24/7</div>
                            <div className="stat-label">Live Monitoring</div>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="cta-section section">
                <div className="container">
                    <div className="cta-content">
                        <h2>Ready to Experience AI-Powered Navigation?</h2>
                        <p>
                            Join the future of intelligent traffic prediction and safe route planning with conversational AI.
                        </p>
                        <Link to="/dashboard" className="btn btn-primary btn-large">
                            <CheckCircle size={24} />
                            Get Started Now
                        </Link>
                    </div>
                </div>
            </section>
        </div>
    );
};

export default Home;
