import React from 'react';
import { Box, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import AuthorsDropdown from '../atoms/authors-dropdown';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const metricTypes = [
  { value: 'commits', label: 'Commits' },
  { value: 'additions', label: 'Additions' },
  { value: 'deletions', label: 'Deletions' },
  { value: 'total_changes', label: 'Total Changes' },
];

const MetricsChart = ({ data, metricType, setMetricType, author, setAuthor, authors, loading }) => {
  console.log('MetricsChart received data:', data);
  console.log('MetricsChart data type:', typeof data);
  
  // Ensure data is an object before processing
  const dataObj = data && typeof data === 'object' ? data : {};
  const chartData = Object.entries(dataObj).map(([day, value]) => ({ day, value }));
  console.log('Processed chartData:', chartData);

  return (
    <Box mb={4}>
      <Box display="flex" alignItems="center" gap={2} mb={2}>
        <ToggleButtonGroup
          value={metricType}
          exclusive
          onChange={(_, v) => v && setMetricType(v)}
          size="small"
        >
          {metricTypes.map(mt => (
            <ToggleButton key={mt.value} value={mt.value}>{mt.label}</ToggleButton>
          ))}
        </ToggleButtonGroup>
        <AuthorsDropdown authors={authors} author={author} setAuthor={setAuthor} />
      </Box>
      <Box height={300} bgcolor="#f5f5f5" borderRadius={2} p={2}>
        {chartData.length === 0 ? (
          <Typography variant="body1" color="text.secondary">No data to display</Typography>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 16, right: 16, left: 16, bottom: 16 }}>
              <XAxis dataKey="day" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#1976d2" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </Box>
    </Box>
  );
};

export default MetricsChart; 