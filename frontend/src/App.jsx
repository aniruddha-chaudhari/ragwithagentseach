import React, { useState } from 'react'
import ChatPage from './pages/ChatPage'
import CurriculumPage from './pages/CurriculumPage'

function App() {
  const [currentPage, setCurrentPage] = useState('chat')

  return (
    <div className="min-h-screen bg-[#1A1B1E] text-white">
      <nav className="bg-gray-900 p-4">
        <div className="container mx-auto flex">
          <button 
            className={`mr-4 px-3 py-1 rounded ${currentPage === 'chat' ? 'bg-blue-600' : 'hover:bg-gray-700'}`}
            onClick={() => setCurrentPage('chat')}
          >
            Chat
          </button>
          <button 
            className={`mr-4 px-3 py-1 rounded ${currentPage === 'curriculum' ? 'bg-blue-600' : 'hover:bg-gray-700'}`}
            onClick={() => setCurrentPage('curriculum')}
          >
            Curriculum
          </button>
        </div>
      </nav>
      
      {currentPage === 'chat' ? <ChatPage /> : <CurriculumPage />}
    </div>
  )
}

export default App
