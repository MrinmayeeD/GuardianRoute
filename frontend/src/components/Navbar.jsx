import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Leaf, MessageSquare, Gift, AlertOctagon, Bell, MapPin, Menu, X } from 'lucide-react';
import './Navbar.css';

const Navbar = () => {
    const location = useLocation();
    const [leafCount, setLeafCount] = useState(0);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    useEffect(() => {
        // Simulate fetching leaf count
        const storedCount = localStorage.getItem('leafCount');
        if (storedCount) {
            setLeafCount(parseInt(storedCount));
        }
    }, []);

    const toggleMobileMenu = () => {
        setIsMobileMenuOpen(!isMobileMenuOpen);
    };

    const closeMobileMenu = () => {
        setIsMobileMenuOpen(false);
    };

    return (
        <nav className="navbar">
            <div className="navbar-container">
                {/* Logo */}
                <Link to="/" className="navbar-logo" onClick={closeMobileMenu}>
                    <MapPin className="logo-icon" size={28} />
                    <span className="logo-text">GeoSense</span>
                </Link>

                {/* Desktop Navigation */}
                <div className="navbar-links desktop-only">
                    <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>
                        Home
                    </Link>
                    <Link to="/dashboard" className={`nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`}>
                        Know the City!
                    </Link>
                    <Link to="/incidents" className={`nav-link ${location.pathname === '/incidents' ? 'active' : ''}`}>
                        Incidents
                    </Link>
                    <Link to="/safety-routes" className={`nav-link ${location.pathname === '/safety-routes' ? 'active' : ''}`}>
                        Safety Routes
                    </Link>
                    <Link to="/sos" className={`nav-link ${location.pathname === '/sos' ? 'active' : ''}`}>
                        SOS
                    </Link>
                    <Link to="/reminders" className={`nav-link ${location.pathname === '/reminders' ? 'active' : ''}`}>
                        Alerts
                    </Link>
                </div>

                {/* Actions (Right Side) */}
                <div className="navbar-actions">
                    <div className="leaf-counter" title="Your Eco Points">
                        <Leaf className="leaf-icon" size={18} />
                        <span className="leaf-count">{leafCount}</span>
                    </div>

                    <div className="desktop-actions">
                        <Link to="/feedback" className="icon-btn" title="Feedback">
                            <MessageSquare size={20} />
                        </Link>

                        <Link to="/rewards" className="icon-btn" title="Rewards">
                            <Gift size={20} />
                        </Link>
                    </div>

                    {/* Mobile Menu Toggle */}
                    <button className="mobile-menu-btn" onClick={toggleMobileMenu}>
                        {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                    </button>
                </div>
            </div>

            {/* Mobile Navigation Menu */}
            <div className={`mobile-menu ${isMobileMenuOpen ? 'open' : ''}`}>
                <div className="mobile-nav-links">
                    <Link to="/" className={`mobile-nav-link ${location.pathname === '/' ? 'active' : ''}`} onClick={closeMobileMenu}>
                        Home
                    </Link>
                    <Link to="/dashboard" className={`mobile-nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`} onClick={closeMobileMenu}>
                        Know the City!
                    </Link>
                    <Link to="/incidents" className={`mobile-nav-link ${location.pathname === '/incidents' ? 'active' : ''}`} onClick={closeMobileMenu}>
                        Incidents
                    </Link>
                    <Link to="/safety-routes" className={`mobile-nav-link ${location.pathname === '/safety-routes' ? 'active' : ''}`} onClick={closeMobileMenu}>
                        Safety Routes
                    </Link>
                    <Link to="/sos" className={`mobile-nav-link ${location.pathname === '/sos' ? 'active' : ''}`} onClick={closeMobileMenu}>
                        SOS
                    </Link>
                    <Link to="/reminders" className={`mobile-nav-link ${location.pathname === '/reminders' ? 'active' : ''}`} onClick={closeMobileMenu}>
                        Alerts
                    </Link>

                    <div className="mobile-nav-divider"></div>

                    <Link to="/feedback" className={`mobile-nav-link ${location.pathname === '/feedback' ? 'active' : ''}`} onClick={closeMobileMenu}>
                        <MessageSquare size={18} /> Feedback
                    </Link>
                    <Link to="/rewards" className={`mobile-nav-link ${location.pathname === '/rewards' ? 'active' : ''}`} onClick={closeMobileMenu}>
                        <Gift size={18} /> Rewards
                    </Link>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
