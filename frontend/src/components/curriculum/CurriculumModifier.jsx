import React, { useState } from 'react';
import { CurriculumService } from '../../services/CurriculumService';

const CurriculumModifier = ({ curriculum, onModified, onCancel }) => {
  const [modificationText, setModificationText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!modificationText.trim()) {
      setError('Please enter your modification request');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      const result = await CurriculumService.modifyCurriculum(
        curriculum.curriculum_id,
        modificationText
      );
      
      if (onModified) {
        onModified(result);
      }
    } catch (err) {
      setError(err.message || 'Failed to modify curriculum');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white border border-gray-200 p-6 rounded-lg shadow-lg">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Modify Curriculum</h2>
      
      {error && (
        <div className="bg-red-500 text-white p-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <div className="mb-4">
        <h3 className="font-medium mb-2 text-gray-700">Current Curriculum Structure:</h3>
        <div className="bg-gray-100 p-3 rounded mb-4">
          <p className="font-medium text-gray-800">{curriculum.title}</p>
          <p className="text-sm mb-2 text-gray-600">Total Time: {curriculum.total_time}</p>
          
          <div className="space-y-1 mt-2">
            {curriculum.steps.map((step, index) => (
              <div key={index}>
                <p className="text-gray-800">{index + 1}. {step.title} ({step.estimated_time})</p>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1 text-gray-700">
            Enter your modification request
          </label>
          <textarea
            value={modificationText}
            onChange={(e) => setModificationText(e.target.value)}
            className="w-full p-3 bg-white border border-gray-300 text-gray-800 rounded h-40"
            placeholder="e.g., Add a section on advanced topics, change the order of topics, etc."
            disabled={isLoading}
          />
          <p className="text-xs mt-1 text-gray-600">
            Describe how you'd like to modify the curriculum. Be specific about additions, removals, or changes to the structure.
          </p>
        </div>
        
        <div className="flex gap-3">
          <button
            type="submit"
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
            disabled={isLoading}
          >
            {isLoading ? 'Modifying...' : 'Apply Modifications'}
          </button>
          
          <button
            type="button"
            onClick={onCancel}
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded"
            disabled={isLoading}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default CurriculumModifier;
