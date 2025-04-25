import React from 'react';
import { Globe } from 'lucide-react';

const SourceViewer = ({ sources }) => {
  // Filter to only include web sources
  const webSources = sources.filter(source => source.type === 'web');
  
  // Don't render if no web sources available
  if (!webSources || webSources.length === 0) return null;

  return (
    <div className="mt-8 p-5 bg-white backdrop-blur-sm rounded-2xl border border-gray-200 max-w-3xl mx-auto animate-slide-up shadow-lg">
      <h3 className="text-base font-medium mb-4 flex items-center">
        <span className="bg-blue-100 p-1.5 rounded-md mr-2">
          <Globe size={16} className="text-blue-600" />
        </span>
        Web Sources
      </h3>
      <div className="flex flex-col gap-3 max-h-64 overflow-y-auto pr-1 scrollbar-thin">
        {webSources.map((source, index) => (
          <div 
            key={index} 
            className="p-4 bg-gray-50 rounded-xl border border-gray-200 hover:border-gray-300 transition-colors"
          >
            <div>
              <p className="font-medium flex items-center text-sm mb-2">
                <Globe size={14} className="mr-2 text-blue-600" /> 
                Web Source
              </p>
              <a 
                href={source.url} 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-blue-600 hover:text-blue-800 text-sm truncate block transition-colors"
              >
                {source.name}
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SourceViewer;
