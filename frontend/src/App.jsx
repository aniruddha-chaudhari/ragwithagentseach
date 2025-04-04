import React, { useState } from 'react'
import ChatPage from './pages/ChatPage'
import Sidebar from './components/Sidebar'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [currentSessionId, setCurrentSessionId] = useState(null)

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen)

  return (
    <div className="flex min-h-screen bg-white text-gray-900">
      <Sidebar 
        isOpen={sidebarOpen} 
        toggleSidebar={toggleSidebar} 
        currentSessionId={currentSessionId}
        onSessionChange={setCurrentSessionId}
      />
      
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-auto">
          <ChatPage 
            currentSessionId={currentSessionId} 
            setCurrentSessionId={setCurrentSessionId} 
          />
        </div>
      </div>
    </div>
  )
}

export default App
