import axios from 'axios';

// Backend API base URL
const API_BASE_URL = 'http://localhost:5050/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Format date for API requests (YYYY-MM-DD)
 * @param {Date|string} date - Date to format
 * @returns {string} Formatted date
 */
const formatDate = (date) => {
  if (!date) return '';
  if (typeof date === 'string') {
    // If already in YYYY-MM-DD format, return as is
    if (/^\d{4}-\d{2}-\d{2}$/.test(date)) return date;
    // Otherwise parse and format
    return new Date(date).toISOString().split('T')[0];
  }
  return date.toISOString().split('T')[0];
};

/**
 * Get list of authors who have committed in the date range
 * @param {Object} params - Request parameters
 * @param {string|Date} params.startDate - Start date
 * @param {string|Date} params.endDate - End date
 * @param {string} params.repoOwner - Repository owner
 * @param {string} params.repoName - Repository name
 * @returns {Promise<Array>} List of authors
 */
export async function getAuthors({ startDate, endDate, repoOwner = 'OpenRA', repoName = 'OpenRA' }) {
  try {
    const response = await api.get('/authors', {
      params: {
        start_date: formatDate(startDate),
        end_date: formatDate(endDate),
        repo_owner: repoOwner,
        repo_name: repoName,
      },
    });
    return response.data.authors || [];
  } catch (error) {
    console.error('Error fetching authors:', error);
    return [];
  }
}

/**
 * Get commits with significant deviations in size
 * @param {Object} params - Request parameters
 * @param {string|Date} params.startDate - Start date
 * @param {string|Date} params.endDate - End date
 * @param {string} params.repoOwner - Repository owner
 * @param {string} params.repoName - Repository name
 * @returns {Promise<Array>} List of outlier commits
 */
export async function getOutliers({ startDate, endDate, repoOwner = 'OpenRA', repoName = 'OpenRA' }) {
  try {
    const response = await api.get('/deviations', {
      params: {
        start_date: formatDate(startDate),
        end_date: formatDate(endDate),
        repo_owner: repoOwner,
        repo_name: repoName,
      },
    });
    
    // Transform the response to match the expected format in the frontend
    return (response.data.commits || []).map(commit => ({
      sha: commit.sha,
      title: commit.message_title,
      linesChanged: commit.total_changes,
      date: new Date(commit.author_date).toISOString().split('T')[0],
      author: commit.author_name,
    }));
  } catch (error) {
    console.error('Error fetching outliers:', error);
    return [];
  }
}

/**
 * Get commit metrics by day of week
 * @param {Object} params - Request parameters
 * @param {string|Date} params.startDate - Start date
 * @param {string|Date} params.endDate - End date
 * @param {string} params.metricType - Type of metric (commits, additions, deletions, total_changes)
 * @param {string} params.author - Filter by author (optional)
 * @param {string} params.repoOwner - Repository owner
 * @param {string} params.repoName - Repository name
 * @returns {Promise<Object>} Metrics data by day of week
 */
export async function getMetrics({ 
  startDate, 
  endDate, 
  metricType = 'commits', 
  author = null,
  repoOwner = 'OpenRA', 
  repoName = 'OpenRA' 
}) {
  try {
    const response = await api.get('/day-of-week', {
      params: {
        start_date: formatDate(startDate),
        end_date: formatDate(endDate),
        repo_owner: repoOwner,
        repo_name: repoName,
        metric_type: metricType,
        author: author,
      },
    });
    
    return response.data.day_activity || {
      Sun: 0, Mon: 0, Tue: 0, Wed: 0, Thu: 0, Fri: 0, Sat: 0,
    };
  } catch (error) {
    console.error('Error fetching metrics:', error);
    return {
      Sun: 0, Mon: 0, Tue: 0, Wed: 0, Thu: 0, Fri: 0, Sat: 0,
    };
  }
}

/**
 * Get word cloud data from commit messages
 * @param {Object} params - Request parameters
 * @param {string|Date} params.startDate - Start date
 * @param {string|Date} params.endDate - End date
 * @param {string} params.repoOwner - Repository owner
 * @param {string} params.repoName - Repository name
 * @param {number} params.limit - Maximum number of words to return
 * @returns {Promise<Array>} Word frequency data
 */
export async function getWordCloud({ 
  startDate, 
  endDate, 
  limit = 20,
  repoOwner = 'OpenRA', 
  repoName = 'OpenRA' 
}) {
  try {
    const response = await api.get('/word-frequencies', {
      params: {
        start_date: formatDate(startDate),
        end_date: formatDate(endDate),
        repo_owner: repoOwner,
        repo_name: repoName,
        limit,
      },
    });
    
    // Transform the response to match the expected format in the frontend
    const words = response.data.word_frequencies || {};
    return Object.entries(words).map(([word, count]) => ({
      word,
      count,
    })).slice(0, limit);
  } catch (error) {
    console.error('Error fetching word cloud data:', error);
    return [];
  }
}

/**
 * Trigger a data fetch from GitHub
 * @param {Object} params - Request parameters
 * @param {string|Date} params.startDate - Start date
 * @param {string|Date} params.endDate - End date
 * @param {string} params.repoOwner - Repository owner
 * @param {string} params.repoName - Repository name
 * @param {boolean} params.useCache - Whether to use cached data
 * @returns {Promise<Object>} Fetch result
 */
export async function fetchData({
  startDate,
  endDate,
  repoOwner = 'OpenRA',
  repoName = 'OpenRA',
  useCache = true,
}) {
  try {
    // Use a longer timeout for this specific operation since fetching GitHub data can take time
    const response = await api.post('/fetch-data', {
      start_date: formatDate(startDate),
      end_date: formatDate(endDate),
      repo_owner: repoOwner,
      repo_name: repoName,
      use_cache: useCache,
    }, {
      timeout: 60000, // 60 seconds timeout for GitHub data fetching
    });
    
    return {
      success: response.data.status === 'success',
      message: response.data.message,
    };
  } catch (error) {
    console.error('Error fetching data from GitHub:', error);
    return {
      success: false,
      message: error.response?.data?.message || 'Failed to fetch data from GitHub',
    };
  }
}
