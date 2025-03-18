import React, { useState, useEffect } from 'react';
import { getSessions, createSession, deleteSession } from '../utils/api';

const SessionManager = ({ currentSessionId, onSessionChange }) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [newSessionName, setNewSessionName] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const data = await getSessions();
      setSessions(data.sessions || []);
    } catch (err) {
      setError('Failed to load sessions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleCreateSession = async (e) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      const { session_id, session_name } = await createSession(newSessionName || undefined);
      setSessions([...sessions, { session_id, session_name }]);
      setNewSessionName('');
      onSessionChange(session_id);
    } catch (err) {
      setError('Failed to create session');
      console.error(err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (window.confirm('Are you sure you want to delete this session?')) {
      try {
        await deleteSession(sessionId);
        setSessions(sessions.filter(session => session.session_id !== sessionId));
        
        // If current session was deleted, set to another session or null
        if (sessionId === currentSessionId) {
          const remainingSessions = sessions.filter(session => session.session_id !== sessionId);
          if (remainingSessions.length > 0) {
            onSessionChange(remainingSessions[0].session_id);
          } else {
            onSessionChange(null);
          }
        }
      } catch (err) {
        setError('Failed to delete session');
        console.error(err);
      }
    }
  };

  return (
    <div className="p-4 border rounded-lg bg-gray-50">
      <h3 className="text-lg font-medium mb-3">Sessions</h3>
      
      {/* Create new session */}
      <form onSubmit={handleCreateSession} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={newSessionName}
            onChange={(e) => setNewSessionName(e.target.value)}
            placeholder="New Session Name"
            className="flex-grow p-2 border rounded-l text-sm"
            disabled={isCreating}
          />
          <button
            type="submit"
            className={`px-3 py-2 rounded-r text-sm font-medium ${
              isCreating
                ? 'bg-gray-300'
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
            disabled={isCreating}
          >
            Create
          </button>
        </div>
      </form>
      
      {/* Error message */}
      {error && (
        <div className="mb-3 text-red-500 text-sm">{error}</div>
      )}
      
      {/* Sessions list */}
      <div className="max-h-60 overflow-y-auto">
        {loading ? (
          <p className="text-gray-500">Loading sessions...</p>
        ) : sessions.length === 0 ? (
          <p className="text-gray-500">No sessions available</p>
        ) : (
          <ul className="divide-y">
            {sessions.map((session) => (
              <li key={session.session_id} className="py-2">
                <div className="flex justify-between items-center">
                  <button
                    onClick={() => onSessionChange(session.session_id)}
                    className={`text-left px-2 py-1 rounded ${
                      session.session_id === currentSessionId
                        ? 'bg-blue-100 font-medium'
                        : 'hover:bg-gray-100'
                    }`}
                  >
                    {session.session_name}
                  </button>
                  <button
                    onClick={() => handleDeleteSession(session.session_id)}
                    className="text-red-500 hover:text-red-700 p-1"
                    title="Delete session"
                  >
                    🗑️
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default SessionManager;
