import React, { useState } from 'react';
import { knowledgeResearchService } from '../../services/KnowledgeResearchService';
import Spinner from '../ui/Spinner';

const CurriculumForm = ({ onCurriculumCreated }) => {
  const [subject, setSubject] = useState('');
  const [syllabusUrl, setSyllabusUrl] = useState('');
  const [timeConstraint, setTimeConstraint] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!subject.trim()) return;

    setIsLoading(true);
    setError('');

    try {
      const curriculum = await knowledgeResearchService.create(
        subject,
        {
          sourceUrl: syllabusUrl || undefined,
          depth: timeConstraint ? parseInt(timeConstraint) || 3 : 3
        }
      );
      
      if (onCurriculumCreated) {
        onCurriculumCreated(curriculum);
      }
      
      // Clear the form
      setSubject('');
      setSyllabusUrl('');
      setTimeConstraint('');
    } catch (err) {
      console.error('Error creating curriculum:', err);
      setError(err.message || 'Failed to create curriculum');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto bg-white border border-gray-200 rounded-lg shadow-lg">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-center text-gray-800">Create a Curriculum</h2>
        <p className="text-center text-gray-600 mt-1">
          Generate customized learning paths for any subject
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
            <label htmlFor="subject" className="block text-sm font-medium text-gray-700">
              Subject / Topic *
            </label>
            <input
              type="text"
              id="subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="E.g., Introduction to JavaScript"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              required
              disabled={isLoading}
            />
          </div>
          
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label htmlFor="syllabusUrl" className="block text-sm font-medium text-gray-700 flex items-center justify-between">
                Source URL
                <span className="text-xs text-gray-500">(Optional)</span>
              </label>
              <input
                type="url"
                id="syllabusUrl"
                value={syllabusUrl}
                onChange={(e) => setSyllabusUrl(e.target.value)}
                placeholder="https://example.com/syllabus"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                disabled={isLoading}
              />
            </div>
            
            <div className="space-y-2">
              <label htmlFor="timeConstraint" className="block text-sm font-medium text-gray-700 flex items-center justify-between">
                Research Depth
                <span className="text-xs text-gray-500">(1-5)</span>
              </label>
              <input
                type="number"
                id="timeConstraint"
                value={timeConstraint}
                onChange={(e) => setTimeConstraint(e.target.value)}
                placeholder="E.g., 3"
                min="1"
                max="5"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                disabled={isLoading}
              />
            </div>
          </div>
        </form>
      </div>
      
      <div className="px-6 py-4 border-t border-gray-200">
        <button
          onClick={handleSubmit}
          disabled={isLoading || !subject.trim()}
          className="w-full h-12 bg-black hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <div className="flex items-center justify-center">
              <Spinner />
              <span className="ml-2">Generating...</span>
            </div>
          ) : "Generate Research"}
        </button>
      </div>
    </div>
  );
};

export default CurriculumForm;
