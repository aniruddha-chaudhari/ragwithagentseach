import React from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import PaperCheckPage from './pages/PaperCheckPage'
import GoogleSearchPage from './pages/GoogleSearchPage'

function App() {
  return (
    <Router>
      <div>
        <nav className="bg-gray-800 text-white p-4">
          <div className="max-w-6xl mx-auto flex gap-4">
            <Link to="/" className="hover:text-gray-300">Chat</Link>
            <Link to="/paper-check" className="hover:text-gray-300">Paper Check</Link>
            <Link to="/google-search" className="hover:text-gray-300">Google Search</Link>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/paper-check" element={<PaperCheckPage />} />
          <Route path="/google-search" element={<GoogleSearchPage />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
