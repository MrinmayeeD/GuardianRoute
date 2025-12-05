import { useState } from 'react';
import { Send, Sparkles, Heart, Star, MessageCircle, TrendingUp } from 'lucide-react';
import './Feedback.css';

const Feedback = () => {
    const [feedback, setFeedback] = useState('');
    const [rating, setRating] = useState(0);
    const [category, setCategory] = useState('general');
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!feedback || rating === 0) return;

        // Award leafs for feedback
        const currentLeafs = parseInt(localStorage.getItem('userLeafs') || '0');
        const newLeafs = currentLeafs + 10; // Award 10 leafs per feedback
        localStorage.setItem('userLeafs', newLeafs.toString());

        // Trigger leaf update event
        window.dispatchEvent(new Event('leafsUpdated'));

        // Show success message
        setSubmitted(true);
        setTimeout(() => {
            setFeedback('');
            setRating(0);
            setCategory('general');
            setSubmitted(false);
        }, 3000);
    };

    return (
        <div className="feedback-page">
            <div className="container">
                {/* Header */}
                <div className="feedback-header">
                    <div className="header-icon">
                        <Sparkles size={48} />
                    </div>
                    <h1>We Value Your Feedback!</h1>
                    <p className="subtitle">
                        Help us improve GeoSense. Share your thoughts and earn <strong>10 Leafs</strong>!
                    </p>
                </div>

                {/* Success Message */}
                {submitted && (
                    <div className="success-banner">
                        <Heart className="success-icon" />
                        <div>
                            <h3>Thank You!</h3>
                            <p>Your feedback has been received. You earned 10 Leafs! 🍃</p>
                        </div>
                    </div>
                )}

                {/* Feedback Form */}
                <div className="feedback-form-container card">
                    <form onSubmit={handleSubmit} className="feedback-form">
                        {/* Category Selection */}
                        <div className="form-section">
                            <label className="form-label">
                                <MessageCircle size={20} />
                                Feedback Category
                            </label>
                            <div className="category-grid">
                                {[
                                    { value: 'general', label: 'General', icon: '💬' },
                                    { value: 'feature', label: 'Feature Request', icon: '✨' },
                                    { value: 'bug', label: 'Report Bug', icon: '🐛' },
                                    { value: 'ui', label: 'UI/UX', icon: '🎨' },
                                ].map((cat) => (
                                    <button
                                        key={cat.value}
                                        type="button"
                                        className={`category-btn ${category === cat.value ? 'active' : ''}`}
                                        onClick={() => setCategory(cat.value)}
                                    >
                                        <span className="category-icon">{cat.icon}</span>
                                        <span>{cat.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Rating */}
                        <div className="form-section">
                            <label className="form-label">
                                <Star size={20} />
                                Rate Your Experience
                            </label>
                            <div className="star-rating">
                                {[1, 2, 3, 4, 5].map((star) => (
                                    <button
                                        key={star}
                                        type="button"
                                        className={`star-btn ${star <= rating ? 'active' : ''}`}
                                        onClick={() => setRating(star)}
                                    >
                                        <Star size={32} fill={star <= rating ? '#f59e0b' : 'none'} />
                                    </button>
                                ))}
                            </div>
                            {rating > 0 && (
                                <p className="rating-text">
                                    {rating === 5 && '🌟 Excellent!'}
                                    {rating === 4 && '😊 Great!'}
                                    {rating === 3 && '👍 Good'}
                                    {rating === 2 && '😐 Could be better'}
                                    {rating === 1 && '😞 Needs improvement'}
                                </p>
                            )}
                        </div>

                        {/* Feedback Text */}
                        <div className="form-section">
                            <label className="form-label">
                                <TrendingUp size={20} />
                                Your Feedback
                            </label>
                            <textarea
                                className="feedback-textarea"
                                placeholder="Tell us what you think... We'd love to hear your ideas, suggestions, or any issues you've encountered."
                                value={feedback}
                                onChange={(e) => setFeedback(e.target.value)}
                                rows={6}
                                required
                            />
                            <div className="char-count">
                                {feedback.length} characters
                            </div>
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            className="btn btn-primary btn-submit"
                            disabled={!feedback || rating === 0}
                        >
                            <Send size={20} />
                            Submit Feedback & Earn 10 Leafs
                        </button>
                    </form>
                </div>

                {/* Info Cards */}
                <div className="info-grid">
                    <div className="info-card card">
                        <div className="info-icon primary">
                            <Heart size={24} />
                        </div>
                        <h3>We Listen</h3>
                        <p>Every piece of feedback helps us create a better experience for you.</p>
                    </div>

                    <div className="info-card card">
                        <div className="info-icon success">
                            <Sparkles size={24} />
                        </div>
                        <h3>Get Rewarded</h3>
                        <p>Earn 10 Leafs for each feedback submission. Redeem them for exclusive offers!</p>
                    </div>

                    <div className="info-card card">
                        <div className="info-icon warning">
                            <TrendingUp size={24} />
                        </div>
                        <h3>Shape the Future</h3>
                        <p>Your suggestions directly influence our roadmap and feature development.</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Feedback;
