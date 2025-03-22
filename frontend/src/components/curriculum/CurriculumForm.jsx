import React, { useState } from 'react';
import { CurriculumService } from '../../services/CurriculumService';

const CurriculumForm = ({ onCurriculumCreated }) => {
  const [subject, setSubject] = useState('');
  const [syllabusUrl, setSyllabusUrl] = useState('');
  const [timeConstraint, setTimeConstraint] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!subject.trim()) {
      setError('Subject is required');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      const result = await CurriculumService.createCurriculum(
        subject,
        syllabusUrl || null,
        timeConstraint || null
      );
      
      if (onCurriculumCreated) {
        onCurriculumCreated(result);
      }
    } catch (err) {
      setError(err.message || 'Failed to create curriculum');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
      <h2 className="text-xl font-bold mb-4">Create New Curriculum</h2>
      
      {error && (
        <div className="bg-red-500 text-white p-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">
            Subject <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="w-full p-2 bg-gray-700 rounded border border-gray-600 text-white"
            placeholder="e.g., Introduction to Python"
            disabled={isLoading}
          />
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">
            Syllabus URL (optional)
          </label>
          <input
            type="url"
            value={syllabusUrl}
            onChange={(e) => setSyllabusUrl(e.target.value)}
            className="w-full p-2 bg-gray-700 rounded border border-gray-600 text-white"
            placeholder="https://example.com/syllabus.pdf"
            disabled={isLoading}
          />
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">
            Time Constraint (optional)
          </label>
          <input
            type="text"
            value={timeConstraint}
            onChange={(e) => setTimeConstraint(e.target.value)}
            className="w-full p-2 bg-gray-700 rounded border border-gray-600 text-white"
            placeholder="e.g., 8 weeks"
            disabled={isLoading}
          />
        </div>
        
        <button
          type="submit"
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
          disabled={isLoading}
        >
          {isLoading ? 'Generating...' : 'Generate Curriculum'}
        </button>
      </form>
    </div>
  );
};

export default CurriculumForm;
