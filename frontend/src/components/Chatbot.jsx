import { useState } from 'react';
import { MessageSquare, X, Send, Loader, Bot, User } from 'lucide-react';
import { chatWithBot } from '../services/api';
import './Chatbot.css';

const Chatbot = ({ selectedLocation }) => {
    // Only render if location is selected
    if (!selectedLocation) return null;

    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        {
            type: 'bot',
            text: '👋 Hi! I\'m your AI traffic assistant. Ask me anything about traffic conditions, safety, or route suggestions!',
            timestamp: new Date(),
        }
    ]);
    const [inputMessage, setInputMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSendMessage = async () => {
        if (!inputMessage.trim() || isLoading) return;

        const userMessage = {
            type: 'user',
            text: inputMessage,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInputMessage('');
        setIsLoading(true);

        try {
            const response = await chatWithBot(selectedLocation, inputMessage);

            const botMessage = {
                type: 'bot',
                text: response.answer,
                confidence: response.confidence,
                sources: response.sources,
                timestamp: new Date(),
            };

            setMessages(prev => [...prev, botMessage]);
        } catch (error) {
            let errorText = '❌ Sorry, I encountered an error. Please make sure the backend is running and try again.';

            if (error.response?.data?.detail) {
                errorText = `❌ ${error.response.data.detail}`;
            } else if (error.message) {
                errorText = `❌ Error: ${error.message}`;
            }

            const errorMessage = {
                type: 'bot',
                text: errorText,
                timestamp: new Date(),
                isError: true,
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const formatTime = (date) => {
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    };

    return (
        <>
            {/* Floating Button */}
            {!isOpen && (
                <button className="chatbot-float-button" onClick={() => setIsOpen(true)}>
                    <MessageSquare size={28} />
                    <span className="chatbot-badge">AI</span>
                </button>
            )}

            {/* Chatbot Window */}
            {isOpen && (
                <div className="chatbot-window">
                    <div className="chatbot-header">
                        <div className="chatbot-header-info">
                            <Bot size={24} />
                            <div>
                                <h3>Traffic AI Assistant</h3>
                                <span className="chatbot-status">● Online</span>
                            </div>
                        </div>
                        <button className="chatbot-close-btn" onClick={() => setIsOpen(false)}>
                            <X size={20} />
                        </button>
                    </div>

                    <div className="chatbot-messages">
                        {messages.map((message, index) => (
                            <div
                                key={index}
                                className={`chatbot-message ${message.type === 'user' ? 'user-message' : 'bot-message'} ${message.isError ? 'error-message' : ''}`}
                            >
                                <div className="message-avatar">
                                    {message.type === 'user' ? <User size={20} /> : <Bot size={20} />}
                                </div>
                                <div className="message-content">
                                    <div className="message-bubble">
                                        {message.text}
                                        {message.confidence && (
                                            <div className="message-meta">
                                                <span className="confidence-badge">
                                                    {(message.confidence * 100).toFixed(0)}% confident
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                    <div className="message-time">{formatTime(message.timestamp)}</div>
                                </div>
                            </div>
                        ))}

                        {isLoading && (
                            <div className="chatbot-message bot-message">
                                <div className="message-avatar">
                                    <Bot size={20} />
                                </div>
                                <div className="message-content">
                                    <div className="message-bubble typing-indicator">
                                        <span></span>
                                        <span></span>
                                        <span></span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="chatbot-input-area">
                        <input
                            type="text"
                            placeholder="Ask about traffic, routes, safety..."
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            onKeyPress={handleKeyPress}
                            disabled={isLoading}
                            className="chatbot-input"
                        />
                        <button
                            onClick={handleSendMessage}
                            disabled={!inputMessage.trim() || isLoading}
                            className="chatbot-send-btn"
                        >
                            {isLoading ? <Loader className="spin" size={20} /> : <Send size={20} />}
                        </button>
                    </div>

                    <div className="chatbot-suggestions">
                        <button
                            onClick={() => setInputMessage(`Is it safe to drive to ${selectedLocation} right now?`)}
                            className="suggestion-chip"
                        >
                            Is it safe to drive?
                        </button>
                        <button
                            onClick={() => setInputMessage(`What is the traffic like at ${selectedLocation}?`)}
                            className="suggestion-chip"
                        >
                            Traffic conditions?
                        </button>
                        <button
                            onClick={() => setInputMessage(`Best time to travel to ${selectedLocation}?`)}
                            className="suggestion-chip"
                        >
                            Best time to travel?
                        </button>
                    </div>
                </div>
            )}
        </>
    );
};

export default Chatbot;
