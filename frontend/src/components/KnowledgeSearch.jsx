import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { knowledgeResearchService } from '../services/KnowledgeResearchService';
import Spinner from './ui/Spinner';

const KnowledgeSearch = ({ onSearchComplete }) => {
  const navigate = useNavigate();
  const [topic, setTopic] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [depth, setDepth] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!topic.trim()) {
      setError('Please enter a topic to research');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const research = await knowledgeResearchService.create(topic, {
        sourceUrl: sourceUrl || undefined,
        depth: depth
      });
      
      if (onSearchComplete) {
        // Call the callback function with the research data
        onSearchComplete(research);
      } else {
        // If no callback is provided, navigate to the research detail page as before
        navigate(`/research/${research.id}`);
      }
    } catch (err) {
      console.error('Error creating knowledge research:', err);
      setError(err.message || 'Failed to create knowledge research');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto bg-white border border-gray-200 rounded-lg shadow-lg">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-center text-gray-800">Knowledge Research</h2>
        <p className="text-center text-gray-600 mt-1">
          Generate comprehensive research on any topic
        </p>
      </div>
      
      <div className="p-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 p-3 rounded mb-4">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="topic" className="block text-sm font-medium text-gray-700">
              Research Topic *
            </label>
            <input
              type="text"
              id="topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="E.g., Quantum Computing Basics"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              required
              disabled={loading}
            />
          </div>
          
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label htmlFor="sourceUrl" className="block text-sm font-medium text-gray-700 flex items-center justify-between">
                Source URL
                <span className="text-xs text-gray-500">(Optional)</span>
              </label>
              <input
                type="url"
                id="sourceUrl"
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                placeholder="https://example.com/reference"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                disabled={loading}
              />
            </div>
            
            <div className="space-y-2">
              <label htmlFor="depth" className="block text-sm font-medium text-gray-700">
                Research Depth
              </label>
              <select
                id="depth"
                value={depth}
                onChange={(e) => setDepth(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                disabled={loading}
              >
                <option value="1">Basic (Level 1)</option>
                <option value="2">Intermediate (Level 2)</option>
                <option value="3">Advanced (Level 3)</option>
                <option value="4">Expert (Level 4)</option>
                <option value="5">Comprehensive (Level 5)</option>
              </select>
            </div>
          </div>
          
          <button
            type="submit"
            disabled={loading || !topic.trim()}
            className="w-full h-12 bg-black hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <Spinner />
                <span className="ml-2">Generating Research...</span>
              </div>
            ) : "Generate Knowledge Research"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default KnowledgeSearch;