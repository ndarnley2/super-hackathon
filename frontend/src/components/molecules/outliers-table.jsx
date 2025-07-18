import React from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TablePagination } from '@mui/material';
import { useDateRange } from '../../context/date-range-context';

const OutliersTable = ({ rows, page, setPage, rowsPerPage, setRowsPerPage }) => {
  const { loading } = useDateRange();

  console.log('OutliersTable rows:', rows);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  return (
    <Paper sx={{ width: '100%', mb: 2 }}>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>SHA</TableCell>
              <TableCell>Title</TableCell>
              <TableCell align="right">Author</TableCell>
              <TableCell align="right">Lines Changed</TableCell>
              <TableCell align="right">Date</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((row, idx) => (
              <TableRow key={row.sha || idx}>
                <TableCell>{row.sha || '-'}</TableCell>
                <TableCell>{row.title || '-'}</TableCell>
                <TableCell align="right">{row.author || '-'}</TableCell>
                <TableCell align="right">{row.linesChanged !== undefined ? row.linesChanged : '-'}</TableCell>
                <TableCell align="right">{row.date || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        component="div"
        count={rows.length}
        page={page}
        onPageChange={handleChangePage}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={handleChangeRowsPerPage}
        rowsPerPageOptions={[5, 10, 25]}
        labelRowsPerPage="Rows per page"
        disabled={loading}
      />
    </Paper>
  );
};

export default OutliersTable; 