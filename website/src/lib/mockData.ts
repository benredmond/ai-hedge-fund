import type { PerformanceData, DailyPerformance } from './types';

// Seeded random for reproducibility based on string
function seededRandom(seed: string): () => number {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    const char = seed.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return () => {
    hash = (hash * 1103515245 + 12345) & 0x7fffffff;
    return hash / 0x7fffffff;
  };
}

// Generate correlated random walk for realistic price movements
function generateRandomWalk(
  days: number,
  dailyMean: number,
  dailyVol: number,
  random: () => number
): number[] {
  const returns: number[] = [0];
  let cumulative = 0;

  for (let i = 1; i < days; i++) {
    // Box-Muller transform for normal distribution
    const u1 = random();
    const u2 = random();
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);

    const dailyReturn = dailyMean + z * dailyVol;
    cumulative += dailyReturn;
    returns.push(cumulative);
  }

  return returns;
}

// Generate benchmark data (SPY/QQQ) with market-like characteristics
function generateBenchmarkReturns(
  days: number,
  seed: string,
  annualReturn: number,
  annualVol: number
): number[] {
  const dailyMean = annualReturn / 252;
  const dailyVol = annualVol / Math.sqrt(252);
  const random = seededRandom(seed);
  return generateRandomWalk(days, dailyMean, dailyVol, random);
}

export function generateMockPerformance(
  symphonyId: string,
  strategyName: string,
  startDate: Date,
  days: number = 90
): PerformanceData {
  const random = seededRandom(symphonyId + strategyName);

  // Strategy characteristics: slightly higher return potential, higher vol
  const strategyAnnualReturn = 0.08 + (random() - 0.5) * 0.20; // 8% +/- 10%
  const strategyAnnualVol = 0.15 + random() * 0.10; // 15-25% vol

  const dailyMean = strategyAnnualReturn / 252;
  const dailyVol = strategyAnnualVol / Math.sqrt(252);

  const strategyReturns = generateRandomWalk(days, dailyMean, dailyVol, random);

  // Generate correlated benchmark data
  const spyReturns = generateBenchmarkReturns(days, symphonyId + 'SPY', 0.10, 0.16);
  const qqqReturns = generateBenchmarkReturns(days, symphonyId + 'QQQ', 0.12, 0.22);

  const daily: DailyPerformance[] = [];
  const baseNav = 10000;

  for (let i = 0; i < days; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);

    // Skip weekends
    const dayOfWeek = date.getDay();
    if (dayOfWeek === 0 || dayOfWeek === 6) continue;

    daily.push({
      date: date.toISOString().split('T')[0],
      nav: baseNav * (1 + strategyReturns[i]),
      cumulative_return: strategyReturns[i],
      spy_cumulative: spyReturns[i],
      qqq_cumulative: qqqReturns[i],
    });
  }

  return {
    symphony_id: symphonyId,
    daily,
  };
}

// Generate mock data for a cohort start date
export function getCohortStartDate(): Date {
  return new Date('2025-01-15');
}
