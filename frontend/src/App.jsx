import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import HomePage from './pages/HomePage'
import Sidebar from './components/Sidebar'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [currentSessionId, setCurrentSessionId] = useState(null)

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen)

  return (
    <Router>
      <div className="flex min-h-screen bg-white text-gray-900">
        <Sidebar 
          isOpen={sidebarOpen} 
          toggleSidebar={toggleSidebar} 
          currentSessionId={currentSessionId}
          onSessionChange={setCurrentSessionId}
        />
        
        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-auto">
            <Routes>
              <Route 
                path="/" 
                element={
                  <ChatPage 
                    currentSessionId={currentSessionId} 
                    setCurrentSessionId={setCurrentSessionId} 
                  />
                }
              />
              <Route 
                path="/deep-research" 
                element={
                  <HomePage 
                    currentSessionId={currentSessionId}
                    setCurrentSessionId={setCurrentSessionId}
                  />
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </div>
      </div>
    </Router>
  )
}

export default App
