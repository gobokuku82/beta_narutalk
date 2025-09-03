import React from 'react';
import { motion } from 'framer-motion';

interface CustomVisualizationProps {
  data: any;
  config?: Record<string, any>;
}

export const CustomVisualization: React.FC<CustomVisualizationProps> = ({ data, config = {} }) => {
  // Handle HTML content
  if (typeof data === 'string' && data.includes('<')) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="w-full p-4 bg-white dark:bg-gray-800 rounded-lg"
        dangerouslySetInnerHTML={{ __html: data }}
      />
    );
  }

  // Handle JSON data with custom rendering
  if (typeof data === 'object') {
    // Check for specific visualization types
    if (data.type === 'progress') {
      return <ProgressVisualization data={data} />;
    }
    
    if (data.type === 'metric') {
      return <MetricVisualization data={data} />;
    }

    if (data.type === 'timeline') {
      return <TimelineVisualization data={data} />;
    }

    // Default JSON display
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="w-full p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
      >
        <pre className="text-sm text-gray-700 dark:text-gray-300 overflow-x-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      </motion.div>
    );
  }

  // Handle plain text
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full p-4 bg-white dark:bg-gray-800 rounded-lg"
    >
      <p className="text-gray-700 dark:text-gray-300">{data}</p>
    </motion.div>
  );
};

// Progress Visualization Component
const ProgressVisualization: React.FC<{ data: any }> = ({ data }) => {
  const { value, max = 100, label, color = '#6366f1' } = data;
  const percentage = (value / max) * 100;

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>
          <span className="text-sm text-gray-500">{value}/{max}</span>
        </div>
      )}
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="h-3 rounded-full"
          style={{ backgroundColor: color }}
        />
      </div>
    </div>
  );
};

// Metric Visualization Component
const MetricVisualization: React.FC<{ data: any }> = ({ data }) => {
  const { title, value, unit, change, icon } = data;

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="p-4 bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900 dark:to-primary-800 rounded-lg"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {value}
            {unit && <span className="text-sm font-normal ml-1">{unit}</span>}
          </p>
          {change && (
            <p className={`text-sm mt-1 ${change > 0 ? 'text-green-500' : 'text-red-500'}`}>
              {change > 0 ? '↑' : '↓'} {Math.abs(change)}%
            </p>
          )}
        </div>
        {icon && (
          <div className="text-4xl opacity-20">{icon}</div>
        )}
      </div>
    </motion.div>
  );
};

// Timeline Visualization Component
const TimelineVisualization: React.FC<{ data: any }> = ({ data }) => {
  const { events } = data;

  return (
    <div className="relative">
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-300 dark:bg-gray-700" />
      {events.map((event: any, index: number) => (
        <motion.div
          key={index}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.1 }}
          className="relative flex items-start mb-4"
        >
          <div className="absolute left-0 w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center">
            <div className="w-3 h-3 bg-white rounded-full" />
          </div>
          <div className="ml-12">
            <p className="text-sm text-gray-500 dark:text-gray-400">{event.date}</p>
            <h4 className="font-medium text-gray-900 dark:text-gray-100">{event.title}</h4>
            {event.description && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{event.description}</p>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  );
};