import React from 'react';

const Ben10Logo = ({ className = "", size = 24 }) => {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Ben 10 Omnitrix Symbol - Hourglass shape */}
      <circle cx="12" cy="12" r="11" fill="#27ae60" stroke="#000" strokeWidth="3"/>
      <path 
        d="M12 3 L17 9 L17 15 L12 21 L7 15 L7 9 Z" 
        fill="#2ecc71" 
        stroke="#fff" 
        strokeWidth="1" 
      />
      <circle cx="12" cy="12" r="3" fill="#fff" />
    </svg>
  );
};

export default Ben10Logo;