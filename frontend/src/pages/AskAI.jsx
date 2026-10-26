import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, 
  Send, 
  Loader2, 
  Copy, 
  Check, 
  Mic, 
  MicOff, 
  RefreshCw, 
  Bot, 
  User, 
  Trash2, 
  MessageSquare,
  AlertCircle,
  HelpCircle,
  Plus
} from 'lucide-react';
import { assistantAPI } from '../services/api';
import { useBrand } from '../context/BrandContext';

const AskAI = () => {
  const { activeBrand } = useBrand();
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, activeTool]);

  // Load conversations and suggestions
  useEffect(() => {
    if (!activeBrand?.id) return;

    const loadData = async () => {
      try {
        const [convRes, suggRes] = await Promise.all([
          assistantAPI.getConversations(activeBrand.id),
          assistantAPI.getSuggestedQuestions(activeBrand.id)
        ]);
        setConversations(convRes.data || []);
        setSuggestedQuestions(suggRes.data?.questions || []);

        if (convRes.data && convRes.data.length > 0) {
          selectConversation(convRes.data[0].id);
        } else {
          startNewChat();
        }
      } catch (err) {
        console.warn('Failed to load assistant data:', err);
      }
    };
    loadData();
  }, [activeBrand?.id]);

  const selectConversation = async (convId) => {
    setActiveConvId(convId);
    setErrorMessage('');
    try {
      const res = await assistantAPI.getConversation(convId);
      setMessages(res.data?.messages || []);
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  };

  const startNewChat = () => {
    setActiveConvId(null);
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: `Hello! I am your AI Business Advisor for ${activeBrand?.name || 'your shop'}. Ask me questions about customer complaints, praise, rating trends, or how to reply to reviews!`
      }
    ]);
  };

  const deleteConversation = async (convId, e) => {
    e.stopPropagation();
    try {
      await assistantAPI.deleteConversation(convId);
      setConversations(prev => prev.filter(c => c.id !== convId));
      if (activeConvId === convId) {
        startNewChat();
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  const handleSend = async (textToSend) => {
    const query = (textToSend || inputValue).trim();
    if (!query || isStreaming || !activeBrand?.id) return;

    setInputValue('');
    setErrorMessage('');
    const userMsgId = `user_${Date.now()}`;
    const assistantMsgId = `asst_${Date.now()}`;

    setMessages(prev => [
      ...prev,
      { id: userMsgId, role: 'user', content: query },
      { id: assistantMsgId, role: 'assistant', content: '' }
    ]);

    setIsStreaming(true);
    setActiveTool('Analyzing business data...');
    let assistantText = '';

    await assistantAPI.streamChat({
      businessId: activeBrand.id,
      message: query,
      conversationId: activeConvId,
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
      onDone: (doneData) => {
        setIsStreaming(false);
        setActiveTool(null);
        if (doneData?.conversation_id) {
          setActiveConvId(doneData.conversation_id);
          // Refresh list
          assistantAPI.getConversations(activeBrand.id).then(res => setConversations(res.data || []));
        }
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

  return (
    <div className="space-y-4 max-w-7xl pb-8 animate-fade-in">
      {/* Top Header Card */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center shadow-xs">
            <Sparkles className="w-5 h-5 text-amber-300" />
          </div>
          <div>
            <h1 className="text-lg sm:text-xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
              <span>Ask AI Advisor</span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 font-bold border border-blue-200">
                {activeBrand?.name || 'Local Business'}
              </span>
            </h1>
            <p className="text-xs text-slate-500">
              Direct, trustworthy answers grounded in your customers' real reviews and ratings.
            </p>
          </div>
        </div>

        {/* Language Selector */}
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-500 font-medium">Language:</span>
          <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
            <button
              onClick={() => setLanguage('en')}
              className={`px-3 py-1 rounded-lg transition ${language === 'en' ? 'bg-white text-blue-600 shadow-xs' : 'text-slate-600'}`}
            >
              English
            </button>
            <button
              onClick={() => setLanguage('ta')}
              className={`px-3 py-1 rounded-lg transition ${language === 'ta' ? 'bg-white text-blue-600 shadow-xs' : 'text-slate-600'}`}
            >
              தமிழ்
            </button>
            <button
              onClick={() => setLanguage('hi')}
              className={`px-3 py-1 rounded-lg transition ${language === 'hi' ? 'bg-white text-blue-600 shadow-xs' : 'text-slate-600'}`}
            >
              हिन्दी
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid: Sidebar + Chat Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 h-[calc(100vh-220px)] min-h-[500px]">
        {/* Left Sidebar: Conversations History (3 cols) */}
        <div className="hidden lg:flex lg:col-span-3 flex-col bg-white rounded-2xl border border-slate-200 shadow-sm p-4 overflow-hidden">
          <button
            onClick={startNewChat}
            className="w-full py-2.5 px-3 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-700 font-bold text-xs flex items-center justify-center space-x-2 transition mb-3 border border-blue-200"
          >
            <Plus className="w-4 h-4" />
            <span>New Conversation</span>
          </button>

          <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2 px-1">
            Recent Conversations
          </h3>

          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
            {conversations.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-6">No previous chats yet</p>
            ) : (
              conversations.map((c) => (
                <div
                  key={c.id}
                  onClick={() => selectConversation(c.id)}
                  className={`w-full text-left p-2.5 rounded-xl text-xs flex items-center justify-between group cursor-pointer transition ${
                    activeConvId === c.id
                      ? 'bg-blue-600 text-white font-semibold'
                      : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <div className="flex items-center space-x-2 truncate">
                    <MessageSquare className="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span className="truncate">{c.title || 'Conversation'}</span>
                  </div>
                  <button
                    onClick={(e) => deleteConversation(c.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Chat Panel (9 cols) */}
        <div className="lg:col-span-9 flex flex-col bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 text-xs">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex items-start space-x-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {m.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center shrink-0 mt-0.5 shadow-xs">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div className={`relative max-w-[80%] p-4 rounded-2xl leading-relaxed text-xs ${
                  m.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-xs font-medium'
                    : 'bg-slate-50 text-slate-800 rounded-bl-xs border border-slate-200/80 shadow-2xs'
                }`}>
                  <div className="whitespace-pre-wrap">{m.content}</div>

                  {m.role === 'assistant' && m.content && (
                    <div className="mt-3 pt-2.5 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-400">
                      <span>Verified from your customer feedback</span>
                      <button
                        onClick={() => copyToClipboard(m.content, m.id)}
                        className="flex items-center space-x-1 hover:text-slate-700 transition"
                      >
                        {copiedId === m.id ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-600" />
                            <span className="text-emerald-600 font-semibold">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            <span>Copy reply</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>

                {m.role === 'user' && (
                  <div className="w-8 h-8 rounded-xl bg-slate-800 text-white flex items-center justify-center shrink-0 mt-0.5">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}

            {activeTool && (
              <div className="flex items-center space-x-2 p-3 rounded-xl bg-blue-50 border border-blue-200 text-blue-700 text-xs animate-pulse">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{activeTool}</span>
              </div>
            )}

            {errorMessage && (
              <div className="p-3.5 rounded-xl bg-red-50 text-red-700 text-xs border border-red-200 flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{errorMessage}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Contextual Suggestions Chips */}
          {suggestedQuestions.length > 0 && (
            <div className="px-5 py-2.5 bg-slate-50 border-t border-slate-100 flex items-center space-x-2 overflow-x-auto no-scrollbar">
              <span className="text-[10px] text-slate-400 font-bold uppercase shrink-0">Suggestions:</span>
              {suggestedQuestions.map((q, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSend(q)}
                  disabled={isStreaming}
                  className="shrink-0 text-xs font-semibold px-3 py-1 bg-white hover:bg-blue-50 hover:text-blue-600 border border-slate-200 rounded-full text-slate-700 transition shadow-2xs disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Chat Input Bar */}
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
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-blue-600 focus:ring-1 focus:ring-blue-600 transition"
                />
              </div>

              <button
                type="submit"
                disabled={isStreaming || !inputValue.trim()}
                className="px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs transition shadow-xs flex items-center space-x-1.5 disabled:opacity-40"
              >
                {isStreaming ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>Send</span>
                  </>
                )}
              </button>
            </form>
            <p className="text-[10px] text-slate-400 text-center mt-2">
              AI can make mistakes. Always check and verify customer replies before sending.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AskAI;
