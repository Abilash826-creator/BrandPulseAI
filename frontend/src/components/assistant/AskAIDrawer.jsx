import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, 
  X, 
  Send, 
  Loader2, 
  Copy, 
  Check, 
  Mic, 
  MicOff, 
  RefreshCw, 
  Bot, 
  User, 
  HelpCircle,
  AlertCircle
} from 'lucide-react';
import { assistantAPI } from '../../services/api';
import { useBrand } from '../../context/BrandContext';

const AskAIDrawer = () => {
  const { activeBrand } = useBrand();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Hello! I am your AI Business Advisor. Ask me anything about your customer feedback, complaints, or how to boost your ratings!`
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeTool, setActiveTool] = useState(null);
  const [language, setLanguage] = useState('en');
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);
  const [copiedId, setCopiedId] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const messagesEndRef = useRef(null);
  const speechRecognitionRef = useRef(null);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen, activeTool]);

  // Load contextual suggested questions when activeBrand changes
  useEffect(() => {
    if (!activeBrand?.id) return;
    const loadSuggestions = async () => {
      try {
        const res = await assistantAPI.getSuggestedQuestions(activeBrand.id);
        setSuggestedQuestions(res.data?.questions || []);
      } catch (err) {
        console.warn('Could not load suggested questions', err);
      }
    };
    loadSuggestions();
  }, [activeBrand?.id]);

  // Web Speech API initialization
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = language === 'ta' ? 'ta-IN' : language === 'hi' ? 'hi-IN' : 'en-IN';

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputValue(prev => (prev ? `${prev} ${transcript}` : transcript));
        setIsListening(false);
      };

      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);
      speechRecognitionRef.current = recognition;
    }
  }, [language]);

  const toggleVoiceInput = () => {
    if (!speechRecognitionRef.current) {
      alert("Voice input is not supported in this browser. Please use Google Chrome or Edge.");
      return;
    }
    if (isListening) {
      speechRecognitionRef.current.stop();
      setIsListening(false);
    } else {
      speechRecognitionRef.current.start();
      setIsListening(true);
    }
  };

  const handleSend = async (textToSend) => {
    const query = (textToSend || inputValue).trim();
    if (!query || isStreaming || !activeBrand?.id) return;

    setInputValue('');
    setErrorMessage('');
    const userMsgId = `user_${Date.now()}`;
    const assistantMsgId = `asst_${Date.now()}`;

    // Add user message
    setMessages(prev => [
      ...prev,
      { id: userMsgId, role: 'user', content: query }
    ]);

    setIsStreaming(true);
    setActiveTool('Analyzing business data...');

    let assistantText = '';

    // Placeholder for assistant stream
    setMessages(prev => [
      ...prev,
      { id: assistantMsgId, role: 'assistant', content: '' }
    ]);

    await assistantAPI.streamChat({
      businessId: activeBrand.id,
      message: query,
      language,
      onToolCall: (toolName) => {
        const toolMap = {
          get_top_issues: 'Scanning customer complaints and negative feedback...',
          get_top_praises: 'Finding what customers love most...',
          get_overview: 'Compiling 30-day review summary and ratings...',
          get_rating_trend: 'Calculating your customer rating trajectory...',
          get_unreplied_reviews: 'Checking unreplied customer reviews...',
          draft_reply: 'Drafting polite, customized reply in customer language...',
          compare_with_nearby: 'Benchmarking against nearby competitors...',
          create_reminder_task: 'Creating action item reminder...'
        };
        setActiveTool(toolMap[toolName] || `Executing ${toolName}...`);
      },
      onDelta: (delta) => {
        setActiveTool(null);
        assistantText += delta;
        setMessages(prev => 
          prev.map(m => m.id === assistantMsgId ? { ...m, content: assistantText } : m)
        );
      },
      onDone: () => {
        setIsStreaming(false);
        setActiveTool(null);
      },
      onError: (err) => {
        setIsStreaming(false);
        setActiveTool(null);
        setErrorMessage(err);
      }
    });
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const resetChat = () => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: `Conversation refreshed! How can I assist ${activeBrand?.name || 'your business'} today?`
      }
    ]);
    setErrorMessage('');
  };

  return (
    <>
      {/* Floating Trigger Button (Bottom-Right) */}
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        aria-label="Open Ask AI Assistant"
        className="fixed bottom-6 right-6 z-40 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white p-3.5 sm:px-5 sm:py-3.5 rounded-full shadow-xl hover:shadow-2xl transition-all duration-300 flex items-center space-x-2.5 group transform hover:scale-105"
      >
        <div className="relative">
          <Sparkles className="w-5 h-5 text-amber-300 animate-pulse" />
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full ring-2 ring-white"></span>
        </div>
        <span className="font-bold text-sm tracking-tight hidden sm:inline">Ask AI</span>
      </button>

      {/* Slide-Over Drawer Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 transition-opacity"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Drawer Container */}
      <div className={`fixed top-0 right-0 h-full w-full sm:w-[480px] bg-white z-50 shadow-2xl flex flex-col transition-transform duration-300 ease-in-out ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}>
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-xs">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="font-extrabold text-slate-900 text-sm">Ask AI Assistant</h3>
                <span className="text-[10px] bg-blue-100 text-blue-700 font-bold px-2 py-0.5 rounded-full">
                  {activeBrand?.name || 'Local Shop'}
                </span>
              </div>
              <p className="text-[11px] text-slate-500">Answers strictly from your customer reviews</p>
            </div>
          </div>

          <div className="flex items-center space-x-1">
            <button
              onClick={resetChat}
              title="Reset conversation"
              className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200/50 transition"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200/50 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Language Switcher Bar */}
        <div className="px-4 py-2 border-b border-slate-100 bg-white flex items-center justify-between text-xs">
          <span className="text-slate-500 text-[11px] font-medium">Assistant Language:</span>
          <div className="flex items-center space-x-1 bg-slate-100 p-0.5 rounded-lg text-[11px] font-semibold">
            <button
              onClick={() => setLanguage('en')}
              className={`px-2.5 py-1 rounded-md transition ${language === 'en' ? 'bg-white text-blue-600 shadow-xs' : 'text-slate-600'}`}
            >
              English
            </button>
            <button
              onClick={() => setLanguage('ta')}
              className={`px-2.5 py-1 rounded-md transition ${language === 'ta' ? 'bg-white text-blue-600 shadow-xs' : 'text-slate-600'}`}
            >
              தமிழ்
            </button>
            <button
              onClick={() => setLanguage('hi')}
              className={`px-2.5 py-1 rounded-md transition ${language === 'hi' ? 'bg-white text-blue-600 shadow-xs' : 'text-slate-600'}`}
            >
              हिन्दी
            </button>
          </div>
        </div>

        {/* Message Stream Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex items-start space-x-2.5 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {m.role === 'assistant' && (
                <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div className={`relative max-w-[85%] p-3.5 rounded-2xl leading-relaxed ${
                m.role === 'user'
                  ? 'bg-blue-600 text-white rounded-br-xs font-medium'
                  : 'bg-slate-100 text-slate-800 rounded-bl-xs border border-slate-200/60'
              }`}>
                <div className="whitespace-pre-wrap">{m.content}</div>

                {m.role === 'assistant' && m.content && (
                  <div className="mt-2.5 pt-2 border-t border-slate-200 flex items-center justify-between text-[10px] text-slate-400">
                    <span>AI-generated from reviews</span>
                    <button
                      onClick={() => copyToClipboard(m.content, m.id)}
                      className="flex items-center space-x-1 hover:text-slate-700 transition"
                    >
                      {copiedId === m.id ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-600" />
                          <span className="text-emerald-600">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy reply</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>

              {m.role === 'user' && (
                <div className="w-7 h-7 rounded-lg bg-slate-800 text-white flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {/* Active Tool Calling Animation */}
          {activeTool && (
            <div className="flex items-center space-x-2 p-2.5 rounded-xl bg-blue-50 border border-blue-200 text-blue-700 text-xs animate-pulse">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>{activeTool}</span>
            </div>
          )}

          {errorMessage && (
            <div className="p-3 rounded-xl bg-red-50 text-red-700 text-xs border border-red-200 flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Contextual Question Chips */}
        {suggestedQuestions.length > 0 && (
          <div className="px-4 py-2 bg-slate-50 border-t border-slate-100 flex items-center space-x-2 overflow-x-auto no-scrollbar">
            <span className="text-[10px] text-slate-400 font-bold uppercase shrink-0">Ask:</span>
            {suggestedQuestions.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSend(q)}
                disabled={isStreaming}
                className="shrink-0 text-[11px] font-semibold px-2.5 py-1 bg-white hover:bg-blue-50 hover:text-blue-600 border border-slate-200 rounded-full text-slate-700 transition shadow-2xs disabled:opacity-50"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-100 bg-white">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center space-x-2"
          >
            <div className="relative flex-1">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={
                  language === 'ta'
                    ? "கேள்வி கேளுங்கள் (எ.கா: வாடிக்கையாளர் குறை என்ன?)..."
                    : language === 'hi'
                    ? "सवाल पूछें (उदा: ग्राहक शिकायत क्या है?)..."
                    : "Ask about complaints, ratings, or draft a reply..."
                }
                disabled={isStreaming}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-blue-600 focus:ring-1 focus:ring-blue-600 transition pr-10"
              />
              <button
                type="button"
                onClick={toggleVoiceInput}
                title="Voice input"
                className={`absolute right-2 top-2.5 p-1 rounded-md transition ${
                  isListening ? 'text-red-600 bg-red-100 animate-pulse' : 'text-slate-400 hover:text-slate-600'
                }`}
              >
                {isListening ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
              </button>
            </div>

            <button
              type="submit"
              disabled={isStreaming || !inputValue.trim()}
              className="p-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold transition shadow-xs disabled:opacity-40"
            >
              {isStreaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </form>

          <p className="text-[10px] text-slate-400 text-center mt-2">
            AI can make mistakes. Always review suggested replies before posting.
          </p>
        </div>
      </div>
    </>
  );
};

export default AskAIDrawer;
