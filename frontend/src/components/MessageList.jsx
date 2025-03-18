import React from 'react';
import ReactMarkdown from 'react-markdown';

const MessageList = ({ messages }) => {
  if (!messages || messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-400">
        <p>No messages yet. Start a conversation!</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 mb-4">
      {messages.map((message, index) => (
        <div 
          key={index}
          className={`p-4 rounded-lg max-w-[85%] ${
            message.role === 'user' 
              ? 'bg-blue-100 self-end ml-auto' 
              : 'bg-gray-100 self-start'
          }`}
        >
          <div className="font-semibold mb-1">
            {message.role === 'user' ? 'You' : 'Assistant'}
          </div>
          <div className="markdown-content">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MessageList;
