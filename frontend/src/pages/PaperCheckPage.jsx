import React, { useState } from 'react'
import FileUpload from '../components/FileUpload'

const PaperCheckPage = () => {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setLoading(true)
    setError(null)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8000/analyze-paper', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()
      if (data.success) {
        setResult(data.results[0])
      } else {
        setError(data.error || 'Failed to analyze paper')
      }
    } catch (error) {
      setError('Failed to upload and analyze paper')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto p-5 min-h-screen">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-2xl font-bold mb-4">Paper Analysis</h1>
        
        <FileUpload onFileUpload={handleFileUpload} loading={loading} />
        
        {error && (
          <div className="mt-4 p-4 bg-red-50 text-red-800 rounded-md">
            {error}
          </div>
        )}
        
        {result && (
          <div className="mt-6 space-y-4">
            <div className="p-4 bg-blue-50 rounded-md">
              <h2 className="text-xl font-semibold mb-2">
                Score: {result.marks}/100 - {result.Name}
              </h2>
            </div>
            
            <div className="p-4 bg-green-50 rounded-md">
              <h3 className="font-semibold mb-2">Positive Remarks:</h3>
              <ul className="list-disc pl-5">
                {result.remarks.map((remark, index) => (
                  <li key={index}>{remark}</li>
                ))}
              </ul>
            </div>
            
            <div className="p-4 bg-yellow-50 rounded-md">
              <h3 className="font-semibold mb-2">Suggestions for Improvement:</h3>
              <ul className="list-disc pl-5">
                {result.suggestions.map((suggestion, index) => (
                  <li key={index}>{suggestion}</li>
                ))}
              </ul>
            </div>
            
            {result.errors.length > 0 && (
              <div className="p-4 bg-red-50 rounded-md">
                <h3 className="font-semibold mb-2">Issues Found:</h3>
                <ul className="list-disc pl-5">
                  {result.errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default PaperCheckPage