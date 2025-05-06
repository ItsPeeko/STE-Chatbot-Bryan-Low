import React, { useState, useEffect, useRef } from 'react';
import './ChatWidget.css';

const isSkippable = (msg) => {
  if (!msg.text) return true;
  const lower = msg.text.toLowerCase();
  return lower.includes("didn’t quite understand") || lower.includes("could you rephrase");
};

const ChatWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([
        {
          sender: 'bot',
          text: "Hello! My name is STEve 👋 How can I help you today?"
        }
      ]);
    }
  }, [isOpen]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);


  const toggleWidget = () => setIsOpen(prev => !prev);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userInput = input;
    setInput('');

    // Add user message to UI immediately
    const userMessage = { sender: 'user', text: userInput };
    setMessages(prev => [...prev, userMessage]);

    // Build chat history excluding skippable system messages
    const history = messages
      .filter(msg => !isSkippable(msg))
      .map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'model',
        parts: [{ text: msg.text }]
      }));

    // Add current message to history
    history.push({
      role: 'user',
      parts: [{ text: userInput }]
    });

    try {
      const res = await fetch('https://ste-chatbot-bryan-low.onrender.com/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          state: 'ready',
          history,
          original_question: userInput
        })
      });

      const data = await res.json();
      setMessages(prev => [...prev, { sender: 'bot', text: data.reply }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { sender: 'bot', text: 'Error reaching backend.' }]);
    }
  };

  return (
    <div className="chatbot-container">
      {isOpen && (
        <div className="chatbox">
          <div className="chat-header">🤖 Chatbot</div>
          <div className="chat-body">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-bubble ${msg.sender}`}>
                {msg.text}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
          <div className="chat-input">
            <input
              type="text"
              placeholder="Type a message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            />
            <button onClick={handleSend}>Send</button>
          </div>
        </div>
      )}
      <button className="chat-toggle" onClick={toggleWidget}>
        {isOpen ? '✖' : '💬'}
      </button>
    </div>
  );
};

export default ChatWidget;
