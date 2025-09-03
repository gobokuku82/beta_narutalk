import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { ChartData } from '../../types/visualization.types';

interface ChartVisualizationProps {
  data: ChartData;
  type?: 'line' | 'bar' | 'pie' | 'area';
  config?: Record<string, any>;
}

const COLORS = ['#6366f1', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#f97316'];

export const ChartVisualization: React.FC<ChartVisualizationProps> = ({ 
  data, 
  type = 'bar',
  config = {} 
}) => {
  // Transform data for Recharts format
  const transformedData = data.labels.map((label, index) => {
    const point: any = { name: label };
    data.datasets.forEach((dataset) => {
      point[dataset.label] = dataset.data[index];
    });
    return point;
  });

  // For pie charts, we need a different data format
  const pieData = data.datasets[0]?.data.map((value, index) => ({
    name: data.labels[index],
    value: value,
  })) || [];

  const renderChart = () => {
    switch (type) {
      case 'line':
        return (
          <LineChart data={transformedData}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis dataKey="name" className="text-xs" />
            <YAxis className="text-xs" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                border: 'none', 
                borderRadius: '8px' 
              }} 
            />
            <Legend />
            {data.datasets.map((dataset, index) => (
              <Line
                key={dataset.label}
                type="monotone"
                dataKey={dataset.label}
                stroke={COLORS[index % COLORS.length]}
                strokeWidth={2}
                dot={{ fill: COLORS[index % COLORS.length] }}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        );

      case 'area':
        return (
          <AreaChart data={transformedData}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis dataKey="name" className="text-xs" />
            <YAxis className="text-xs" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                border: 'none', 
                borderRadius: '8px' 
              }} 
            />
            <Legend />
            {data.datasets.map((dataset, index) => (
              <Area
                key={dataset.label}
                type="monotone"
                dataKey={dataset.label}
                stroke={COLORS[index % COLORS.length]}
                fill={COLORS[index % COLORS.length]}
                fillOpacity={0.3}
              />
            ))}
          </AreaChart>
        );

      case 'pie':
        return (
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={(entry) => `${entry.name}: ${entry.value}`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                border: 'none', 
                borderRadius: '8px' 
              }} 
            />
          </PieChart>
        );

      case 'bar':
      default:
        return (
          <BarChart data={transformedData}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis dataKey="name" className="text-xs" />
            <YAxis className="text-xs" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                border: 'none', 
                borderRadius: '8px' 
              }} 
            />
            <Legend />
            {data.datasets.map((dataset, index) => (
              <Bar
                key={dataset.label}
                dataKey={dataset.label}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </BarChart>
        );
    }
  };

  return (
    <div className="w-full h-64 md:h-80">
      <ResponsiveContainer width="100%" height="100%">
        {renderChart()}
      </ResponsiveContainer>
    </div>
  );
};