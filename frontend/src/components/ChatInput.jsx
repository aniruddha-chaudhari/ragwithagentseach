import React from 'react'

const ChatInput = ({ onSubmit, inputMessage, setInputMessage, loading }) => {
  return (
    <form onSubmit={onSubmit} className="flex gap-2 mt-2">
      <input
        type="text"
        value={inputMessage}
        onChange={(e) => setInputMessage(e.target.value)}
        placeholder="Type your message..."
        disabled={loading}
        className="flex-1 p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
      />
      <button 
        type="submit" 
        disabled={loading}
        className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        Send
      </button>
    </form>
  )
}

export default ChatInput