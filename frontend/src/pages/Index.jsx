import React, { useState, useEffect } from 'react';
import MessageList from '../components/MessageList';
import MessageInput from '../components/MessageInput';
import SourceViewer from '../components/SourceViewer';
import AttachModal from '../components/AttachModal';
import SessionDrawer from '../components/SessionDrawer';
import { sendMessage, getSession } from '../utils/api';
import { Menu, FileText, Image, Globe, Bot, Sparkles } from 'lucide-react';

const Index = () => {
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sources, setSources] = useState([]);
  const [processedDocs, setProcessedDocs] = useState([]);
  const [isAttachModalOpen, setIsAttachModalOpen] = useState(false);
  const [isSessionDrawerOpen, setIsSessionDrawerOpen] = useState(false);

  // Load session data when session changes
  useEffect(() => {
    const loadSession = async () => {
      if (!currentSessionId) return;
      
      setLoading(true);
      try {
        const sessionData = await getSession(currentSessionId);
        setMessages(sessionData.history || []);
        setProcessedDocs(sessionData.processed_documents || []);
      } catch (err) {
        console.error('Failed to load session:', err);
        setError('Failed to load chat data');
      } finally {
        setLoading(false);
      }
    };

    loadSession();
  }, [currentSessionId]);

  const handleSendMessage = async (content, forceWebSearch) => {
    if (!content.trim()) return;

    // Optimistically add user message
    const userMessage = { role: 'user', content };
    setMessages(prev => [...prev, userMessage]);
    
    setLoading(true);
    setError('');
    
    try {
      const response = await sendMessage(content, currentSessionId, forceWebSearch);
      
      // Add assistant response
      const assistantMessage = { role: 'assistant', content: response.content };
      setMessages(prev => [...prev, assistantMessage]);
      
      // Update sources display
      setSources(response.sources || []);
      
      // Update session ID if it was created during this request
      if (response.session_id && (!currentSessionId || currentSessionId !== response.session_id)) {
        setCurrentSessionId(response.session_id);
      }
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to get response. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentProcessed = (result) => {
    if (result && result.success && result.session_id) {
      // If a new session was created, switch to it
      if (!currentSessionId) {
        setCurrentSessionId(result.session_id);
      }
      
      // Update processed documents list
      setProcessedDocs(prev => {
        const newDocs = Array.isArray(result.sources) ? result.sources : [];
        return [...new Set([...prev, ...newDocs])];
      });
    }
  };

  const showWelcomeScreen = messages.length === 0;

  return (
    <div className="flex h-screen overflow-hidden bg-gradient-to-b from-background to-background/95 text-foreground">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full">
        {/* Header */}
        <header className="glass-effect border-b border-white/10 sticky top-0 z-10 shadow-md">
          <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
            <div className="w-8" /> {/* Spacer for alignment */}
            <h1 className="text-xl font-semibold flex items-center gap-2">
              <Bot className="text-violet-400" size={20} />
              <span>Teacher Assistant</span>
            </h1>
            <button 
              onClick={() => setIsSessionDrawerOpen(true)}
              className="p-2.5 hover:bg-white/5 rounded-lg transition-colors flex items-center gap-2 text-sm"
              aria-label="Open chats"
            >
              <Menu size={18} />
              <span className="hidden sm:inline-block">Conversations</span>
            </button>
          </div>
        </header>

        {/* Messages or Welcome Screen */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-muted">
          {showWelcomeScreen ? (
            <div className="h-full flex flex-col items-center justify-center text-center px-4 animate-fade-in">
              <div className="w-20 h-20 bg-primary/20 rounded-2xl flex items-center justify-center mb-8 shadow-lg">
                <Sparkles className="text-primary-foreground w-10 h-10" />
              </div>
              <h2 className="text-3xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-primary-foreground to-violet-400">How can I help you today?</h2>
              <p className="text-muted-foreground max-w-lg mb-8 text-lg leading-relaxed">
                Ask questions about your documents or any topic. You can upload files or share URLs to get more precise answers.
              </p>
              <div className="max-w-3xl w-full">
                <MessageInput 
                  onSendMessage={handleSendMessage} 
                  isLoading={loading}
                  onAttach={() => setIsAttachModalOpen(true)}
                />
              </div>
            </div>
          ) : (
            <div className="max-w-6xl mx-auto">
              <MessageList messages={messages} />
              
              {sources.length > 0 && <SourceViewer sources={sources} />}
              
              {error && (
                <div className="mt-4 p-5 bg-destructive/10 border border-destructive/20 text-destructive rounded-xl max-w-3xl mx-auto shadow-lg">
                  {error}
                </div>
              )}
              
              {/* Processed Documents Info */}
              {processedDocs.length > 0 && (
                <div className="mt-8 p-5 glass-effect rounded-2xl max-w-3xl mx-auto shadow-lg">
                  <h3 className="text-base font-medium mb-4 flex items-center">
                    <span className="bg-primary/20 p-1.5 rounded-md mr-2">
                      <FileText size={16} className="text-primary-foreground" />
                    </span>
                    Processed Documents
                  </h3>
                  <div className="max-h-40 overflow-y-auto scrollbar-thin">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {processedDocs.map((doc, index) => (
                        <div 
                          key={index} 
                          className="flex items-center gap-2 p-3 bg-background/30 rounded-xl border border-white/5 text-sm hover:bg-background/50 transition-colors"
                        >
                          {doc.toLowerCase().endsWith('.pdf') ? (
                            <FileText size={14} className="text-amber-400" />
                          ) : doc.toLowerCase().match(/\.(png|jpg|jpeg|gif|webp)$/) ? (
                            <Image size={14} className="text-emerald-400" />
                          ) : (
                            <Globe size={14} className="text-blue-400" />
                          )}
                          <span className="truncate">{doc}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Input Area - Only show if not on welcome screen or we're already showing it there */}
        {!showWelcomeScreen && (
          <div className="border-t border-white/10 p-4 md:p-6 glass-effect shadow-lg">
            <div className="max-w-3xl mx-auto">
              <MessageInput 
                onSendMessage={handleSendMessage} 
                isLoading={loading}
                onAttach={() => setIsAttachModalOpen(true)}
              />
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <AttachModal 
        isOpen={isAttachModalOpen} 
        onClose={() => setIsAttachModalOpen(false)}
        sessionId={currentSessionId}
        onDocumentProcessed={handleDocumentProcessed}
      />

      {/* Session Drawer */}
      <SessionDrawer
        isOpen={isSessionDrawerOpen}
        onClose={() => setIsSessionDrawerOpen(false)}
        currentSessionId={currentSessionId}
        onSessionChange={setCurrentSessionId}
      />
    </div>
  );
};

export default Index;
