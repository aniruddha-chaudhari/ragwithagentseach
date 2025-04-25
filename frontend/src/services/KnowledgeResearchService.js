const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || '';

// Headers with API key
const headers = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY
};

export const knowledgeResearchService = {
  // Get all knowledge researches
  getAll: async () => {
    try {
      const response = await fetch(`${API_URL}/knowledge`, {
        headers
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get knowledge researches');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting knowledge researches:', error);
      throw error;
    }
  },

  // Create a new research with full generation
  create: async (topic, options = {}) => {
    try {
      const response = await fetch(`${API_URL}/knowledge`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          topic,
          depth: options.depth || 3,
          source_url: options.sourceUrl
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create research');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating research:', error);
      throw error;
    }
  },
  
  // Create a new empty research
  createEmpty: async (researchName) => {
    try {
      const response = await fetch(`${API_URL}/knowledge/new`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          research_name: researchName
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create empty research');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating empty research:', error);
      throw error;
    }
  },
  
  // Get a research by ID
  getById: async (researchId) => {
    try {
      const response = await fetch(`${API_URL}/knowledge/${researchId}`, {
        headers
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get research');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting research:', error);
      throw error;
    }
  },
  
  // Modify an existing research
  modifyResearch: async (researchId, modificationText) => {
    try {
      const response = await fetch(`${API_URL}/knowledge/${researchId}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({
          modification_text: modificationText
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to modify research');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error modifying research:', error);
      throw error;
    }
  },
  
  // Delete a research
  deleteResearch: async (researchId) => {
    try {
      const response = await fetch(`${API_URL}/knowledge/${researchId}`, {
        method: 'DELETE',
        headers
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete research');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error deleting research:', error);
      throw error;
    }
  },
  
  // Generate section details for a research
  generateSectionDetails: async (researchId) => {
    try {
      const response = await fetch(`${API_URL}/knowledge/${researchId}/details`, {
        method: 'POST',
        headers
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate section details');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error generating section details:', error);
      throw error;
    }
  },
  
  // Get a specific section detail
  getSectionDetail: async (researchId, sectionIndex) => {
    try {
      const response = await fetch(`${API_URL}/knowledge/${researchId}/details/${sectionIndex}`, {
        headers
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get section detail');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting section detail:', error);
      throw error;
    }
  },
  
  // Generate a knowledge map
  generateKnowledgeMap: async (researchId) => {
    try {
      const response = await fetch(`${API_URL}/knowledge/${researchId}/map`, {
        headers
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate knowledge map');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error generating knowledge map:', error);
      throw error;
    }
  }
};