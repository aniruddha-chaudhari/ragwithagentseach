import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import MessageList from '../components/chatbot/MessageList';
import MessageInput from '../components/chatbot/MessageInput';
import SourceViewer from '../components/chatbot/SourceViewer';
import AttachModal from '../components/chatbot/AttachModal';
import Spinner from '../components/ui/Spinner';
import { sendMessage, getSession } from '../utils/api';
import { FileText, Image, Globe } from 'lucide-react';

const ChatPage = ({ currentSessionId, setCurrentSessionId }) => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sources, setSources] = useState([]);
  const [processedDocs, setProcessedDocs] = useState([]);
  const [isAttachModalOpen, setIsAttachModalOpen] = useState(false);
  const [baselineResponses, setBaselineResponses] = useState({});
  const [isDeepResearchActive, setIsDeepResearchActive] = useState(false);

  // Load session data when session changes
  useEffect(() => {
    const loadSession = async () => {
      if (!currentSessionId) return;
      
      setLoading(true);
      try {
        const sessionData = await getSession(currentSessionId);
        setMessages(sessionData.history || []);
        setProcessedDocs(sessionData.processed_documents || []);
        
 
        if (sessionData.baseline_responses) {
          console.log('Loaded baseline responses:', sessionData.baseline_responses);
          setBaselineResponses(sessionData.baseline_responses);
        } else {
          console.log('No baseline responses in session data');
        }
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
    const userMsgIndex = messages.length;
    const userMsgKey = `user_msg_${userMsgIndex}`;
    
    setMessages(prev => [...prev, userMessage]);
    
    setLoading(true);
    setError('');
    
    try {
      // Pass deep research flag if active
      const response = await sendMessage(content, currentSessionId, forceWebSearch, isDeepResearchActive);
      
      // Add assistant response
      const assistantMessage = { role: 'assistant', content: response.content };
      setMessages(prev => [...prev, assistantMessage]);
      
      // Check response structure in detail
      console.log('Response from API:', response);
      
      // Update baseline responses if available
      if (response.baseline_response) {
        console.log(`Setting baseline response for ${userMsgKey}:`, response.baseline_response);
        setBaselineResponses(prev => ({
          ...prev,
          [userMsgKey]: response.baseline_response
        }));
      } else {
        console.log('No baseline response in API response');
      }
      
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
    <div className="flex h-screen overflow-hidden bg-white text-gray-800">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full">
        {/* Header */}
        <header className="bg-gray-50 border-b border-gray-200 z-10">
          <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
            <div className="w-8" /> {/* Spacer for alignment */}
            
            <div className="flex items-center space-x-3">
              {/* Deep Research button */}
              {/* <button 
                onClick={() => navigate('/deep-research')}
                className="p-2 rounded-lg transition-colors cursor-pointer flex items-center gap-2 hover:bg-gray-100 text-gray-700"
                aria-label="Deep Research"
                title="Open Deep Research mode"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-gray-700">
                  <path d="M5.047 5.15c.122-.23.327-.39.732-.445.44-.06 1.072.02 1.884.31 1.613.576 3.67 1.885 5.746 3.834.403.378.792.768 1.156 1.156a.875.875 0 0 0 1.278-1.196 26.79 26.79 0 0 0-1.236-1.235C12.42 5.52 10.162 4.048 8.25 3.367c-.95-.34-1.883-.507-2.706-.396-.858.116-1.612.544-2.043 1.36-.374.701-.423 1.539-.301 2.37.123.842.434 1.762.88 2.704a.875.875 0 0 0 1.582-.75c-.398-.838-.64-1.588-.73-2.208-.093-.63-.019-1.046.113-1.293l.002-.004Zm10.298.512c.838-.398 1.588-.64 2.208-.73.63-.093 1.046-.019 1.293.113l.004.002c.23.122.39.327.445.732.06.44-.02 1.072-.31 1.884-.575 1.613-1.885 3.67-3.834 5.746-.378.403-.768.792-1.156 1.156a.875.875 0 0 0 1.196 1.278c.417-.39.833-.807 1.235-1.236 2.054-2.187 3.526-4.445 4.207-6.357.34-.95.508-1.883.396-2.706-.116-.858-.544-1.612-1.36-2.043-.701-.374-1.539-.423-2.37-.301-.842.123-1.762.434-2.704.881a.875.875 0 0 0 .75 1.581Zm-5.309 2.513a.875.875 0 0 1-.02 1.237c-.396.384-.789.776-1.166 1.178v.001c-1.95 2.076-3.26 4.133-3.835 5.746-.29.812-.37 1.445-.31 1.884.055.405.216.61.445.732.256.134.678.208 1.31.116.624-.092 1.378-.334 2.223-.732a.875.875 0 0 1 .746 1.583c-.948.446-1.87.757-2.716.88-.836.122-1.674.072-2.38-.3-.817-.431-1.246-1.186-1.362-2.044-.111-.823.056-1.755.396-2.707.681-1.911 2.153-4.17 4.207-6.356.402-.429.815-.842 1.225-1.238a.875.875 0 0 1 1.237.02Zm3.27 3.832a1.3 1.3 0 1 0-2.599 0 1.3 1.3 0 0 0 2.6 0Zm-5.131 1.97a.875.875 0 0 1 1.237.02c.384.396.776.789 1.178 1.166h.001c2.076 1.95 4.133 3.26 5.746 3.835.812.29 1.445.37 1.884.31.405-.055.61-.216.731-.445.135-.256.209-.678.116-1.31-.09-.624-.333-1.378-.731-2.224a.875.875 0 0 1 1.583-.745c.446.947.757 1.87.88 2.716.122.835.072 1.674-.3 2.38-.431.817-1.186 1.246-2.044 1.362-.823.111-1.755-.056-2.707-.396-1.911-.681-4.17-2.153-6.356-4.207-.429-.402-.842-.815-1.238-1.225a.875.875 0 0 1 .02-1.237Z" 
                  fill="currentColor"/>
                </svg>
                <span className="text-sm font-medium">Deep Research</span>
              </button> */}
              
              {/* Attach files button */}
              <button 
                onClick={() => setIsAttachModalOpen(true)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
                aria-label="Attach files"
                title="Attach files or URLs"
              >
                <FileText size={20} className="text-gray-700" />
              </button>
            </div>
          </div>
        </header>

        {/* Messages or Welcome Screen */}
        <div className="flex-1 overflow-y-auto p-4 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-gray-300">
          {showWelcomeScreen ? (
            <div className="h-full flex flex-col items-center justify-center text-center px-4 animate-fade-in">
              <h2 className="text-3xl font-medium mb-6 text-gray-900">What can I help with?</h2>
              <p className="text-gray-600 max-w-md mb-8">
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
              <MessageList 
                messages={messages} 
                baselineResponses={baselineResponses} 
              />
              
              {/* Loading Spinner - show when loading responses */}
              {loading && (
                <div className="flex justify-center items-center my-6 animate-fade-in">
                  <div className="flex flex-col items-center gap-2">
                    <Spinner size="lg" />
                    <p className="text-sm text-gray-600 animate-pulse-subtle">Thinking...</p>
                  </div>
                </div>
              )}
              
              {/* Always show SourceViewer component - it will internally filter for web sources */}
              {sources.length > 0 && <SourceViewer sources={sources} />}
              
              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-100 text-red-600 rounded-lg max-w-3xl mx-auto">
                  {error}
                </div>
              )}
              
              {/* Processed Documents Info */}
              {processedDocs.length > 0 && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200 max-w-3xl mx-auto">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-base font-medium text-gray-900">Processed Documents</h3>
                  </div>
                  <div className="max-h-40 overflow-y-auto">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {processedDocs.map((doc, index) => (
                        <div key={index} className="flex items-center gap-2 p-2 bg-gray-100 rounded-lg text-sm">
                          {doc.toLowerCase().endsWith('.pdf') ? (
                            <FileText size={14} className="text-amber-600" />
                          ) : doc.toLowerCase().match(/\.(png|jpg|jpeg|gif|webp)$/) ? (
                            <Image size={14} className="text-emerald-600" />
                          ) : (
                            <Globe size={14} className="text-blue-600" />
                          )}
                          <span className="truncate text-gray-800">{doc}</span>
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
          <div className="border-t border-gray-200 p-4 bg-white backdrop-blur-sm">
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
        className="light-bg"
      />
    </div>
  );
};

export default ChatPage;
