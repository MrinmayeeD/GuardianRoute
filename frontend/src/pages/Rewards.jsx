import { useState, useEffect } from 'react';
import { Gift, Leaf, Trophy, Star, Zap, Check, Lock } from 'lucide-react';
import './Rewards.css';

const Rewards = () => {
    const [leafs, setLeafs] = useState(0);
    const [claimedRewards, setClaimedRewards] = useState([]);

    useEffect(() => {
        // Load leafs and claimed rewards
        const storedLeafs = localStorage.getItem('userLeafs');
        const storedClaimed = localStorage.getItem('claimedRewards');

        setLeafs(parseInt(storedLeafs || '0'));
        setClaimedRewards(JSON.parse(storedClaimed || '[]'));

        // Listen for leaf updates
        const handleLeafUpdate = () => {
            const updated = localStorage.getItem('userLeafs');
            setLeafs(parseInt(updated || '0'));
        };

        window.addEventListener('leafsUpdated', handleLeafUpdate);
        return () => window.removeEventListener('leafsUpdated', handleLeafUpdate);
    }, []);

    const rewards = [
        {
            id: 1,
            title: '10% Off Premium Features',
            description: 'Get 10% discount on premium traffic analytics',
            cost: 50,
            icon: '🎯',
            tier: 'bronze',
        },
        {
            id: 2,
            title: 'Early Access Pass',
            description: 'Access new features before anyone else',
            cost: 100,
            icon: '⚡',
            tier: 'silver',
        },
        {
            id: 3,
            title: 'Custom Route Planning',
            description: 'Personalized route recommendations for a week',
            cost: 150,
            icon: '🗺️',
            tier: 'silver',
        },
        {
            id: 4,
            title: '20% Off Annual Subscription',
            description: 'Save 20% on annual GeoSense premium',
            cost: 200,
            icon: '💎',
            tier: 'gold',
        },
        {
            id: 5,
            title: 'VIP Traffic Alerts',
            description: 'Priority real-time alerts and incident notifications',
            cost: 250,
            icon: '🚨',
            tier: 'gold',
        },
        {
            id: 6,
            title: 'Exclusive GeoSense Merch',
            description: 'Limited edition GeoSense t-shirt or mug',
            cost: 300,
            icon: '👕',
            tier: 'platinum',
        },
    ];

    const handleClaimReward = (reward) => {
        if (leafs >= reward.cost && !claimedRewards.includes(reward.id)) {
            const newLeafs = leafs - reward.cost;
            const newClaimed = [...claimedRewards, reward.id];

            localStorage.setItem('userLeafs', newLeafs.toString());
            localStorage.setItem('claimedRewards', JSON.stringify(newClaimed));

            setLeafs(newLeafs);
            setClaimedRewards(newClaimed);

            // Trigger leaf update event
            window.dispatchEvent(new Event('leafsUpdated'));

            // Show success animation
            alert('🎉 Congratulations! You\'ve claimed: ' + reward.title);
        }
    };

    const getTierColor = (tier) => {
        const colors = {
            bronze: { bg: '#f59e0b', light: '#fef3c7' },
            silver: { bg: '#6366f1', light: '#e0e7ff' },
            gold: { bg: '#f59e0b', light: '#fef3c7' },
            platinum: { bg: '#8b5cf6', light: '#ede9fe' },
        };
        return colors[tier] || colors.bronze;
    };

    return (
        <div className="rewards-page">
            <div className="container">
                {/* Header */}
                <div className="rewards-header">
                    <div className="header-icon">
                        <Trophy size={48} />
                    </div>
                    <h1>Rewards Marketplace</h1>
                    <p className="subtitle">
                        Redeem your Leafs for exclusive offers and premium features!
                    </p>
                </div>

                {/* User Stats */}
                <div className="stats-banner">
                    <div className="stat-card">
                        <Leaf className="stat-icon" size={32} />
                        <div className="stat-content">
                            <div className="stat-label">Your Balance</div>
                            <div className="stat-value">{leafs} Leafs</div>
                        </div>
                    </div>

                    <div className="stat-card">
                        <Gift className="stat-icon" size={32} />
                        <div className="stat-content">
                            <div className="stat-label">Rewards Claimed</div>
                            <div className="stat-value">{claimedRewards.length}</div>
                        </div>
                    </div>

                    <div className="stat-card">
                        <Star className="stat-icon" size={32} />
                        <div className="stat-content">
                            <div className="stat-label">Loyalty Tier</div>
                            <div className="stat-value">
                                {leafs >= 300 ? 'Platinum' : leafs >= 150 ? 'Gold' : leafs >= 50 ? 'Silver' : 'Bronze'}
                            </div>
                        </div>
                    </div>
                </div>

                {/* How to Earn More */}
                <div className="earn-more-section">
                    <h2>
                        <Zap size={24} />
                        How to Earn More Leafs
                    </h2>
                    <div className="earn-grid">
                        <div className="earn-card">
                            <div className="earn-icon">💬</div>
                            <h3>Share Feedback</h3>
                            <p>+10 Leafs per feedback</p>
                        </div>
                        <div className="earn-card">
                            <div className="earn-icon">🎯</div>
                            <h3>Daily Check-in</h3>
                            <p>+5 Leafs per day (Coming Soon)</p>
                        </div>
                        <div className="earn-card">
                            <div className="earn-icon">📍</div>
                            <h3>Report Traffic</h3>
                            <p>+15 Leafs per report (Coming Soon)</p>
                        </div>
                        <div className="earn-card">
                            <div className="earn-icon">🔗</div>
                            <h3>Refer Friends</h3>
                            <p>+25 Leafs per referral (Coming Soon)</p>
                        </div>
                    </div>
                </div>

                {/* Rewards Grid */}
                <div className="rewards-section">
                    <h2>Available Rewards</h2>
                    <div className="rewards-grid">
                        {rewards.map((reward) => {
                            const isClaimed = claimedRewards.includes(reward.id);
                            const canAfford = leafs >= reward.cost;
                            const tierColors = getTierColor(reward.tier);

                            let cardClassName = 'reward-card';
                            if (isClaimed) cardClassName += ' claimed';
                            if (!canAfford && !isClaimed) cardClassName += ' locked';

                            return (
                                <div
                                    key={reward.id}
                                    className={cardClassName}
                                    style={{ borderColor: tierColors.bg }}
                                >
                                    <div className="reward-tier-badge" style={{ background: tierColors.bg }}>
                                        {reward.tier}
                                    </div>

                                    {isClaimed && (
                                        <div className="claimed-badge">
                                            <Check size={16} />
                                            Claimed
                                        </div>
                                    )}

                                    <div className="reward-icon">{reward.icon}</div>
                                    <h3>{reward.title}</h3>
                                    <p>{reward.description}</p>

                                    <div className="reward-footer">
                                        <div className="reward-cost">
                                            <Leaf size={18} />
                                            {reward.cost} Leafs
                                        </div>

                                        {isClaimed ? (
                                            <button className="btn-claimed" disabled>
                                                <Check size={18} />
                                                Claimed
                                            </button>
                                        ) : canAfford ? (
                                            <button
                                                className="btn btn-primary btn-claim"
                                                onClick={() => handleClaimReward(reward)}
                                            >
                                                <Gift size={18} />
                                                Claim
                                            </button>
                                        ) : (
                                            <button className="btn-locked" disabled>
                                                <Lock size={18} />
                                                Locked
                                            </button>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Rewards;
