import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { FiSend, FiMic, FiMicOff } from 'react-icons/fi';

const API_BASE_URL = 'http://localhost:8000';

const CareerCoach = () => {
  const [language, setLanguage] = useState("English");
  
  const languages = [
    "English", "Hindi", "Marathi", "Telugu", "Tamil", 
    "Kannada", "Punjabi", "Bhojpuri", "Bihari", "Bengali", 
    "Assamese", "Kashmiri"
  ];

  const [messages, setMessages] = useState([
    { role: 'model', parts: "Hi! I'm your AI Career Coach. What should I call you? Ask me anything like 'Why is my ATS score low?' or 'Can you rewrite my projects section?'" }
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [bgColor, setBgColor] = useState('rgba(255, 255, 255, 0.05)');
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  // Helper to determine text color based on background brightness
  const getContrastTextColor = (hexColor) => {
    if (!hexColor || hexColor.startsWith('rgba')) return '#ffffff'; // Default dark theme text
    
    let color = hexColor.replace('#', '');
    if (color.length === 3) color = color.split('').map(c => c + c).join('');
    
    const r = parseInt(color.substr(0, 2), 16);
    const g = parseInt(color.substr(2, 2), 16);
    const b = parseInt(color.substr(4, 2), 16);
    
    const yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
    return (yiq >= 128) ? '#1a1a2e' : '#ffffff'; // Dark text for light bg, Light text for dark bg
  };

  const currentTextColor = getContrastTextColor(bgColor);

  const handleMicClick = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice input is not supported in this browser. Try Google Chrome.");
      return;
    }

    if (!recognitionRef.current) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;

      recognitionRef.current.onresult = (event) => {
        let transcript = '';
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        setInputText(transcript);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    // Attempt to map selected language to BCP-47 standard
    const langMap = {
      "English": "en-IN", "Hindi": "hi-IN", "Marathi": "mr-IN", 
      "Telugu": "te-IN", "Tamil": "ta-IN", "Kannada": "kn-IN", 
      "Punjabi": "pa-IN", "Bengali": "bn-IN", "Bhojpuri": "hi-IN",
      "Bihari": "hi-IN", "Assamese": "as-IN", "Kashmiri": "ks-IN"
    };
    recognitionRef.current.lang = langMap[language] || "en-US";

    try {
      recognitionRef.current.start();
      setIsListening(true);
    } catch (e) {
      console.error(e);
      setIsListening(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const userMessage = { role: 'user', parts: inputText };
    const currentHistory = [...messages.filter(m => m.role === 'user' || m.role === 'model')];
    
    // Add user message and a placeholder for model response
    setMessages(prev => [...prev, userMessage, { role: 'model', parts: "" }]);
    setInputText('');
    setLoading(true);

    try {
      const historyToSend = currentHistory.slice(1).map(m => ({ role: m.role, parts: m.parts }));

      const payload = {
        message: userMessage.parts,
        language: language,
        history: historyToSend
      };

      const response = await fetch(`${API_BASE_URL}/api/coach`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      let currentResponseText = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunkText = decoder.decode(value, { stream: true });
        currentResponseText += chunkText;
        
        // Update the last message (the model's response) with the accumulated text
        setMessages(prev => {
          const newMessages = [...prev];
          newMessages[newMessages.length - 1] = { 
            ...newMessages[newMessages.length - 1], 
            parts: currentResponseText 
          };
          return newMessages;
        });
      }
    } catch (err) {
      console.error(err);
      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1].parts = "❌ Error: Could not reach the server.";
        return newMessages;
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="coach-container fade-up delay-100" style={{ maxWidth: '800px', margin: '0 auto', width: '100%', textAlign: 'left', display: 'flex', flexDirection: 'column', height: '80vh' }}>
      
      {/* Chat Area */}
      <div className="upload-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', backgroundColor: bgColor, color: currentTextColor, transition: 'all 0.3s ease' }}>
        <div className="upload-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: currentTextColor }}>
          <div>
            <span className="green-dot"></span>
            AI CAREER STRATEGIST CHAT
          </div>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <label htmlFor="bg-color" style={{ fontSize: '0.85rem', color: currentTextColor === '#ffffff' ? 'var(--text-muted)' : currentTextColor }}>Theme:</label>
              <input 
                id="bg-color"
                type="color" 
                value={bgColor === 'rgba(255, 255, 255, 0.05)' ? '#2b2b36' : bgColor} 
                onChange={(e) => setBgColor(e.target.value)}
                style={{ 
                  width: '30px', 
                  height: '30px', 
                  padding: '0', 
                  border: 'none', 
                  borderRadius: '50%',
                  cursor: 'pointer',
                  background: 'none'
                }}
                title="Change Background Color"
              />
            </div>
            <select 
              value={language} 
              onChange={(e) => setLanguage(e.target.value)}
              style={{ 
                padding: '0.3rem 0.5rem', 
                borderRadius: '5px', 
                background: 'var(--surface-color)', 
                color: 'var(--text-light)', 
                border: '1px solid var(--border-color)',
                fontFamily: 'inherit',
                cursor: 'pointer'
              }}
            >
              {languages.map(lang => <option key={lang} value={lang}>{lang}</option>)}
            </select>
          </div>
        </div>
        
        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {messages.map((msg, index) => (
            <div key={index} style={{
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              background: msg.role === 'user' 
                ? 'var(--primary-color)' 
                : (currentTextColor === '#ffffff' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'),
              color: msg.role === 'user' ? '#fff' : currentTextColor,
              padding: '1rem',
              borderRadius: '12px',
              maxWidth: '85%',
              border: msg.role === 'model' ? `1px solid ${currentTextColor === '#ffffff' ? 'var(--border-color)' : 'rgba(0,0,0,0.1)'}` : 'none',
              boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
            }}>
              <div style={{ fontWeight: 'bold', marginBottom: '0.8rem', fontSize: '0.85rem', color: msg.role === 'user' ? 'rgba(255,255,255,0.8)' : (currentTextColor === '#ffffff' ? 'var(--primary-color)' : currentTextColor) }}>
                {msg.role === 'user' ? 'You' : 'AI Coach'}
              </div>
              <div 
                style={{ whiteSpace: 'pre-wrap', lineHeight: '1.8', fontFamily: 'system-ui, sans-serif' }}
                dangerouslySetInnerHTML={{ 
                  __html: msg.parts
                    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color: #4da6ff; text-decoration: underline;">$1</a>')
                    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                }}
              />
            </div>
          ))}
          {loading && (
             <div style={{ alignSelf: 'flex-start', color: 'var(--text-muted)' }}>
               <div className="loader" style={{ width: '20px', height: '20px', borderWidth: '2px' }}></div>
             </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={handleSendMessage} style={{ padding: '1rem', borderTop: '1px solid var(--border-color)', display: 'flex', gap: '0.5rem' }}>
          <button 
            type="button" 
            onClick={handleMicClick}
            className={`btn ${isListening ? 'btn-danger' : 'btn-outline'}`}
            style={{ 
              padding: '0 1rem', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              background: isListening ? '#ff4d4d' : 'rgba(255, 255, 255, 0.05)',
              color: isListening ? '#fff' : 'var(--text-light)',
              border: isListening ? 'none' : '1px solid var(--border-color)',
              borderRadius: '8px',
              transition: 'all 0.2s ease'
            }}
            title="Click to speak"
          >
            {isListening ? <FiMicOff /> : <FiMic />}
          </button>
          
          <input 
            type="text" 
            value={inputText} 
            onChange={(e) => setInputText(e.target.value)}
            placeholder={isListening ? "Listening..." : "Ask anything..."} 
            style={{ ...inputStyle, marginTop: 0, flex: 1 }}
            disabled={loading}
          />
          <button type="submit" className="btn btn-primary" disabled={loading || !inputText.trim()} style={{ padding: '0 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <FiSend />
          </button>
        </form>
      </div>
    </div>
  );
};

const inputStyle = {
  width: '100%',
  padding: '0.75rem 1rem',
  background: 'rgba(255, 255, 255, 0.05)',
  border: '1px solid var(--border-color)',
  borderRadius: '8px',
  color: 'var(--text-light)',
  fontFamily: 'inherit',
  marginTop: '0.5rem',
  boxSizing: 'border-box'
};

export default CareerCoach;
