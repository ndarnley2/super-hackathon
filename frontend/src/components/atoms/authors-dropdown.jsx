import React from 'react';
import { FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { useDateRange } from '../../context/date-range-context';

const AuthorsDropdown = ({ authors, author, setAuthor }) => {
  const { loading } = useDateRange();

  return (
    <FormControl size="small" sx={{ minWidth: 180 }} disabled={loading}>
      <InputLabel id="author-label">Author</InputLabel>
      <Select
        labelId="author-label"
        value={author || ''}
        label="Author"
        onChange={e => setAuthor(e.target.value)}
      >
        <MenuItem value="">All</MenuItem>
        {authors.map(a => (
          <MenuItem key={a} value={a}>{a}</MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

export default AuthorsDropdown; 