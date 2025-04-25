import { Loader } from 'lucide-react';
import React from 'react';

const Spinner = ({ size = 'md', className = '' }) => {
  return (
    <div className={` animate-spin ${className}`}><Loader className='opacity-60 stroke-3'/></div>
  );
};

export default Spinner;
