import React from 'react';

const SourceViewer = ({ sources }) => {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
      <h3 className="text-lg font-medium mb-2">Sources</h3>
      <div className="flex flex-col gap-2 max-h-64 overflow-y-auto">
        {sources.map((source, index) => (
          <div key={index} className="p-2 border-b last:border-b-0">
            {source.type === 'web' ? (
              <div>
                <p className="font-medium flex items-center">
                  <span className="mr-1">🌐</span> Web Source:
                </p>
                <a 
                  href={source.url} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="text-blue-500 hover:underline text-sm"
                >
                  {source.name}
                </a>
              </div>
            ) : source.type === 'image' ? (
              <div>
                <p className="font-medium flex items-center">
                  <span className="mr-1">🖼️</span> Image: {source.name}
                </p>
                {source.content && (
                  <p className="text-sm text-gray-600 mt-1">{source.content}</p>
                )}
              </div>
            ) : (
              <div>
                <p className="font-medium flex items-center">
                  <span className="mr-1">📄</span> Document: {source.name}
                </p>
                {source.content && (
                  <p className="text-sm text-gray-600 mt-1">{source.content}</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default SourceViewer;
