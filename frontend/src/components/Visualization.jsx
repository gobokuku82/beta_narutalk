import React from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const Visualization = ({ data }) => {
  if (!data) return null;

  // 차트 렌더링
  const renderChart = (chartData, type) => {
    switch (type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#8884d8" />
            </LineChart>
          </ResponsiveContainer>
        );
      
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        );
      
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        );
      
      default:
        return null;
    }
  };

  // 테이블 렌더링
  const renderTable = (tableData) => {
    if (!tableData.rows || tableData.rows.length === 0) return null;

    return (
      <table className="data-table">
        <thead>
          <tr>
            {tableData.columns.map((col, idx) => (
              <th key={idx}>{col.label || col.key}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tableData.rows.map((row, rowIdx) => (
            <tr key={rowIdx}>
              {tableData.columns.map((col, colIdx) => (
                <td key={colIdx}>{row[col.key] || '-'}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  // HTML 렌더링
  const renderHTML = (htmlContent) => {
    return (
      <div 
        dangerouslySetInnerHTML={{ __html: htmlContent }}
        style={{ padding: '10px' }}
      />
    );
  };

  // 시각화 타입에 따른 렌더링
  return (
    <div className="visualization-container">
      {data.title && <div className="visualization-title">{data.title}</div>}
      
      {data.type === 'chart' && (
        <div className="chart-container">
          {renderChart(data.data, data.chartType || 'bar')}
        </div>
      )}
      
      {data.type === 'table' && renderTable(data.data)}
      
      {data.type === 'html' && renderHTML(data.data)}
      
      {data.type === 'custom' && (
        <div style={{ padding: '10px' }}>
          {typeof data.data === 'string' 
            ? data.data 
            : JSON.stringify(data.data, null, 2)}
        </div>
      )}
    </div>
  );
};

export default Visualization;