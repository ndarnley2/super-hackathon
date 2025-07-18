import React from 'react';
import { Modal, Box, CircularProgress, Typography } from '@mui/material';
import { useDateRange } from '../../context/date-range-context';

const PleaseWaitModal = () => {
  const { loading } = useDateRange();

  return (
    <Modal open={loading} aria-labelledby="please-wait-modal" sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Box bgcolor="background.paper" p={4} borderRadius={2} boxShadow={3} display="flex" flexDirection="column" alignItems="center" gap={2}>
        <CircularProgress color="primary" />
        <Typography variant="h6">Please Wait…</Typography>
      </Box>
    </Modal>
  );
};

export default PleaseWaitModal; 