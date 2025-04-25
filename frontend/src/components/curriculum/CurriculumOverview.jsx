import React, { useState } from 'react';
import { knowledgeResearchService } from '../../services/KnowledgeResearchService';
import Spinner from '../../components/ui/Spinner';

const CurriculumOverview = ({ curriculum, onDetailsGenerated, onModificationRequested }) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  
  const handleGenerateDetails = async () => {
    setIsGenerating(true);
    setError('');
    
    try {
      const details = await knowledgeResearchService.generateSectionDetails(curriculum.curriculum_id);
      if (onDetailsGenerated) {
        onDetailsGenerated(details);
      }
    } catch (err) {
      setError(err.message || 'Failed to generate section details');
    } finally {
      setIsGenerating(false);
    }
  };
  
  const handleDownload = () => {
    const blob = new Blob([curriculum.formatted_text], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${curriculum.title.replace(/\s+/g, '_')}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-white border border-gray-200 rounded-lg shadow-lg">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-2xl font-bold text-center text-gray-800">{curriculum.title}</h1>
        <p className="text-center text-gray-600 mt-1">{curriculum.total_time}</p>
      </div>
      
      <div className="p-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 p-3 rounded mb-4">
            {error}
          </div>
        )}
        
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-2 text-gray-800">Overview</h2>
          <p className="text-gray-700">{curriculum.overview}</p>
        </div>
        
        <div className="my-6 pt-6 border-t border-gray-200">
          <h2 className="text-xl font-semibold mb-3 text-gray-800">Learning Steps</h2>
          
          <div className="space-y-3">
            {curriculum.steps.map((step, index) => (
              <div key={index} className="bg-gray-50 p-4 rounded-md border border-gray-100">
                <h3 className="font-medium text-gray-800">{index + 1}. {step.title}</h3>
                <p className="text-sm text-gray-600 mt-1">Estimated Time: {step.estimated_time}</p>
              </div>
            ))}
          </div>
        </div>

        {curriculum.steps.length > 0 && (
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 mt-6 mb-6">
            <p className="text-blue-800">
              <strong>Next Step:</strong> Click "Generate Details" to create comprehensive content for each step.
              After generation, you can view step details in the "Step Details" tab.
            </p>
          </div>
        )}
      </div>
      
      <div className="px-6 py-4 border-t border-gray-200 flex flex-wrap gap-3 justify-center">
        <button
          onClick={handleDownload}
          className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-6 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
        >
          Download Curriculum
        </button>
        
        <button
          onClick={handleGenerateDetails}
          className="bg-black hover:bg-gray-700 text-white font-medium py-2 px-6 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={isGenerating}
        >
          {isGenerating ? (
            <>
              <Spinner size="sm" className="border-white border-t-transparent" />
              <span>Generating...</span>
            </>
          ) : (
            'Generate Detailed Curriculum'
          )}
        </button>
        
        <button
          onClick={onModificationRequested}
          className="bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-6 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
        >
          Modify Curriculum
        </button>
      </div>
    </div>
  );
};

export default CurriculumOverview;
