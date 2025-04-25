import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import KnowledgeSearch from '../components/KnowledgeSearch';
import { ArrowLeft, BookOpen, Edit3, Trash2, Plus, FileText, BookOpen as BookIcon } from 'lucide-react';
import { knowledgeResearchService } from '../services/KnowledgeResearchService';
import Spinner from '../components/ui/Spinner';

const ResearchPage = () => {
  const navigate = useNavigate();
  const { researchId } = useParams();
  const [researches, setResearches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [newResearchName, setNewResearchName] = useState('');
  const [currentResearch, setCurrentResearch] = useState(null);
  const [searchSuccessful, setSearchSuccessful] = useState(false);
  const [researchResponse, setResearchResponse] = useState(null);

  // Fetch all knowledge researches on initial load
  useEffect(() => {
    const fetchResearches = async () => {
      setLoading(true);
      try {
        const data = await knowledgeResearchService.getAll();
        setResearches(data.researches || []);
      } catch (error) {
        console.error('Error fetching researches:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchResearches();
  }, []);

  // Fetch specific research if ID is provided
  useEffect(() => {
    if (researchId) {
      const fetchResearch = async () => {
        setLoading(true);
        try {
          const data = await knowledgeResearchService.getById(researchId);
          setCurrentResearch(data);
        } catch (error) {
          console.error('Error fetching research details:', error);
          navigate('/research'); // Redirect if research not found
        } finally {
          setLoading(false);
        }
      };

      fetchResearch();
    } else {
      setCurrentResearch(null);
    }
  }, [researchId, navigate]);

  // Create new empty research
  const handleCreateEmptyResearch = async () => {
    if (!newResearchName.trim()) {
      alert('Please enter a research name');
      return;
    }

    setLoading(true);
    try {
      const research = await knowledgeResearchService.createEmpty(newResearchName);
      setResearches([...researches, research]);
      setCreateModalOpen(false);
      setNewResearchName('');
      alert('Research created successfully');
      navigate(`/research/${research.id}`);
    } catch (error) {
      console.error('Error creating research:', error);
      alert('Failed to create research');
    } finally {
      setLoading(false);
    }
  };

  // Delete research
  const handleDeleteResearch = async (id) => {
    if (window.confirm('Are you sure you want to delete this research?')) {
      setLoading(true);
      try {
        await knowledgeResearchService.deleteResearch(id);
        setResearches(researches.filter(research => research.id !== id));
        if (currentResearch && currentResearch.id === id) {
          navigate('/research');
        }
      } catch (error) {
        console.error('Error deleting research:', error);
        alert('Failed to delete research');
      } finally {
        setLoading(false);
      }
    }
  };

  // Generate section details
  const handleGenerateDetails = async (id) => {
    setLoading(true);
    try {
      await knowledgeResearchService.generateSectionDetails(id);
      // Refresh the current research
      const updated = await knowledgeResearchService.getById(id);
      setCurrentResearch(updated);
      setSearchSuccessful(true);
      setResearchResponse(updated);
      alert('Section details generated successfully');
      
      // Navigate to curriculum overview page after successful response
      navigate('/curriculum/overview');
    } catch (error) {
      console.error('Error generating details:', error);
      alert('Failed to generate section details');
    } finally {
      setLoading(false);
    }
  };

  // Generate knowledge map
  const handleGenerateMap = async (id) => {
    setLoading(true);
    try {
      const mapData = await knowledgeResearchService.generateKnowledgeMap(id);
      // Here you would handle the map data - perhaps open a modal to display it
      console.log('Map data:', mapData);
      setSearchSuccessful(true);
      setResearchResponse(mapData);
      alert('Knowledge map generated successfully');
      
      // Navigate to curriculum overview page after successful response
      navigate('/curriculum/overview');
    } catch (error) {
      console.error('Error generating map:', error);
      alert('Failed to generate knowledge map');
    } finally {
      setLoading(false);
    }
  };

  // Custom handler for knowledge search completion
  const handleSearchComplete = (response) => {
    setSearchSuccessful(true);
    setResearchResponse(response);
    
    // Navigate to curriculum overview page after successful response
    navigate('/curriculum/overview');
  };

  // Render create modal
  const renderCreateModal = () => {
    if (!createModalOpen) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <h2 className="text-xl font-bold mb-4">Create New Research</h2>
          <input
            type="text"
            placeholder="Research name"
            value={newResearchName}
            onChange={(e) => setNewResearchName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md mb-4"
          />
          <div className="flex justify-end space-x-2">
            <button
              onClick={() => {
                setCreateModalOpen(false);
                setNewResearchName('');
              }}
              className="px-4 py-2 bg-gray-200 rounded-md"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateEmptyResearch}
              className="px-4 py-2 bg-black text-white rounded-md"
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="container mx-auto px-4 py-8 bg-white text-gray-900">
      <div className="mb-6">
        <button 
          onClick={() => navigate('/')}
          className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          aria-label="Back to Chat"
          title="Back to Chat"
        >
          <ArrowLeft size={24} className="text-gray-700" />
        </button>
      </div>
      
      {/* Knowledge Research Section */}
      <div>
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-4 text-gray-800">Knowledge Research System</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Generate comprehensive, in-depth research on any topic with our advanced knowledge system
          </p>
        </div>
        
        {!researchId && <KnowledgeSearch onSearchComplete={handleSearchComplete} />}
        
        {/* Research List Section */}
        {!researchId && (
          <div className="mt-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Your Research Projects</h2>
              <button
                onClick={() => setCreateModalOpen(true)}
                className="flex items-center space-x-1 px-3 py-2 bg-black text-white rounded-md hover:bg-gray-800"
              >
                <Plus size={16} />
                <span>New Research</span>
              </button>
            </div>
            
            {loading && !researches.length ? (
              <div className="flex justify-center py-8">
                <Spinner />
              </div>
            ) : researches.length ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {researches.map(research => (
                  <div key={research.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-medium text-lg truncate">{research.name || 'Untitled Research'}</h3>
                      <div className="flex space-x-1">
                        <button 
                          onClick={() => handleDeleteResearch(research.id)}
                          className="p-1 text-gray-500 hover:text-red-500"
                          title="Delete research"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                    <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                      {research.topic || 'No description available'}
                    </p>
                    <div className="flex space-x-3">
                      <button
                        onClick={() => navigate(`/research/${research.id}`)}
                        className="mt-2 text-blue-600 hover:underline flex items-center space-x-1"
                      >
                        <BookOpen size={16} />
                        <span>View Research</span>
                      </button>
                    
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 border border-dashed border-gray-300 rounded-lg">
                <p className="text-gray-500 mb-2">No research projects found</p>
                <button
                  onClick={() => setCreateModalOpen(true)}
                  className="text-blue-600 hover:underline flex items-center space-x-1 mx-auto"
                >
                  <Plus size={16} />
                  <span>Create your first research</span>
                </button>
              </div>
            )}
          </div>
        )}
        
        {/* Single Research View */}
        {researchId && (
          <div className="mt-4">
            {loading ? (
              <div className="flex justify-center py-12">
                <Spinner />
              </div>
            ) : currentResearch ? (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <div>
                    <h2 className="text-2xl font-bold">{currentResearch.name || 'Untitled Research'}</h2>
                    <p className="text-gray-600 mt-1">{currentResearch.topic || 'No topic specified'}</p>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleGenerateDetails(currentResearch.id)}
                      className="px-3 py-2 bg-blue-600 text-white rounded-md flex items-center space-x-1"
                      disabled={loading}
                    >
                      <FileText size={16} />
                      <span>Generate Details</span>
                    </button>
                    <button
                      onClick={() => handleGenerateMap(currentResearch.id)}
                      className="px-3 py-2 bg-green-600 text-white rounded-md flex items-center space-x-1"
                      disabled={loading}
                    >
                      <BookOpen size={16} />
                      <span>Generate Map</span>
                    </button>
                    <button
                      onClick={() => navigate(`/curriculum/overview?researchId=${currentResearch.id}`)}
                      className="px-3 py-2 bg-purple-600 text-white rounded-md flex items-center space-x-1"
                    >
                      <BookIcon size={16} />
                      <span>View Curriculum</span>
                    </button>
                  </div>
                </div>
                
                {/* Research Content */}
                <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                  {/* Sections */}
                  {currentResearch.sections && currentResearch.sections.length > 0 ? (
                    <div className="space-y-6">
                      {currentResearch.sections.map((section, index) => (
                        <div key={index} className="pb-4 border-b border-gray-200 last:border-b-0">
                          <h3 className="font-semibold text-xl mb-2">{section.title}</h3>
                          <p className="text-gray-700 whitespace-pre-line">{section.content}</p>
                          
                          {/* If section has details */}
                          {section.details && (
                            <div className="mt-3 pl-4 border-l-2 border-gray-200">
                              <p className="text-gray-600 whitespace-pre-line">{section.details}</p>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-gray-500">No content available yet</p>
                      <button
                        onClick={() => handleGenerateDetails(currentResearch.id)}
                        className="mt-2 text-blue-600 hover:underline flex items-center space-x-1 mx-auto"
                      >
                        <FileText size={16} />
                        <span>Generate content</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-500">Research not found</p>
                <button
                  onClick={() => navigate('/research')}
                  className="mt-2 text-blue-600 hover:underline"
                >
                  Go back to research list
                </button>
              </div>
            )}
          </div>
        )}
        
      
      </div>
      
      {/* Modals */}
      {renderCreateModal()}
    </div>
  );
};

export default ResearchPage;
