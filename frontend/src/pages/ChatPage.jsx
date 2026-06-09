import { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  Send, AlertTriangle, Heart, LogOut, History,
  LayoutDashboard, Stethoscope, Menu, X, Trash2,
  Shield, ChevronRight, Plus, MessageSquare, Pencil, Check
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

const URGENCY_CONFIG = {
  emergency: { variant: 'destructive', icon: '🚨', label: 'Emergency' },
  high:      { variant: 'destructive', icon: '⚠️', label: 'High' },
  medium:    { variant: 'secondary', icon: '🔔', label: 'Medium' },
  low:       { variant: 'outline', icon: '✅', label: 'Low' },
};

const welcomeMessage = (name) => ({
  sender: 'bot',
  text: `Hello${name ? ', ' + name.split(' ')[0] : ''}! I'm your AI Healthcare Assistant. I can help with symptoms, medications, chronic diseases, emergency guidance, and more.\n\nHow can I help you today?`,
  timestamp: new Date(),
});

export default function ChatPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([welcomeMessage(user?.full_name)]);

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

  const loadConversations = useCallback(() => {
    api.get('/api/chat/conversations?limit=30')
      .then((res) => setConversations(res.data.conversations || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversation = async (convId) => {
    setActiveConvId(convId);
    setExpandedDescriptions({});
    try {
      const res = await api.get(`/api/chat/conversations/${convId}`);
      const msgs = res.data.messages || [];

      const chatMessages = [welcomeMessage(user?.full_name)];
      msgs.forEach((m) => {
        chatMessages.push({
          sender: 'user',
          text: m.query_text,
          timestamp: new Date(m.created_at),
        });
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

  const handleNewChat = () => {
    setActiveConvId(null);
    setMessages([welcomeMessage(user?.full_name)]);
    setExpandedDescriptions({});
    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  };

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

      if (d.new_conversation && d.conversation_id) {
        setActiveConvId(d.conversation_id);
        loadConversations(); 
      } else if (d.conversation_id && !d.new_conversation) {
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

  const handleDeleteConv = async (e, convId) => {
    e.stopPropagation();
    try {
      await api.delete(`/api/chat/conversations/${convId}`);
      setConversations(prev => prev.filter(c => c._id !== convId));
      if (activeConvId === convId) {
        handleNewChat();
      }
    } catch (err) {
      console.error('Error deleting conversation:', err);
    }
  };

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
    <div className="flex h-screen bg-background">
      {/* ── Sidebar ──────────────────────────────────────── */}
      <div className={`
        fixed inset-y-0 left-0 z-30 w-72 bg-card border-r flex flex-col
        transform transition-transform duration-300 ease-in-out
        md:relative md:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Sidebar Header */}
        <div className="p-5 border-b">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-primary-foreground shadow-md">
              <Heart className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-foreground">HealthBot</h2>
              <p className="text-xs text-muted-foreground">AI Medical Assistant</p>
            </div>
            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(false)} className="ml-auto md:hidden">
              <X className="w-5 h-5" />
            </Button>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <Button onClick={handleNewChat} variant="outline" className="w-full justify-start gap-2">
            <Plus className="w-4 h-4" />
            New Chat
          </Button>
        </div>

        {/* Nav Links */}
        <nav className="px-3 space-y-1">
          <Button asChild variant="secondary" className="w-full justify-start gap-3">
            <Link to="/chat"><Stethoscope className="w-4 h-4" /> Chat</Link>
          </Button>
          <Button asChild variant="ghost" className="w-full justify-start gap-3 text-muted-foreground">
            <Link to="/history"><History className="w-4 h-4" /> History</Link>
          </Button>
          <Button asChild variant="ghost" className="w-full justify-start gap-3 text-muted-foreground">
            <Link to="/dashboard"><LayoutDashboard className="w-4 h-4" /> Dashboard</Link>
          </Button>
        </nav>

        {/* Conversations List */}
        <ScrollArea className="flex-1 px-3 py-3">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-1">
            Conversations
          </h3>
          {conversations.length === 0 && (
            <p className="text-xs text-muted-foreground italic px-1">No conversations yet</p>
          )}
          <div className="space-y-1">
            {conversations.map((conv) => (
              <div
                key={conv._id}
                className={`group flex items-center relative w-full rounded-md transition-colors ${
                  activeConvId === conv._id
                    ? 'bg-secondary text-secondary-foreground'
                    : 'hover:bg-muted text-muted-foreground'
                }`}
              >
                {editingConvId === conv._id ? (
                  <div className="flex items-center w-full px-2 py-1 gap-1">
                    <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
                    <Input
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') handleSaveRename(e, conv._id); }}
                      className="h-6 text-xs px-2"
                      autoFocus
                      onClick={(e) => e.stopPropagation()}
                    />
                    <Button variant="ghost" size="icon" className="h-6 w-6" onClick={(e) => handleSaveRename(e, conv._id)}>
                      <Check className="w-3 h-3" />
                    </Button>
                  </div>
                ) : (
                  <>
                    <button
                      onClick={() => loadConversation(conv._id)}
                      className="w-full text-left pl-2 pr-16 py-2 text-sm truncate flex items-center gap-2"
                    >
                      <MessageSquare className="w-4 h-4 flex-shrink-0 opacity-70" />
                      <span className="truncate">{conv.title}</span>
                    </button>
                    <div className="absolute right-1 flex items-center gap-0.5 opacity-0 group-hover:opacity-100">
                      <Button variant="ghost" size="icon" className="h-6 w-6" onClick={(e) => handleStartRename(e, conv)}>
                        <Pencil className="w-3 h-3" />
                      </Button>
                      <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive hover:bg-destructive/10" onClick={(e) => handleDeleteConv(e, conv._id)}>
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>

        {/* User Section */}
        <div className="p-4 border-t">
          <div className="flex items-center gap-3">
            <Avatar className="h-9 w-9">
              <AvatarFallback className="bg-primary/10 text-primary font-medium">
                {user?.full_name?.[0]?.toUpperCase() || 'U'}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.full_name || 'User'}</p>
              <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
            </div>
            <Button variant="ghost" size="icon" onClick={handleLogout} className="text-muted-foreground hover:text-destructive hover:bg-destructive/10">
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Main Chat Area ───────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        <div className="md:hidden flex items-center gap-3 p-4 border-b bg-card">
          <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(true)}>
            <Menu className="w-5 h-5" />
          </Button>
          <div className="flex items-center gap-2">
            <Heart className="w-5 h-5 text-primary" />
            <span className="font-bold">HealthBot</span>
          </div>
        </div>

        <ScrollArea className="flex-1 px-4 py-6">
          <div className="max-w-3xl mx-auto space-y-6">
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
                  {!isUser && (
                    <Avatar className="h-8 w-8 mr-3 mt-1 shadow-sm">
                      <AvatarFallback className="bg-primary text-primary-foreground">
                        <Heart className="w-4 h-4" />
                      </AvatarFallback>
                    </Avatar>
                  )}

                  <div className={`max-w-[85%] md:max-w-[75%]`}>
                    {!isUser && msg.intent && (
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <Badge variant="outline" className="gap-1 bg-card">
                          <Stethoscope className="w-3 h-3" />
                          {msg.category}
                        </Badge>
                        {msg.confidence != null && (
                          <span className="text-xs text-muted-foreground">
                            {Math.round(msg.confidence * 100)}% conf
                          </span>
                        )}
                        {isDiseaseResult && (
                          <Badge variant={urgencyConfig.variant} className="gap-1">
                            {urgencyConfig.icon} {urgencyConfig.label}
                          </Badge>
                        )}
                      </div>
                    )}

                    {!isUser && isDiseaseResult && matchedSymptoms.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-2">
                        {matchedSymptoms.map((s, si) => (
                          <Badge key={si} variant="secondary" className="text-[10px] uppercase">
                            {s}
                          </Badge>
                        ))}
                      </div>
                    )}

                    <div
                      className={`rounded-2xl px-4 py-3 shadow-sm text-sm whitespace-pre-line ${
                        isUser
                          ? 'bg-primary text-primary-foreground rounded-br-sm'
                          : isEmergency
                            ? 'bg-destructive/10 border border-destructive text-destructive-foreground rounded-bl-sm'
                            : msg.isError
                              ? 'bg-destructive/10 border border-destructive text-destructive-foreground rounded-bl-sm'
                              : 'bg-card border text-card-foreground rounded-bl-sm'
                      }`}
                    >
                      {isEmergency && !isUser && (
                        <div className="flex items-center gap-2 mb-2 text-destructive font-semibold">
                          <AlertTriangle className="w-4 h-4 animate-pulse" />
                          EMERGENCY — Seek Immediate Help
                        </div>
                      )}
                      {msg.text}
                    </div>

                    {!isUser && msg.recommendations && (
                      <div className="mt-2 space-y-2">
                        {isDiseaseResult && precautions.length > 0 && (
                          <div className="bg-muted rounded-xl px-3 py-2 text-sm border">
                            <p className="font-semibold mb-1 flex items-center gap-1.5 text-foreground">
                              <Shield className="w-3.5 h-3.5 text-primary" /> Recommended Precautions
                            </p>
                            <ul className="space-y-1">
                              {precautions.map((p, pi) => (
                                <li key={pi} className="flex items-start gap-2 text-muted-foreground">
                                  <span className="mt-1 w-1 h-1 rounded-full bg-primary flex-shrink-0" />
                                  <span>{typeof p === 'string' ? p.charAt(0).toUpperCase() + p.slice(1) : p}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {isDiseaseResult && (urgency === 'high' || urgency === 'emergency') && (
                          <div className="mt-2">
                            <Button
                              variant="destructive"
                              size="sm"
                              className="w-full gap-2 shadow-sm"
                              onClick={() => {
                                if (navigator.geolocation) {
                                  navigator.geolocation.getCurrentPosition(
                                    (position) => {
                                      const { latitude, longitude } = position.coords;
                                      window.open(`https://www.google.com/maps/search/hospitals/@${latitude},${longitude},14z`, '_blank');
                                    },
                                    () => {
                                      window.open('https://www.google.com/maps/search/hospitals+near+me', '_blank');
                                    }
                                  );
                                } else {
                                  window.open('https://www.google.com/maps/search/hospitals+near+me', '_blank');
                                }
                              }}
                            >
                              <Shield className="w-4 h-4" /> Find Nearby Hospitals
                            </Button>
                          </div>
                        )}

                        {isDiseaseResult && specialist && (
                          <div className="bg-primary/5 border border-primary/20 rounded-xl px-3 py-2 flex items-center gap-2 text-sm">
                            <Stethoscope className="w-4 h-4 text-primary flex-shrink-0" />
                            <p className="text-foreground">
                              <span className="font-semibold">Specialist:</span> {specialist}
                            </p>
                          </div>
                        )}

                        {isDiseaseResult && description && (
                          <button
                            onClick={() => toggleDescription(idx)}
                            className="w-full text-left bg-card border rounded-xl px-3 py-2 hover:bg-muted/50 transition-colors"
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-semibold text-foreground">About {msg.category}</span>
                              <ChevronRight className={`w-3.5 h-3.5 text-muted-foreground transition-transform ${expandedDescriptions[idx] ? 'rotate-90' : ''}`} />
                            </div>
                            {expandedDescriptions[idx] && (
                              <p className="text-xs text-muted-foreground mt-2 leading-relaxed">{description}</p>
                            )}
                          </button>
                        )}
                        
                        {msg.follow_up_question && (
                          <div className="bg-primary/10 border border-primary/20 rounded-xl px-3 py-3 mt-3">
                            <p className="font-semibold text-sm mb-1 flex items-center gap-1.5 text-primary">
                              <MessageSquare className="w-3.5 h-3.5" /> Follow-up Question
                            </p>
                            <p className="text-sm text-foreground leading-relaxed">{msg.follow_up_question}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {isUser && (
                    <Avatar className="h-8 w-8 ml-3 mt-1 shadow-sm">
                      <AvatarFallback className="bg-muted text-muted-foreground font-semibold">
                        {user?.full_name?.[0]?.toUpperCase() || 'U'}
                      </AvatarFallback>
                    </Avatar>
                  )}
                </div>
              );
            })}

            {loading && (
              <div className="flex justify-start">
                <Avatar className="h-8 w-8 mr-3 mt-1 shadow-sm">
                  <AvatarFallback className="bg-primary text-primary-foreground">
                    <Heart className="w-4 h-4" />
                  </AvatarFallback>
                </Avatar>
                <div className="bg-card border rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-primary/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        </ScrollArea>

        <div className="bg-card border-t p-4 shadow-[0_-4px_20px_-15px_rgba(0,0,0,0.1)] z-10">
          <form onSubmit={handleSend} className="max-w-3xl mx-auto flex items-end gap-3">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              maxLength={500}
              placeholder="Describe your symptoms or ask a medical question..."
              className="resize-none flex-1 min-h-[44px] max-h-32 bg-background focus-visible:ring-1"
              rows={1}
            />
            <Button type="submit" disabled={loading || !input.trim()} size="icon" className="h-11 w-11 flex-shrink-0">
              <Send className="w-5 h-5" />
            </Button>
          </form>
          <p className="text-center text-[11px] text-muted-foreground mt-2">
            For informational purposes only — not medical advice.
          </p>
        </div>
      </div>
    </div>
  );
}
