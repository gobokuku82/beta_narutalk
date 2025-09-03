export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }[];
}

export interface TableData {
  columns: {
    key: string;
    label: string;
    sortable?: boolean;
    width?: string;
  }[];
  rows: Record<string, any>[];
}

export interface CustomVisualization {
  component: string;
  props: Record<string, any>;
}

export type VisualizationType = 'line' | 'bar' | 'pie' | 'doughnut' | 'area' | 'scatter' | 'table' | 'custom';

export interface VisualizationConfig {
  type: VisualizationType;
  title?: string;
  description?: string;
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  options?: Record<string, any>;
}