import React, { useState, useEffect } from 'react';
import { MessageSquare, Menu, PenLine, Trash2, FileText, Image, Globe, Layers, X } from 'lucide-react';
import { getSessions, createSession, deleteSession, getSession } from '../utils/api';

const Sidebar = ({ currentPage, isOpen, toggleSidebar, currentSessionId, onSessionChange }) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [sessionDocuments, setSessionDocuments] = useState([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [showDocuments, setShowDocuments] = useState(false);

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    if (currentSessionId && showDocuments) {
      fetchSessionDocuments();
    }
  }, [currentSessionId, showDocuments]);

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const data = await getSessions();
      setSessions(data.sessions || []);
    } catch (err) {
      setError('Failed to load chats');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSessionDocuments = async () => {
    if (!currentSessionId) return;
    
    setLoadingDocuments(true);
    try {
      const sessionData = await getSession(currentSessionId);
      setSessionDocuments(sessionData.processed_documents || []);
    } catch (err) {
      console.error('Failed to load session documents:', err);
    } finally {
      setLoadingDocuments(false);
    }
  };

  const handleCreateSession = async () => {
    setIsCreating(true);
    try {
      const { session_id } = await createSession("New chat");
      setSessions([...sessions, { session_id, session_name: "New chat" }]);
      onSessionChange(session_id);
    } catch (err) {
      setError('Failed to create chat');
      console.error(err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this chat?')) {
      try {
        await deleteSession(sessionId);
        setSessions(sessions.filter(session => session.session_id !== sessionId));
        
        if (sessionId === currentSessionId) {
          const remainingSessions = sessions.filter(session => session.session_id !== sessionId);
          if (remainingSessions.length > 0) {
            onSessionChange(remainingSessions[0].session_id);
          } else {
            onSessionChange(null);
          }
        }
      } catch (err) {
        setError('Failed to delete chat');
        console.error(err);
      }
    }
  };

  const toggleDocumentsView = () => {
    setShowDocuments(!showDocuments);
    if (!showDocuments && currentSessionId) {
      fetchSessionDocuments();
    }
  };

  return (
    <div
      className={`min-h-screen bg-white shadow-lg transition-all duration-300 ease-in-out 
      ${isOpen ? 'w-72' : 'w-20'} relative flex flex-col`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100">
        {isOpen && (
          <h1 className="text-xl font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Teacher AI
          </h1>
        )}
        <button
          onClick={toggleSidebar}
          className="p-2.5 rounded-xl hover:bg-gray-100 transition-colors duration-200"
          aria-label="Toggle sidebar"
        >
          <Menu size={22} className="text-gray-600" />
        </button>
      </div>

      {/* Actions */}
      {isOpen && (
        <div className="p-4">
          <button
            onClick={handleCreateSession}
            disabled={isCreating}
            className="flex items-center w-full gap-2 p-3 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-left text-gray-800"
          >
            <PenLine size={18} />
            <span>New chat</span>
          </button>
          
          {currentSessionId && (
            <button
              onClick={toggleDocumentsView}
              className={`flex items-center w-full gap-2 p-3 mt-2 ${
                showDocuments ? 'bg-blue-50 text-blue-700' : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
              } rounded-lg transition-colors text-left`}
            >
              <Layers size={18} />
              <span>{showDocuments ? 'Show Chats' : 'Show Documents'}</span>
            </button>
          )}
          
          {error && (
            <div className="p-3 mt-2 bg-red-50 border border-red-100 text-red-600 rounded-lg text-sm">
              {error}
            </div>
          )}
        </div>
      )}

      {/* Session List or Documents */}
      <div className={`flex-1 flex flex-col gap-2 p-4 ${isOpen ? '' : 'items-center'} overflow-y-auto`}>
        {isOpen ? (
          showDocuments ? (
            // Documents View
            <div className="w-full">
              <h3 className="text-xs text-gray-500 uppercase font-medium px-2 mb-2">Session Documents</h3>
              
              {!currentSessionId ? (
                <div className="p-4 text-center text-gray-500 text-sm">
                  Select a chat to view documents
                </div>
              ) : loadingDocuments ? (
                <div className="flex justify-center p-4">
                  <div className="animate-pulse-subtle text-gray-500">Loading...</div>
                </div>
              ) : sessionDocuments.length === 0 ? (
                <div className="p-4 text-center border border-dashed border-gray-200 rounded-lg">
                  <p className="text-gray-500 text-sm">No documents</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {sessionDocuments.map((doc, index) => (
                    <div 
                      key={index} 
                      className="flex items-center gap-2 p-2 bg-gray-100 rounded-lg text-sm"
                    >
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
              )}
            </div>
          ) : (
            // Chats List
            <div className="w-full">
              <h3 className="text-xs text-gray-500 uppercase font-medium px-2 mb-2">Recent chats</h3>
              
              {loading ? (
                <div className="flex justify-center p-4">
                  <div className="animate-pulse-subtle text-gray-500">Loading...</div>
                </div>
              ) : sessions.length === 0 ? (
                <p className="text-gray-500 text-sm p-2">No chats available</p>
              ) : (
                <div className="space-y-0.5">
                  {sessions.map((session) => (
                    <div 
                      key={session.session_id}
                      className={`flex items-center justify-between py-2 px-3 rounded-lg cursor-pointer transition-colors ${
                        session.session_id === currentSessionId
                          ? 'bg-blue-50 text-blue-700'
                          : 'hover:bg-gray-100 text-gray-800'
                      }`}
                      onClick={() => onSessionChange(session.session_id)}
                    >
                      <span className="truncate text-sm">{session.session_name}</span>
                      <button
                        onClick={(e) => handleDeleteSession(session.session_id, e)}
                        className="p-1 rounded-full opacity-60 hover:opacity-100 hover:bg-gray-200 transition-all"
                        aria-label="Delete chat"
                      >
                        <Trash2 size={14} className="text-gray-600" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        ) : (
          // Collapsed sidebar - just show icon for chat
          <button
            className="flex items-center justify-center p-3.5 rounded-xl bg-blue-50 text-blue-600 shadow-sm"
          >
            <MessageSquare size={22} />
          </button>
        )}
      </div>
    </div>
  );
};

export default Sidebar;