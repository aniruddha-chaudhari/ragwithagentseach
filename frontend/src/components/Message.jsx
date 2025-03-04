import React from 'react'

const Message = ({ role, content }) => {
  const messageStyles = {
    user: 'self-end bg-blue-600 text-white',
    assistant: 'self-start bg-gray-100 text-gray-800',
    system: 'self-center bg-blue-50 text-blue-800 font-mono whitespace-pre-wrap',
    error: 'self-center bg-red-50 text-red-800'
  }

  return (
    <div className={`max-w-[80%] p-3 rounded-lg my-1 ${messageStyles[role]}`}>
      <div className="message-content">{content}</div>
    </div>
  )
}

export default Message