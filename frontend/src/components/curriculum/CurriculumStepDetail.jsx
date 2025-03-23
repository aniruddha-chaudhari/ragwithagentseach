import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';

const CurriculumStepDetail = ({ stepDetail, stepIndex }) => {
  const [showRawFormat, setShowRawFormat] = useState(false);
  const [copySuccess, setCopySuccess] = useState('');
  
  useEffect(() => {
    // Log raw data for debugging
    if (stepDetail) {
      console.log("Raw step detail data:", stepDetail);
      console.log("Formatted text content:", stepDetail.formatted_text);
    }
  }, [stepDetail]);

  // Clear copy success message after 2 seconds
  useEffect(() => {
    if (copySuccess) {
      const timer = setTimeout(() => {
        setCopySuccess('');
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [copySuccess]);

  if (!stepDetail) {
    return (
      <div className="bg-white border border-gray-200 p-6 rounded-lg shadow-lg text-center">
        <p className="text-gray-700">Select a step to view its details</p>
      </div>
    );
  }

  const handleDownload = () => {
    const blob = new Blob([stepDetail.formatted_text], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${stepDetail.step_title.replace(/\s+/g, '_')}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(stepDetail.formatted_text)
      .then(() => {
        setCopySuccess('Copied!');
      })
      .catch(err => {
        console.error('Failed to copy text: ', err);
        setCopySuccess('Failed to copy');
      });
  };

  return (
    <div className="bg-white border border-gray-200 p-6 rounded-lg shadow-lg">
      <div className="flex justify-between items-start mb-4">
        <h2 className="text-xl font-bold text-gray-800">
          Step {stepIndex + 1}: {stepDetail.step_title}
        </h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowRawFormat(!showRawFormat)}
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 text-sm font-medium py-1 px-3 rounded"
          >
            {showRawFormat ? 'Show Formatted' : 'Show Raw'}
          </button>
          <button
            onClick={handleCopy}
            className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-1 px-3 rounded flex items-center"
          >
            <span>{copySuccess || 'Copy'}</span>
          </button>
          <button
            onClick={handleDownload}
            className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-1 px-3 rounded"
          >
            Download
          </button>
        </div>
      </div>
      
      <p className="text-sm mb-4 text-gray-600">
        Estimated Time: {stepDetail.estimated_time}
      </p>
      
      <div className="pt-4 border-t border-gray-200">
        {showRawFormat ? (
          <pre className="bg-gray-100 text-gray-800 p-4 rounded overflow-auto whitespace-pre-wrap text-sm">
            {stepDetail.formatted_text}
          </pre>
        ) : (
          <div className="prose prose-gray max-w-none">
            <ReactMarkdown 
              rehypePlugins={[rehypeRaw, rehypeHighlight]} 
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({node, ...props}) => <h1 className="text-2xl font-bold my-4 text-gray-800" {...props} />,
                h2: ({node, ...props}) => <h2 className="text-xl font-bold my-3 text-gray-800" {...props} />,
                h3: ({node, ...props}) => <h3 className="text-lg font-bold my-2 text-gray-800" {...props} />,
                strong: ({node, ...props}) => <strong className="font-bold text-gray-800" {...props} />,
                code: ({node, inline, ...props}) => 
                  inline ? <code className="bg-gray-200 px-1 rounded" {...props} /> : <code {...props} />
              }}
            >
              {stepDetail.formatted_text}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
};

export default CurriculumStepDetail;
