import { useState, useEffect } from 'react';
import MessageList from '../components/MessageList';
import MessageInput from '../components/MessageInput';
import DocumentUploader from '../components/DocumentUploader';
import SessionManager from '../components/SessionManager';
import SourceViewer from '../components/SourceViewer';
import { sendMessage, getSession } from '../utils/api';

const ChatPage = () => {
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sources, setSources] = useState([]);
  const [processedDocs, setProcessedDocs] = useState([]);

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
        setError('Failed to load session data');
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

  const handleSessionChange = (sessionId) => {
    setCurrentSessionId(sessionId);
    setSources([]);
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

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-center">Teacher Assistant</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          <SessionManager 
            currentSessionId={currentSessionId} 
            onSessionChange={handleSessionChange} 
          />
          
          <DocumentUploader 
            sessionId={currentSessionId}
            onDocumentProcessed={handleDocumentProcessed}
          />
          
          {processedDocs.length > 0 && (
            <div className="p-4 border rounded-lg bg-gray-50">
              <h3 className="text-lg font-medium mb-3">Processed Documents</h3>
              <ul className="max-h-40 overflow-y-auto">
                {processedDocs.map((doc, index) => (
                  <li key={index} className="flex items-center gap-1 text-sm py-1">
                    {doc.toLowerCase().endsWith('.pdf') ? (
                      <span>📄</span>
                    ) : doc.toLowerCase().match(/\.(png|jpg|jpeg|gif|webp)$/) ? (
                      <span>🖼️</span>
                    ) : (
                      <span>🌐</span>
                    )}
                    <span className="truncate">{doc}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        {/* Main Chat Area */}
        <div className="lg:col-span-3 flex flex-col bg-white border rounded-lg p-6 h-[calc(100vh-10rem)]">
          <div className="flex-grow overflow-y-auto">
            {loading && messages.length === 0 ? (
              <div className="flex justify-center items-center h-full">
                <p>Loading messages...</p>
              </div>
            ) : (
              <>
                <MessageList messages={messages} />
                {sources.length > 0 && <SourceViewer sources={sources} />}
              </>
            )}
            
            {error && (
              <div className="p-4 mt-4 bg-red-100 text-red-700 rounded-lg">
                {error}
              </div>
            )}
          </div>
          
          <MessageInput onSendMessage={handleSendMessage} isLoading={loading} />
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
