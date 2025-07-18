import React, { useCallback, useRef } from 'react';
import { Button } from '@mui/material';
import { useDateRange } from '../../context/date-range-context';

const ReloadButton = ({ onReload }) => {
  const { loading } = useDateRange();
  const timeout = useRef();

  const handleClick = useCallback(() => {
    if (timeout.current) clearTimeout(timeout.current);
    timeout.current = setTimeout(() => {
      onReload();
    }, 400);
  }, [onReload]);

  return (
    <Button style={{marginLeft: '0', marginBottom: '20px' }} variant="contained" color="primary" onClick={handleClick} disabled={loading} sx={{ ml: 2}}>
      Reload
    </Button>
  );
};

export default ReloadButton; 