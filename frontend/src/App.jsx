import React, { useEffect, useState, useCallback } from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { createTheme } from '@mui/material/styles';
import { BrowserRouter } from 'react-router-dom';
import { DateRangeProvider, useDateRange } from './context/date-range-context';
import MainLayout from './layout/main-layout';
import PleaseWaitModal from './components/organisms/please-wait-modal';
import DateRangeSelector from './components/molecules/date-range-selector';
import ReloadButton from './components/atoms/reload-button';
import OutliersTable from './components/molecules/outliers-table';
import MetricsChart from './components/organisms/metrics-chart';
import WordCloud from './components/organisms/word-cloud';
import {
  getOutliers,
  getMetrics,
  getWordCloud,
} from './services/api-mock';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#1976d2' },
    secondary: { main: '#9c27b0' },
    background: { default: '#f4f6fa' },
  },
  typography: {
    fontFamily: 'Inter, Avenir, Helvetica, Arial, sans-serif',
  },
});

function DashboardContainer() {
  const { startDate, endDate, loading, setLoading, cache, setCache } = useDateRange();
  const [author, setAuthor] = useState('');
  const [outliers, setOutliers] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [metricType, setMetricType] = useState('commits');
  const [wordCloud, setWordCloud] = useState([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const authors = Array.from(new Set(outliers.map(o => o.author))).sort();

  // Filter outliers by selected author only
  const filteredOutliers = author ? outliers.filter(o => o.author === author) : outliers;

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [outliersRes, metricsRes, wordCloudRes] = await Promise.all([
        getOutliers({ startDate, endDate }),
        getMetrics({ startDate, endDate, metricType, author }),
        getWordCloud({ startDate, endDate }),
      ]);
      setOutliers(outliersRes);
      setMetrics(metricsRes);
      setWordCloud(wordCloudRes);
      setCache({
        outliers: outliersRes,
        metrics: metricsRes,
        wordCloud: wordCloudRes,
      });
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, metricType, author, setLoading, setCache]);

  useEffect(() => {
    fetchAll();
  }, [startDate, endDate, metricType, author]);

  return (
    <>
      <PleaseWaitModal />
      <DateRangeSelector />
      <ReloadButton onReload={fetchAll} />
      <OutliersTable rows={filteredOutliers} page={page} setPage={setPage} rowsPerPage={rowsPerPage} setRowsPerPage={setRowsPerPage} />
      <MetricsChart
        data={metrics}
        metricType={metricType}
        setMetricType={setMetricType}
        author={author}
        setAuthor={setAuthor}
        authors={authors}
        loading={loading}
      />
      <WordCloud words={wordCloud} />
    </>
  );
}

const App = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <DateRangeProvider>
        <BrowserRouter>
          <MainLayout>
            <DashboardContainer />
          </MainLayout>
        </BrowserRouter>
      </DateRangeProvider>
    </ThemeProvider>
  );
};

export default App;
