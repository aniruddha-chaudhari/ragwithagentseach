import React from 'react';
import { MessageSquare, BookOpen, Menu } from 'lucide-react';

const routes = [
  {
    id: 'chat',
    label: 'Chat',
    icon: MessageSquare,
  },
  {
    id: 'Curriculum',
    label: 'Curriculum',
    icon: BookOpen,
  },
];

const Sidebar = ({ currentPage, setCurrentPage, isOpen, toggleSidebar }) => {
  return (
    <div
      className={`min-h-screen bg-white shadow-lg transition-all duration-300 ease-in-out 
      ${isOpen ? 'w-72' : 'w-20'} relative`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100">
        {isOpen && (
          <h1 className="text-xl font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Teacher AI
          </h1>
        )}
        <button
          onClick={toggleSidebar}
          className="p-2.5 rounded-xl hover:bg-gray-100 transition-colors duration-200"
          aria-label="Toggle sidebar"
        >
          <Menu size={22} className="text-gray-600" />
        </button>
      </div>

      {/* Navigation */}
      <div className="flex flex-col gap-2 p-4">
        {routes.map((route) => (
          <button
            key={route.id}
            onClick={() => setCurrentPage(route.id)}
            className={`flex items-center gap-4 px-4 py-3.5 rounded-xl transition-all duration-200
              ${
                currentPage === route.id
                  ? 'bg-blue-50 text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:bg-gray-50'
              }
              ${!isOpen && 'justify-center'}`}
          >
            <route.icon
              size={22}
              className={`${
                currentPage === route.id ? 'text-blue-600' : 'text-gray-500'
              }`}
            />
            {isOpen && (
              <span
                className={`font-medium ${
                  currentPage === route.id ? 'text-blue-600' : 'text-gray-700'
                }`}
              >
                {route.label}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};

export default Sidebar;