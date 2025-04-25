import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

const CurriculumRoadmap = ({ roadmapData }) => {
  const mermaidRef = useRef(null);
  
  useEffect(() => {
    if (roadmapData && mermaidRef.current) {
      mermaid.initialize({
        startOnLoad: true,
        theme: 'default', // Changed from 'dark' to match light theme
        securityLevel: 'loose',
        flowchart: {
          htmlLabels: true
        }
      });
      
      try {
        mermaid.render('mermaid-diagram', roadmapData.mermaid_code, (svg) => {
          if (mermaidRef.current) {
            mermaidRef.current.innerHTML = svg;
          }
        });
      } catch (error) {
        console.error('Error rendering mermaid diagram:', error);
      }
    }
  }, [roadmapData]);

  if (!roadmapData) {
    return (
      <div className="w-full max-w-4xl mx-auto bg-white border border-gray-200 rounded-lg shadow-lg p-6 text-center">
        <p className="text-gray-700">No roadmap data available</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto bg-white border border-gray-200 rounded-lg shadow-lg">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-center text-gray-800">Curriculum Roadmap</h2>
        <p className="text-center text-gray-600 mt-1">Visual learning path</p>
      </div>
      
      <div className="p-6">
        <div ref={mermaidRef} className="overflow-auto" id="mermaid-diagram-container"></div>
      </div>
    </div>
  );
};

export default CurriculumRoadmap;
