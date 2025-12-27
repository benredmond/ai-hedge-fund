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
