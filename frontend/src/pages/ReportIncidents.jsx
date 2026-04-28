import { useState, useEffect } from 'react';
import {
    FileText, Plus, Trash2, Download, AlertTriangle, TrendingUp,
    CheckCircle, AlertCircle, Loader, ChevronDown, ChevronUp, Sparkles, X
} from 'lucide-react';
import { getAllIncidents, addIncident, deleteIncident, updateIncident, exportIncidentsAsJSON } from '../services/incidentStorage';
import { generateIncidentReport, callGroqAPI } from '../services/groqAPI';
import './ReportIncidents.css';

const ReportIncidents = () => {
    const [reportedIncidents, setReportedIncidents] = useState([]);
    
    // Report Form States
    const [formData, setFormData] = useState({
        type: 'accident',
        severity: 'medium',
        description: '',
        location: { lat: 19.0760, lng: 72.8777 },
        locationName: '',
        status: 'active',
        reporterName: '',
        reporterContact: ''
    });
    const [reportLoading, setReportLoading] = useState(false);
    const [reportSuccess, setReportSuccess] = useState(false);
    
    // AI Report States
    const [aiReport, setAiReport] = useState('');
    const [aiLoading, setAiLoading] = useState(false);
    const [showAiReport, setShowAiReport] = useState(false);
    const [filterStatus, setFilterStatus] = useState('all');
    
    // Individual Incident AI Suggestion States
    const [incidentSuggestions, setIncidentSuggestions] = useState({});
    const [suggestionLoading, setSuggestionLoading] = useState({});
    const [expandedSuggestions, setExpandedSuggestions] = useState(new Set());

    // Load incidents on mount
    useEffect(() => {
        loadIncidents();
        window.addEventListener('storage', loadIncidents);
        return () => window.removeEventListener('storage', loadIncidents);
    }, []);

    const loadIncidents = () => {
        const incidents = getAllIncidents();
        setReportedIncidents(incidents);
    };

    // Handle incident form submission
    const handleReportIncident = async (e) => {
        e.preventDefault();
        
        if (!formData.reporterName || !formData.description) {
            alert('Please fill in all required fields');
            return;
        }

        setReportLoading(true);

        const newIncident = addIncident({
            type: formData.type,
            severity: formData.severity,
            title: `${formData.type.charAt(0).toUpperCase() + formData.type.slice(1).replace(/_/g, ' ')} - ${formData.locationName || 'Location'}`,
            description: formData.description,
            location: formData.location,
            locationName: formData.locationName,
            status: formData.status,
            reporterName: formData.reporterName,
            reporterContact: formData.reporterContact,
            resolvedAt: null
        });

        if (newIncident) {
            setReportedIncidents([...reportedIncidents, newIncident]);
            setFormData({
                type: 'accident',
                severity: 'medium',
                description: '',
                location: { lat: 19.0760, lng: 72.8777 },
                locationName: '',
                status: 'active',
                reporterName: '',
                reporterContact: ''
            });
            setReportSuccess(true);
            
            // Smooth scroll to incidents section below
            setTimeout(() => {
                document.querySelector('.incidents-section')?.scrollIntoView({ behavior: 'smooth' });
                setReportSuccess(false);
            }, 500);
        }

        setReportLoading(false);
    };

    // Handle AI Report generation
    const handleGenerateAIReport = async () => {
        if (reportedIncidents.length === 0) {
            alert('No incidents to generate report from');
            return;
        }

        setAiLoading(true);

        try {
            const report = await generateIncidentReport(reportedIncidents);
            setAiReport(report);
            setShowAiReport(true);
        } catch (error) {
            console.error('Error generating report:', error);
            setAiReport('Error generating report. Please try again.');
            setShowAiReport(true);
        } finally {
            setAiLoading(false);
        }
    };

    // Handle Individual Incident AI Suggestion
    const handleGenerateIncidentSuggestion = async (incident) => {
        setSuggestionLoading({ ...suggestionLoading, [incident.id]: true });

        try {
            const prompt = `You are a public safety expert. Analyze the following incident report and provide actionable suggestions and insights:

**Incident Type:** ${incident.type}
**Severity Level:** ${incident.severity}
**Location:** ${incident.locationName}
**Description:** ${incident.description}
**Reporter:** ${incident.reporterName}
**Status:** ${incident.status}

Please provide:
1. **Risk Assessment** - Evaluate the immediate danger level
2. **Recommended Actions** - What should be done immediately
3. **Prevention Tips** - How to prevent similar incidents
4. **Community Safety Impact** - Broader implications for the area
5. **Follow-up Steps** - What needs to happen next

Keep the response concise, professional, and actionable.`;

            const suggestion = await callGroqAPI(prompt);
            setIncidentSuggestions({
                ...incidentSuggestions,
                [incident.id]: suggestion
            });
            // Add incident to expanded suggestions set
            const newExpanded = new Set(expandedSuggestions);
            newExpanded.add(incident.id);
            setExpandedSuggestions(newExpanded);
        } catch (error) {
            console.error('Error generating suggestion:', error);
            setIncidentSuggestions({
                ...incidentSuggestions,
                [incident.id]: 'Error generating AI suggestion. Please try again.'
            });
            // Add incident to expanded suggestions set even on error
            const newExpanded = new Set(expandedSuggestions);
            newExpanded.add(incident.id);
            setExpandedSuggestions(newExpanded);
        } finally {
            setSuggestionLoading({ ...suggestionLoading, [incident.id]: false });
        }
    };

    // Toggle AI suggestion expansion
    const toggleSuggestionExpanded = (incidentId) => {
        const newExpanded = new Set(expandedSuggestions);
        if (newExpanded.has(incidentId)) {
            newExpanded.delete(incidentId);
        } else {
            newExpanded.add(incidentId);
        }
        setExpandedSuggestions(newExpanded);
    };

    // Delete incident
    const handleDeleteIncident = (incidentId) => {
        if (window.confirm('Are you sure you want to delete this incident?')) {
            deleteIncident(incidentId);
            setReportedIncidents(reportedIncidents.filter(inc => inc.id !== incidentId));
        }
    };

    // Update incident status
    const handleUpdateStatus = (incidentId, newStatus) => {
        const updated = updateIncident(incidentId, { 
            status: newStatus,
            resolvedAt: newStatus === 'resolved' ? new Date().toISOString() : null
        });
        if (updated) {
            loadIncidents();
        }
    };

    // Filter incidents
    const filteredIncidents = filterStatus === 'all' 
        ? reportedIncidents 
        : reportedIncidents.filter(inc => inc.status === filterStatus);

    const getIncidentTypeIcon = (type) => {
        const iconMap = {
            'accident': '🚗',
            'theft': '🚨',
            'assault': '⚠️',
            'missing_person': '🔍',
            'harassment': '🛑',
            'other': '📌'
        };
        return iconMap[type] || '📌';
    };

    const getStatusColor = (status) => {
        const colors = {
            'active': '#ef4444',
            'in_progress': '#f59e0b',
            'resolved': '#10b981',
            'false_alarm': '#6b7280'
        };
        return colors[status] || '#6b7280';
    };

    const getSeverityColor = (severity) => {
        const colors = {
            'low': '#10b981',
            'medium': '#f59e0b',
            'high': '#f97316',
            'critical': '#ef4444'
        };
        return colors[severity] || '#6b7280';
    };

    // Parse markdown-like AI content and format it
    const parseAIContent = (content) => {
        if (!content) return null;

        const lines = content.split('\n');
        const elements = [];
        let listItems = [];

        lines.forEach((line, index) => {
            const trimmedLine = line.trim();

            // Skip empty lines but track them for spacing
            if (!trimmedLine) {
                if (listItems.length > 0) {
                    elements.push(
                        <ul key={`list-${index}`} className="ai-list">
                            {listItems.map((item, i) => (
                                <li key={i} className="ai-list-item">{item}</li>
                            ))}
                        </ul>
                    );
                    listItems = [];
                }
                return;
            }

            // Check if line is a numbered list item (1., 2., etc.) or bullet point
            const numberedMatch = trimmedLine.match(/^\d+\.\s+(.*)/);
            const bulletMatch = trimmedLine.match(/^[-*]\s+(.*)/);

            if (numberedMatch || bulletMatch) {
                const itemText = numberedMatch ? numberedMatch[1] : bulletMatch[1];
                // Parse bold **text** to formatted text
                const formattedText = itemText.split(/\*\*(.*?)\*\*/).map((part, i) => 
                    i % 2 === 1 ? <strong key={i}>{part}</strong> : part
                );
                listItems.push(formattedText);
            } else {
                // Flush any pending list items
                if (listItems.length > 0) {
                    elements.push(
                        <ul key={`list-${index}`} className="ai-list">
                            {listItems.map((item, i) => (
                                <li key={i} className="ai-list-item">{item}</li>
                            ))}
                        </ul>
                    );
                    listItems = [];
                }

                // Check if it's a section header (contains ** or is all caps or ends with :)
                if (trimmedLine.includes('**') || trimmedLine.endsWith(':') || /^[A-Z\s]+:?$/.test(trimmedLine)) {
                    // Parse bold text in headers
                    const headerText = trimmedLine.split(/\*\*(.*?)\*\*/).map((part, i) => 
                        i % 2 === 1 ? part : part
                    ).join('');
                    elements.push(
                        <h4 key={`header-${index}`} className="ai-section-header">
                            {headerText.replace(/\*\*/g, '')}
                        </h4>
                    );
                } else {
                    // Regular paragraph - parse bold text
                    const formattedPara = trimmedLine.split(/\*\*(.*?)\*\*/).map((part, i) => 
                        i % 2 === 1 ? <strong key={i}>{part}</strong> : part
                    );
                    elements.push(
                        <p key={`para-${index}`} className="ai-paragraph">{formattedPara}</p>
                    );
                }
            }
        });

        // Flush any remaining list items
        if (listItems.length > 0) {
            elements.push(
                <ul key={`list-end`} className="ai-list">
                    {listItems.map((item, i) => (
                        <li key={i} className="ai-list-item">{item}</li>
                    ))}
                </ul>
            );
        }

        return elements.length > 0 ? elements : content;
    };

    return (
        <div className="report-incidents-page">
            <div className="container">
                {/* Header */}
                <div className="page-header">
                    <div className="header-icon">
                        <FileText size={32} />
                    </div>
                    <h1>Report Safety Incidents</h1>
                    <p className="subtitle">Help keep the community safe by reporting incidents</p>
                </div>

                {/* SECTION 1: AI Analytics at TOP */}
                <div className="analytics-section">
                    <h2>
                        <TrendingUp size={24} />
                        AI-Powered Incident Analysis
                    </h2>
                    <p className="section-description">Generate an official safety report summarizing all reported incidents</p>

                    {reportedIncidents.length === 0 ? (
                        <div className="empty-state">
                            <AlertTriangle size={48} />
                            <h3>No Incidents to Analyze</h3>
                            <p>Report some incidents first to generate analysis</p>
                        </div>
                    ) : (
                        <>
                            <div className="analytics-stats">
                                <div className="stat-card">
                                    <span className="stat-number">{reportedIncidents.length}</span>
                                    <span className="stat-label">Total Incidents</span>
                                </div>
                                <div className="stat-card">
                                    <span className="stat-number">{reportedIncidents.filter(i => i.status === 'active').length}</span>
                                    <span className="stat-label">Active</span>
                                </div>
                                <div className="stat-card">
                                    <span className="stat-number">{reportedIncidents.filter(i => i.status === 'resolved').length}</span>
                                    <span className="stat-label">Resolved</span>
                                </div>
                                <div className="stat-card">
                                    <span className="stat-number">{reportedIncidents.filter(i => i.severity === 'critical').length}</span>
                                    <span className="stat-label">Critical</span>
                                </div>
                            </div>

                            <button
                                className="btn btn-primary btn-large"
                                onClick={handleGenerateAIReport}
                                disabled={aiLoading}
                            >
                                {/* {aiLoading ? (
                                    <>
                                        <Loader size={18} className="spin" />
                                        Generating Report...
                                    </>
                                ) : (
                                    <>
                                        <TrendingUp size={18} />
                                        Generate AI Safety Report
                                    </>
                                )} */}
                            </button>
                        </>
                    )}
                </div>

                {/* Success Banner */}
                {reportSuccess && (
                    <div className="success-banner">
                        <CheckCircle size={24} className="success-icon" />
                        <div>
                            <h3>Incident Reported Successfully!</h3>
                            <p>Your incident has been recorded and is now visible to other users.</p>
                        </div>
                    </div>
                )}

                {/* SECTION 2: Report Form */}
                <div className="report-form-section">
                    <div className="form-container">
                        <h2>Report a Safety Incident</h2>
                        <form onSubmit={handleReportIncident} className="incident-form">
                            {/* Reporter Info */}
                            <div className="form-section">
                                <h3>Reporter Information</h3>
                                <div className="form-group">
                                    <label>Your Name *</label>
                                    <input
                                        type="text"
                                        required
                                        value={formData.reporterName}
                                        onChange={(e) => setFormData({...formData, reporterName: e.target.value})}
                                        placeholder="Enter your full name"
                                        className="form-input"
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Contact Number</label>
                                    <input
                                        type="tel"
                                        value={formData.reporterContact}
                                        onChange={(e) => setFormData({...formData, reporterContact: e.target.value})}
                                        placeholder="Your phone number (optional)"
                                        className="form-input"
                                    />
                                </div>
                            </div>

                            {/* Incident Details */}
                            <div className="form-section">
                                <h3>Incident Details</h3>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Incident Type *</label>
                                        <select
                                            required
                                            value={formData.type}
                                            onChange={(e) => setFormData({...formData, type: e.target.value})}
                                            className="form-input"
                                        >
                                            <option value="accident">🚗 Accident</option>
                                            <option value="theft">🚨 Theft</option>
                                            <option value="assault">⚠️ Assault</option>
                                            <option value="missing_person">🔍 Missing Person</option>
                                            <option value="harassment">🛑 Harassment</option>
                                            <option value="other">📌 Other</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label>Severity Level *</label>
                                        <select
                                            required
                                            value={formData.severity}
                                            onChange={(e) => setFormData({...formData, severity: e.target.value})}
                                            className="form-input"
                                        >
                                            <option value="low">🟢 Low</option>
                                            <option value="medium">🟡 Medium</option>
                                            <option value="high">🟠 High</option>
                                            <option value="critical">🔴 Critical</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Location *</label>
                                    <input
                                        type="text"
                                        required
                                        value={formData.locationName}
                                        onChange={(e) => setFormData({...formData, locationName: e.target.value})}
                                        placeholder="Where did this incident occur?"
                                        className="form-input"
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Detailed Description *</label>
                                    <textarea
                                        required
                                        value={formData.description}
                                        onChange={(e) => setFormData({...formData, description: e.target.value})}
                                        placeholder="Provide a detailed description of the incident..."
                                        rows="6"
                                        className="form-textarea"
                                    ></textarea>
                                </div>
                            </div>

                            <button type="submit" disabled={reportLoading} className="btn btn-primary">
                                {reportLoading ? (
                                    <>
                                        <Loader size={18} className="spin" />
                                        Submitting...
                                    </>
                                ) : (
                                    <>
                                        <Plus size={18} />
                                        Report Incident
                                    </>
                                )}
                            </button>
                        </form>
                    </div>
                </div>

                {/* SECTION 2: All Reported Incidents */}
                <div className="incidents-section">
                    <div className="incidents-header">
                        <div>
                            <h2>All Reported Incidents</h2>
                            <p>View and manage incident reports from this community</p>
                        </div>
                        {reportedIncidents.length > 0 && (
                            <button 
                                className="btn btn-secondary"
                                onClick={() => exportIncidentsAsJSON()}
                            >
                                <Download size={18} />
                                Export Data
                            </button>
                        )}
                    </div>

                    {/* Filter */}
                    {reportedIncidents.length > 0 && (
                        <div className="filter-section">
                            <label>Filter by Status:</label>
                            <select 
                                value={filterStatus} 
                                onChange={(e) => setFilterStatus(e.target.value)}
                                className="filter-select"
                            >
                                <option value="all">All Statuses</option>
                                <option value="active">Active</option>
                                <option value="in_progress">In Progress</option>
                                <option value="resolved">Resolved</option>
                                <option value="false_alarm">False Alarm</option>
                            </select>
                        </div>
                    )}

                    {/* Incidents List */}
                    {filteredIncidents.length === 0 ? (
                        <div className="empty-state">
                            <AlertCircle size={64} />
                            <h3>No Incidents Found</h3>
                            <p>{reportedIncidents.length === 0 ? 'Start by reporting an incident above' : 'No incidents match your filter'}</p>
                        </div>
                    ) : (
                        <div className="incidents-list">
                            {filteredIncidents.map((incident) => (
                                <div key={incident.id} className="incident-item">
                                    <div className="incident-header">
                                        <div className="incident-title">
                                            <span className="incident-emoji">{getIncidentTypeIcon(incident.type)}</span>
                                            <div>
                                                <h3>{incident.title}</h3>
                                                <p className="incident-id">Incident ID: {incident.id}</p>
                                            </div>
                                        </div>
                                        <div className="incident-badges">
                                            <span 
                                                className="badge severity"
                                                style={{backgroundColor: getSeverityColor(incident.severity) + '20', color: getSeverityColor(incident.severity)}}
                                            >
                                                {incident.severity.toUpperCase()}
                                            </span>
                                            <span 
                                                className="badge status"
                                                style={{backgroundColor: getStatusColor(incident.status) + '20', color: getStatusColor(incident.status)}}
                                            >
                                                {incident.status.replace('_', ' ').toUpperCase()}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="incident-body">
                                        <p><strong>Description:</strong> {incident.description}</p>
                                        <p><strong>Location:</strong> {incident.locationName || 'Not specified'}</p>
                                        <p><strong>Reporter:</strong> {incident.reporterName}</p>
                                        {incident.reporterContact && <p><strong>Contact:</strong> {incident.reporterContact}</p>}
                                        <p className="incident-time">
                                            Reported: {new Date(incident.createdAt).toLocaleString()}
                                        </p>
                                    </div>

                                    <div className="incident-footer">
                                        <select
                                            value={incident.status}
                                            onChange={(e) => handleUpdateStatus(incident.id, e.target.value)}
                                            className="status-select"
                                        >
                                            <option value="active">Active</option>
                                            <option value="in_progress">In Progress</option>
                                            <option value="resolved">Resolved</option>
                                            <option value="false_alarm">False Alarm</option>
                                        </select>
                                        <button
                                            className="btn btn-ai-suggestion btn-sm"
                                            onClick={() => handleGenerateIncidentSuggestion(incident)}
                                            disabled={suggestionLoading[incident.id]}
                                            title="Get AI suggestions and analysis for this incident"
                                        >
                                            {suggestionLoading[incident.id] ? (
                                                <>
                                                    <Loader size={16} className="spin" />
                                                </>
                                            ) : (
                                                <>
                                                    <Sparkles size={16} />
                                                </>
                                            )}
                                            AI Insights
                                        </button>
                                        <button
                                            className="btn btn-danger btn-sm"
                                            onClick={() => handleDeleteIncident(incident.id)}
                                        >
                                            <Trash2 size={16} />
                                            Delete
                                        </button>
                                    </div>

                                    {/* AI Suggestion Section */}
                                    {incidentSuggestions[incident.id] && (
                                        <div className="ai-suggestion-container">
                                            <div 
                                                className="ai-suggestion-header"
                                                onClick={() => toggleSuggestionExpanded(incident.id)}
                                            >
                                                <div className="ai-header-content">
                                                    <Sparkles size={20} />
                                                    <span>AI Safety Insights & Suggestions</span>
                                                </div>
                                                {expandedSuggestions.has(incident.id) ? (
                                                    <ChevronUp size={20} />
                                                ) : (
                                                    <ChevronDown size={20} />
                                                )}
                                            </div>
                                            {expandedSuggestions.has(incident.id) && (
                                                <div className="ai-suggestion-content">
                                                    {parseAIContent(incidentSuggestions[incident.id])}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ReportIncidents;
