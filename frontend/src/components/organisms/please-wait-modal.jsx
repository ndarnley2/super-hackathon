import React, { useState, useEffect } from 'react';
import { Modal, Box, CircularProgress, Typography, LinearProgress } from '@mui/material';
import { useDateRange } from '../../context/date-range-context';

const PleaseWaitModal = () => {
  const { loading } = useDateRange();
  const [waitTime, setWaitTime] = useState(0);
  const [message, setMessage] = useState('Loading data...');
  
  useEffect(() => {
    let timer;
    if (loading) {
      // Reset timer when loading starts
      setWaitTime(0);
      setMessage('Loading data...');
      
      timer = setInterval(() => {
        setWaitTime(prev => {
          const newTime = prev + 1;
          
          // Update message based on wait time
          if (newTime === 5) {
            setMessage('Fetching commits from GitHub...');
          } else if (newTime === 15) {
            setMessage('Still working - fetching large repositories can take time...');
          } else if (newTime === 30) {
            setMessage('Processing data, please be patient...');
          }
          
          return newTime;
        });
      }, 1000);
    }
    
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [loading]);

  return (
    <Modal 
      open={loading} 
      aria-labelledby="please-wait-modal" 
      sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}
    >
      <Box 
        bgcolor="background.paper" 
        p={4} 
        borderRadius={2} 
        boxShadow={3} 
        display="flex" 
        flexDirection="column" 
        alignItems="center" 
        gap={2}
        width="400px"
        maxWidth="90%"
      >
        <CircularProgress color="primary" />
        <Typography variant="h6" align="center">{message}</Typography>
        
        {waitTime > 10 && (
          <LinearProgress sx={{ width: '100%', mt: 1 }} />
        )}
        
        {waitTime > 5 && (
          <Typography variant="body2" color="text.secondary" align="center">
            GitHub data fetching may take up to a minute for large repositories.
            {waitTime > 20 && ' Please don\'t refresh the page.'}
          </Typography>
        )}
      </Box>
    </Modal>
  );
};

export default PleaseWaitModal; 