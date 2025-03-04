import React, { useState } from 'react';

const GoogleSearchPage = () => {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);

  const handleSearch = async () => {
    if (!query.trim()) {
      setResult('Please enter a search query.');
      return;
    }
    console.log("Searching for:", query);
    try {
      const res = await fetch('http://localhost:8000/chat/google-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      if (!res.ok) {
        const errorData = await res.json();
        console.error("Response error data:", errorData);
        throw new Error(errorData.detail || 'Unprocessable Entity');
      }
      const data = await res.json();
      // Check if candidates field exists and use its content if available
      const candidateText = data.candidates && data.candidates.length > 0 
        ? data.candidates[0].content || data.candidates[0].text 
        : null;
      console.log("Received response:", candidateText || data.response);
      setResult(candidateText || data.response);
    } catch (error) {
      console.error("Search error:", error);
      setResult('Error: ' + error.message);
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Google Search</h1>
      <input
        type="text"
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder="Enter search query"
        className="border p-2 mr-2"
      />
      <button onClick={handleSearch} className="bg-blue-500 text-white p-2">
        Search
      </button>
      <pre className="mt-4 bg-gray-100 p-4">{ result ? JSON.stringify(result, null, 2) : '' }</pre>
    </div>
  );
};

export default GoogleSearchPage;