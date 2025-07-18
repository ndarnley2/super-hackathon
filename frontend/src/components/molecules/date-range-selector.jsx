import React from 'react';
import { Box, TextField } from '@mui/material';
import { useDateRange } from '../../context/date-range-context';

const DateRangeSelector = () => {
  const { startDate, setStartDate, endDate, setEndDate } = useDateRange();

  const handleStartChange = (e) => {
    setStartDate(new Date(e.target.value));
  };
  const handleEndChange = (e) => {
    setEndDate(new Date(e.target.value));
  };

  return (
    <Box display="flex" gap={2} alignItems="center" mb={3}>
      <TextField
        label="Start Date"
        type="date"
        size="small"
        value={startDate.toISOString().slice(0, 10)}
        onChange={handleStartChange}
        InputLabelProps={{ shrink: true }}
      />
      <TextField
        label="End Date"
        type="date"
        size="small"
        value={endDate.toISOString().slice(0, 10)}
        onChange={handleEndChange}
        InputLabelProps={{ shrink: true }}
      />
    </Box>
  );
};

export default DateRangeSelector; 