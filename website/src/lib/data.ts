import fs from 'fs';
import path from 'path';
import type { CohortData, PerformanceData, WorkflowResult, DailyPerformance } from './types';
import { generateMockPerformance, getCohortStartDate } from './mockData';
import { fetchSymphonyPerformance } from './composerApi';
import { fetchBenchmarkReturns, type BenchmarkReturns } from './benchmarkData';

const DATA_DIR = path.join(process.cwd(), '..', 'data', 'cohorts');

export async function listCohorts(): Promise<string[]> {
  try {
    const entries = await fs.promises.readdir(DATA_DIR, { withFileTypes: true });
    return entries
      .filter(e => e.isDirectory())
      .map(e => e.name);
  } catch {
    return [];
  }
}

export async function loadCohort(cohortId: string): Promise<CohortData | null> {
  const filePath = path.join(DATA_DIR, cohortId, 'strategies.json');
  try {
    const content = await fs.promises.readFile(filePath, 'utf-8');
    return JSON.parse(content) as CohortData;
  } catch {
    return null;
  }
}

/**
 * Load performance data from local file.
 */
async function loadPerformanceFromFile(
  cohortId: string,
  symphonyId: string
): Promise<PerformanceData | null> {
  const filePath = path.join(DATA_DIR, cohortId, 'performance', `${symphonyId}.json`);
  try {
    const content = await fs.promises.readFile(filePath, 'utf-8');
    return JSON.parse(content) as PerformanceData;
  } catch {
    return null;
  }
}

/**
 * Load performance data for a symphony.
 *
 * Tries data sources in order:
 * 1. Composer API (if symphony_id exists and API configured)
 * 2. Local file (data/cohorts/{cohortId}/performance/{symphonyId}.json)
 * 3. Returns null (caller should fall back to mock data)
 */
export async function loadPerformance(
  cohortId: string,
  symphonyId: string
): Promise<PerformanceData | null> {
  // Try Composer API first
  const composerData = await fetchSymphonyPerformance(symphonyId);
  if (composerData) {
    return composerData;
  }

  // Fall back to local file
  return loadPerformanceFromFile(cohortId, symphonyId);
}

/**
 * Generate a unique key for a strategy based on its index.
 * Uses symphony_id if available, otherwise combines model with index.
 */
export function getStrategyKey(strategy: WorkflowResult, index: number): string {
  return strategy.symphony_id || `${strategy.model}__${index}`;
}

/**
 * Merge benchmark returns into performance data.
 */
function mergeBenchmarks(
  performance: PerformanceData,
  benchmarks: BenchmarkReturns[]
): PerformanceData {
  // Create lookup map for benchmarks
  const benchmarkMap = new Map<string, BenchmarkReturns>();
  for (const b of benchmarks) {
    benchmarkMap.set(b.date, b);
  }

  // Update daily performance with benchmarks
  const updatedDaily: DailyPerformance[] = performance.daily.map(day => {
    const benchmark = benchmarkMap.get(day.date);
    if (benchmark) {
      return {
        ...day,
        spy_cumulative: benchmark.spy_cumulative,
        qqq_cumulative: benchmark.qqq_cumulative,
      };
    }
    return day;
  });

  return {
    ...performance,
    daily: updatedDaily,
  };
}

/**
 * Load all performance data for strategies in a cohort.
 *
 * Fetches from Composer API and Yahoo Finance when available,
 * falls back to mock data when not.
 */
export async function loadAllPerformance(
  cohortId: string,
  strategies: WorkflowResult[]
): Promise<Map<string, PerformanceData>> {
  const result = new Map<string, PerformanceData>();
  const startDate = getCohortStartDate();

  // Load performance for each strategy
  const performancePromises = strategies.map(async (strategy, i) => {
    const key = getStrategyKey(strategy, i);
    const symphonyId = strategy.symphony_id || strategy.model;

    // Try loading real data first
    const realData = await loadPerformance(cohortId, symphonyId);
    if (realData) {
      return { key, data: realData, isReal: true };
    }

    // Fall back to mock data
    const mockData = generateMockPerformance(
      symphonyId,
      strategy.strategy.name,
      startDate
    );
    return { key, data: mockData, isReal: false };
  });

  const performances = await Promise.all(performancePromises);

  // Collect all trading dates from any real performance data
  let tradingDates: string[] = [];
  for (const { data, isReal } of performances) {
    if (isReal && data.daily.length > 0) {
      tradingDates = data.daily.map(d => d.date);
      break;
    }
  }

  // If no real data, use mock data dates
  if (tradingDates.length === 0 && performances.length > 0) {
    tradingDates = performances[0].data.daily.map(d => d.date);
  }

  // Fetch benchmark returns for the date range
  let benchmarks: BenchmarkReturns[] | null = null;
  if (tradingDates.length > 0) {
    const firstDate = new Date(tradingDates[0]);
    const lastDate = new Date(tradingDates[tradingDates.length - 1]);
    // Add a day buffer to ensure we get all data
    firstDate.setDate(firstDate.getDate() - 1);
    lastDate.setDate(lastDate.getDate() + 1);

    benchmarks = await fetchBenchmarkReturns(firstDate, lastDate, tradingDates);
  }

  // Merge benchmarks into each performance record
  for (const { key, data } of performances) {
    if (benchmarks) {
      result.set(key, mergeBenchmarks(data, benchmarks));
    } else {
      result.set(key, data);
    }
  }

  return result;
}
