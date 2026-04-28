import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Incidents from './pages/Incidents';
import ReportIncidents from './pages/ReportIncidents';
import RestrictedZones from './pages/RestrictedZones';
import SafeRoutes from './pages/SafeRoutes';
import SOS from './pages/SOS';
import Reminders from './pages/Reminders';
import Feedback from './pages/Feedback';
import Rewards from './pages/Rewards';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/incidents" element={<Incidents />} />
          <Route path="/report-incidents" element={<ReportIncidents />} />
          <Route path="/restricted-zones" element={<RestrictedZones />} />
          <Route path="/safety-routes" element={<SafeRoutes />} />
          <Route path="/sos" element={<SOS />} />
          <Route path="/reminders" element={<Reminders />} />
          <Route path="/feedback" element={<Feedback />} />
          <Route path="/rewards" element={<Rewards />} />
          <Route path="/about" element={<div className="container" style={{ padding: '4rem 0', textAlign: 'center' }}><h1>About</h1><p>About page coming soon!</p></div>} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
