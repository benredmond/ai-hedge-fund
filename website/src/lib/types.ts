// Enums matching Python Pydantic models
export type RebalanceFrequency = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'none';
export type EdgeType = 'unspecified' | 'behavioral' | 'structural' | 'informational' | 'risk_premium';
export type StrategyArchetype = 'unspecified' | 'momentum' | 'mean_reversion' | 'carry' | 'directional' | 'volatility' | 'multi_strategy';
export type ConcentrationIntent = 'diversified' | 'high_conviction' | 'core_satellite' | 'barbell' | 'sector_focus';

export interface Strategy {
  name: string;
  assets: string[];
  weights: Record<string, number>;
  rebalance_frequency: RebalanceFrequency;
  logic_tree: Record<string, unknown>;
  thesis_document: string;
  rebalancing_rationale: string;
  edge_type: EdgeType;
  archetype: StrategyArchetype;
  concentration_intent: ConcentrationIntent;
}

export interface Charter {
  market_thesis: string;
  strategy_selection: string;
  expected_behavior: string;
  failure_modes: string[];
  outlook_90d: string;
}

export interface EdgeScorecard {
  thesis_quality: number;
  edge_economics: number;
  risk_framework: number;
  regime_awareness: number;
  strategic_coherence: number;
  reasoning: string;
}

export interface SelectionReasoning {
  winner_index: number;
  why_selected: string;
  tradeoffs_accepted: string;
  alternatives_rejected: string[];
  conviction_level: number;
}

export interface WorkflowResult {
  strategy: Strategy;
  charter: Charter;
  all_candidates: Strategy[];
  scorecards: EdgeScorecard[];
  selection_reasoning: SelectionReasoning;
  symphony_id: string | null;
  deployed_at: string | null;
  strategy_summary: string | null;
  model: string;
}

export interface CohortData {
  cohort_id: string;
  strategies: WorkflowResult[];
}

export interface DailyPerformance {
  date: string;
  nav: number;
  cumulative_return: number;
  spy_cumulative: number;
  qqq_cumulative: number;
}

export interface PerformanceData {
  symphony_id: string;
  daily: DailyPerformance[];
}

// Market Context Pack types
export interface MarketContextMetadata {
  anchor_date: string;
  data_cutoff: string;
  generated_at: string;
  version: string;
}

export interface TimeSeriesValue {
  current: number | null;
  '1m_ago': number | null;
  '3m_ago': number | null;
  '6m_ago': number | null;
  '12m_ago': number | null;
}

export interface RegimeSnapshot {
  trend: {
    regime: 'bull' | 'bear';
    SPY_vs_200d_ma: TimeSeriesValue;
  };
  volatility: {
    regime: 'low' | 'normal' | 'elevated' | 'high';
    VIX_current: TimeSeriesValue;
    VIX_30d_avg: number;
  };
  breadth: {
    sectors_above_50d_ma_pct: TimeSeriesValue;
  };
  sector_leadership: {
    leaders: [string, number][];
    laggards: [string, number][];
  };
  dispersion: {
    sector_return_std_30d: number;
    regime: 'low' | 'normal' | 'high';
  };
  factor_regime: {
    value_vs_growth: {
      regime: 'value_favored' | 'growth_favored' | 'neutral';
    };
    momentum_premium_30d: TimeSeriesValue;
    quality_premium_30d: TimeSeriesValue;
    size_premium_30d: TimeSeriesValue;
  };
}

export interface MacroIndicators {
  interest_rates: {
    fed_funds_rate: TimeSeriesValue;
    treasury_10y: TimeSeriesValue;
    treasury_2y: TimeSeriesValue;
    yield_curve_2s10s: TimeSeriesValue;
  };
  inflation: {
    cpi_yoy: TimeSeriesValue;
    core_cpi_yoy: TimeSeriesValue;
    tips_spread_10y: TimeSeriesValue;
  };
  employment: {
    unemployment_rate: TimeSeriesValue;
    nonfarm_payrolls: TimeSeriesValue;
    wage_growth_yoy: TimeSeriesValue;
    initial_claims_4wk_avg: TimeSeriesValue;
  };
}

export interface BenchmarkPerformance {
  returns: {
    '30d': number;
    '60d': number;
    '90d': number;
    '1y': number;
  };
  volatility_annualized: {
    '30d': number;
    '60d': number;
    '90d': number;
  };
  sharpe_ratio: {
    '30d': number;
    '60d': number;
    '90d': number;
  };
  max_drawdown: {
    '30d': number;
    '90d': number;
  };
}

export interface MarketContextPack {
  metadata: MarketContextMetadata;
  regime_snapshot: RegimeSnapshot;
  macro_indicators: MacroIndicators;
  benchmark_performance: {
    SPY: BenchmarkPerformance;
    QQQ: BenchmarkPerformance;
    AGG: BenchmarkPerformance;
    '60_40': BenchmarkPerformance;
    risk_parity: BenchmarkPerformance;
  };
  recent_events: unknown[];
}
