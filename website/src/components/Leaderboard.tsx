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

  // Winner is the first (highest score) - expand by default
  const winnerIndex = sortedStrategies.length > 0 ? 0 : null;

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
            {sortedStrategies.map(({ result, originalIndex }, index) => (
              <LeaderboardRow
                key={originalIndex}
                result={result}
                rank={index + 1}
                isWinner={index === 0}
                isExpanded={expandedIndex === index}
                showDetail={detailIndex === index}
                onToggleExpand={() => handleToggleExpand(index)}
                onToggleDetail={() => handleToggleDetail(index)}
                metrics={metricsMap.get(originalIndex)}
                isMobile={false}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile: Card layout */}
      <div className="md:hidden space-y-3">
        {sortedStrategies.map(({ result, originalIndex }, index) => (
          <LeaderboardRow
            key={originalIndex}
            result={result}
            rank={index + 1}
            isWinner={index === 0}
            isExpanded={expandedIndex === index}
            showDetail={detailIndex === index}
            onToggleExpand={() => handleToggleExpand(index)}
            onToggleDetail={() => handleToggleDetail(index)}
            metrics={metricsMap.get(originalIndex)}
            isMobile={true}
          />
        ))}
      </div>
    </>
  );
}
