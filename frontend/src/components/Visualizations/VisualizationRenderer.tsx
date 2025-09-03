import React from 'react';
import { motion } from 'framer-motion';
import { VisualizationData } from '../../types/chat.types';
import { ChartVisualization } from './ChartVisualization';
import { TableVisualization } from './TableVisualization';
import { CustomVisualization } from './CustomVisualization';
import { VisualizationService } from '../../services/visualizationService';
import { AlertCircle } from 'lucide-react';

interface VisualizationRendererProps {
  data: VisualizationData;
  className?: string;
}

export const VisualizationRenderer: React.FC<VisualizationRendererProps> = ({ 
  data, 
  className = '' 
}) => {
  const renderVisualization = () => {
    try {
      switch (data.type) {
        case 'chart': {
          const chartData = VisualizationService.transformChartData(data.data);
          const chartType = data.config?.chartType || 'bar';
          return (
            <ChartVisualization 
              data={chartData} 
              type={chartType}
              config={data.config}
            />
          );
        }

        case 'table': {
          const tableData = VisualizationService.transformTableData(data.data);
          return <TableVisualization data={tableData} config={data.config} />;
        }

        case 'custom':
        case 'html':
          return <CustomVisualization data={data.data} config={data.config} />;

        default:
          return (
            <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
              <AlertCircle className="w-5 h-5" />
              <span>Unsupported visualization type: {data.type}</span>
            </div>
          );
      }
    } catch (error) {
      console.error('Error rendering visualization:', error);
      return (
        <div className="flex items-center gap-2 text-red-600 dark:text-red-400 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <AlertCircle className="w-5 h-5" />
          <span>Failed to render visualization</span>
        </div>
      );
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={`w-full ${className}`}
    >
      <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow-md">
        {renderVisualization()}
      </div>
    </motion.div>
  );
};