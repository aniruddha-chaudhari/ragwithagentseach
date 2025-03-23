import React, { useState, useEffect } from 'react';
import { CurriculumService } from '../services/CurriculumService';
import CurriculumForm from '../components/curriculum/CurriculumForm';
import CurriculumOverview from '../components/curriculum/CurriculumOverview';
import CurriculumModifier from '../components/curriculum/CurriculumModifier';
import CurriculumStepDetail from '../components/curriculum/CurriculumStepDetail';

const CurriculumPage = () => {
  const [curriculum, setCurriculum] = useState(null);
  const [detailedSteps, setDetailedSteps] = useState({});
  const [selectedStepIndex, setSelectedStepIndex] = useState(null);
  const [isModifying, setIsModifying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [allCurricula, setAllCurricula] = useState([]);

  // Fetch all curricula when component mounts
  useEffect(() => {
    const fetchCurricula = async () => {
      try {
        setLoading(true);
        const response = await CurriculumService.getAllCurricula();
        console.log('Curricula fetched:', response);
        // Extract the array of curricula from the response
        setAllCurricula(response.curriculums || []);
        setError('');
      } catch (err) {
        console.error('Failed to fetch curricula:', err);
        setError('Failed to load existing curricula');
      } finally {
        setLoading(false);
      }
    };
    
    fetchCurricula();
  }, []);

  // Handle curriculum creation
  const handleCurriculumCreated = (newCurriculum) => {
    setCurriculum(newCurriculum);
    setActiveTab('overview');
    // Reset other states
    setDetailedSteps({});
    setSelectedStepIndex(null);
    // Add new curriculum to the list
    setAllCurricula(prev => [newCurriculum, ...prev]);
  };

  // Handle loading an existing curriculum
  const handleLoadCurriculum = async (curriculumId) => {
    try {
      setLoading(true);
      setError('');
      const loadedCurriculum = await CurriculumService.getCurriculum(curriculumId);
      setCurriculum(loadedCurriculum);
      setActiveTab('overview');
      setDetailedSteps({});
      setSelectedStepIndex(null);
    } catch (err) {
      console.error('Error loading curriculum:', err);
      setError(`Failed to load curriculum: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Handle curriculum modification
  const handleCurriculumModified = (modifiedCurriculum) => {
    setCurriculum(modifiedCurriculum);
    setIsModifying(false);
    // Since curriculum changed, reset detailed steps
    setDetailedSteps({});
    setSelectedStepIndex(null);
    // Update the curriculum in the list
    setAllCurricula(prev => prev.map(item => 
      item.curriculum_id === modifiedCurriculum.curriculum_id ? modifiedCurriculum : item
    ));
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

  return (
    <div className="container mx-auto px-4 py-8 bg-white text-gray-900">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Curriculum Generator</h1>
      </div>
      
      {error && (
        <div className="bg-red-500 text-white p-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {!curriculum ? (
        <div>
          <CurriculumForm onCurriculumCreated={handleCurriculumCreated} />
          
          {/* Display all curricula as cards */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">Your Curricula</h2>
            {loading ? (
              <div className="flex justify-center">
                <p className="text-gray-500">Loading curricula...</p>
              </div>
            ) : allCurricula.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {allCurricula.map((item) => (
                  <div 
                    key={item.curriculum_id} 
                    className="bg-white border border-gray-200 p-4 rounded-lg shadow-lg cursor-pointer hover:bg-gray-50 transition"
                    onClick={() => handleLoadCurriculum(item.curriculum_id)}
                  >
                    <h3 className="font-bold text-lg mb-2 truncate text-gray-800">{item.curriculum_name || item.title || 'Untitled Curriculum'}</h3>
                    <p className="text-sm mb-3 line-clamp-2 text-gray-600">
                      {item.overview || 'No description available'}
                    </p>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-500">
                        {item.total_time || 'Duration not specified'}
                      </span>
                      <span className="text-xs bg-blue-600 text-white rounded-full px-2 py-1">
                        {(item.steps && item.steps.length) ? `${item.steps.length} step${item.steps.length !== 1 ? 's' : ''}` : 'Details on click'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex justify-center">
                <p className="text-gray-500">No curricula found. Create one to get started!</p>
              </div>
            )}
          </div>
        </div>
      ) : isModifying ? (
        <CurriculumModifier 
          curriculum={curriculum} 
          onModified={handleCurriculumModified} 
          onCancel={() => setIsModifying(false)} 
        />
      ) : (
        <div>
          {/* Tabs */}
          <div className="flex mb-6 border-b border-gray-300">
            <button
              className={`py-2 px-4 mr-2 ${
                activeTab === 'overview' 
                  ? 'border-b-2 border-blue-500 text-blue-500' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button
              className={`py-2 px-4 mr-2 ${
                activeTab === 'details' 
                  ? 'border-b-2 border-blue-500 text-blue-500' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              onClick={() => setActiveTab('details')}
              disabled={Object.keys(detailedSteps).length === 0}
            >
              Step Details
            </button>
            {/* Return to list button */}
            <button
              className="ml-auto py-2 px-4 text-gray-600 hover:text-gray-900"
              onClick={() => setCurriculum(null)}
            >
              ← Back to List
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
              <div className="bg-white border border-gray-200 p-4 rounded-lg shadow-lg">
                <h3 className="font-bold text-lg mb-3 text-gray-800">Steps</h3>
                <div className="space-y-2">
                  {curriculum.steps.map((step, index) => (
                    <button
                      key={index}
                      className={`block w-full text-left p-2 rounded ${
                        selectedStepIndex === index 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
                      }`}
                      onClick={() => setSelectedStepIndex(index)}
                    >
                      <p className="font-medium truncate">{index + 1}. {step.title}</p>
                      <p className={`text-xs ${selectedStepIndex === index ? 'text-gray-200' : 'text-gray-500'}`}>
                        {step.estimated_time}
                      </p>
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
        </div>
      )}
    </div>
  );
};

export default CurriculumPage;
