'use client';

import { useState, useMemo } from 'react';
import type { WorkflowResult } from '../lib/types';
import { LeaderboardRow } from './LeaderboardRow';

interface Props {
  strategies: WorkflowResult[];
}

function calculateScore(result: WorkflowResult): number {
  if (result.scorecards.length === 0) return 0;
  return result.scorecards.reduce((sum, sc) => {
    const total = sc.thesis_quality + sc.edge_economics + sc.risk_framework + sc.regime_awareness + sc.strategic_coherence;
    return sum + total / 5;
  }, 0) / result.scorecards.length;
}

export function Leaderboard({ strategies }: Props) {
  // Sort strategies by score to determine winner
  const sortedStrategies = useMemo(() => {
    return [...strategies]
      .map((s, originalIndex) => ({ result: s, score: calculateScore(s), originalIndex }))
      .sort((a, b) => b.score - a.score);
  }, [strategies]);

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
    <div className="border border-border rounded-lg overflow-hidden">
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
              Alpha
            </th>
            <th className="px-4 py-3 text-right font-sans text-xs font-medium text-muted uppercase tracking-wide">
              Sharpe
            </th>
            <th className="px-4 py-3 text-right font-sans text-xs font-medium text-muted uppercase tracking-wide">
              Drawdown
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
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
