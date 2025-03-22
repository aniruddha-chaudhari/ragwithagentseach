import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

const CurriculumRoadmap = ({ roadmapData }) => {
  const mermaidRef = useRef(null);
  
  useEffect(() => {
    if (roadmapData && mermaidRef.current) {
      mermaid.initialize({
        startOnLoad: true,
        theme: 'dark',
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
      <div className="bg-gray-800 p-6 rounded-lg shadow-lg text-center">
        <p>No roadmap data available</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
      <h2 className="text-xl font-bold mb-4">Curriculum Roadmap</h2>
      <div ref={mermaidRef} className="overflow-auto" id="mermaid-diagram-container"></div>
    </div>
  );
};

export default CurriculumRoadmap;
