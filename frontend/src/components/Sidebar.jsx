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
      className={`h-screen bg-gray-100 transition-all duration-300 border-r border-gray-200 ${
        isOpen ? 'w-64' : 'w-16'
      } flex flex-col`}
    >
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        {isOpen && <h1 className="text-xl font-bold text-gray-800">Teacher AI</h1>}
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-lg hover:bg-gray-200 transition-colors"
          aria-label="Toggle sidebar"
        >
          <Menu size={20} className="text-gray-700" />
        </button>
      </div>
      <div className="flex flex-col gap-2 p-3 mt-2">
        {routes.map((route) => (
          <button
            key={route.id}
            onClick={() => setCurrentPage(route.id)}
            className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
              currentPage === route.id
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-800 hover:bg-gray-200'
            }`}
          >
            <route.icon size={20} />
            {isOpen && <span className="font-medium">{route.label}</span>}
          </button>
        ))}
      </div>
    </div>
  );
};

export default Sidebar;
