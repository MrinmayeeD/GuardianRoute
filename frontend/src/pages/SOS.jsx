import { useState, useEffect } from 'react';
import { AlertTriangle, Phone, MapPin, Navigation, X, Plus, Send, Loader, CheckCircle, XCircle } from 'lucide-react';
import { sendSOSAlert } from '../services/api';
import './SOS.css';

const SOS = () => {
    const [origin, setOrigin] = useState('');
    const [destination, setDestination] = useState('');
    const [phoneNumbers, setPhoneNumbers] = useState(['']);
    const [currentLocation, setCurrentLocation] = useState(null);
    const [loading, setLoading] = useState(false);
    const [locationLoading, setLocationLoading] = useState(false);
    const [result, setResult] = useState(null);

    // Load saved contacts from localStorage
    useEffect(() => {
        const savedContacts = localStorage.getItem('sosContacts');
        if (savedContacts) {
            setPhoneNumbers(JSON.parse(savedContacts));
        }
    }, []);

    // Save contacts to localStorage whenever they change
    useEffect(() => {
        if (phoneNumbers.length > 0 && phoneNumbers[0] !== '') {
            localStorage.setItem('sosContacts', JSON.stringify(phoneNumbers));
        }
    }, [phoneNumbers]);

    const addPhoneNumber = () => {
        setPhoneNumbers([...phoneNumbers, '']);
    };

    const removePhoneNumber = (index) => {
        const updated = phoneNumbers.filter((_, i) => i !== index);
        setPhoneNumbers(updated.length > 0 ? updated : ['']);
    };

    const updatePhoneNumber = (index, value) => {
        const updated = [...phoneNumbers];
        updated[index] = value;
        setPhoneNumbers(updated);
    };

    const getCurrentLocation = () => {
        setLocationLoading(true);
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    setCurrentLocation({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    });
                    setLocationLoading(false);
                },
                (error) => {
                    console.error('Error getting location:', error);
                    alert('Unable to get your location. Please enable location services.');
                    setLocationLoading(false);
                }
            );
        } else {
            alert('Geolocation is not supported by your browser.');
            setLocationLoading(false);
        }
    };

    const handleSendSOS = async () => {
        // Validation
        const validPhones = phoneNumbers.filter(p => p.trim() !== '');
        if (validPhones.length === 0) {
            alert('Please add at least one emergency contact phone number');
            return;
        }
        if (!origin.trim()) {
            alert('Please enter your origin location');
            return;
        }
        if (!destination.trim()) {
            alert('Please enter your destination');
            return;
        }

        setLoading(true);
        setResult(null);

        try {
            const response = await sendSOSAlert({
                origin: origin.trim(),
                destination: destination.trim(),
                phone_numbers: validPhones,
                current_location: currentLocation || { latitude: 0, longitude: 0 }
            });

            setResult(response);
        } catch (error) {
            setResult({
                success: false,
                message: error.message || 'Failed to send SOS alert',
                sent_to: [],
                failed: validPhones.map(p => ({ phone: p, error: 'Network error' }))
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="sos-page">
            <div className="container">
                {/* Header */}
                <div className="sos-header">
                    <div className="sos-icon-wrapper">
                        <AlertTriangle size={48} className="sos-icon" />
                    </div>
                    <h1>🆘 Emergency SOS Alert</h1>
                    <p className="sos-subtitle">
                        Send your travel details and location to emergency contacts via WhatsApp
                    </p>
                </div>

                <div className="sos-content">
                    {/* Main Form Card */}
                    <div className="sos-card">
                        <h2>Trip Details</h2>

                        {/* Origin */}
                        <div className="input-group">
                            <label htmlFor="origin">
                                <MapPin size={18} />
                                Origin (Starting Location)
                            </label>
                            <input
                                type="text"
                                id="origin"
                                value={origin}
                                onChange={(e) => setOrigin(e.target.value)}
                                placeholder="e.g., Koregaon Park, Pune"
                                className="sos-input"
                            />
                        </div>

                        {/* Destination */}
                        <div className="input-group">
                            <label htmlFor="destination">
                                <Navigation size={18} />
                                Destination (Where you're going)
                            </label>
                            <input
                                type="text"
                                id="destination"
                                value={destination}
                                onChange={(e) => setDestination(e.target.value)}
                                placeholder="e.g., Baner, Pune"
                                className="sos-input"
                            />
                        </div>

                        {/* Current Location */}
                        <div className="location-section">
                            <label>Current Location</label>
                            <div className="location-controls">
                                <button
                                    onClick={getCurrentLocation}
                                    disabled={locationLoading}
                                    className="btn-secondary"
                                >
                                    {locationLoading ? (
                                        <>
                                            <Loader className="spin" size={18} />
                                            Getting Location...
                                        </>
                                    ) : (
                                        <>
                                            <MapPin size={18} />
                                            {currentLocation ? 'Update Location' : 'Get Current Location'}
                                        </>
                                    )}
                                </button>
                                {currentLocation && (
                                    <div className="location-display">
                                        📍 {currentLocation.latitude.toFixed(4)}, {currentLocation.longitude.toFixed(4)}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Emergency Contacts */}
                        <div className="contacts-section">
                            <label>
                                <Phone size={18} />
                                Emergency Contacts (WhatsApp Numbers)
                            </label>
                            {phoneNumbers.map((phone, index) => (
                                <div key={index} className="phone-input-row">
                                    <input
                                        type="tel"
                                        value={phone}
                                        onChange={(e) => updatePhoneNumber(index, e.target.value)}
                                        placeholder="+91XXXXXXXXXX"
                                        className="sos-input"
                                    />
                                    {phoneNumbers.length > 1 && (
                                        <button
                                            onClick={() => removePhoneNumber(index)}
                                            className="btn-remove"
                                            title="Remove contact"
                                        >
                                            <X size={18} />
                                        </button>
                                    )}
                                </div>
                            ))}
                            <button onClick={addPhoneNumber} className="btn-add">
                                <Plus size={18} />
                                Add Another Contact
                            </button>
                        </div>

                        {/* Send SOS Button */}
                        <button
                            onClick={handleSendSOS}
                            disabled={loading}
                            className="btn-sos"
                        >
                            {loading ? (
                                <>
                                    <Loader className="spin" size={24} />
                                    Sending SOS Alert...
                                </>
                            ) : (
                                <>
                                    <Send size={24} />
                                    SEND SOS ALERT
                                </>
                            )}
                        </button>
                    </div>

                    {/* Info Card */}
                    <div className="info-card">
                        <h3>How It Works</h3>
                        <div className="info-steps">
                            <div className="info-step">
                                <div className="step-number">1</div>
                                <div>
                                    <strong>Enter Trip Details</strong>
                                    <p>Add your starting point and destination</p>
                                </div>
                            </div>
                            <div className="info-step">
                                <div className="step-number">2</div>
                                <div>
                                    <strong>Share Location</strong>
                                    <p>Allow access to share your current GPS location</p>
                                </div>
                            </div>
                            <div className="info-step">
                                <div className="step-number">3</div>
                                <div>
                                    <strong>Add Contacts</strong>
                                    <p>Add emergency contact numbers (WhatsApp enabled)</p>
                                </div>
                            </div>
                            <div className="info-step">
                                <div className="step-number">4</div>
                                <div>
                                    <strong>Send Alert</strong>
                                    <p>WhatsApp messages sent instantly with your details</p>
                                </div>
                            </div>
                        </div>

                        <div className="info-note">
                            <AlertTriangle size={16} />
                            <p><strong>Note:</strong> Make sure phone numbers include country code (e.g., +91 for India)</p>
                        </div>
                    </div>
                </div>

                {/* Result Display */}
                {result && (
                    <div className={`result-card ${result.success ? 'success' : 'error'}`}>
                        {result.success ? (
                            <>
                                <CheckCircle size={32} />
                                <h3>{result.message}</h3>
                                {result.sent_to.length > 0 && (
                                    <div className="sent-list">
                                        <strong>Alert sent to:</strong>
                                        <ul>
                                            {result.sent_to.map((phone, idx) => (
                                                <li key={idx}>✓ {phone}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </>
                        ) : (
                            <>
                                <XCircle size={32} />
                                <h3>{result.message}</h3>
                            </>
                        )}
                        {result.failed && result.failed.length > 0 && (
                            <div className="failed-list">
                                <strong>Failed to send:</strong>
                                <ul>
                                    {result.failed.map((item, idx) => (
                                        <li key={idx}>✗ {item.phone}: {item.error}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default SOS;
