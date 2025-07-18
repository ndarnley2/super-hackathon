import React from 'react';
import { Box, Typography, Chip } from '@mui/material';
import { useDateRange } from '../../context/date-range-context';

const WordCloud = ({ words }) => {
  const { loading } = useDateRange();
  if (!words || words.length === 0) return null;

  return (
    <Box mt={4} p={2} bgcolor="#f5f5f5" borderRadius={2} minHeight={180}>
      <Typography variant="subtitle1" mb={2}>Word Cloud</Typography>
      {loading ? (
        <Typography color="text.secondary">Loading…</Typography>
      ) : (
        <Box display="flex" flexWrap="wrap" gap={1}>
          {words.map(w => (
            <Chip key={w.word} label={`${w.word} (${w.count})`} size="small" color="primary" variant="outlined" />
          ))}
        </Box>
      )}
    </Box>
  );
};

export default WordCloud; 