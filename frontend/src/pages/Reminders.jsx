import { useState, useEffect } from 'react';
import { Bell, Plus, Trash2, Calendar, Mail, MessageCircle, CheckCircle, XCircle, Clock, AlertCircle, Loader } from 'lucide-react';
import { createReminder, listReminders, getReminderStats, deleteReminder } from '../services/api';
import './Reminders.css';

const Reminders = () => {
    const [reminders, setReminders] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(false);
    const [creating, setCreating] = useState(false);
    const [showForm, setShowForm] = useState(false);

    // Filters
    const [statusFilter, setStatusFilter] = useState('');
    const [typeFilter, setTypeFilter] = useState('');

    // Form state
    const [formData, setFormData] = useState({
        message: '',
        recipient: '',
        reminder_type: 'whatsapp',
        scheduled_time: ''
    });

    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        fetchReminders();
        fetchStats();
    }, [statusFilter, typeFilter]);

    const fetchReminders = async () => {
        setLoading(true);
        try {
            const data = await listReminders(statusFilter, typeFilter);
            setReminders(data.reminders || []);
        } catch (err) {
            console.error('Error fetching reminders:', err);
            setError('Failed to load reminders');
        } finally {
            setLoading(false);
        }
    };

    const fetchStats = async () => {
        try {
            const data = await getReminderStats();
            setStats(data);
        } catch (err) {
            console.error('Error fetching stats:', err);
        }
    };

    const handleCreateReminder = async (e) => {
        e.preventDefault();
        setCreating(true);
        setError('');
        setSuccess('');

        try {
            await createReminder(formData);
            setSuccess('Reminder created successfully!');
            setFormData({
                message: '',
                recipient: '',
                reminder_type: 'whatsapp',
                scheduled_time: ''
            });
            setShowForm(false);
            fetchReminders();
            fetchStats();
        } catch (err) {
            setError(err.message || 'Failed to create reminder');
        } finally {
            setCreating(false);
        }
    };

    const handleDeleteReminder = async (reminderId) => {
        if (!confirm('Are you sure you want to delete this reminder?')) return;

        try {
            await deleteReminder(reminderId);
            setSuccess('Reminder deleted successfully');
            fetchReminders();
            fetchStats();
        } catch (err) {
            setError('Failed to delete reminder');
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'sent': return <CheckCircle size={16} />;
            case 'failed': return <XCircle size={16} />;
            case 'pending': return <Clock size={16} />;
            case 'cancelled': return <XCircle size={16} />;
            default: return <AlertCircle size={16} />;
        }
    };

    const getTypeIcon = (type) => {
        switch (type) {
            case 'whatsapp': return <MessageCircle size={16} />;
            case 'email': return <Mail size={16} />;
            case 'both': return <><MessageCircle size={14} /><Mail size={14} /></>;
            default: return <Bell size={16} />;
        }
    };

    const formatDateTime = (isoString) => {
        const date = new Date(isoString);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="reminders-page">
            <div className="container">
                {/* Header */}
                <div className="reminders-header">
                    <div>
                        <h1><Bell size={36} /> Alerts & Notifications</h1>
                        <p className="subtitle">Schedule WhatsApp and Email reminders for important events</p>
                    </div>
                    <button onClick={() => setShowForm(!showForm)} className="btn-primary">
                        <Plus size={20} />
                        New Reminder
                    </button>
                </div>

                {/* Stats */}
                {stats && (
                    <div className="stats-grid">
                        <div className="stat-card total">
                            <Bell size={28} />
                            <div>
                                <div className="stat-value">{stats.total}</div>
                                <div className="stat-label">Total Reminders</div>
                            </div>
                        </div>
                        <div className="stat-card pending">
                            <Clock size={28} />
                            <div>
                                <div className="stat-value">{stats.by_status?.pending || 0}</div>
                                <div className="stat-label">Pending</div>
                            </div>
                        </div>
                        <div className="stat-card sent">
                            <CheckCircle size={28} />
                            <div>
                                <div className="stat-value">{stats.by_status?.sent || 0}</div>
                                <div className="stat-label">Sent</div>
                            </div>
                        </div>
                        <div className="stat-card failed">
                            <XCircle size={28} />
                            <div>
                                <div className="stat-value">{stats.by_status?.failed || 0}</div>
                                <div className="stat-label">Failed</div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Success/Error Messages */}
                {success && <div className="alert alert-success">{success}</div>}
                {error && <div className="alert alert-error">{error}</div>}

                {/* Create Form */}
                {showForm && (
                    <div className="reminder-form-card">
                        <h2>Create New Reminder</h2>
                        <form onSubmit={handleCreateReminder}>
                            <div className="form-grid">
                                <div className="form-field">
                                    <label>Message</label>
                                    <textarea
                                        value={formData.message}
                                        onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                                        placeholder="Enter reminder message..."
                                        required
                                        rows={3}
                                    />
                                </div>

                                <div className="form-field">
                                    <label>Recipient</label>
                                    <input
                                        type="text"
                                        value={formData.recipient}
                                        onChange={(e) => setFormData({ ...formData, recipient: e.target.value })}
                                        placeholder="Phone (+91...) or Email"
                                        required
                                    />
                                </div>

                                <div className="form-field">
                                    <label>Type</label>
                                    <select
                                        value={formData.reminder_type}
                                        onChange={(e) => setFormData({ ...formData, reminder_type: e.target.value })}
                                    >
                                        <option value="whatsapp">WhatsApp</option>
                                        <option value="email">Email</option>
                                        <option value="both">Both</option>
                                    </select>
                                </div>

                                <div className="form-field">
                                    <label>Scheduled Time</label>
                                    <input
                                        type="datetime-local"
                                        value={formData.scheduled_time}
                                        onChange={(e) => setFormData({ ...formData, scheduled_time: e.target.value })}
                                        required
                                    />
                                </div>
                            </div>

                            <div className="form-actions">
                                <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">
                                    Cancel
                                </button>
                                <button type="submit" disabled={creating} className="btn-primary">
                                    {creating ? <><Loader className="spin" size={16} /> Creating...</> : <>Create Reminder</>}
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Filters */}
                <div className="filters-bar">
                    <div className="filter-group">
                        <label>Status:</label>
                        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                            <option value="">All</option>
                            <option value="pending">Pending</option>
                            <option value="sent">Sent</option>
                            <option value="failed">Failed</option>
                            <option value="cancelled">Cancelled</option>
                        </select>
                    </div>
                    <div className="filter-group">
                        <label>Type:</label>
                        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
                            <option value="">All</option>
                            <option value="whatsapp">WhatsApp</option>
                            <option value="email">Email</option>
                            <option value="both">Both</option>
                        </select>
                    </div>
                </div>

                {/* Reminders List */}
                <div className="reminders-section">
                    <h2>Your Reminders ({reminders.length})</h2>

                    {loading ? (
                        <div className="loading-state">
                            <Loader className="spin" size={48} />
                            <p>Loading reminders...</p>
                        </div>
                    ) : reminders.length === 0 ? (
                        <div className="empty-state">
                            <Bell size={64} />
                            <h3>No reminders found</h3>
                            <p>Create your first reminder to get started!</p>
                        </div>
                    ) : (
                        <div className="reminders-grid">
                            {reminders.map((reminder) => (
                                <div key={reminder.reminder_id} className={`reminder-card ${reminder.status}`}>
                                    <div className="reminder-header">
                                        <div className="reminder-type">
                                            {getTypeIcon(reminder.reminder_type)}
                                            <span>{reminder.reminder_type}</span>
                                        </div>
                                        <div className={`status-badge ${reminder.status}`}>
                                            {getStatusIcon(reminder.status)}
                                            {reminder.status}
                                        </div>
                                    </div>

                                    <div className="reminder-message">
                                        {reminder.message}
                                    </div>

                                    <div className="reminder-details">
                                        <div className="detail-row">
                                            <Calendar size={14} />
                                            <span>{formatDateTime(reminder.scheduled_time)}</span>
                                        </div>
                                        <div className="detail-row">
                                            <Mail size={14} />
                                            <span>{reminder.recipient}</span>
                                        </div>
                                        {reminder.sent_at && (
                                            <div className="detail-row">
                                                <CheckCircle size={14} />
                                                <span>Sent: {formatDateTime(reminder.sent_at)}</span>
                                            </div>
                                        )}
                                        {reminder.error_message && (
                                            <div className="detail-row error">
                                                <XCircle size={14} />
                                                <span>{reminder.error_message}</span>
                                            </div>
                                        )}
                                    </div>

                                    <button
                                        onClick={() => handleDeleteReminder(reminder.reminder_id)}
                                        className="btn-delete"
                                        title="Delete reminder"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Reminders;
