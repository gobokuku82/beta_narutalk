import { VisualizationData } from '../types/chat.types';
import { ChartData, TableData, CustomVisualization } from '../types/visualization.types';

export class VisualizationService {
  static parseVisualization(data: any): VisualizationData | null {
    if (!data) return null;

    // Check if data contains visualization markers
    if (typeof data === 'string') {
      // Parse markdown-embedded visualizations
      const vizMatch = data.match(/```viz\n(.*?)\n```/s);
      if (vizMatch) {
        try {
          return JSON.parse(vizMatch[1]);
        } catch (e) {
          console.error('Failed to parse visualization data:', e);
        }
      }
    }

    // Direct visualization object
    if (data.type && data.data) {
      return data as VisualizationData;
    }

    return null;
  }

  static transformChartData(rawData: any): ChartData {
    // Transform various data formats to ChartJS format
    if (Array.isArray(rawData)) {
      return {
        labels: rawData.map((_, i) => `Item ${i + 1}`),
        datasets: [{
          label: 'Data',
          data: rawData,
          backgroundColor: [
            '#6366f1',
            '#8b5cf6',
            '#10b981',
            '#f59e0b',
            '#ef4444',
            '#06b6d4',
          ],
          borderWidth: 1,
        }],
      };
    }

    if (rawData.labels && rawData.datasets) {
      return rawData;
    }

    // Handle key-value pairs
    if (typeof rawData === 'object') {
      const entries = Object.entries(rawData);
      return {
        labels: entries.map(([key]) => key),
        datasets: [{
          label: 'Values',
          data: entries.map(([, value]) => Number(value) || 0),
          backgroundColor: '#6366f1',
          borderColor: '#4f46e5',
          borderWidth: 1,
        }],
      };
    }

    return {
      labels: [],
      datasets: [],
    };
  }

  static transformTableData(rawData: any): TableData {
    if (Array.isArray(rawData)) {
      if (rawData.length === 0) {
        return { columns: [], rows: [] };
      }

      // Auto-detect columns from first row
      const firstRow = rawData[0];
      const columns = Object.keys(firstRow).map(key => ({
        key,
        label: key.charAt(0).toUpperCase() + key.slice(1),
        sortable: true,
      }));

      return {
        columns,
        rows: rawData,
      };
    }

    if (rawData.columns && rawData.rows) {
      return rawData;
    }

    // Convert object to table
    if (typeof rawData === 'object') {
      const columns = [
        { key: 'property', label: 'Property', sortable: true },
        { key: 'value', label: 'Value', sortable: true },
      ];
      const rows = Object.entries(rawData).map(([key, value]) => ({
        property: key,
        value: String(value),
      }));

      return { columns, rows };
    }

    return { columns: [], rows: [] };
  }

  static detectVisualizationType(content: string): 'chart' | 'table' | null {
    // Simple heuristics to detect visualization type from content
    const chartKeywords = ['graph', 'chart', 'plot', 'trend', 'distribution'];
    const tableKeywords = ['table', 'list', 'rows', 'columns', 'grid'];

    const lowerContent = content.toLowerCase();

    if (chartKeywords.some(keyword => lowerContent.includes(keyword))) {
      return 'chart';
    }

    if (tableKeywords.some(keyword => lowerContent.includes(keyword))) {
      return 'table';
    }

    return null;
  }
}