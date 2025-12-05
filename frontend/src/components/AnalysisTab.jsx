import {
    LineChart,
    Line,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
    PieChart,
    Pie,
    Cell,
} from 'recharts';
import {
    MapPin,
    TrendingUp,
    Clock,
    Zap,
    Activity,
    Info,
    ThumbsUp,
    ThumbsDown,
    MapPinned,
} from 'lucide-react';

const AnalysisTab = ({ trafficData, selectedLocation }) => {
    const getSeverityColor = (severity) => {
        const colors = {
            LOW: '#10b981',
            MODERATE: '#f59e0b',
            HIGH: '#ef4444',
            SEVERE: '#dc2626',
            CLOSED: '#991b1b',
        };
        return colors[severity] || '#64748b';
    };

    const formatScoresForRadar = (scores) => {
        if (!scores) return [];
        return [
            { category: 'Walkability', value: scores.walkability_score || 0 },
            { category: 'Nightlife', value: scores.nightlife_score || 0 },
            { category: 'Parking', value: scores.parking_ease_score || 0 },
            { category: 'Shopping', value: scores.shopping_score || 0 },
            { category: 'Dining', value: scores.dining_options || 0 },
            { category: 'Safety', value: scores.safety_score || 0 },
        ];
    };

    const getTopPOIs = (poiBreakdown) => {
        if (!poiBreakdown) return [];
        const entries = Object.entries(poiBreakdown)
            .filter(([_, count]) => count > 0)
            .sort(([_, a], [__, b]) => b - a)
            .slice(0, 10);

        return entries.map(([name, count]) => ({
            name: name.replace(/_/g, ' '),
            value: count,
        }));
    };

    const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

    return (
        <div className="analysis-tab">
            {/* Zone Classification */}
            {trafficData.insights.zone_classification && (
                <div className="zone-classification card">
                    <div className="zone-header">
                        <MapPinned size={32} />
                        <div>
                            <h3>{trafficData.insights.zone_classification.primary}</h3>
                            <p className="zone-subcat">{trafficData.insights.zone_classification.sub_category}</p>
                            <p className="zone-vibe">{trafficData.insights.zone_classification.vibe}</p>
                        </div>
                    </div>
                    {trafficData.insights.summary && (
                        <div className="zone-summary">
                            <Info size={20} />
                            <p>{trafficData.insights.summary}</p>
                        </div>
                    )}
                </div>
            )}

            {/* Lifestyle Insights */}
            {trafficData.insights.lifestyle_insights && (
                <div className="lifestyle-section">
                    <h3 className="subsection-title">
                        <MapPin size={20} />
                        Lifestyle Insights
                    </h3>

                    <div className="lifestyle-grid">
                        {trafficData.insights.lifestyle_insights.best_for && (
                            <div className="lifestyle-card card">
                                <div className="lifestyle-header">
                                    <ThumbsUp size={20} className="icon-success" />
                                    <h4>Best For</h4>
                                </div>
                                <ul className="lifestyle-list">
                                    {trafficData.insights.lifestyle_insights.best_for.map((item, idx) => (
                                        <li key={idx}>{item}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {trafficData.insights.lifestyle_insights.avoid_if && (
                            <div className="lifestyle-card card">
                                <div className="lifestyle-header">
                                    <ThumbsDown size={20} className="icon-danger" />
                                    <h4>Avoid If</h4>
                                </div>
                                <ul className="lifestyle-list">
                                    {trafficData.insights.lifestyle_insights.avoid_if.map((item, idx) => (
                                        <li key={idx}>{item}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {trafficData.insights.lifestyle_insights.ideal_times && (
                            <div className="lifestyle-card card">
                                <div className="lifestyle-header">
                                    <Clock size={20} className="icon-info" />
                                    <h4>Ideal Times</h4>
                                </div>
                                <ul className="lifestyle-list">
                                    {trafficData.insights.lifestyle_insights.ideal_times.map((item, idx) => (
                                        <li key={idx}>{item}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {trafficData.insights.lifestyle_insights.activities && (
                            <div className="lifestyle-card card">
                                <div className="lifestyle-header">
                                    <Activity size={20} className="icon-primary" />
                                    <h4>Activities</h4>
                                </div>
                                <ul className="lifestyle-list">
                                    {trafficData.insights.lifestyle_insights.activities.map((item, idx) => (
                                        <li key={idx}>{item}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Scores Grid */}
            {trafficData.insights.scores && (
                <div className="scores-section">
                    <h3 className="subsection-title">
                        <Zap size={20} />
                        Area Scores
                    </h3>
                    <div className="scores-grid">
                        {Object.entries(trafficData.insights.scores).map(([key, value]) => (
                            <div key={key} className="score-card card">
                                <div className="score-label">{key.replace(/_/g, ' ')}</div>
                                <div className="score-value">{value.toFixed(1)}/10</div>
                                <div className="score-bar">
                                    <div
                                        className="score-fill"
                                        style={{ width: `${(value / 10) * 100}%` }}
                                    ></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Traffic Stats */}
            {trafficData.insights.traffic_stats && (
                <div className="traffic-stats-section">
                    <h3 className="subsection-title">
                        <TrendingUp size={20} />
                        Traffic Statistics
                    </h3>
                    <div className="traffic-stats-grid">
                        <div className="stat-card card">
                            <div className="stat-icon primary">
                                <Activity size={24} />
                            </div>
                            <div className="stat-content">
                                <div className="stat-label">Average Congestion</div>
                                <div className="stat-value">
                                    {(trafficData.insights.traffic_stats.avg_congestion * 100).toFixed(0)}%
                                </div>
                            </div>
                        </div>

                        <div className="stat-card card">
                            <div className="stat-icon warning">
                                <Clock size={24} />
                            </div>
                            <div className="stat-content">
                                <div className="stat-label">Morning Congestion</div>
                                <div className="stat-value">
                                    {(trafficData.insights.traffic_stats.morning_congestion * 100).toFixed(0)}%
                                </div>
                            </div>
                        </div>

                        <div className="stat-card card">
                            <div className="stat-icon info">
                                <Clock size={24} />
                            </div>
                            <div className="stat-content">
                                <div className="stat-label">Evening Congestion</div>
                                <div className="stat-value">
                                    {(trafficData.insights.traffic_stats.evening_congestion * 100).toFixed(0)}%
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Charts */}
            <div className="charts-grid">
                <div className="chart-card card">
                    <h3>24-Hour Congestion</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={trafficData.hourly_forecast}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey="hour" stroke="#64748b" />
                            <YAxis stroke="#64748b" />
                            <Tooltip />
                            <Legend />
                            <Line
                                type="monotone"
                                dataKey="congestion_ratio"
                                stroke="#3b82f6"
                                strokeWidth={2}
                                name="Congestion Ratio"
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                <div className="chart-card card">
                    <h3>Speed Analysis (km/h)</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={trafficData.hourly_forecast}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis dataKey="hour" stroke="#64748b" />
                            <YAxis stroke="#64748b" />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="current_speed" fill="#10b981" name="Current Speed" />
                            <Bar dataKey="free_flow_speed" fill="#3b82f6" name="Free Flow" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                <div className="chart-card card">
                    <h3>Area Scores Radar</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <RadarChart data={formatScoresForRadar(trafficData.insights.scores)}>
                            <PolarGrid stroke="#e2e8f0" />
                            <PolarAngleAxis dataKey="category" stroke="#64748b" />
                            <PolarRadiusAxis stroke="#64748b" />
                            <Radar
                                name="Score"
                                dataKey="value"
                                stroke="#3b82f6"
                                fill="#3b82f6"
                                fillOpacity={0.6}
                            />
                            <Tooltip />
                        </RadarChart>
                    </ResponsiveContainer>
                </div>

                <div className="chart-card card">
                    <h3>Top POI Categories</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={getTopPOIs(trafficData.insights.poi_breakdown)}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={(entry) => `${entry.name}: ${entry.value}`}
                                outerRadius={80}
                                fill="#8884d8"
                                dataKey="value"
                            >
                                {getTopPOIs(trafficData.insights.poi_breakdown).map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Hourly Table */}
            <div className="forecast-table-card card">
                <h3>Detailed Hourly Forecast</h3>
                <div className="table-wrapper">
                    <table className="forecast-table">
                        <thead>
                            <tr>
                                <th>Hour</th>
                                <th>Severity</th>
                                <th>Current Speed</th>
                                <th>Free Flow</th>
                                <th>Congestion</th>
                                <th>Confidence</th>
                            </tr>
                        </thead>
                        <tbody>
                            {trafficData.hourly_forecast.map((hour) => (
                                <tr key={hour.hour}>
                                    <td><strong>{hour.hour}:00</strong></td>
                                    <td>
                                        <span
                                            className="severity-badge"
                                            style={{ backgroundColor: getSeverityColor(hour.severity) }}
                                        >
                                            {hour.severity}
                                        </span>
                                    </td>
                                    <td>{hour.current_speed.toFixed(1)} km/h</td>
                                    <td>{hour.free_flow_speed.toFixed(1)} km/h</td>
                                    <td>{(hour.congestion_ratio * 100).toFixed(0)}%</td>
                                    <td>{(hour.confidence * 100).toFixed(0)}%</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Model Info */}
            {trafficData.insights.model_info && (
                <div className="model-info card">
                    <h3>
                        <Info size={20} />
                        Model Information
                    </h3>
                    <div className="model-stats">
                        <div className="model-stat">
                            <span className="model-label">Method:</span>
                            <span className="model-value">{trafficData.insights.model_info.ensemble_method}</span>
                        </div>
                        <div className="model-stat">
                            <span className="model-label">KNN Weight:</span>
                            <span className="model-value">{trafficData.insights.model_info.knn_weight}</span>
                        </div>
                        <div className="model-stat">
                            <span className="model-label">RF Weight:</span>
                            <span className="model-value">{trafficData.insights.model_info.rf_weight}</span>
                        </div>
                        <div className="model-stat">
                            <span className="model-label">Confidence:</span>
                            <span className="model-value">{(trafficData.insights.model_info.ensemble_confidence * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                    <p className="model-recommendation">{trafficData.insights.recommendation_confidence}</p>
                </div>
            )}
        </div>
    );
};

export default AnalysisTab;
