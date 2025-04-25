import React from 'react';

const CurriculumStepDetail = ({ step }) => {
  if (!step) {
    return (
      <div className="w-full max-w-4xl mx-auto bg-white border border-gray-200 rounded-lg shadow-lg p-6 text-center">
        <p className="text-gray-700">Select a step to view its details</p>
      </div>
    );
  }

  // Helper function to render content with markdown-like formatting
  const renderContent = (content) => {
    if (!content) return null;
    
    // Split by newlines and process each line
    return content.split('\n').map((line, index) => {
      // Headers
      if (line.startsWith('# ')) {
        return <h2 key={index} className="text-xl font-bold mt-4 mb-2">{line.substring(2)}</h2>;
      } else if (line.startsWith('## ')) {
        return <h3 key={index} className="text-lg font-semibold mt-3 mb-2">{line.substring(3)}</h3>;
      } else if (line.startsWith('### ')) {
        return <h4 key={index} className="text-md font-semibold mt-3 mb-1">{line.substring(4)}</h4>;
      }
      
      // Lists
      else if (line.startsWith('- ')) {
        return <li key={index} className="ml-4 mb-1">{line.substring(2)}</li>;
      } else if (line.startsWith('* ')) {
        return <li key={index} className="ml-4 mb-1">{line.substring(2)}</li>;
      } else if (line.match(/^\d+\. /)) {
        const content = line.replace(/^\d+\. /, '');
        return <li key={index} className="ml-6 mb-1 list-decimal">{content}</li>;
      }
      
      // Code blocks (simple implementation)
      else if (line.startsWith('```')) {
        return <div key={index} className="bg-gray-100 p-2 rounded my-2 font-mono text-sm">{line.substring(3)}</div>;
      }
      
      // Empty lines become paragraph breaks
      else if (line.trim() === '') {
        return <br key={index} />;
      }
      
      // Default: regular paragraph
      else {
        return <p key={index} className="mb-2">{line}</p>;
      }
    });
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-white border border-gray-200 rounded-lg shadow-lg">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-center text-gray-800">{step.title}</h2>
        <p className="text-center text-gray-600 mt-1">Estimated Time: {step.estimated_time}</p>
      </div>
      
      <div className="p-6">
        {step.objectives && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-3 text-gray-800">Learning Objectives</h3>
            <ul className="list-disc pl-5 space-y-1">
              {step.objectives.map((objective, index) => (
                <li key={index} className="text-gray-700">{objective}</li>
              ))}
            </ul>
          </div>
        )}
        
        {step.description && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-3 text-gray-800">Description</h3>
            <div className="text-gray-700 space-y-1">
              {renderContent(step.description)}
            </div>
          </div>
        )}
        
        {step.content && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-3 text-gray-800">Content</h3>
            <div className="text-gray-700 space-y-1">
              {renderContent(step.content)}
            </div>
          </div>
        )}
        
        {step.activities && step.activities.length > 0 && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-3 text-gray-800">Activities</h3>
            <div className="space-y-3">
              {step.activities.map((activity, index) => (
                <div key={index} className="bg-gray-50 p-4 rounded-md border border-gray-100">
                  <h4 className="font-medium text-gray-800 mb-2">{activity.title}</h4>
                  <p className="text-gray-700">{activity.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {step.resources && step.resources.length > 0 && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-3 text-gray-800">Resources</h3>
            <ul className="space-y-2">
              {step.resources.map((resource, index) => (
                <li key={index} className="flex items-start">
                  <span className="mr-2">📚</span>
                  <div>
                    <a 
                      href={resource.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline font-medium"
                    >
                      {resource.title}
                    </a>
                    {resource.description && (
                      <p className="text-sm text-gray-600 mt-1">{resource.description}</p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {step.assessment && (
          <div className="mt-6 p-4 bg-blue-50 rounded-md border border-blue-100">
            <h3 className="text-xl font-semibold mb-3 text-gray-800">Assessment</h3>
            <div className="text-gray-700">
              {renderContent(step.assessment)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CurriculumStepDetail;
