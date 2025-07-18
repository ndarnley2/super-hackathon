const delay = (ms) => new Promise((res) => setTimeout(res, ms));

const authorsList = [
  'Alice', 'Bob', 'Carol', 'David', 'Eve', 'Frank', 'Grace', 'Heidi', 'Ivan', 'Judy',
  'Mallory', 'Niaj', 'Olivia', 'Peggy', 'Rupert', 'Sybil', 'Trent', 'Uma', 'Victor', 'Wendy',
];

export async function getAuthors({ startDate, endDate }) {
  await delay(400);
  return authorsList;
}

const hardcodedDates = [
  '2024-07-18', '2024-07-10', '2024-07-01', '2024-06-25', '2024-06-15',
  '2024-06-01', '2024-05-20', '2024-05-10', '2024-05-01', '2024-04-20',
  '2024-04-10', '2024-04-01', '2024-03-20', '2024-03-10', '2024-03-01',
  '2024-02-20', '2024-02-10', '2024-02-01', '2024-01-20', '2024-01-10',
];

export async function getOutliers({ startDate, endDate }) {
  await delay(500);
  return Array.from({ length: 20 }, (_, i) => ({
    sha: `sha${(i + 1).toString().padStart(4, '0')}`,
    title: [
      'Big refactor',
      'Massive update',
      'Remove dead code',
      'Add new feature',
      'Fix critical bug',
      'Update dependencies',
      'Optimize performance',
      'Rewrite module',
      'Cleanup',
      'Improve docs',
    ][i % 10] + ` #${i + 1}`,
    linesChanged: Math.floor(Math.random() * 2000) + 100,
    date: hardcodedDates[i % hardcodedDates.length],
    author: authorsList[i % authorsList.length],
  }));
}

const metricsData = {
  commits: {
    Sun: 5, Mon: 12, Tue: 8, Wed: 15, Thu: 20, Fri: 7, Sat: 3,
  },
  additions: {
    Sun: 100, Mon: 250, Tue: 180, Wed: 300, Thu: 400, Fri: 120, Sat: 60,
  },
  deletions: {
    Sun: 40, Mon: 90, Tue: 60, Wed: 110, Thu: 150, Fri: 50, Sat: 20,
  },
  total_changes: {
    Sun: 140, Mon: 340, Tue: 240, Wed: 410, Thu: 550, Fri: 170, Sat: 80,
  },
};

export async function getMetrics({ startDate, endDate, metricType, author }) {
  await delay(600);
  return metricsData[metricType] || metricsData.commits;
}

export async function getWordCloud({ startDate, endDate }) {
  await delay(300);
  return [
    { word: 'fix', count: 22 },
    { word: 'feature', count: 18 },
    { word: 'update', count: 16 },
    { word: 'add', count: 15 },
    { word: 'remove', count: 14 },
    { word: 'refactor', count: 13 },
    { word: 'test', count: 12 },
    { word: 'optimize', count: 11 },
    { word: 'docs', count: 10 },
    { word: 'performance', count: 9 },
    { word: 'security', count: 8 },
    { word: 'cleanup', count: 7 },
    { word: 'bug', count: 6 },
    { word: 'ci', count: 5 },
    { word: 'lint', count: 4 },
    { word: 'merge', count: 3 },
    { word: 'release', count: 2 },
    { word: 'hotfix', count: 2 },
    { word: 'chore', count: 1 },
    { word: 'breaking', count: 1 },
  ];
} 