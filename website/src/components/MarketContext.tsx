"use client";

import { useState } from "react";
import type { MarketContextPack } from "../lib/types";

interface MarketContextProps {
  contextPack: MarketContextPack;
  cohortId: string;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatPercent(value: number | null, showSign = true): string {
  if (value === null || isNaN(value)) return "—";
  const sign = showSign && value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

function formatNumber(value: number | null, decimals = 2): string {
  if (value === null || isNaN(value)) return "—";
  return value.toFixed(decimals);
}

function formatFactorRegime(regime: string): string {
  switch (regime) {
    case "value_favored":
      return "Value-favored";
    case "growth_favored":
      return "Growth-favored";
    default:
      return "Neutral";
  }
}

function capitalizeFirst(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function MarketContext({ contextPack, cohortId }: MarketContextProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const { regime_snapshot, macro_indicators, benchmark_performance, metadata } =
    contextPack;

  const startDate = formatDate(metadata.anchor_date);
  const trendRegime = capitalizeFirst(regime_snapshot.trend.regime);
  const volRegime = capitalizeFirst(regime_snapshot.volatility.regime);
  const factorRegime = formatFactorRegime(
    regime_snapshot.factor_regime.value_vs_growth.regime
  );

  const regimeTags = `${trendRegime} · ${volRegime} Vol · ${factorRegime}`;

  return (
    <div className="mb-8">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full text-left group"
      >
        <div className="flex items-center justify-between py-2 px-3 rounded hover:bg-stone-50/50 transition-colors">
          <div className="flex items-center gap-2 text-sm">
            <span className="font-sans text-muted">{startDate}</span>
            <span className="text-border">·</span>
            <span className="font-mono text-xs text-foreground">
              {regimeTags}
            </span>
          </div>
          <span className="text-muted group-hover:text-foreground transition-colors">
            {isExpanded ? "▼" : "▶"}
          </span>
        </div>
      </button>

      {isExpanded && (
        <div className="mt-2 p-4 bg-stone-50 rounded border border-border">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left Column: Market Regime + Sector Leadership */}
            <div className="space-y-4">
              <div>
                <h4 className="font-sans text-xs text-muted uppercase tracking-wide mb-2">
                  Market Regime
                </h4>
                <div className="space-y-1 font-mono text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted">Trend</span>
                    <span className="text-foreground">
                      {trendRegime} (SPY{" "}
                      {formatPercent(
                        regime_snapshot.trend.SPY_vs_200d_ma.current
                      )}{" "}
                      vs 200d)
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Volatility</span>
                    <span className="text-foreground">
                      {volRegime} (VIX{" "}
                      {formatNumber(
                        regime_snapshot.volatility.VIX_current.current
                      )}
                      )
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Factors</span>
                    <span className="text-foreground">{factorRegime}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Momentum</span>
                    <span
                      className={
                        (regime_snapshot.factor_regime.momentum_premium_30d
                          .current ?? 0) >= 0
                          ? "text-vermillion"
                          : "text-negative"
                      }
                    >
                      {formatPercent(
                        regime_snapshot.factor_regime.momentum_premium_30d
                          .current
                      )}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-sans text-xs text-muted uppercase tracking-wide mb-2">
                  Sector Leadership (30d)
                </h4>
                <div className="space-y-1 font-mono text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted">Leaders</span>
                    <span className="text-foreground">
                      {regime_snapshot.sector_leadership.leaders
                        .slice(0, 2)
                        .map(
                          ([ticker, ret]) =>
                            `${ticker} ${formatPercent(ret, true)}`
                        )
                        .join("  ")}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Laggards</span>
                    <span className="text-negative">
                      {regime_snapshot.sector_leadership.laggards
                        .slice(0, 2)
                        .map(
                          ([ticker, ret]) =>
                            `${ticker} ${formatPercent(ret, true)}`
                        )
                        .join("  ")}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Benchmarks + Macro */}
            <div className="space-y-4">
              <div>
                <h4 className="font-sans text-xs text-muted uppercase tracking-wide mb-2">
                  Benchmarks (30d)
                </h4>
                <div className="space-y-1 font-mono text-sm">
                  {(
                    [
                      ["SPY", benchmark_performance.SPY],
                      ["QQQ", benchmark_performance.QQQ],
                      ["60/40", benchmark_performance["60_40"]],
                      ["AGG", benchmark_performance.AGG],
                    ] as const
                  ).map(([name, data]) => (
                    <div key={name} className="flex justify-between">
                      <span className="text-muted">{name}</span>
                      <span
                        className={
                          data.returns["30d"] >= 0
                            ? "text-vermillion"
                            : "text-negative"
                        }
                      >
                        {formatPercent(data.returns["30d"])}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-sans text-xs text-muted uppercase tracking-wide mb-2">
                  Macro Snapshot
                </h4>
                <div className="space-y-1 font-mono text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted">Fed Funds</span>
                    <span className="text-foreground">
                      {formatNumber(
                        macro_indicators.interest_rates.fed_funds_rate.current
                      )}
                      %
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">CPI YoY</span>
                    <span className="text-foreground">
                      {formatNumber(macro_indicators.inflation.cpi_yoy.current)}
                      %
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Yield Curve</span>
                    <span
                      className={
                        (macro_indicators.interest_rates.yield_curve_2s10s
                          .current ?? 0) >= 0
                          ? "text-foreground"
                          : "text-negative"
                      }
                    >
                      {formatPercent(
                        macro_indicators.interest_rates.yield_curve_2s10s
                          .current,
                        true
                      )}{" "}
                      (2s10s)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Download link */}
          <div className="mt-4 pt-3 border-t border-border">
            <a
              href={`/data/cohorts/${cohortId}/context.json`}
              download
              className="font-sans text-xs text-muted hover:text-foreground transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              ↓ Download full context (.json)
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
