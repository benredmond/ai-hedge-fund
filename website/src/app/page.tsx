import {
  listCohorts,
  loadCohort,
  loadAllPerformance,
  getStrategyKey,
} from "../lib/data";
import { Leaderboard } from "../components/Leaderboard";
import { PerformanceChart } from "../components/PerformanceChart";
import type { WorkflowResult } from "../lib/types";

function calculateScore(result: WorkflowResult): number {
  if (result.scorecards.length === 0) return 0;
  return (
    result.scorecards.reduce((sum, sc) => {
      const total =
        sc.thesis_quality +
        sc.edge_economics +
        sc.risk_framework +
        sc.regime_awareness +
        sc.strategic_coherence;
      return sum + total / 5;
    }, 0) / result.scorecards.length
  );
}

export default async function Home() {
  const cohortIds = await listCohorts();
  const cohorts = await Promise.all(cohortIds.map((id) => loadCohort(id)));

  const activeCohort = cohorts.find((c) => c !== null);

  if (!activeCohort) {
    return (
      <main className="min-h-screen bg-background p-8">
        <p className="text-muted">No cohorts found.</p>
      </main>
    );
  }

  // Load performance data for all strategies
  const performanceMap = await loadAllPerformance(
    activeCohort.cohort_id,
    activeCohort.strategies,
  );

  // Sort strategies by score to determine winner (same logic as Leaderboard)
  const sortedStrategies = [...activeCohort.strategies]
    .map((s, i) => ({ result: s, index: i, score: calculateScore(s) }))
    .sort((a, b) => b.score - a.score);

  const winnerKey =
    sortedStrategies.length > 0
      ? getStrategyKey(sortedStrategies[0].result, sortedStrategies[0].index)
      : null;

  // Transform for chart
  const performances = activeCohort.strategies
    .map((strategy, index) => {
      const key = getStrategyKey(strategy, index);
      const data = performanceMap.get(key);
      if (!data) return null;
      return {
        key,
        model: strategy.model,
        strategyName: strategy.strategy.name,
        isWinner: key === winnerKey,
        data,
      };
    })
    .filter((p): p is NonNullable<typeof p> => p !== null);

  return (
    <main className="min-h-screen bg-background p-8">
      <header className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="font-sans text-xl font-semibold text-foreground">
            AI Strategy Cohort
          </h1>
          <span className="px-2 py-0.5 bg-vermillion/10 text-vermillion text-xs font-mono rounded">
            LIVE
          </span>
        </div>
        <p className="font-sans text-sm text-muted">
          <span className="uppercase tracking-wide">
            {activeCohort.cohort_id}
          </span>
          <span className="mx-2 text-border">·</span>
          <span className="font-serif italic">
            5 AI models. 90 days. Real money.
          </span>
        </p>
      </header>

      <section className="mb-8">
        <p className="font-sans text-xs text-muted uppercase tracking-wide mb-3">
          What is this?
        </p>
        <div className="max-w-2xl space-y-3">
          <p className="font-serif text-base leading-relaxed text-foreground">
            Can AI generate alpha?
          </p>
          <p className="font-serif text-base leading-relaxed text-foreground">
            This is an experiment in AI reasoning — with real stakes. We&apos;re
            not testing stock-picking. We&apos;re testing whether AI models can
            reason clearly about uncertainty, identify an edge, commit to a
            thesis, and explain when they&apos;d be wrong.
          </p>
          <p className="font-serif text-base leading-relaxed text-foreground">
            Each model designs a trading strategy. We deploy it with real money.
            90 days later, we see who reasoned well — not just who got lucky.
          </p>
        </div>
      </section>

      <details className="mb-10 max-w-2xl">
        <summary className="font-sans text-xs text-muted uppercase tracking-wide cursor-pointer hover:text-foreground transition-colors">
          How it works
        </summary>
        <div className="mt-4 space-y-4">
          <p className="font-serif text-base leading-relaxed text-foreground">
            Each model receives identical market data: macro conditions, sector
            trends, volatility regime, recent events.
          </p>
          <div className="space-y-3">
            <div className="flex gap-2">
              <span className="font-mono text-xs text-muted uppercase tracking-wide shrink-0 pt-0.5">
                GENERATE
              </span>
              <span className="text-muted shrink-0 pt-0.5">→</span>
              <span className="font-serif text-base leading-relaxed text-foreground">
                The model creates 5 distinct strategy candidates. Not variations
                — genuinely different theses about what will work.
              </span>
            </div>
            <div className="flex gap-2">
              <span className="font-mono text-xs text-muted uppercase tracking-wide shrink-0 pt-0.5">
                EVALUATE
              </span>
              <span className="text-muted shrink-0 pt-0.5">→</span>
              <span className="font-serif text-base leading-relaxed text-foreground">
                It scores each candidate across four dimensions: thesis quality,
                edge economics, risk framework, and regime awareness.
              </span>
            </div>
            <div className="flex gap-2">
              <span className="font-mono text-xs text-muted uppercase tracking-wide shrink-0 pt-0.5">
                SELECT
              </span>
              <span className="text-muted shrink-0 pt-0.5">→</span>
              <span className="font-serif text-base leading-relaxed text-foreground">
                The model picks a winner and defends the choice. Why this one?
                What&apos;s it sacrificing? What would make it wrong?
              </span>
            </div>
            <div className="flex gap-2">
              <span className="font-mono text-xs text-muted uppercase tracking-wide shrink-0 pt-0.5">
                PREDICT
              </span>
              <span className="text-muted shrink-0 pt-0.5">→</span>
              <span className="font-serif text-base leading-relaxed text-foreground">
                It writes falsifiable statements — specific, checkable
                predictions about how the strategy should behave.
              </span>
            </div>
            <div className="flex gap-2">
              <span className="font-mono text-xs text-muted uppercase tracking-wide shrink-0 pt-0.5">
                DEPLOY
              </span>
              <span className="text-muted shrink-0 pt-0.5">→</span>
              <span className="font-serif text-base leading-relaxed text-foreground">
                We put real money behind it on Composer.trade.
              </span>
            </div>
          </div>
          <p className="font-serif text-base leading-relaxed text-muted italic">
            Coming next cohort: board meetings every 30 days, where a panel of
            AI models reviews performance against the original thesis and
            debates whether to hold or adjust.
          </p>
        </div>
      </details>

      <div className="mb-8">
        <PerformanceChart performances={performances} />
      </div>

      <Leaderboard strategies={activeCohort.strategies} />

      <footer className="mt-12 pt-6 border-t border-border">
        <p className="font-sans text-xs text-muted">
          Built by{" "}
          <a
            href="https://benr.build"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline"
          >
            Ben
          </a>{" "}
          · An experiment in AI-generated trading strategies
        </p>
        <p className="font-sans text-xs text-muted/60 mt-1">
          Not financial advice — just robots with opinions
        </p>
      </footer>
    </main>
  );
}
