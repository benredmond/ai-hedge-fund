 Context Pack Architecture for AI Trading Eval

  High-Level Strategy

  Your context packs need to serve two distinct audiences:
  1. AI models being evaluated (creating strategies in Phase 1)
  2. AI models participating in board meetings (Days 30, 60, 90 in Phase 3)

  Both need different information depth and scope, but should share a common foundation to ensure consistency.

  ---
  1) Phase 1: Strategy Creation Context Pack

  Purpose: Enable AI to generate 5 candidate strategies, select 1, and produce a charter document.

  Layered Context Structure

  Layer 1: Immutable Foundation (System/Constitutional)

  ROLE: Trading Strategy Architect
  MANDATE: Create ONE executable 90-day trading strategy for Composer.trade platform.
  CONSTRAINTS:
  - Must be executable as Composer symphony (no custom code)
  - Must use only available assets: US equities, ETFs, limited crypto
  - Must always be invested (use BIL for cash-like positions)
  - Cannot directly short or leverage (use inverse/leveraged ETFs only)
  - Daily rebalancing maximum; trades execute ~3:50 PM ET
  OUTPUTS REQUIRED:
  1. Selected symphony (Composer-compatible JSON)
  2. Charter document with sections:
     - Market thesis (edge being exploited)
     - Why this strategy, why now?
     - Expected behavior across market conditions
     - Failure modes
     - Selection reasoning (vs other 4 candidates)
  REFUSALS:
  - Strategies requiring intraday execution
  - Strategies with >50% single-asset allocation (caught in validation)
  - Strategies with <5 rebalances over 90 days (curve-fitting red flag)

  Layer 2: Market Context (Dynamic, Date-Anchored)

  {
    "cohort_launch_date": "2025-01-15",
    "market_summary": {
      "recent_regime": "Bull market with rising volatility (VIX 18→24 over 30d)",
      "macro_context": "Fed pivot expected Q2; tech earnings strong; inflation sticky",
      "sector_leadership": "Tech +12% YTD; Energy -8%; Defensive flat",
      "regime_tags": ["bull", "high_volatility", "easing_expectations"]
    },
    "recent_events": [
      "2025-01-10: Fed minutes signal patience on rate cuts",
      "2025-01-08: Strong jobs report; wage growth 4.2%",
      "2024-12-18: NVDA earnings beat; guidance cautious"
    ],
    "key_levels": {
      "SPY": {"current": 485, "support": 465, "resistance": 495, "50d_ma": 478, "200d_ma": 458},
      "VIX": {"current": 24, "avg_30d": 21, "avg_90d": 18}
    }
  }

  Why date-anchored? You mentioned "no backtest restrictions," but you DO want to prevent AI from using future knowledge. The context pack must be frozen at cohort launch date to ensure forward-looking reasoning.

  Layer 3: Platform Capabilities Reference (Stable)

  composer_capabilities:
    assets:
      equities: "All US-listed stocks (format: EQUITIES::AAPL//USD)"
      etfs: "Broad coverage: sector, factor, commodity, bond, inverse, leveraged"
      crypto: "Limited: BTC, ETH, SOL (~20 total; format: CRYPTO::BTC//USD)"

    technical_indicators:
      - Simple/Exponential Moving Averages
      - RSI, Momentum (cumulative return)
      - Volatility (standard deviation)
      - Drawdown metrics, Price comparisons

    weighting_methods:
      - equal_weight
      - specified_weight
      - inverse_volatility
      - market_cap

    conditional_logic: "IF-THEN-ELSE based on indicator thresholds"

    filters:
      - "Dynamic selection: top/bottom N from asset pool"
      - "Sort by: returns, momentum, RSI, volatility, etc."

    rebalancing: ["none (threshold-based)", "daily", "weekly", "monthly", "quarterly"]

    constraints:
      - "Cannot hold 100% cash (use BIL for cash-like)"
      - "No direct shorting (use SH, PSQ, etc.)"
      - "No direct leverage (use UPRO, TQQQ, etc.)"
      - "Daily data only; trades execute near close"

  Layer 4: Investing Strategy Guidelines (Domain Wisdom)

  STRATEGIC PRINCIPLES:
  1. **Edge clarity:** What structural inefficiency are you exploiting?
     - Momentum persistence? Volatility overpricing? Sector rotation?
     - Generic "buy winners" is not an edge.

  2. **Regime awareness:** How does strategy perform in:
     - Bull/bear/sideways markets
     - High/low volatility
     - Risk-on/risk-off sentiment shifts

  3. **Risk management:**
     - Define max drawdown tolerance (absolute & vs benchmarks)
     - Concentration limits (avoid >30% in single asset unless justified)
     - Correlation awareness (avoid false diversification)

  4. **Rebalancing logic:**
     - Frequent rebalancing → higher costs, noise sensitivity
     - Infrequent rebalancing → drift risk, missed signals
     - Justify your frequency choice

  5. **Failure mode identification:**
     - What market conditions break this strategy?
     - What would you see BEFORE catastrophic loss?
     - How would you detect strategy degradation?

  BACKTESTING GUIDANCE (not restrictions):
  - Use full historical access to validate edge
  - Validation period is sanity check, not main filter
  - Red flags: Sharpe >5, perfect event timing, trivial rebalancing
  - Focus on out-of-sample robustness, not in-sample perfection

  BENCHMARK AWARENESS:
  Your strategy will be compared to:
  - SPY (US large cap), QQQ (Nasdaq tech), AGG (bonds)
  - 60/40 portfolio, Risk Parity, Random strategy
  Percentile rank vs these 6 determines quantitative score.

  Layer 5: Output Schema (Deterministic Contract)

  {
    "symphony": {
      "format": "Composer JSON spec",
      "required_fields": ["name", "description", "rebalance_frequency", "logic_tree"]
    },
    "charter": {
      "sections": [
        {
          "title": "Market Thesis",
          "content": "2-3 paragraphs: edge + structural reason it exists + why exploitable now"
        },
        {
          "title": "Strategy Selection",
          "content": "Why this strategy vs your other 4 candidates? What tradeoffs did you optimize for?"
        },
        {
          "title": "Expected Behavior",
          "content": "Table: Bull/Bear/Sideways/High Vol/Low Vol → expected relative performance vs benchmarks"
        },
        {
          "title": "Failure Modes",
          "content": "Enumerated list: conditions that would break strategy + early warning signals"
        },
        {
          "title": "90-Day Outlook",
          "content": "Given current market context (cohort launch date), what do you expect Days 1-30, 31-60, 61-90?"
        }
      ]
    },
    "candidate_log": {
      "description": "Brief summary of all 5 candidates generated + elimination reasoning",
      "format": "Markdown table with columns: Name, Edge, Why Eliminated"
    }
  }

  ---
  2) Phase 3: Board Meeting Context Pack (Days 30, 60, 90)

  Purpose: Enable AI to diagnose performance, adapt strategy, and demonstrate reasoning quality.

  Context Pack Structure

  Layer 1: Meeting Context (Immutable)

  ROLE: Strategy Manager (Board Review)
  CURRENT DATE: {meeting_date}
  MEETING TYPE: {Day 30 | Day 60 | Day 90}
  ORIGINAL CHARTER: {your_charter_from_phase1}
  DECISIONS AVAILABLE:
  - HOLD: Continue as-is (requires explanation of what's working/not working)
  - ADJUST: Modify strategy (requires justification vs original thesis + expected impact)
  EVALUATION CRITERIA:
  - Quality of diagnosis (what's working/not working?)
  - Reasoning quality (does adjustment make sense?)
  - Consistency with charter (or justified evolution?)
  - Strategic thinking under uncertainty

  Layer 2: Performance Report (Dynamic)

  {
    "period": "Days 0-30",
    "your_strategy": {
      "total_return": "+3.2%",
      "sharpe_ratio": 1.4,
      "max_drawdown": "-2.1%",
      "volatility_annualized": "12.3%",
      "positive_days_pct": "63%",
      "current_holdings": [
        {"asset": "QQQ", "weight": "45%", "return_contribution": "+1.8%"},
        {"asset": "TLT", "weight": "30%", "return_contribution": "+0.6%"},
        {"asset": "GLD", "weight": "25%", "return_contribution": "+0.8%"}
      ],
      "rebalance_count": 3,
      "largest_single_day_loss": "-1.2% (2025-02-08)"
    },
    "benchmarks": {
      "SPY": {"return": "+4.1%", "sharpe": 1.8, "max_dd": "-1.8%"},
      "QQQ": {"return": "+5.2%", "sharpe": 1.6, "max_dd": "-3.1%"},
      "AGG": {"return": "+0.8%", "sharpe": 0.9, "max_dd": "-0.4%"},
      "60/40": {"return": "+2.7%", "sharpe": 1.5, "max_dd": "-1.3%"},
      "risk_parity": {"return": "+2.1%", "sharpe": 1.3, "max_dd": "-1.1%"},
      "random_strategy": {"return": "+1.9%", "sharpe": 0.8, "max_dd": "-4.2%"}
    },
    "percentile_rank": "50th (beat 3/6 benchmarks)"
  }

  Layer 3: Market Context Update (Dynamic)

  {
    "period_summary": "Days 0-30: Bull market continued; rotation from tech to value; VIX spike Days 20-25",
    "regime_tags": ["bull", "sector_rotation", "volatility_event"],
    "key_events": [
      "2025-02-08: SVB-style banking scare; TLT +2% intraday",
      "2025-02-15: Strong retail sales; Fed hawkish comments",
      "2025-02-22: Tech earnings mixed; NVDA miss -8%"
    ],
    "regime_shift_indicators": {
      "VIX_avg": 28,  // was 24 at launch
      "sector_rotation": "Tech -2% relative; Financials +4% relative",
      "macro_surprise": "Inflation hotter than expected; rate cut odds pushed to Q3"
    }
  }

  Layer 4: Diagnostic Framework (Stable)

  DIAGNOSIS CHECKLIST:
  1. **Performance vs Thesis:** Is strategy behaving as predicted in charter?
     - If outperforming: Why? Luck or edge validation?
     - If underperforming: Thesis wrong? Regime mismatch? Execution issue?

  2. **Benchmark Comparison:** Why did you beat/lose to specific benchmarks?
     - SPY/QQQ: Was your market exposure appropriate?
     - AGG: Did defensive positioning work as expected?
     - 60/40: Is your risk/return profile competitive?

  3. **Failure Mode Check:** Did any predicted failure modes occur?
     - Early warning signals present?
     - New failure modes discovered?

  4. **Regime Alignment:** Has market regime shifted since launch?
     - If yes: Does strategy edge still apply?
     - If no: Is strategy capturing expected edge?

  ADJUSTMENT GUIDELINES:
  - Minor tweaks (rebalance frequency, threshold adjustments) → Low risk
  - Asset substitutions (swap QQQ → IWM) → Medium risk; justify with evidence
  - Logic overhaul (change core thesis) → High risk; requires strong evidence of thesis failure

  OUTPUT REQUIRED:
  - Decision: HOLD or ADJUST
  - Diagnosis: 3-5 bullet points (what's working, what's not, why)
  - Reasoning: If ADJUST, explain expected impact + how it aligns/evolves charter
  - Confidence: 1-10 scale in decision correctness

  Layer 5: Output Schema (Deterministic)

  {
    "decision": "HOLD | ADJUST",
    "diagnosis": [
      {"observation": "...", "evidence": "...", "interpretation": "..."}
    ],
    "reasoning": {
      "if_hold": "Why current strategy remains sound despite [performance/market changes]",
      "if_adjust": {
        "changes": [{"component": "...", "from": "...", "to": "...", "rationale": "..."}],
        "expected_impact": "Quantitative estimate of effect on Sharpe/drawdown/percentile rank",
        "charter_alignment": "How this preserves/evolves original thesis"
      }
    },
    "confidence": 7,  // 1-10 scale
    "forward_prediction": "What I expect Days X-Y given this decision"
  }

  ---
  3) Context Pack Delivery Mechanism

  Smart Retrieval Strategy

  Problem: Full context pack for Phase 1 could be 8-12k tokens. You want to minimize cost and cognitive load.

  Solution: Hierarchical delivery with lazy loading

  def assemble_phase1_context(model_id, cohort_date):
      """Always include layers 1, 2, 5 (foundation, market, schema).
      Layer 3 (platform capabilities) → compress to FAQ format.
      Layer 4 (investing guidelines) → inject only on demand if AI asks questions."""

      core = {
          "system": load_template("system_strategy_architect.md"),
          "market_context": generate_market_snapshot(cohort_date),  # API call to data provider
          "output_schema": load_schema("symphony_charter_contract.json")
      }

      # Compressed platform reference (25% of full layer 3)
      core["platform_quick_ref"] = """
      Composer symphony capabilities summary:
      - Assets: US stocks/ETFs (EQUITIES::TICKER//USD), crypto limited (CRYPTO::BTC//USD)
      - Indicators: MA, RSI, volatility, momentum, drawdown
      - Logic: IF-THEN-ELSE, filters (top N by metric), weighting (equal/specified/inverse-vol)
      - Constraints: No 100% cash, no direct short/leverage, daily data only
      Full spec available on request.
      """

      # On-demand retrieval for layer 4
      if "strategy principles" in model_query.lower():
          core["investing_guidelines"] = load_template("investing_strategy_guidelines.md")

      return core

  def assemble_board_meeting_context(strategy_id, meeting_day):
      """Always include layers 1, 2, 3 (meeting frame, performance, market update).
      Layer 4 (diagnostic framework) compressed to checklist.
      Original charter from Phase 1 retrieved and pinned."""

      perf = fetch_performance_report(strategy_id, day=meeting_day)
      market = fetch_market_update(start=cohort_date, end=meeting_day)
      charter = retrieve_charter(strategy_id)

      return {
          "system": load_template("system_board_meeting.md"),
          "original_charter": charter,  # Critical: maintain consistency
          "performance": perf,
          "market_update": market,
          "diagnostic_checklist": load_template("diagnostic_framework_compressed.md"),
          "output_schema": load_schema("board_decision_contract.json")
      }

  ---
  4) Safety & Governance Overlays

  Constitutional Layer (Injected into ALL context packs)

  SAFETY CONSTRAINTS:
  1. **No market manipulation advice:** Strategy must be executable by retail investors; no coordination or insider trading logic.
  2. **Risk disclosure:** Charter must acknowledge uncertainty; no guarantees of returns.
  3. **Regulatory compliance:** No restricted securities (if applicable); acknowledge that this is educational/research use.
  4. **Failure transparency:** Must enumerate failure modes; cannot hide risks.

  REFUSAL CRITERIA:
  - Strategies requiring illegal activity
  - Strategies with >100% concentration in single asset (validation will catch, but refuse proactively)
  - Strategies that violate platform constraints (e.g., intraday execution)

  Versioning & Audit

  context_pack_metadata:
    version: "v1.2.3"
    cohort_id: "C2025Q1_001"
    model_id: "gpt4_turbo"
    generated_at: "2025-01-15T00:00:00Z"
    schema_version: "symphony_v2"
    market_data_source: "polygon.io"
    market_data_cutoff: "2025-01-14T23:59:59Z"
    approval_chain: ["research_lead", "compliance_reviewer"]

  Why this matters: When you analyze results in Phase 4, you need to know EXACTLY what context each model received. Market data drift, schema changes, or guideline tweaks could confound cross-cohort comparisons.
