'use client';

import { useState, useMemo } from 'react';
import type { WorkflowResult, PerformanceData } from '../lib/types';
import { LeaderboardRow } from './LeaderboardRow';
import { Tooltip } from './Tooltip';

interface Props {
  strategies: WorkflowResult[];
  performanceMap?: Map<string, PerformanceData>;
}

function getStrategyKey(result: WorkflowResult, index: number): string {
  return result.symphony_id || `${result.model}-${index}`;
}

function calculateScore(result: WorkflowResult): number {
  if (result.scorecards.length === 0) return 0;
  return result.scorecards.reduce((sum, sc) => {
    const total = sc.thesis_quality + sc.edge_economics + sc.risk_framework + sc.regime_awareness + sc.strategic_coherence;
    return sum + total / 5;
  }, 0) / result.scorecards.length;
}

interface BenchmarkMetrics {
  return: number;
  alpha: number;
  sharpe: number;
  maxDrawdown: number;
}

function calcMetricsFromNavSeries(navs: number[]): BenchmarkMetrics | null {
  if (navs.length < 2) return null;

  const cumReturn = navs[navs.length - 1] / navs[0] - 1;

  const dailyReturns = navs.slice(1).map((nav, i) => navs[i] > 0 ? (nav - navs[i]) / navs[i] : 0);
  const mean = dailyReturns.reduce((a, b) => a + b, 0) / dailyReturns.length;
  const variance = dailyReturns.length > 1
    ? dailyReturns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / (dailyReturns.length - 1)
    : 0;
  const dailyVol = Math.sqrt(variance);
  const annualizedReturn = mean * 252;
  const annualizedVol = dailyVol * Math.sqrt(252);
  const sharpe = annualizedVol > 0 ? annualizedReturn / annualizedVol : 0;

  let peak = navs[0];
  let maxDrawdown = 0;
  for (const nav of navs) {
    if (nav > peak) peak = nav;
    const drawdown = (peak - nav) / peak;
    if (drawdown > maxDrawdown) maxDrawdown = drawdown;
  }

  return { return: cumReturn, alpha: 0, sharpe, maxDrawdown: -maxDrawdown };
}

export function Leaderboard({ strategies, performanceMap }: Props) {
  // Calculate performance metrics for each strategy
  const metricsMap = useMemo(() => {
    const map = new Map<number, { return: number; alpha: number; sharpe: number; maxDrawdown: number }>();
    if (!performanceMap) return map;

    strategies.forEach((result, originalIndex) => {
      const key = getStrategyKey(result, originalIndex);
      const perf = performanceMap.get(key);
      if (perf && perf.daily.length > 0) {
        const latest = perf.daily[perf.daily.length - 1];
        const cumReturn = latest.cumulative_return;
        const spyReturn = latest.spy_cumulative;
        const alpha = cumReturn - spyReturn;

        // Calculate simple Sharpe (annualized return / annualized vol)
        const dailyReturns = perf.daily.map((d, i) => {
          if (i === 0) return 0;
          const prevNav = perf.daily[i - 1].nav;
          return prevNav > 0 ? (d.nav - prevNav) / prevNav : 0;
        }).slice(1);

        const mean = dailyReturns.length > 0 ? dailyReturns.reduce((a, b) => a + b, 0) / dailyReturns.length : 0;
        const variance = dailyReturns.length > 1
          ? dailyReturns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / (dailyReturns.length - 1)
          : 0;
        const dailyVol = Math.sqrt(variance);
        const annualizedReturn = mean * 252;
        const annualizedVol = dailyVol * Math.sqrt(252);
        const sharpe = annualizedVol > 0 ? annualizedReturn / annualizedVol : 0;

        // Calculate max drawdown
        let peak = perf.daily[0].nav;
        let maxDrawdown = 0;
        for (const d of perf.daily) {
          if (d.nav > peak) peak = d.nav;
          const drawdown = (peak - d.nav) / peak;
          if (drawdown > maxDrawdown) maxDrawdown = drawdown;
        }

        map.set(originalIndex, {
          return: cumReturn,
          alpha,
          sharpe,
          maxDrawdown: -maxDrawdown, // negative for display
        });
      }
    });

    return map;
  }, [strategies, performanceMap]);

  // Extract benchmark metrics from performance data
  const benchmarkMetrics = useMemo(() => {
    if (!performanceMap) return { spy: null as BenchmarkMetrics | null, qqq: null as BenchmarkMetrics | null };

    // Find the first strategy with performance data to extract benchmark series
    let daily: { spy_cumulative: number; qqq_cumulative: number }[] | null = null;
    for (const [, perf] of performanceMap) {
      if (perf.daily.length > 0) {
        daily = perf.daily;
        break;
      }
    }

    if (!daily || daily.length < 2) return { spy: null, qqq: null };

    // Build NAV series from cumulative returns (starting at 1.0)
    const spyNavs = daily.map(d => 1 + d.spy_cumulative);
    const qqqNavs = daily.map(d => 1 + d.qqq_cumulative);

    return {
      spy: calcMetricsFromNavSeries(spyNavs),
      qqq: calcMetricsFromNavSeries(qqqNavs),
    };
  }, [performanceMap]);

  // Sort by cumulative return (descending), fall back to scorecard score
  const sortedStrategies = useMemo(() => {
    return [...strategies]
      .map((s, originalIndex) => ({ result: s, score: calculateScore(s), originalIndex }))
      .sort((a, b) => {
        const aReturn = metricsMap.get(a.originalIndex)?.return ?? -Infinity;
        const bReturn = metricsMap.get(b.originalIndex)?.return ?? -Infinity;
        return bReturn - aReturn;
      });
  }, [strategies, metricsMap]);

  // Build a merged list: strategies + benchmarks, sorted by return
  type RowEntry =
    | { type: 'strategy'; result: WorkflowResult; originalIndex: number; returnVal: number }
    | { type: 'benchmark'; ticker: string; description: string; metrics: BenchmarkMetrics; returnVal: number };

  const sortedRows = useMemo(() => {
    const rows: RowEntry[] = sortedStrategies.map(({ result, originalIndex }) => ({
      type: 'strategy' as const,
      result,
      originalIndex,
      returnVal: metricsMap.get(originalIndex)?.return ?? -Infinity,
    }));

    if (benchmarkMetrics.spy) {
      rows.push({ type: 'benchmark', ticker: 'SPY', description: 'S&P 500 ETF', metrics: benchmarkMetrics.spy, returnVal: benchmarkMetrics.spy.return });
    }
    if (benchmarkMetrics.qqq) {
      rows.push({ type: 'benchmark', ticker: 'QQQ', description: 'Nasdaq-100 ETF', metrics: benchmarkMetrics.qqq, returnVal: benchmarkMetrics.qqq.return });
    }

    rows.sort((a, b) => b.returnVal - a.returnVal);
    return rows;
  }, [sortedStrategies, metricsMap, benchmarkMetrics]);

  // Winner is the first strategy (highest return) - expand by default
  const winnerIndex = sortedRows.length > 0 ? 0 : null;

  const [expandedIndex, setExpandedIndex] = useState<number | null>(winnerIndex);
  const [detailIndex, setDetailIndex] = useState<number | null>(null);

  const handleToggleExpand = (index: number) => {
    if (expandedIndex === index) {
      setExpandedIndex(null);
      setDetailIndex(null);
    } else {
      setExpandedIndex(index);
      setDetailIndex(null);
    }
  };

  const handleToggleDetail = (index: number) => {
    setDetailIndex(detailIndex === index ? null : index);
  };

  // Calculate strategy rank (1-based, skipping benchmarks)
  const strategyRanks = useMemo(() => {
    const ranks = new Map<number, number>();
    let rank = 1;
    for (const row of sortedRows) {
      if (row.type === 'strategy') {
        ranks.set(row.originalIndex, rank);
        rank++;
      }
    }
    return ranks;
  }, [sortedRows]);

  // Dummy result for benchmark rows (never accessed since benchmark short-circuits rendering)
  const dummyResult = strategies[0];

  return (
    <>
      {/* Desktop: Table layout */}
      <div className="hidden md:block border border-border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-background">
              <th className="px-4 py-3 text-left font-sans text-xs font-medium text-muted uppercase tracking-wide w-12">
                #
              </th>
              <th className="px-4 py-3 text-left font-sans text-xs font-medium text-muted uppercase tracking-wide">
                Model
              </th>
              <th className="px-4 py-3 text-left font-sans text-xs font-medium text-muted uppercase tracking-wide">
                Strategy
              </th>
              <th className="px-4 py-3 text-left font-sans text-xs font-medium text-muted uppercase tracking-wide">
                Assets
              </th>
              <th className="px-4 py-3 text-right font-sans text-xs font-medium text-muted uppercase tracking-wide">
                Return
              </th>
              <th className="px-4 py-3 text-right font-sans text-xs font-medium text-muted uppercase tracking-wide">
                <Tooltip text="Excess return vs benchmark (SPY)">
                  Alpha
                </Tooltip>
              </th>
              <th className="px-4 py-3 text-right font-sans text-xs font-medium text-muted uppercase tracking-wide">
                <Tooltip text="Risk-adjusted return (return ÷ volatility)">
                  Sharpe
                </Tooltip>
              </th>
              <th className="px-4 py-3 text-right font-sans text-xs font-medium text-muted uppercase tracking-wide">
                <Tooltip text="Largest peak-to-trough decline" align="right">
                  Drawdown
                </Tooltip>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedRows.map((row, index) => {
              if (row.type === 'benchmark') {
                return (
                  <LeaderboardRow
                    key={`benchmark-${row.ticker}`}
                    result={dummyResult}
                    rank={0}
                    isWinner={false}
                    isExpanded={false}
                    showDetail={false}
                    onToggleExpand={() => {}}
                    onToggleDetail={() => {}}
                    metrics={row.metrics}
                    isMobile={false}
                    benchmark={{ ticker: row.ticker, description: row.description }}
                  />
                );
              }
              const strategyRank = strategyRanks.get(row.originalIndex) ?? 0;
              return (
                <LeaderboardRow
                  key={row.originalIndex}
                  result={row.result}
                  rank={strategyRank}
                  isWinner={strategyRank === 1}
                  isExpanded={expandedIndex === index}
                  showDetail={detailIndex === index}
                  onToggleExpand={() => handleToggleExpand(index)}
                  onToggleDetail={() => handleToggleDetail(index)}
                  metrics={metricsMap.get(row.originalIndex)}
                  isMobile={false}
                />
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile: Card layout */}
      <div className="md:hidden space-y-3">
        {sortedRows.map((row, index) => {
          if (row.type === 'benchmark') {
            return (
              <LeaderboardRow
                key={`benchmark-${row.ticker}`}
                result={dummyResult}
                rank={0}
                isWinner={false}
                isExpanded={false}
                showDetail={false}
                onToggleExpand={() => {}}
                onToggleDetail={() => {}}
                metrics={row.metrics}
                isMobile={true}
                benchmark={{ ticker: row.ticker, description: row.description }}
              />
            );
          }
          const strategyRank = strategyRanks.get(row.originalIndex) ?? 0;
          return (
            <LeaderboardRow
              key={row.originalIndex}
              result={row.result}
              rank={strategyRank}
              isWinner={strategyRank === 1}
              isExpanded={expandedIndex === index}
              showDetail={detailIndex === index}
              onToggleExpand={() => handleToggleExpand(index)}
              onToggleDetail={() => handleToggleDetail(index)}
              metrics={metricsMap.get(row.originalIndex)}
              isMobile={true}
            />
          );
        })}
      </div>
    </>
  );
}
