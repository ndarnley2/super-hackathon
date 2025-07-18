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
  getAuthors,
  fetchData,
} from './services/api';

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
  const [outliers, setOutliers] = useState(cache?.outliers || []);
  const [metrics, setMetrics] = useState(cache?.metrics || {});
  const [metricType, setMetricType] = useState('commits');
  const [wordCloud, setWordCloud] = useState(cache?.wordCloud || []);
  const [authorsList, setAuthorsList] = useState([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [fetchMessage, setFetchMessage] = useState('');

  // Filter outliers by selected author only
  const filteredOutliers = author ? outliers.filter(o => o.author === author) : outliers;
  
  // Fetch authors separately to populate dropdown
  const fetchAuthors = useCallback(async () => {
    try {
      const authors = await getAuthors({ startDate, endDate });
      setAuthorsList(authors);
      return authors;
    } catch (error) {
      console.error('Error fetching authors:', error);
      return [];
    }
  }, [startDate, endDate]);

  // Reload data from GitHub
  const reloadFromGitHub = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetchData({
        startDate, 
        endDate,
        useCache: false
      });
      
      setFetchMessage(result.message);
      
      // If fetch was successful, reload all data
      if (result.success) {
        await fetchAll();
      }
      
      setTimeout(() => setFetchMessage(''), 5000); // Clear message after 5 seconds
      return result.success;
    } catch (error) {
      console.error('Error reloading data from GitHub:', error);
      return false;
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, setLoading]);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [outliersRes, metricsRes, wordCloudRes, authorsRes] = await Promise.all([
        getOutliers({ startDate, endDate }),
        getMetrics({ startDate, endDate, metricType, author }),
        getWordCloud({ startDate, endDate }),
        fetchAuthors(),
      ]);
      
      console.log('Outliers data received:', outliersRes);
      setOutliers(outliersRes);
      console.log('Day of Week Metrics Response:', metricsRes);
      setMetrics(metricsRes);
      setWordCloud(wordCloudRes);
      
      // Store in cache for page reloads
      setCache({
        outliers: outliersRes,
        metrics: metricsRes,
        wordCloud: wordCloudRes,
        authors: authorsRes,
      });
    } catch (error) {
      console.error('Error fetching data:', error);
      // Use cached data if available and fetch fails
      if (cache) {
        setOutliers(cache.outliers || []);
        setMetrics(cache.metrics || {});
        setWordCloud(cache.wordCloud || []);
      }
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, metricType, author, setLoading, setCache, cache, fetchAuthors]);

  useEffect(() => {
    fetchAll();
  }, [startDate, endDate, metricType, author]);

  return (
    <>
      <PleaseWaitModal />
      <DateRangeSelector />
      {fetchMessage && (
        <div style={{ margin: '10px 0', padding: '10px', backgroundColor: '#e3f2fd', borderRadius: '4px' }}>
          {fetchMessage}
        </div>
      )}
      <ReloadButton onReload={reloadFromGitHub} />
      <OutliersTable rows={filteredOutliers} page={page} setPage={setPage} rowsPerPage={rowsPerPage} setRowsPerPage={setRowsPerPage} />
      <MetricsChart
        data={metrics}
        metricType={metricType}
        setMetricType={setMetricType}
        author={author}
        setAuthor={setAuthor}
        authors={authorsList}
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
