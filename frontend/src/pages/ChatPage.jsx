import { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  Send, AlertTriangle, Heart, LogOut, History,
  LayoutDashboard, Stethoscope, Pill, Activity, ChevronDown,
  Siren, UserRound, ThumbsUp, ThumbsDown, Menu, X, Trash2,
  Shield, ChevronRight, Plus, MessageSquare, Pencil, Check
} from 'lucide-react';

const URGENCY_CONFIG = {
  emergency: { color: 'bg-red-100 text-red-800 border-red-200', icon: '🚨', label: 'Emergency' },
  high:      { color: 'bg-orange-100 text-orange-800 border-orange-200', icon: '⚠️', label: 'High' },
  medium:    { color: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: '🔔', label: 'Medium' },
  low:       { color: 'bg-green-100 text-green-800 border-green-200', icon: '✅', label: 'Low' },
};

const INTENT_COLORS = {
  disease_prediction: 'bg-blue-100 text-blue-800 border-blue-200',
  general_query: 'bg-gray-100 text-gray-700 border-gray-200',
};

const welcomeMessage = (name) => ({
  sender: 'bot',
  text: `Hello${name ? ', ' + name.split(' ')[0] : ''}! I'm your AI Healthcare Assistant. I can help with symptoms, medications, chronic diseases, emergency guidance, and more.\n\nHow can I help you today?`,
  timestamp: new Date(),
});

export default function ChatPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Conversation state
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([welcomeMessage(user?.full_name)]);

  // UI state
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [expandedDescriptions, setExpandedDescriptions] = useState({});
  const [editingConvId, setEditingConvId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const messagesEndRef = useRef(null);

  const toggleDescription = (idx) => {
    setExpandedDescriptions(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  // ── Load conversations list ───────────────────────────
  const loadConversations = useCallback(() => {
    api.get('/api/chat/conversations?limit=30')
      .then((res) => setConversations(res.data.conversations || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── Load a conversation's messages ─────────────────────
  const loadConversation = async (convId) => {
    setActiveConvId(convId);
    setExpandedDescriptions({});
    try {
      const res = await api.get(`/api/chat/conversations/${convId}`);
      const msgs = res.data.messages || [];

      // Rebuild messages array: welcome + pairs of user/bot messages
      const chatMessages = [welcomeMessage(user?.full_name)];
      msgs.forEach((m) => {
        // User message
        chatMessages.push({
          sender: 'user',
          text: m.query_text,
          timestamp: new Date(m.created_at),
        });
        // Bot response
        chatMessages.push({
          sender: 'bot',
          text: m.response_text,
          intent: m.intent,
          confidence: m.confidence,
          category: m.category,
          recommendations: m.recommendations,
          entities: m.entities_extracted,
          query_id: m._id,
          timestamp: new Date(m.created_at),
        });
      });

      setMessages(chatMessages);
    } catch (err) {
      console.error('Error loading conversation:', err);
    }

    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  };

  // ── New Chat ───────────────────────────────────────────
  const handleNewChat = () => {
    setActiveConvId(null);
    setMessages([welcomeMessage(user?.full_name)]);
    setExpandedDescriptions({});
    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  };

  // ── Send Message ───────────────────────────────────────
  const handleSend = async (e) => {
    if (e) e.preventDefault();
    const query = input.trim();
    if (!query || query.length > 500 || loading) return;

    setMessages((prev) => [...prev, { sender: 'user', text: query, timestamp: new Date() }]);
    setInput('');
    setLoading(true);

    try {
      const payload = { user_query: query };
      if (activeConvId) {
        payload.conversation_id = activeConvId;
      }

      const res = await api.post('/api/chat/query', payload);
      const d = res.data;

      // If a new conversation was auto-created, update state
      if (d.new_conversation && d.conversation_id) {
        setActiveConvId(d.conversation_id);
        loadConversations(); // Refresh sidebar
      } else if (d.conversation_id && !d.new_conversation) {
        // Update existing conversation in sidebar (updated_at changed)
        loadConversations();
      }

      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: d.response,
          intent: d.intent,
          confidence: d.confidence,
          category: d.category,
          recommendations: d.recommendations,
          entities: d.entities,
          query_id: d.query_id,
          timestamp: new Date(),
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: 'Sorry, I encountered an error connecting to the server. Please try again.',
          isError: true,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // ── Feedback ───────────────────────────────────────────
  const handleFeedback = async (queryId, feedback) => {
    try {
      await api.post('/api/chat/feedback', { query_id: queryId, feedback });
    } catch {}
  };

  // ── Delete Conversation ────────────────────────────────
  const handleDeleteConv = async (e, convId) => {
    e.stopPropagation();
    try {
      await api.delete(`/api/chat/conversations/${convId}`);
      setConversations(prev => prev.filter(c => c._id !== convId));
      // If deleting the active conversation, reset to new chat
      if (activeConvId === convId) {
        handleNewChat();
      }
    } catch (err) {
      console.error('Error deleting conversation:', err);
    }
  };

  // ── Rename Conversation ────────────────────────────────
  const handleStartRename = (e, conv) => {
    e.stopPropagation();
    setEditingConvId(conv._id);
    setEditTitle(conv.title);
  };

  const handleSaveRename = async (e, convId) => {
    e.stopPropagation();
    if (editTitle.trim()) {
      try {
        await api.patch(`/api/chat/conversations/${convId}`, { title: editTitle.trim() });
        setConversations(prev =>
          prev.map(c => c._id === convId ? { ...c, title: editTitle.trim() } : c)
        );
      } catch (err) {
        console.error('Error renaming:', err);
      }
    }
    setEditingConvId(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-gray-50" style={{ fontFamily: "'Inter', sans-serif" }}>
      {/* ── Sidebar ──────────────────────────────────────── */}
      <div className={`
        fixed inset-y-0 left-0 z-30 w-72 bg-white border-r border-gray-200 flex flex-col
        transform transition-transform duration-300 ease-in-out
        md:relative md:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Sidebar Header */}
        <div className="p-5 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-md">
              <Heart className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="font-bold text-gray-900">HealthBot</h2>
              <p className="text-xs text-gray-400">AI Medical Assistant</p>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="ml-auto md:hidden p-1 text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl border border-gray-200 text-gray-700 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200 transition-all text-sm font-medium"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>

        {/* Nav Links */}
        <nav className="px-3 space-y-1">
          <Link to="/chat"
            className="flex items-center gap-3 px-4 py-2.5 rounded-xl bg-blue-50 text-blue-700 font-medium text-sm">
            <Stethoscope className="w-4 h-4" /> Chat
          </Link>
          <Link to="/history"
            className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-gray-600 hover:bg-gray-50 text-sm transition-colors">
            <History className="w-4 h-4" /> History
          </Link>
          <Link to="/dashboard"
            className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-gray-600 hover:bg-gray-50 text-sm transition-colors">
            <LayoutDashboard className="w-4 h-4" /> Dashboard
          </Link>
        </nav>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto px-3 py-3">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2 px-1">
            Conversations
          </h3>
          {conversations.length === 0 && (
            <p className="text-xs text-gray-400 italic px-1">No conversations yet</p>
          )}
          <div className="space-y-0.5">
            {conversations.map((conv) => (
              <div
                key={conv._id}
                className={`group flex items-center relative w-full rounded-lg transition-colors ${
                  activeConvId === conv._id
                    ? 'bg-blue-50 text-blue-700'
                    : 'hover:bg-gray-50 text-gray-600'
                }`}
              >
                {editingConvId === conv._id ? (
                  /* Inline rename input */
                  <div className="flex items-center w-full px-2 py-1.5 gap-1">
                    <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 text-gray-400" />
                    <input
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') handleSaveRename(e, conv._id); }}
                      className="flex-1 text-xs bg-white border border-blue-300 rounded px-1.5 py-1 focus:outline-none focus:ring-1 focus:ring-blue-400"
                      autoFocus
                      onClick={(e) => e.stopPropagation()}
                    />
                    <button
                      onClick={(e) => handleSaveRename(e, conv._id)}
                      className="p-1 text-blue-600 hover:bg-blue-100 rounded"
                    >
                      <Check className="w-3 h-3" />
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      onClick={() => loadConversation(conv._id)}
                      className="w-full text-left pl-2 pr-16 py-2 text-xs truncate flex items-center gap-2"
                      title={conv.title}
                    >
                      <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 opacity-60" />
                      <span className="truncate">{conv.title}</span>
                    </button>
                    {/* Action buttons (show on hover) */}
                    <div className="absolute right-1 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => handleStartRename(e, conv)}
                        className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                        title="Rename"
                      >
                        <Pencil className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => handleDeleteConv(e, conv._id)}
                        className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* User Section */}
        <div className="p-4 border-t border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center text-white text-sm font-semibold">
              {user?.full_name?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">{user?.full_name || 'User'}</p>
              <p className="text-xs text-gray-400 truncate">{user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Main Chat Area ───────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile Header */}
        <div className="md:hidden flex items-center gap-3 p-4 bg-white border-b border-gray-200">
          <button onClick={() => setSidebarOpen(true)} className="p-1.5 text-gray-500">
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <Heart className="w-5 h-5 text-blue-600" />
            <span className="font-bold text-gray-900">HealthBot</span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-5">
          {messages.map((msg, idx) => {
            const isUser = msg.sender === 'user';
            const isEmergency = msg.intent === 'emergency_urgent' || msg.recommendations?.emergency;
            const urgency = msg.recommendations?.urgency || 'low';
            const urgencyConfig = URGENCY_CONFIG[urgency] || URGENCY_CONFIG.low;
            const matchedSymptoms = msg.entities?.matched_symptoms || [];
            const description = msg.entities?.description || '';
            const specialist = msg.recommendations?.specialist;
            const precautions = msg.recommendations?.home_remedies || [];
            const isDiseaseResult = msg.intent === 'disease_prediction';

            return (
              <div key={idx} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                {/* Avatar for bot */}
                {!isUser && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center mr-3 mt-1 flex-shrink-0">
                    <Heart className="w-4 h-4 text-white" />
                  </div>
                )}

                <div className={`max-w-[80%] md:max-w-[65%] ${isUser ? '' : ''}`}>
                  {/* Intent Badge & Metadata */}
                  {!isUser && msg.intent && (
                    <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                      {/* Disease / Category Badge */}
                      <span className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-medium border ${INTENT_COLORS[msg.intent] || INTENT_COLORS.general_query}`}>
                        <Stethoscope className="w-3 h-3" />
                        {msg.category}
                      </span>

                      {/* Confidence */}
                      {msg.confidence != null && (
                        <span className="text-xs text-gray-400">
                          {Math.round(msg.confidence * 100)}% confidence
                        </span>
                      )}

                      {/* Urgency Badge */}
                      {isDiseaseResult && (
                        <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium border ${urgencyConfig.color}`}>
                          {urgencyConfig.icon} {urgencyConfig.label}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Matched Symptoms Tags */}
                  {!isUser && isDiseaseResult && matchedSymptoms.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                      {matchedSymptoms.map((s, si) => (
                        <span key={si} className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600 border border-indigo-100 font-medium">
                          {s}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Message Bubble */}
                  <div
                    className={`rounded-2xl px-4 py-3 shadow-sm ${
                      isUser
                        ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-br-md'
                        : isEmergency
                          ? 'bg-red-50 border-2 border-red-200 text-red-900 rounded-bl-md'
                          : msg.isError
                            ? 'bg-red-50 border border-red-200 text-red-700 rounded-bl-md'
                            : 'bg-white border border-gray-200 text-gray-800 rounded-bl-md'
                    }`}
                  >
                    {isEmergency && !isUser && (
                      <div className="flex items-center gap-2 mb-2 text-red-700 font-semibold text-sm">
                        <AlertTriangle className="w-4 h-4 animate-pulse" />
                        EMERGENCY — Seek Immediate Help
                      </div>
                    )}

                    <p className="text-sm leading-relaxed whitespace-pre-line">{msg.text}</p>
                  </div>

                  {/* Rich Recommendations (bot messages only) */}
                  {!isUser && msg.recommendations && (
                    <div className="mt-2 space-y-2">

                      {/* Precautions / Home Remedies */}
                      {isDiseaseResult && precautions.length > 0 && (
                        <div className="bg-emerald-50 border border-emerald-100 rounded-xl px-3 py-2">
                          <p className="text-xs font-semibold text-emerald-700 mb-1 flex items-center gap-1">
                            <Shield className="w-3 h-3" /> Recommended Precautions
                          </p>
                          <ul className="space-y-0.5">
                            {precautions.map((p, pi) => (
                              <li key={pi} className="text-xs text-emerald-800 flex items-start gap-1.5">
                                <span className="mt-0.5 text-emerald-500">•</span>
                                <span>{typeof p === 'string' ? p.charAt(0).toUpperCase() + p.slice(1) : p}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Specialist Recommendation */}
                      {isDiseaseResult && specialist && (
                        <div className="bg-blue-50 border border-blue-100 rounded-xl px-3 py-2 flex items-center gap-2">
                          <Stethoscope className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" />
                          <p className="text-xs text-blue-800">
                            <span className="font-semibold">Recommended Specialist:</span> {specialist}
                          </p>
                        </div>
                      )}

                      {/* Expandable Disease Description */}
                      {isDiseaseResult && description && (
                        <button
                          onClick={() => toggleDescription(idx)}
                          className="w-full text-left bg-gray-50 border border-gray-100 rounded-xl px-3 py-2 hover:bg-gray-100 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-gray-600">About {msg.category}</span>
                            <ChevronRight className={`w-3.5 h-3.5 text-gray-400 transition-transform ${expandedDescriptions[idx] ? 'rotate-90' : ''}`} />
                          </div>
                          {expandedDescriptions[idx] && (
                            <p className="text-xs text-gray-600 mt-1.5 leading-relaxed">{description}</p>
                          )}
                        </button>
                      )}

                      {/* Feedback */}
                      {msg.query_id && (
                        <div className="flex items-center gap-2 pt-1">
                          <span className="text-xs text-gray-400">Helpful?</span>
                          <button
                            onClick={() => handleFeedback(msg.query_id, 'helpful')}
                            className="p-1 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
                          >
                            <ThumbsUp className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleFeedback(msg.query_id, 'not_helpful')}
                            className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                          >
                            <ThumbsDown className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Avatar for user */}
                {isUser && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center ml-3 mt-1 flex-shrink-0 text-gray-600 text-sm font-semibold">
                    {user?.full_name?.[0]?.toUpperCase() || 'U'}
                  </div>
                )}
              </div>
            );
          })}

          {/* Typing indicator */}
          {loading && (
            <div className="flex justify-start">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center mr-3 flex-shrink-0">
                <Heart className="w-4 h-4 text-white" />
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 p-4">
          <form onSubmit={handleSend} className="max-w-3xl mx-auto">
            <div className="flex items-end gap-3">
              <div className="flex-1 relative">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={loading}
                  maxLength={500}
                  rows={1}
                  placeholder="Describe your symptoms or ask a medical question..."
                  className="w-full resize-none bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 pr-14 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-sm max-h-32"
                />
                <span className="absolute right-3 bottom-3 text-xs text-gray-400 font-mono pointer-events-none">
                  {input.length}/500
                </span>
              </div>
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="h-[46px] px-5 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl hover:from-blue-600 hover:to-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg active:scale-95 flex items-center justify-center"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <p className="text-center text-xs text-gray-400 mt-2">
              Press Enter to send • For informational purposes only — not medical advice
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
