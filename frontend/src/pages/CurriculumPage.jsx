import React, { useState, useEffect } from 'react';
import { CurriculumService } from '../services/CurriculumService';
import CurriculumForm from '../components/curriculum/CurriculumForm';
import CurriculumOverview from '../components/curriculum/CurriculumOverview';
import CurriculumModifier from '../components/curriculum/CurriculumModifier';
import CurriculumStepDetail from '../components/curriculum/CurriculumStepDetail';
import CurriculumRoadmap from '../components/curriculum/CurriculumRoadmap';

const CurriculumPage = () => {
  const [curriculum, setCurriculum] = useState(null);
  const [detailedSteps, setDetailedSteps] = useState({});
  const [selectedStepIndex, setSelectedStepIndex] = useState(null);
  const [roadmapData, setRoadmapData] = useState(null);
  const [isModifying, setIsModifying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  // Handle curriculum creation
  const handleCurriculumCreated = (newCurriculum) => {
    setCurriculum(newCurriculum);
    setActiveTab('overview');
    // Reset other states
    setDetailedSteps({});
    setSelectedStepIndex(null);
    setRoadmapData(null);
  };

  // Handle curriculum modification
  const handleCurriculumModified = (modifiedCurriculum) => {
    setCurriculum(modifiedCurriculum);
    setIsModifying(false);
    // Since curriculum changed, reset detailed steps and roadmap
    setDetailedSteps({});
    setSelectedStepIndex(null);
    setRoadmapData(null);
  };

  // Handle detailed curriculum generation
  const handleDetailsGenerated = (details) => {
    setDetailedSteps(details);
    // Set the first step as selected
    const firstIndex = Object.keys(details)[0];
    if (firstIndex) {
      setSelectedStepIndex(parseInt(firstIndex));
      setActiveTab('details');
    }
  };

  // Generate roadmap
  const handleGenerateRoadmap = async () => {
    if (!curriculum) return;
    
    setLoading(true);
    setError('');
    
    try {
      const roadmap = await CurriculumService.generateRoadmap(curriculum.curriculum_id);
      setRoadmapData(roadmap);
      setActiveTab('roadmap');
    } catch (err) {
      setError(err.message || 'Failed to generate roadmap');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Curriculum Generator</h1>
      
      {error && (
        <div className="bg-red-500 text-white p-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {!curriculum ? (
        <CurriculumForm onCurriculumCreated={handleCurriculumCreated} />
      ) : isModifying ? (
        <CurriculumModifier 
          curriculum={curriculum} 
          onModified={handleCurriculumModified} 
          onCancel={() => setIsModifying(false)} 
        />
      ) : (
        <div>
          {/* Tabs */}
          <div className="flex border-b border-gray-700 mb-6">
            <button
              className={`py-2 px-4 mr-2 ${activeTab === 'overview' ? 'border-b-2 border-blue-500 text-blue-500' : 'text-gray-400 hover:text-white'}`}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button
              className={`py-2 px-4 mr-2 ${activeTab === 'details' ? 'border-b-2 border-blue-500 text-blue-500' : 'text-gray-400 hover:text-white'}`}
              onClick={() => setActiveTab('details')}
              disabled={Object.keys(detailedSteps).length === 0}
            >
              Step Details
            </button>
            <button
              className={`py-2 px-4 mr-2 ${activeTab === 'roadmap' ? 'border-b-2 border-blue-500 text-blue-500' : 'text-gray-400 hover:text-white'}`}
              onClick={roadmapData ? () => setActiveTab('roadmap') : handleGenerateRoadmap}
              disabled={loading}
            >
              {loading && activeTab !== 'roadmap' ? 'Generating...' : 'Roadmap'}
            </button>
          </div>
          
          {/* Tab content */}
          {activeTab === 'overview' && (
            <CurriculumOverview 
              curriculum={curriculum} 
              onDetailsGenerated={handleDetailsGenerated}
              onModificationRequested={() => setIsModifying(true)}
            />
          )}
          
          {activeTab === 'details' && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {/* Step selector sidebar */}
              <div className="bg-gray-800 p-4 rounded-lg shadow-lg">
                <h3 className="font-bold text-lg mb-3">Steps</h3>
                <div className="space-y-2">
                  {curriculum.steps.map((step, index) => (
                    <button
                      key={index}
                      className={`block w-full text-left p-2 rounded ${selectedStepIndex === index ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}
                      onClick={() => setSelectedStepIndex(index)}
                    >
                      <p className="font-medium truncate">{index + 1}. {step.title}</p>
                      <p className="text-xs text-gray-400">{step.estimated_time}</p>
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Step detail content */}
              <div className="md:col-span-3">
                <CurriculumStepDetail 
                  stepDetail={detailedSteps[selectedStepIndex]} 
                  stepIndex={selectedStepIndex}
                />
              </div>
            </div>
          )}
          
          {activeTab === 'roadmap' && (
            <CurriculumRoadmap roadmapData={roadmapData} />
          )}
        </div>
      )}
    </div>
  );
};

export default CurriculumPage;
