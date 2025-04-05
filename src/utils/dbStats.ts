
// Simple local storage for db statistics
const DB_STATS_KEY = 'better-bulk-recipe-stats';

interface DBStats {
  totalQueries: number;
  apiCalls: number;
  dbHits: number;
  lastUpdated: string;
}

const defaultStats: DBStats = {
  totalQueries: 0,
  apiCalls: 0,
  dbHits: 0,
  lastUpdated: new Date().toISOString()
};

export const getStats = (): DBStats => {
  try {
    const stored = localStorage.getItem(DB_STATS_KEY);
    return stored ? JSON.parse(stored) : defaultStats;
  } catch (e) {
    console.error('Failed to load DB stats:', e);
    return defaultStats;
  }
};

export const incrementTotalQueries = () => {
  const stats = getStats();
  stats.totalQueries += 1;
  stats.lastUpdated = new Date().toISOString();
  saveStats(stats);
  return stats;
};

export const incrementApiCalls = () => {
  const stats = getStats();
  stats.apiCalls += 1;
  stats.lastUpdated = new Date().toISOString();
  saveStats(stats);
  return stats;
};

export const incrementDbHits = () => {
  const stats = getStats();
  stats.dbHits += 1;
  stats.lastUpdated = new Date().toISOString();
  saveStats(stats);
  return stats;
};

const saveStats = (stats: DBStats) => {
  try {
    localStorage.setItem(DB_STATS_KEY, JSON.stringify(stats));
  } catch (e) {
    console.error('Failed to save DB stats:', e);
  }
};

export const resetStats = () => {
  defaultStats.lastUpdated = new Date().toISOString();
  saveStats(defaultStats);
  return defaultStats;
};
