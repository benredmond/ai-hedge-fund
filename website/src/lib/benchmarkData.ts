/**
 * Benchmark data fetcher for SPY/QQQ historical returns.
 *
 * Uses Yahoo Finance chart API (v8 endpoint) for free historical data.
 * Returns null on any error for graceful degradation.
 */

export interface BenchmarkReturns {
  date: string;
  spy_cumulative: number;
  qqq_cumulative: number;
}

interface YahooChartResponse {
  chart: {
    result: Array<{
      timestamp: number[];
      indicators: {
        quote: Array<{
          close: (number | null)[];
        }>;
        adjclose?: Array<{
          adjclose: (number | null)[];
        }>;
      };
    }> | null;
    error?: {
      code: string;
      description: string;
    };
  };
}

/**
 * Fetch historical prices for a single ticker from Yahoo Finance.
 *
 * @param ticker - Stock symbol (e.g., 'SPY', 'QQQ')
 * @param startDate - Start date for the range
 * @param endDate - End date for the range
 * @returns Map of date string to closing price, or null on error
 */
async function fetchTickerPrices(
  ticker: string,
  startDate: Date,
  endDate: Date
): Promise<Map<string, number> | null> {
  // Convert dates to Unix timestamps
  const period1 = Math.floor(startDate.getTime() / 1000);
  const period2 = Math.floor(endDate.getTime() / 1000);

  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?period1=${period1}&period2=${period2}&interval=1d`;

  try {
    const response = await fetch(url, {
      headers: {
        // User-Agent required to avoid 403
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      console.warn(`Yahoo Finance ${ticker} failed: ${response.status}`);
      return null;
    }

    const data: YahooChartResponse = await response.json();

    if (data.chart.error) {
      console.warn(`Yahoo Finance ${ticker} error: ${data.chart.error.description}`);
      return null;
    }

    const result = data.chart.result?.[0];
    if (!result?.timestamp || !result.indicators?.quote?.[0]?.close) {
      console.warn(`Yahoo Finance ${ticker}: no data in response`);
      return null;
    }

    const timestamps = result.timestamp;
    // Prefer adjusted close if available, fall back to regular close
    const prices = result.indicators.adjclose?.[0]?.adjclose ?? result.indicators.quote[0].close;

    const priceMap = new Map<string, number>();

    for (let i = 0; i < timestamps.length; i++) {
      const price = prices[i];
      if (price === null || price === undefined) {
        continue;
      }

      // Convert Unix timestamp to date string
      const date = new Date(timestamps[i] * 1000);

      // Skip weekends (shouldn't happen but just in case)
      const dayOfWeek = date.getUTCDay();
      if (dayOfWeek === 0 || dayOfWeek === 6) {
        continue;
      }

      const dateStr = date.toISOString().split('T')[0];
      priceMap.set(dateStr, price);
    }

    return priceMap;
  } catch (error) {
    console.warn(`Yahoo Finance ${ticker} fetch error:`, error);
    return null;
  }
}

/**
 * Calculate cumulative returns from a price series.
 *
 * @param prices - Map of date to price
 * @param dates - Ordered list of dates to calculate returns for
 * @returns Map of date to cumulative return
 */
function calculateCumulativeReturns(
  prices: Map<string, number>,
  dates: string[]
): Map<string, number> {
  const returns = new Map<string, number>();

  // Find first available price to use as base
  let basePrice: number | null = null;
  for (const date of dates) {
    const price = prices.get(date);
    if (price !== undefined) {
      basePrice = price;
      break;
    }
  }

  if (basePrice === null) {
    return returns;
  }

  for (const date of dates) {
    const price = prices.get(date);
    if (price !== undefined) {
      returns.set(date, (price / basePrice) - 1);
    }
  }

  return returns;
}

/**
 * Fetch benchmark returns (SPY, QQQ) for a date range.
 *
 * @param startDate - Start of the period
 * @param endDate - End of the period
 * @param tradingDates - Optional list of specific trading dates to align with
 * @returns Array of benchmark returns per date, or null on error
 */
export async function fetchBenchmarkReturns(
  startDate: Date,
  endDate: Date,
  tradingDates?: string[]
): Promise<BenchmarkReturns[] | null> {
  // Fetch SPY and QQQ in parallel
  const [spyPrices, qqqPrices] = await Promise.all([
    fetchTickerPrices('SPY', startDate, endDate),
    fetchTickerPrices('QQQ', startDate, endDate),
  ]);

  // Both must succeed for meaningful comparison
  if (!spyPrices || !qqqPrices) {
    return null;
  }

  // Determine the dates to use
  let dates: string[];
  if (tradingDates && tradingDates.length > 0) {
    // Use provided dates (align with strategy data)
    dates = tradingDates;
  } else {
    // Use all dates from SPY (largest index)
    dates = Array.from(spyPrices.keys()).sort();
  }

  if (dates.length === 0) {
    return null;
  }

  // Calculate cumulative returns
  const spyReturns = calculateCumulativeReturns(spyPrices, dates);
  const qqqReturns = calculateCumulativeReturns(qqqPrices, dates);

  const results: BenchmarkReturns[] = [];

  for (const date of dates) {
    const spyCum = spyReturns.get(date);
    const qqqCum = qqqReturns.get(date);

    // Skip dates where we don't have both benchmarks
    if (spyCum === undefined || qqqCum === undefined) {
      continue;
    }

    results.push({
      date,
      spy_cumulative: spyCum,
      qqq_cumulative: qqqCum,
    });
  }

  return results.length > 0 ? results : null;
}
