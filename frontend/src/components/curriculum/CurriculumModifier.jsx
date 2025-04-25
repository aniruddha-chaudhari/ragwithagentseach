import React, { useState } from 'react';
import { knowledgeResearchService } from '../../services/KnowledgeResearchService';
import Spinner from '../ui/Spinner';

const CurriculumModifier = ({ curriculum, onModified, onCancel }) => {
  const [modificationText, setModificationText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!modificationText.trim()) return;

    setIsLoading(true);
    setError('');

    try {
      const modifiedCurriculum = await knowledgeResearchService.modifyResearch(
        curriculum.curriculum_id,
        modificationText
      );
      
      if (onModified) {
        onModified(modifiedCurriculum);
      }
    } catch (err) {
      console.error('Error modifying curriculum:', err);
      setError(err.message || 'Failed to modify curriculum');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto bg-white border border-gray-200 rounded-lg shadow-lg">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-center text-gray-800">Modify Curriculum</h2>
        <p className="text-center text-gray-600 mt-1">
          {curriculum.title}
        </p>
      </div>
      
      <div className="p-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 p-3 rounded mb-4">
            {error}
          </div>
        )}
        
        <div className="mb-6 p-4 bg-gray-50 rounded-md border border-gray-100">
          <h3 className="text-lg font-semibold mb-2 text-gray-700">
            Current Overview
          </h3>
          <p className="text-gray-600">{curriculum.overview}</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700" htmlFor="modificationText">
              Modification Instructions
            </label>
            <textarea
              id="modificationText"
              value={modificationText}
              onChange={(e) => setModificationText(e.target.value)}
              placeholder="Describe how you want to modify the curriculum. E.g., Add a section on async programming, make it more beginner-friendly, etc."
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 h-40"
              required
              disabled={isLoading}
            />
          </div>
        </form>
      </div>
      
      <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
        <button
          type="button"
          onClick={onCancel}
          className="bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-6 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
          disabled={isLoading}
        >
          Cancel
        </button>
        
        <button
          onClick={handleSubmit}
          disabled={isLoading || !modificationText.trim()}
          className={`${
            isLoading || !modificationText.trim()
              ? 'bg-blue-300 cursor-not-allowed'
              : 'bg-black hover:bg-gray-700'
          } text-white font-medium py-2 px-6 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 flex items-center gap-2`}
        >
          {isLoading ? (
            <>
              <Spinner size="sm" className="border-white border-t-transparent" />
              <span>Updating...</span>
            </>
          ) : (
            'Apply Modifications'
          )}
        </button>
      </div>
    </div>
  );
};

export default CurriculumModifier;
