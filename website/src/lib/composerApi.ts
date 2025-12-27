/**
 * Composer Trade API client for fetching symphony performance data.
 *
 * Uses direct REST API calls with header-based authentication.
 * Returns null on any error for graceful degradation.
 */

import type { PerformanceData, DailyPerformance } from './types';

const COMPOSER_API_URL = 'https://api.composer.trade';

interface ComposerSymphonyResponse {
  epoch_ms: number[];
  series: number[];
  deposit_adjusted_series: number[];
}

interface ComposerAccountsResponse {
  accounts: Array<{
    id: string;
    name?: string;
  }>;
}

/**
 * Get Composer API credentials from environment.
 * Returns null if not configured.
 */
function getCredentials(): { apiKey: string; apiSecret: string } | null {
  const apiKey = process.env.COMPOSER_API_KEY;
  const apiSecret = process.env.COMPOSER_API_SECRET;

  if (!apiKey || !apiSecret) {
    return null;
  }

  return { apiKey, apiSecret };
}

/**
 * Build authentication headers for Composer API.
 */
function getAuthHeaders(credentials: { apiKey: string; apiSecret: string }): HeadersInit {
  return {
    'x-api-key-id': credentials.apiKey,
    'Authorization': `Bearer ${credentials.apiSecret}`,
    'Accept': 'application/json',
  };
}

/**
 * List available Composer accounts.
 * Used to discover account ID if not provided.
 */
export async function listAccounts(): Promise<string[]> {
  const credentials = getCredentials();
  if (!credentials) {
    return [];
  }

  try {
    const response = await fetch(`${COMPOSER_API_URL}/api/v0.1/accounts/list`, {
      headers: getAuthHeaders(credentials),
      next: { revalidate: 86400 }, // Cache for 24 hours - accounts rarely change
    });

    if (!response.ok) {
      console.warn(`Composer list_accounts failed: ${response.status}`);
      return [];
    }

    const data: ComposerAccountsResponse = await response.json();
    return data.accounts?.map(a => a.id) ?? [];
  } catch (error) {
    console.warn('Composer list_accounts error:', error);
    return [];
  }
}

/**
 * Get the primary Composer account ID.
 * Uses COMPOSER_ACCOUNT_ID env var if set, otherwise fetches first account.
 */
async function getAccountId(): Promise<string | null> {
  // Check environment first
  const envAccountId = process.env.COMPOSER_ACCOUNT_ID;
  if (envAccountId) {
    return envAccountId;
  }

  // Fall back to fetching accounts
  const accounts = await listAccounts();
  if (accounts.length === 0) {
    console.warn('No Composer accounts found');
    return null;
  }

  return accounts[0];
}

/**
 * Fetch symphony performance data from Composer API.
 *
 * @param symphonyId - The symphony ID to fetch performance for
 * @returns PerformanceData with daily values, or null if unavailable
 */
export async function fetchSymphonyPerformance(
  symphonyId: string
): Promise<PerformanceData | null> {
  const credentials = getCredentials();
  if (!credentials) {
    // Credentials not configured - silent failure
    return null;
  }

  const accountId = await getAccountId();
  if (!accountId) {
    return null;
  }

  try {
    const url = `${COMPOSER_API_URL}/api/v0.1/portfolio/accounts/${accountId}/symphonies/${symphonyId}`;

    const response = await fetch(url, {
      headers: getAuthHeaders(credentials),
      next: { revalidate: 3600 }, // Cache for 1 hour
    });

    if (!response.ok) {
      if (response.status === 404) {
        // Symphony not found - might be newly deployed
        console.warn(`Symphony ${symphonyId} not found in Composer`);
      } else if (response.status === 429) {
        console.warn('Composer rate limit exceeded');
      } else {
        console.warn(`Composer API error: ${response.status}`);
      }
      return null;
    }

    const data: ComposerSymphonyResponse = await response.json();
    return transformComposerResponse(symphonyId, data);
  } catch (error) {
    console.warn(`Failed to fetch Composer performance for ${symphonyId}:`, error);
    return null;
  }
}

/**
 * Transform Composer API response to our DailyPerformance format.
 *
 * Note: Composer returns absolute values. We calculate cumulative returns
 * as percentage change from first value.
 *
 * SPY/QQQ benchmarks are NOT included here - they come from benchmarkData.ts
 * and are merged in data.ts.
 */
function transformComposerResponse(
  symphonyId: string,
  data: ComposerSymphonyResponse
): PerformanceData | null {
  if (!data.epoch_ms?.length || !data.series?.length) {
    return null;
  }

  const firstValue = data.series[0];
  if (firstValue <= 0) {
    return null;
  }

  const daily: DailyPerformance[] = [];

  for (let i = 0; i < data.epoch_ms.length; i++) {
    const timestamp = data.epoch_ms[i];
    const value = data.series[i];

    // Convert epoch ms to date string (YYYY-MM-DD)
    const date = new Date(timestamp);
    const dateStr = date.toISOString().split('T')[0];

    // Skip weekends (trading days only)
    const dayOfWeek = date.getUTCDay();
    if (dayOfWeek === 0 || dayOfWeek === 6) {
      continue;
    }

    // Calculate cumulative return from first value
    const cumulativeReturn = (value / firstValue) - 1;

    daily.push({
      date: dateStr,
      nav: value,
      cumulative_return: cumulativeReturn,
      // Benchmarks will be filled in by data.ts from benchmarkData
      spy_cumulative: 0,
      qqq_cumulative: 0,
    });
  }

  return {
    symphony_id: symphonyId,
    daily,
  };
}
