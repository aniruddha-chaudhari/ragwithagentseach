import React, { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import Message from '../components/Message'
import FileUpload from '../components/FileUpload'
import ChatInput from '../components/ChatInput'

const ChatPage = () => {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [chatId, setChatId] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessageProgrammatically = async (messageContent, currentChatId) => {
    try {
      console.log('Sending message:', messageContent, 'with chat ID:', currentChatId)
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageContent,
          chat_id: currentChatId
        }),
      })

      const data = await response.json()
      console.log('Response from chat endpoint:', data)
      return data
    } catch (error) {
      console.error('Error in sendMessageProgrammatically:', error)
      throw error
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim()) return

    setLoading(true)
    const newMessage = { role: 'user', content: inputMessage }
    setMessages(prev => [...prev, newMessage])
    setInputMessage('')

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          chat_id: chatId
        }),
      })

      const data = await response.json()
      if (!chatId && data.chat_id) {
        setChatId(data.chat_id)
      }
      setMessages(prev => [...prev, { role: 'assistant', content: data.message }])
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, { role: 'error', content: 'Failed to send message' }])
    }
    setLoading(false)
  }

  const handleFileUpload = async (e) => {
    console.log('File input event triggered:', e)
    const file = e.target.files[0]
    console.log('File object:', file)
    
    if (!file) {
      console.log('No file selected')
      return
    }

    console.log('File details:', {
      name: file.name,
      type: file.type,
      size: file.size
    })

    setLoading(true)
    const formData = new FormData()
    formData.append('file', file)
    
    const currentChatId = chatId || String(Date.now())
    console.log('Using chat ID:', currentChatId)
    formData.append('chat_id', currentChatId)
    
    try {
      const response = await fetch('http://localhost:8000/chat/upload-document', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (data.success && data.document_response) {
        if (!chatId) {
          setChatId(currentChatId)
        }
        
        setMessages(prev => [
          ...prev,
          { role: 'system', content: `File uploaded: ${file.name}` }
        ])

        try {
          const chatResponse = await sendMessageProgrammatically(data.document_response, currentChatId)
          if (chatResponse.message) {
            setMessages(prev => [...prev, { role: 'assistant', content: chatResponse.message }])
          }
        } catch (chatError) {
          console.error('Chat processing error:', chatError)
          setMessages(prev => [...prev, {
            role: 'error',
            content: 'Failed to process document response'
          }])
        }
      } else {
        console.error('Document processing failed:', data.error)
        setMessages(prev => [...prev, {
          role: 'error',
          content: data.error || 'Failed to process document'
        }])
      }
    } catch (error) {
      console.log('Upload error details:', {
        message: error.message,
        stack: error.stack
      })
      setMessages(prev => [...prev, {
        role: 'error',
        content: 'Failed to upload document'
      }])
    }
    setLoading(false)
  }

  return (
    <div className="max-w-6xl mx-auto p-5 h-screen flex flex-col">
      <div className="flex-1 flex flex-col bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="flex-1 p-5 overflow-y-auto space-y-3">
          {messages.map((msg, index) => (
            <div key={index}>
              {msg.role === 'assistant' ? (
                // Only display the markdown-converted response
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              ) : (
                <Message role={msg.role} content={msg.content} />
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <div className="p-5 bg-gray-50 border-t border-gray-200">
          <div className="flex items-center">
            <FileUpload onFileUpload={handleFileUpload} loading={loading} />
            {loading && <span className="ml-2 text-sm text-gray-600">Loading...</span>}
          </div>
          <ChatInput 
            onSubmit={handleSendMessage}
            inputMessage={inputMessage}
            setInputMessage={setInputMessage}
            loading={loading}
          />
        </div>
      </div>
    </div>
  )
}

export default ChatPage