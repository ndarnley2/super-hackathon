import React from 'react';
import { AppBar, Toolbar, Typography, Container, Box } from '@mui/material';

const MainLayout = ({ children }) => (
  <Box display="flex" flexDirection="column" minHeight="100vh">
    <AppBar position="static" color="primary">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Super Hackathon Dashboard
        </Typography>
        {/* Aquí podría ir la navegación o el usuario */}
      </Toolbar>
    </AppBar>
    <Container maxWidth="lg" sx={{ flex: 1, py: 4 }}>
      {children}
    </Container>
  </Box>
);

export default MainLayout; 