import React, { useState } from 'react'
import ChatPage from './pages/ChatPage'
import CurriculumPage from './pages/CurriculumPage'
import Sidebar from './components/Sidebar'

function App() {
  const [currentPage, setCurrentPage] = useState('chat')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen)

  return (
    <div className="flex min-h-screen bg-white text-gray-900">
      <Sidebar 
        currentPage={currentPage} 
        setCurrentPage={setCurrentPage} 
        isOpen={sidebarOpen} 
        toggleSidebar={toggleSidebar} 
      />
      
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-auto">
          {currentPage === 'chat' ? <ChatPage /> : <CurriculumPage />}
        </div>
      </div>
    </div>
  )
}

export default App
