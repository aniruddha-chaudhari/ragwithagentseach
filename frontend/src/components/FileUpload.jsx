import React, { useState, useRef, useEffect } from 'react'

const FileUpload = ({ onFileUpload, loading }) => {
  return (
    <input
      type="file"
      onChange={onFileUpload}
      disabled={loading}
      className="w-full p-2 mb-2 border border-dashed border-gray-300 rounded-md hover:border-blue-500 cursor-pointer disabled:opacity-50"
    />
  )
}

export default FileUpload