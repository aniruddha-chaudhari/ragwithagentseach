import React, { useState } from 'react';

const MessageInput = ({ onSendMessage, isLoading }) => {
  const [message, setMessage] = useState('');
  const [forceWebSearch, setForceWebSearch] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message, forceWebSearch);
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t pt-4">
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask a question..."
          className="flex-grow p-2 border rounded-lg"
          disabled={isLoading}
        />
        <div className="flex items-center">
          <label className="flex items-center gap-1 cursor-pointer mr-2">
            <input
              type="checkbox"
              checked={forceWebSearch}
              onChange={() => setForceWebSearch(!forceWebSearch)}
              className="accent-blue-500"
            />
            <span className="text-sm">🌐 Web</span>
          </label>
          <button
            type="submit"
            className={`px-4 py-2 rounded-lg ${
              isLoading || !message.trim()
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
            disabled={isLoading || !message.trim()}
          >
            {isLoading ? 'Thinking...' : 'Send'}
          </button>
        </div>
      </div>
    </form>
  );
};

export default MessageInput;
