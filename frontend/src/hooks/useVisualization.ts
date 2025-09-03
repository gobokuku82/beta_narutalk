import { useState, useEffect } from 'react';
import { VisualizationData } from '../types/chat.types';
import { ChartData, TableData } from '../types/visualization.types';
import { VisualizationService } from '../services/visualizationService';

export const useVisualization = (data: VisualizationData | undefined) => {
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [tableData, setTableData] = useState<TableData | null>(null);
  const [customData, setCustomData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!data) {
      setChartData(null);
      setTableData(null);
      setCustomData(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      switch (data.type) {
        case 'chart':
          const transformed = VisualizationService.transformChartData(data.data);
          setChartData(transformed);
          setTableData(null);
          setCustomData(null);
          break;

        case 'table':
          const table = VisualizationService.transformTableData(data.data);
          setTableData(table);
          setChartData(null);
          setCustomData(null);
          break;

        case 'custom':
        case 'html':
          setCustomData(data.data);
          setChartData(null);
          setTableData(null);
          break;

        default:
          setError(`Unsupported visualization type: ${data.type}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process visualization data');
      console.error('Visualization processing error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [data]);

  return {
    chartData,
    tableData,
    customData,
    isLoading,
    error,
    hasVisualization: !!(chartData || tableData || customData),
  };
};