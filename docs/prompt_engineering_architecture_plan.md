# Prompt Engineering Architecture Plan
**Date:** November 2, 2024 (Updated: November 3, 2024)
**Status:** Updated with Latest Run Validation Results
**Model Target:** Kimi K2 (openai:kimi-k2-0905-preview)
**Task ID:** 5fcGnzeMzoezmS5Q5LbYm
**Latest Test Run:** November 3, 2024 - Phase 5 End-to-End Integration Test

---

## Executive Summary

### Current State
- **Quality**: 6.1/10 (up from 3.2/10 baseline after 90-minute validation package)
- **Core Problem**: Only 20% (1/5) strategies implement conditional logic despite 80% (4/5) describing it in their thesis
- **Root Cause**: Validation exists in prompts but doesn't enforce - Kimi K2 bypasses non-blocking rules
- **Model**: Kimi K2 (cost-optimized) - strong narrative (7.5/10), weak implementation (5/10)

### Revised Architecture Plan (v1.2 - Post-Subagent Reviews)
**Key Changes:**
- **Restructured priorities:** Only 2 TRUE deployment blockers (35 min), not 4 (105 min)
- **Added RSIP checkpoints:** Pre-generation reasoning → Post-generation reflection → Pre-submission validation
- **Added Alpha vs Beta framework:** Security selection requirements by archetype with conceptual foundation
- **Realistic time estimates:** 8-12 hours (not 4.5 hours optimistic)
- **Pure prompt engineering:** No Pydantic validators per user request

**Expected Quality:** 6.1/10 → 8.5+/10 (+39%) through architectural prompt improvements

---

## Latest Run Validation Results (November 3, 2024)

**Test Configuration:**
- Model: Kimi K2 (openai:kimi-k2-0905-preview)
- Test: Full Phase 5 end-to-end workflow
- Result: ✅ Pipeline complete, ❌ 4 critical blockers identified

### What Worked

✅ **Post-Validation Retry Mechanism (Fix #1)**
- Successfully caught 3 thesis/logic_tree mismatches
- Retry prompt triggered and recovered all failures
- Evidence: Validation enforcement works when implemented
- **Conclusion:** Original architectural decision validated

✅ **Pipeline Orchestration**
- All 4 stages completed: Candidate Generation → Edge Scoring → Winner Selection → Charter Generation
- Token tracking functional (~43k tokens, well under budget)
- MCP integration working (FRED API calls successful)

### Critical Blockers Identified

❌ **Priority 1 Blocker #1: Asset Drift in Retry**
- **Issue:** Retry changed strategy assets instead of fixing thesis language
- **Evidence:** Candidate #1 original [XLK, XLY, XLF] → retry [XLK, XLV, XLU]
- **Impact:** Different strategy created, data integrity compromised
- **Root Cause:** Retry prompt doesn't preserve asset selection
- **Status:** NEW - not identified in original analysis

❌ **Priority 1 Blocker #2: Edge Scorecard Enforcement Broken**
- **Issue:** Strategies marked "FAIL" in reasoning but `overall_pass=True` in code
- **Evidence:** 2 strategies scored 2/5 on Edge Economics with "FAIL" recommendation but passed workflow
- **Impact:** Low-quality strategies bypass quality gate
- **Root Cause:** `overall_pass` boolean not enforced in winner selection
- **Status:** CONFIRMED - suspected in analysis, now validated

❌ **Priority 1 Blocker #3: Charter Generation Truncation**
- **Issue:** Charter Day 90 outlook section cuts off mid-sentence
- **Evidence:** "Day 90 (January 31, 2026):\n- " [ends abruptly]
- **Impact:** Incomplete charter cannot be deployed
- **Root Cause:** max_tokens insufficient or no truncation detection
- **Status:** CONFIRMED - suspected, now validated

🆕 **Priority 1 Blocker #4: Sector ETF Default (No Stock Selection)**
- **Issue:** ALL 5 candidates use broad sector ETFs instead of individual stock selection
- **Evidence:** Winner "Defensive Sector Mean Reversion" uses [XLF, XLC, XLB] - sector indexes, not specific oversold stocks
- **Impact:** Low strategic sophistication - passive sector beta, not alpha generation
- **Root Cause Analysis:**
  1. Prompts don't require stock-level analysis for mean reversion/value strategies
  2. Worked examples were ETF-heavy, setting precedent for broad ETF usage (stock-selection example now added to counterbalance)
  3. Edge Scorecard accepts "sector rotation" as edge without requiring security selection justification
  4. Tool usage for stock fundamentals is optional, not mandatory for certain archetypes
- **Status:** CRITICAL NEW ISSUE - not identified in original analysis or architecture plan

### Strategic Sophistication Gap: Why Sector ETFs Are Problematic

**The Core Issue:**
Mean reversion strategies REQUIRE security selection to identify mispriced securities. Buying an entire sector ETF is passive beta exposure, not active alpha generation.

**Example of the Problem:**
```
Current (Low Sophistication):
  Strategy: "Defensive Sector Mean Reversion"
  Assets: [XLF, XLC, XLB]
  Thesis: "Sector mean reversion for 30-day laggards"

  Problem: XLF = ALL financials equally weighted
           No differentiation between JPM (quality) vs regional banks (risk)
           No security selection edge
```

**What We Should See (High Sophistication):**
```
Target (High Sophistication):
  Strategy: "Oversold Financial Stock Selection"
  Assets: [JPM, BAC, WFC, C]
  Thesis: "JPM trading at 8.5x P/E vs sector avg 11.2x, down 12% on
          rate fears despite fortress balance sheet. Specific security
          selection based on fundamental mispricing, not sector rotation."

  Edge: Individual stock fundamentals + behavioral overreaction
        (NOT sector rotation, which is widely arbitraged)
```

**Why Edge Scorecard Should Catch This:**
- Strategy scored 3/5 on Edge Economics despite no security selection
- Scorer accepted "ETF rebalancing flows" as edge without scrutiny
- Should require: "Why these specific stocks vs sector index?"

**Industry Benchmark (from Analysis Doc):**
- Fama-French factors use sector/market-level exposures ✅ (academic research)
- But professional mean reversion strategies ALWAYS use stock selection ✅
- Sector rotation is a known, crowded trade ❌
- True alpha requires differentiation within sectors ✅

### Updated Success Criteria

**Original Plan:**
- Primary Goal: Implementation-thesis coherence 40% → 90%+
- Secondary Goal: Conditional logic rate 20% → 40-60%

**Revised After Latest Run:**
- **Primary Goal: Implementation-thesis coherence 40% → 90%+** ✅ (unchanged, validated)
- **Secondary Goal: Conditional logic rate 20% → 40-60%** ✅ (validated by industry benchmark)
- **🆕 NEW Primary Goal: Security selection sophistication 0% → 80%+**
  - Metric: % of mean reversion/value strategies using individual stocks vs broad ETFs
  - Rationale: Strategic sophistication requirement for certain archetypes
- **🆕 Blocker Resolution: All 4 Priority 1 blockers fixed before production** (100% required)

### Impact on Quality Targets

**Original Plan:**
- Expected quality: 6.1/10 → 8.0+/10 (+31%)

**Revised After Blocker Discovery:**
- Expected quality: 6.1/10 → 8.5+/10 (+39%)
- Additional +0.5 points from:
  - Security selection sophistication (+0.3)
  - Data integrity (asset preservation) (+0.1)
  - Quality gate enforcement (+0.1)

---

### The Problem (From Analysis Document)
**Top Root Causes (85%+ probability):**
1. **RC-1**: Validation happens AFTER all 5 strategies generated → too late, agent rationalizes
2. **RC-2B**: Only one concrete example (VIX at the time) showed conditional logic → only that archetype implemented it (100% correlation)
3. **RC-5B**: No planning checkpoint → agent jumps to implementation without structured thinking
4. **NEW**: Unvalidated quantitative claims (60%, 70%, 85% without evidence)

### The Solution (Chosen Architecture: Solution C)

**10 Targeted Fixes (Restructured: 2 True Blockers + 8 Quality Improvements):**

| Fix | What | Why | Where | Time |
|-----|------|-----|-------|------|
| **Phase 0: True Blockers (MUST FIX FIRST)** |
| **#0.1** | Fix Edge Scorecard enforcement | Filter overall_pass=False before winner selection | `edge_scorer.py` | 20 min |
| **#0.2** | Fix charter truncation | Increase max_tokens OR detect/retry | `charter_generator.py` | 15 min |
| **Phase 1: Core Quality Improvements (Prompt Architecture)** |
| **#1** | Constitutional validation layer | Move validation rules to top of system prompt | `system.md` | 30 min |
| **#2** | Post-validation retry with RSIP | Add reflection checkpoints + surgical retry | `candidate_generator.py` | 90 min |
| **#3** | Alpha vs Beta framework | Security selection requirements by archetype | `system.md` + examples | 120 min |
| **#4** | 3 worked examples (stock, factor, macro) | Show conditional logic + stock selection | After `recipe:429` | 135 min |
| **#5** | Mandatory planning matrix | Force structured thinking before generation | Before `recipe:149` | 25 min |
| **Phase 2: Validation & Polish** |
| **#6** | Backtesting validation | Require evidence OR hypothesis language for % claims | `system:638` | 20 min |
| **#7** | Reporting bug fix | Summary correctly identifies conditional vs static | TBD via grep | 15 min |
| **#8** | Diversity revision | Allow duplicate types with different assets | `system:345-369` | 10 min |

**Total Time (Realistic):** 8-12 hours
- Phase 0 (True Blockers): 35 minutes
- Phase 1 (Core Architecture): 6-8 hours
- Phase 2 (Polish): 45 minutes
- Testing & Integration: 1-2 hours

**Note:** Original estimate of 270 minutes (4.5 hours) was optimistic - did not account for integration testing, debugging, iteration cycles, or context switching overhead.

**Flow:**
```
Planning Matrix (mandatory)
  ↓
Generate 5 strategies in batch (efficient - 1 API call)
  ↓
Post-validation checks coherence
  ↓
IF failures: Targeted retry with specific errors (1 additional call)
  ↓
Pydantic safety net (catches bypasses)
  ↓
Return validated strategies
```

### Expected Impact

**Primary Goal: Implementation-Thesis Coherence**
- **Current**: 40% (4/5 describe conditionals but don't implement)
- **Target**: 90%+ (if thesis says conditional, must implement)
- **Rationale**: Industry uses 40-50% static successfully - real problem is coherence, not complexity

**Quality Metrics:**

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Implementation-thesis coherence | 40% | 90%+ | +125% |
| Conditional logic rate | 20% | 40-60% | +100-200% |
| **🆕 Security selection sophistication** | **0%** | **80%+** | **NEW - Critical** |
| Overall quality score | 6.1/10 | 8.5+/10 | +39% (was +31%) |
| Quantitative claims validated | 0% | 100% | NEW |
| Validation pass rate | Unknown | 80%+ | NEW |
| **🆕 Blocker resolution rate** | **N/A** | **100%** | **4 blockers MUST fix** |

### Implementation Scope

**Files Modified:** 6 (was 4, added 2 for blocker fixes)
1. `candidate_generation.md` (+360 lines) - examples + planning + references + stock selection example
2. `candidate_generator.py` (+130 lines, was +110) - validation + retry + asset preservation
3. `models.py` (+35 lines) - conditional logic validator
4. `candidate_generation_system.md` (+90 lines, was +10) - stock selection requirements + clarifications
5. **🆕 `edge_scorer.py`** (+20 lines) - overall_pass enforcement
6. **🆕 `charter_generator.py`** (+10 lines) - truncation fix

**Total Effort:** ~270 minutes (4.5 hours, was 2.75 hours)
- Phase 0 Blockers: +105 minutes
- Original Plan: +165 minutes

---

## ARTIFACT 1: Chain of Thought Analysis

### Current State

**What Exists:**
- **Validation package**: 90-minute package ALREADY IMPLEMENTED (analysis doc lines 60-124)
  - Logic tree validation matrix (system:578-598)
  - Weight derivation requirements (system:600-638)
  - Rebalancing coherence AUTO-REJECT matrix (system:723-797)
  - Worked examples now include stock selection, factor regime, and macro cross-asset (recipe: Worked Examples section)
  - Current quality: 6.1/10 (up from 3.2/10 baseline)
  - Remaining gap: Still only 20% conditional logic implementation (1/5 strategies)

- **Prompt structure**:
  - Recipe: candidate_generation.md (684 lines)
  - System: candidate_generation_system.md (841 lines)
  - Validation matrices: 8 matrices present, declared as AUTO-REJECT
  - Worked examples: 3 concrete (stock selection, factor, macro), 5 abstract templates

- **Code enforcement**:
  - Pydantic validators: 7 validators exist
  - Missing validators: No keyword→logic_tree validator, no edge→frequency validator
  - Generation flow: Single batch (all 5 at once), no retry mechanism

### How It Got Here

- **Commit bb4c883**: Added tool guidance + abstract examples (Nov 2)
  - Result: Partial improvement, quality 3.2→6.1/10

- **Commit 45cfdde**: Added VIX worked example (Nov 1)
  - Result: Proved model capability; example later replaced with stock/factor/macro set to reduce ETF anchoring

- **Test runs**: 2 runs with Kimi K2, 10 total strategies evaluated
  - Finding: 1/5 implement conditional logic despite 4/5 describing it
  - Proof of capability: worked examples drive conditional logic (prior VIX example scored 8.5/10; now replaced)

- **Root cause confirmed**: "Won't problem, not can't problem" (analysis doc line 243)
  - Evidence: Model CAN do it with concrete worked examples, defaults to simple otherwise

### Dependencies

**What depends on this:**
- Edge scoring receives candidates (stage 2 of 5)
- Winner selection evaluates quality (stage 3 of 5)
- Charter generation documents strategy (stage 4 of 5)
- Entire evaluation framework depends on quality candidates

**What this depends on:**
- Market context pack v2.0 (already implemented)
- Kimi K2 model capabilities (cost-optimized, weak implementation discipline)
- Pydantic Strategy model (defines what's possible)
- User preference: prompt-first solutions (minimal code changes)

### Problem Decomposition

**Core Problem:**
Validation exists but doesn't enforce - prompts declare AUTO-REJECT but code doesn't block (analysis doc RC-1, 85% probability)

**Sub-Problems:**

1. **Validation timing** - happens AFTER all 5 generated (RC-1A/1B, RC-4B)
   - Impact: Agent sees rules too late, rationalizes exceptions
   - Evidence: Doc lines 256-276: "generates all 5→reads rules→too late→rationalizes"
   - Probability: 85%

2. **Only 1 example** showed conditional logic (RC-2B/5A)
   - Impact: VIX archetype = 100% conditional, others = 0%
   - Evidence: Doc lines 308-322: ONE detailed example (VIX at the time) → ONLY that archetype uses conditional logic
   - Probability: 80%

3. **No planning checkpoint** before generation (RC-5B)
   - Impact: Agent jumps to implementation without structured thinking
   - Evidence: Doc lines 382-390: Ideation→generation, no intermediate logic_tree design
   - Probability: 60%

4. **Unvalidated quantitative claims** (doc NEW issue #6)
   - Impact: 60%, 70%, 85% probability claims without evidence
   - Evidence: Doc lines 989-993: Confident assertions without rigor
   - Probability: 80%

5. **Reporting bug** shows 'static' when logic_tree populated (RC-7)
   - Impact: Incorrect feedback confuses quality assessment
   - Evidence: Doc lines 413-422: VIX shows 'static' but has conditional logic
   - Probability: 30%

6. **Diversity requirements unclear** (user correction)
   - Impact: Should ALLOW duplicate types with different assets, not prevent
   - User guidance: "Allow duplicate strategy types with different assets/theses"

---

## Root Causes - Latest Run Empirical Validation (November 3, 2024)

### Validated Root Causes (From Original Analysis)

**✅ RC-1: Validation Too Late + No Blocking (85% confidence)**
- **Original Hypothesis:** Agent generates all 5 → reads rules → too late → rationalizes
- **Evidence from Latest Run:** Post-validation retry caught 3 failures and successfully recovered
- **Conclusion:** VALIDATED - retry mechanism works, confirms validation timing was the issue
- **Status:** Fix #1 (post-validation retry) proven effective

**✅ RC-2B: One Example → One Implementation (80% confidence)**
- **Original Hypothesis:** Only VIX has detailed example → only VIX uses conditional logic
- **Evidence from Latest Run:** After retry with generic fixes, strategies still defaulted to simple
- **Conclusion:** VALIDATED - need archetype-specific examples (Fix #2)
- **Status:** Fix #2 (4 detailed examples) required

**✅ RC-4B: Validation-Generation Phase Mismatch (85% confidence)**
- **Original Hypothesis:** Validation after generation creates backtracking resistance
- **Evidence from Latest Run:** Retry loop worked when validation errors explicit
- **Conclusion:** VALIDATED - structural fix (post-validation retry) addresses this
- **Status:** Architecture decision confirmed

### New Root Causes Discovered (November 3, 2024 Run)

**🆕 RC-RETRY-1: Asset Drift in Retry** (Priority 1 - Data Integrity)
- **Problem:** Retry prompt regenerates entire strategy instead of fixing specific thesis language
- **Evidence:** Candidate #1 changed from [XLK, XLY, XLF] → [XLK, XLV, XLU]
- **Impact:** Different strategy created vs thesis-only fix, data integrity compromised
- **Probability:** 100% (observed in run)
- **Root Cause:** Retry prompt doesn't include asset/weight/logic_tree preservation instructions
- **Fix Required:** Update `create_fix_prompt()` to preserve original assets, weights, logic_tree

**🆕 RC-EDGE-1: Edge Scorecard Pass/Fail Not Enforced** (Priority 1 - Quality Gate)
- **Problem:** `overall_pass` boolean calculated but not enforced in code
- **Evidence:**
  - Dividend Aristocrats: Edge Economics 2/5, overall_pass=False, reasoning says "FAIL"
  - Tech Momentum: Edge Economics 2/5, overall_pass=False, reasoning says "FAIL"
  - But workflow shows "✓ 5/5 candidates passed Edge Scorecard"
- **Impact:** Low-quality strategies bypass quality gate and proceed to winner selection
- **Probability:** 100% (observed in run)
- **Root Cause:** Winner selector doesn't filter on `overall_pass=False`
- **Fix Required:** Add filtering in `edge_scorer.py` or `winner_selector.py`

**🆕 RC-CHARTER-1: Charter Generation Truncation** (Priority 1 - Deployment Blocker)
- **Problem:** Charter generation cuts off before completion
- **Evidence:** Day 90 outlook section ends mid-sentence: "Day 90 (January 31, 2026):\n- "
- **Impact:** Incomplete charter cannot be used for deployment
- **Probability:** 100% (observed in run)
- **Root Cause:** max_tokens too low OR no truncation detection/retry
- **Fix Required:** Increase token limit for charter OR detect truncation and retry

**🆕 RC-SECTOR-1: Sector ETF Default (No Stock Selection)** (Priority 1 - Strategic Quality)
- **Problem:** ALL strategies default to broad sector ETFs instead of individual stock selection
- **Evidence:** Winner "Defensive Sector Mean Reversion" uses [XLF, XLC, XLB] instead of [JPM, BAC, WFC, C]
- **Impact:** Low strategic sophistication - passive sector beta, not alpha generation
- **Probability:** 100% (all 5 candidates used broad ETFs)
- **Root Cause Analysis:**
  - **RC-SECTOR-1A:** Prompts don't explicitly require stock-level analysis for mean reversion/value
  - **RC-SECTOR-1B:** ETF-heavy worked examples (prior VIX example used broad ETFs) created precedent
  - **RC-SECTOR-1C:** Edge Scorecard accepts "sector rotation" without security selection scrutiny
  - **RC-SECTOR-1D:** Tool usage for fundamentals optional, not mandatory
- **Fix Required:**
  1. Add stock selection requirement to mean reversion/value archetypes (prompts)
  2. Add worked example showing individual stock selection with fundamental justification (implemented in candidate_generation.md)
  3. Update Edge Scorecard to require security selection for certain archetypes
  4. Make fundamental analysis tools mandatory for value/mean-reversion strategies

### Cross-Reference with Industry Practice (Analysis Doc Alternative Hypothesis #1)

**Important Context from Analysis Document:**
- Industry practice: 40-50% of systematic strategies use simple periodic rebalancing
- Fama-French, AQR, DFA all use sector/factor-level allocations successfully
- Forcing 80%+ conditional logic may be over-engineering

**How This Relates to Sector ETF Issue:**
- ✅ Sector-level allocations ARE appropriate for factor strategies (momentum, carry, quality)
- ❌ Sector-level allocations are NOT appropriate for mean reversion (requires security selection)
- ✅ Conditional logic should match strategy archetype needs (not universal requirement)
- ❌ But strategic sophistication MUST match archetype requirements (universal for quality)

**Refined Principle:**
- **Conditional Logic:** 40-60% is acceptable (matches industry practice)
- **Security Selection:** 80%+ required for mean reversion/value (industry standard)
- **Coherence:** 90%+ always required (if thesis says X, must implement X)

---

### Hidden Complexity

- **Industry uses 40-50% static successfully** (doc lines 815-907)
  - Implication: Forcing 80%+ conditional may be over-engineering
  - New goal: Implementation-thesis coherence (not universal conditional logic)

- **Kimi K2 specific weakness** (doc lines 958-1102)
  - Characteristics: Strong narrative (7.5/10), weak implementation (5/10)
  - Implication: Cost-optimized models trade rigor for fluency

- **Effort asymmetry** (doc RC-3A)
  - Data: Conditional 18x harder time, 8x more tokens
  - Implication: Agent allocates 'complex budget' to ONE showcase (VIX)

- **Academic factor priors** (doc RC-2A)
  - Evidence: 4/5 identical across runs (Fama-French taxonomy)
  - Implication: Deep training priors override prompt diversity requests

### Success Criteria

1. **Implementation-thesis coherence (PRIMARY GOAL)**
   - Current: ~40% (4/5 describe conditionals but don't implement)
   - Target: 90%+ (if thesis says conditional, must implement)
   - Measurement: Manual review - does logic_tree match thesis keywords?

2. **Conditional logic implementation rate (SECONDARY)**
   - Current: 20% (1/5 strategies)
   - Target: 40-60% (matching industry practice, not 80%+)
   - Rationale: Doc Alternative Hypothesis #1: simple can be optimal
   - Measurement: Count strategies with populated logic_tree

3. **Overall quality score**
   - Current: 6.1/10
   - Target: 8.0+/10
   - Measurement: Doc rubric (Market Understanding, Edge ID, Implementation, Risk, Consistency)

4. **Validation pass rate (first attempt)**
   - Current: Unknown (validation not blocking)
   - Target: 80%+ pass without retry
   - Measurement: Track validation failures, retry count

5. **Quantitative claims validated**
   - Current: 0% (all unvalidated)
   - Target: 100% (must show evidence OR use hypothesis language)
   - Measurement: Check thesis for % claims, verify backtesting or hedged language

---

## ARTIFACT 2: Tree of Thought Solutions

### Solution A: One-at-a-Time Validation (Doc's Fix #1)

**Approach:** Restructure recipe to generate candidates sequentially with blocking validation. Agent cannot proceed to next candidate until current one passes validation. Implements critique→revise loop with hard enforcement.

**Implementation:**
1. Restructure recipe Step 2.2 for sequential generation
   - Replace "generate all 5" with "For i in 1..5: generate→validate→revise if needed→continue"
   - Location: candidate_generation.md lines 169-190

2. Add BLOCKING validation gates after each candidate
   - If thesis has conditional keywords AND logic_tree={} → MUST REVISE, cannot proceed
   - Enforcement: Boolean YES/NO gates prevent rationalization

3. Add candidate_generator.py iteration logic
   - Generate one Strategy, validate, if fails create targeted fix prompt, retry once, repeat for all 5
   - Code change: ~50 lines

4. Keep existing validation matrices (already good)
   - System prompt lines 578-797 have comprehensive validation - just need enforcement

**Patterns Used:**
- Constitutional AI (doc references Anthropic 2024)
- Blocking checkpoints (doc Fix #1)
- One-at-a-time > batch (67% better per research)

**Pros:**
- Directly addresses RC-1 (85% probability root cause)
- Expected 60-80% improvement per doc lines 520
- Proven pattern from research
- VIX proves model CAN do it when forced

**Cons:**
- Requires prompt restructuring (medium effort)
- May still allow batch generation with post-validation retry (cheaper)
- Kimi K2 may still bypass even with blocking (known issue)

**Complexity:** 6 | **Risk:** MEDIUM | **Time:** 30 minutes

---

### Solution B: Add 4 Detailed Examples + Planning Matrix

**Approach:** Keep batch generation efficient but add pre-generation planning checkpoint and 4 VIX-quality examples for other archetypes. Rely on prompt engineering over code changes (user's preference).

**Implementation:**
1. Add planning matrix before Step 2.2
   - Mandatory table: 5 rows × columns (Conditional?, Triggers, Weight Method, Rationale)
   - Location: candidate_generation.md after line 148, before 149
   - Source: Doc lines 546-575 (Fix #3)

2. Add 4 detailed worked examples
   - Momentum, Mean-reversion, Carry, Multi-factor with VIX-level detail
   - Location: candidate_generation.md after line 429
   - Source: Doc lines 526-544 (Fix #2)
   - Time: 90 minutes (4 × 22 min each)

3. Add backtesting validation requirement
   - If thesis contains % claims (60%, 70%), must show validation OR use hypothesis language
   - Location: candidate_generation_system.md after line 638
   - Source: Doc lines 652-714 (Fix #5)

4. Fix reporting bug
   - Search for summary generation, ensure checks logic_tree not weights
   - Source: Doc RC-7 lines 413-422
   - Time: 10 minutes

5. Revise diversity requirements
   - Allow duplicate archetypes with different assets/theses
   - User correction: Explicitly rejected cross-run diversity database

**Patterns Used:**
- Example-based learning (3+ examples)
- Planning matrix (forces structured thinking)
- Validation checkpoint (end of generation)

**Pros:**
- Honors user's "prompt-first" preference
- Maintains batch efficiency (1 API call)
- Expected 40-60% improvement from examples (doc line 541)
- Expected 20-30% improvement from planning (doc line 572)
- Lower complexity than Solution A

**Cons:**
- No iterative feedback during generation
- Kimi K2 may skip planning matrix (known to bypass constraints)
- If validation fails, must regenerate all 5
- Less enforcement rigor than Solution A

**Complexity:** 5 | **Risk:** MEDIUM-HIGH | **Time:** 120 minutes

---

### Solution C: Batch + Planning + Examples + Post-Validation Retry + Blocker Fixes (CHOSEN - REVISED)

**Approach:** Restructured based on November 3 run + subagent reviews. Focus on prompt architecture (constitutional constraints + RSIP reflection) rather than code enforcement. Prioritize true deployment blockers separately from quality improvements.

**Implementation:**

**Phase 0: True Deployment Blockers (35 minutes)**

1. **Fix Edge Scorecard Enforcement** (RC-EDGE-1)
   - File: `edge_scorer.py`
   - Add: Filter candidates where `overall_pass=False` before returning to winner_selector
   - Code change: ~15 lines
   - Time: 20 minutes

2. **Fix Charter Truncation** (RC-CHARTER-1)
   - File: `charter_generator.py`
   - Increase max_tokens to 8000+ OR add truncation detection/retry
   - Code change: ~10 lines
   - Time: 15 minutes

**Phase 1: Core Prompt Architecture (6-8 hours)**

3. **Constitutional Validation Layer** (NEW - from Prompt Engineering Review)
   - File: `candidate_generation_system.md` (top of file)
   - Add: "Constitutional Constraints (Non-Negotiable)" section at lines 1-50
   - Move: All AUTO-REJECT rules to priority window (seen BEFORE generation context)
   - Structure: Hierarchical priority - Constraints → Current Task → Context → Examples
   - Time: 30 minutes

4. **Post-Validation Retry with RSIP Reflection** (Enhanced Fix #1)
   - File: `candidate_generator.py`
   - Add: validate_semantics() function (~50 lines)
   - Add: create_surgical_fix_prompt() with asset preservation (~40 lines)
   - Add: retry_failed_strategies() with single retry (~30 lines)
   - **NEW: RSIP Checkpoints** in recipe prompt:
     - Pre-generation: Planning Matrix (reasoning)
     - Post-generation: Self-Critique checklist (reflection)
     - Pre-submission: Validation summary (improvement plan)
   - Time: 90 minutes (60 code + 30 RSIP prompts)

5. **Alpha vs Beta Framework** (Enhanced Fix #10 - from Strategic Review)
   - File: `candidate_generation_system.md` (after market regime section)
   - Add: "Alpha Generation vs Beta Exposure" conceptual framework (~100 lines)
   - Add: Decision matrix: Which archetypes need stocks vs sectors acceptable
   - Add: Security selection workflow (universe → screening → fundamental analysis → ranking)
   - File: `candidate_generation.md` (worked examples)
   - Add: Dual-sophistication example - Mean reversion WITH stock selection (~150 lines)
   - Update: Worked examples now include stock selection; VIX-specific commentary removed
   - Time: 120 minutes

6. **3 Archetype Examples** (Original Fix #2 + Stock Selection)
   - File: `candidate_generation.md` after line 429
   - Add: Stock selection example with conditional logic (~60 lines)
   - Add: Factor regime example with ETF rotation (~60 lines)
   - Add: Macro cross-asset example with regime-based triggers (~60 lines)
   - Each includes: Context → Edge → Planning → Strategy object → Coherence validation
   - Time: 135 minutes (45 min each for 3 examples)

7. **Mandatory Planning Matrix with RSIP** (Enhanced Fix #3)
   - File: `candidate_generation.md` after line 148
   - Add: Pre-generation planning table (5 rows × 8 columns)
   - Add: Post-generation reflection checklist (coherence review)
   - Add: Pre-submission validation summary (blocking checkpoint)
   - Time: 25 minutes

**Phase 2: Validation & Polish (45 minutes)**

8. **Backtesting Validation** (Original Fix #4)
   - File: `candidate_generation_system.md` after line 638
   - Add: Quantitative claims validation rule (evidence OR hypothesis language)
   - Time: 20 minutes

9. **Reporting Bug Fix** (Original Fix #5)
   - Search for summary generation code, fix logic_tree check
   - Time: 15 minutes

10. **Diversity Revision** (Original Fix #6)
    - File: `candidate_generation_system.md` lines 345-369
    - Update: Allow duplicate archetypes with different assets/theses
    - Time: 10 minutes

**Patterns Used:**
- Constitutional AI (constraints at top priority window)
- RSIP (Reasoning → Self-Critique → Improvement → Plan)
- Hybrid batch+sequential (efficiency + iteration)
- Alpha vs Beta framework (strategic sophistication)
- Surgical retry (preserves structure, fixes thesis only)
- Concrete examples (learning from VIX success)

**Pros:**
- **✅ Restructured priorities:** Only 35 minutes of TRUE blockers (not 105)
- **✅ Addresses all 4 critical issues from November 3 run:**
  - RC-EDGE-1 (scorecard bypass): Filter overall_pass=False
  - RC-CHARTER-1 (truncation): Increase tokens or detect/retry
  - RC-RETRY-1 (asset drift): Surgical fix prompt with preservation
  - RC-SECTOR-1 (ETF default): Alpha vs Beta framework + stock selection example
- **✅ Prompt architecture fixes validated by subagent reviews:**
  - Constitutional constraints (top priority window)
  - RSIP reflection checkpoints (pre/post/final)
  - Security selection workflow (universe → screening → analysis)
  - Dual-sophistication examples (conditional logic + stock selection)
- **✅ Realistic time estimates:** 8-12 hours (not 4.5 hours optimistic)
- **✅ Honors user preference:** Pure prompt engineering (no Pydantic validators)
- **✅ Best balance:** 1 call happy path, 2 calls if validation fails
- **✅ Expected 70-90% improvement combined**

**Cons:**
- **⚠️ Higher implementation effort:** 8-12 hours (up from original 4.5 hour estimate)
- **⚠️ No programmatic enforcement:** Relies entirely on prompt discipline (Kimi K2 may bypass)
- **⚠️ RSIP checkpoints may be ignored:** Model known to skip non-blocking constraints
- **⚠️ Still 2x cost if validation fails:** vs 1x for Solution B
- **⚠️ Alpha vs Beta framework complex:** 120 minutes for conceptual + workflow + examples
- **⚠️ Testing overhead:** 1-2 hours for integration validation not included in fix times

**Complexity:** 7/10 (down from 8 - removed Pydantic validators)
**Risk:** MEDIUM (up from LOW-MEDIUM - no programmatic enforcement fallback)
**Time:** 8-12 hours realistic (was 4.5 hours optimistic)

---

### Comparative Analysis

**Winner:** Solution C

**Reasoning:**

1. **Addresses top 4 root causes** (cumulative 85%+ probability):
   - RC-1A/1B (85%): Post-validation retry gives blocking feedback
   - RC-2B/5A (80%): 4 concrete examples show implementation
   - RC-5B (60%): Planning matrix forces structured thinking
   - RC-7 (30%): Bug fix improves reporting accuracy

2. **Matches document's recommendations**:
   - Doc Fix #1 (validation timing): Implemented via retry loop
   - Doc Fix #2 (examples): 3 detailed examples added
   - Doc Fix #3 (planning): Mandatory matrix
   - Doc Fix #5 (backtesting): Validation requirement added
   - Doc RC-7 (bug): Fixed

3. **Honors user corrections**:
   - Prompt-first with code as safety net (not static analysis)
   - Allows duplicate strategy types with different assets
   - Ignores cross-run diversity tracking
   - Ignores threshold guidance

4. **Balances cost and quality**:
   - Happy path: 1 API call (efficient)
   - Failure path: 2 API calls (vs 5 for pure sequential)
   - Expected quality: 8.0+/10 (doc target)

5. **Proven effectiveness**:
   - Worked examples prove model CAN comply when shown how
   - Doc estimates 70-90% cumulative improvement from all fixes
   - Industry practice: 40-60% conditional is acceptable (not 80%+)

**Runner-Up:** Solution B

**Why Not Runner-Up:**
- Simpler but lacks enforcement
- Kimi K2 bypasses format constraints (web research finding)
- Current system has AUTO-REJECT declarations that are ignored
- Without retry loop, validation failure → regenerate all 5 (wasteful)
- Would likely achieve 50-60% improvement vs Solution C's 70-90%

---

## ARTIFACT 3: Architecture Decision Record

### Decision

**Implement Solution C: Batch Generation + Planning Matrix + 3 Concrete Examples + Post-Validation Retry Loop**

### Files to Modify

#### 1. `src/agent/prompts/candidate_generation.md`
**Purpose:** Add RSIP checkpoints, planning matrix, 4 concrete examples, reference frameworks

**Changes:**
- **Line 148**: Insert Step 2.0.5 "Mandatory Planning Matrix with Pre-Generation Reasoning" (~60 lines)
- **Line 149**: Enhance Step 2.1 with edge-frequency matrix reference (~30 lines)
- **Line 190**: Enhance Step 2.2 with weight derivation methods reference (~20 lines)
- **After Step 2.3**: Add "Post-Generation Self-Critique Checklist" (RSIP reflection) (~50 lines)
- **Line 429**: Add "Worked Examples by Archetype" section with 4 examples (~300-350 lines)
  - Mean Reversion example WITH individual stock selection (~75 lines)
  - Momentum example with conditional logic (~60 lines)
  - Carry example with regime triggers (~60 lines)
  - Multi-Factor example with dynamic allocation (~60 lines)
- **Before submission**: Add "Pre-Submission Validation Summary" (RSIP plan) (~40 lines)
- **Line 202**: Enhance diversity checklist with correlation anti-pattern (~10 lines)

**Size estimate:** ~500-560 lines added (684 → 1184-1244 lines total)

#### 2. `src/agent/stages/candidate_generator.py`
**Purpose:** Add post-validation layer + surgical retry mechanism with asset preservation

**Changes:**
- After line 204: Add `validate_semantics()` function (~50 lines)
  - Check thesis-logic_tree coherence (conditional keywords → logic_tree populated)
  - Check archetype-frequency alignment (momentum + quarterly = violation)
  - Check weight derivation explanation (no arbitrary round numbers without justification)
- After validate_semantics: Add `create_surgical_fix_prompt()` function (~40 lines)
  - Preserve assets, weights, logic_tree from original strategy
  - Only revise thesis_document and rebalancing_rationale text
  - Include specific validation errors to address
- After create_fix_prompt: Add `retry_failed_strategies()` function (~30 lines)
  - Single retry attempt with surgical fix prompt
  - Fallback to original candidates with warnings if retry fails
- Update `generate()` to call validation + retry if needed (~15 lines)

**Size estimate:** ~135 lines added (204 → 339 lines total)

#### 3. `src/agent/models.py`
**Purpose:** Fix reporting bug only (NO Pydantic validators per user request)

**Changes:**
- Search for summary generation code, fix logic_tree check if bug exists (location TBD, ~5-10 lines)

**Size estimate:** ~5-10 lines modified (269 → 274-279 lines total)

#### 4. `src/agent/prompts/system/candidate_generation_system.md`
**Purpose:** Add constitutional constraints layer + Alpha vs Beta framework

**Changes:**
- **Lines 1-50**: Add "Constitutional Constraints (Non-Negotiable)" section at TOP
  - Conditional logic coherence rule
  - Weight derivation transparency rule
  - Rebalancing coherence matrix (edge-frequency alignment)
  - Quantitative claims validation rule
  - Priority: These appear BEFORE market context in prompt hierarchy
- **After market regime section (~line 200)**: Add "Alpha Generation vs Beta Exposure" framework (~120 lines)
  - Conceptual foundation: Why security selection matters
  - Decision matrix: Which archetypes need stocks vs sectors acceptable
  - Security selection workflow: Universe → Screening → Fundamental Analysis → Ranking → Selection
  - AUTO-REJECT triggers for coherence violations
- **Line 638**: Add backtesting validation rule (evidence OR hypothesis language)
- **Line 345-369**: Update diversity requirements (allow duplicate archetypes with different assets)

**Size estimate:** ~200-220 lines added (841 → 1041-1061 lines total)

#### 🆕 5. `src/agent/stages/edge_scorer.py`
**Purpose:** Fix Edge Scorecard enforcement (RC-EDGE-1) - filter overall_pass=False strategies

**Changes:**
- Update scoring logic to properly filter strategies with overall_pass=False
- Add explicit check before returning scored candidates to winner_selector
- Option 1: Filter in edge_scorer.py before return
- Option 2: Filter in winner_selector.py before evaluation

**Size estimate:** ~15 lines modified or added

#### 🆕 6. `src/agent/stages/charter_generator.py`
**Purpose:** Fix charter truncation (RC-CHARTER-1) - increase max_tokens or add detection/retry

**Changes:**
- Option 1: Increase max_tokens from current value to 8000+ in LLM call
- Option 2: Add truncation detection (check if output ends mid-sentence) + retry logic
- Recommended: Try Option 1 first (simple), add Option 2 if truncation persists

**Size estimate:** ~10 lines modified (Option 1) or ~40 lines added (Option 2)

### Implementation Sequence (Revised)

#### Phase 0: True Deployment Blockers (35 minutes)
**Files:** edge_scorer.py, charter_generator.py
**Purpose:** Fix only the issues that prevent production deployment

**Steps:**

**Fix #1: Edge Scorecard Enforcement (RC-EDGE-1) - 20 minutes**
1. Open edge_scorer.py, locate where scored candidates are returned
2. Add filtering: `passing = [c for c in scored if c.overall_pass]`
3. Raise error if len(passing) == 0 (no valid candidates)
4. Test: Generate strategy with overall_pass=False, verify filtered

**Fix #2: Charter Truncation (RC-CHARTER-1) - 15 minutes**
1. Open charter_generator.py, locate LLM generation call
2. Increase max_tokens from current value to 8000+
3. If truncation persists, add detection (check if ends with ":\n- ") + retry
4. Test: Generate charter, verify all sections present

**Validation:**
- Run pytest on modified files
- Manual test: Verify Edge Scorecard rejects overall_pass=False
- Manual test: Verify charter completes without truncation

**Go/No-Go Checkpoint:** System must deploy end-to-end with complete charters and quality gate enforcement. If this fails, halt and debug before Phase 1.

---

#### Phase 1: Core Prompt Architecture (6-8 hours)
**Files:** candidate_generation_system.md, candidate_generation.md, candidate_generator.py
**Purpose:** Implement prompt architecture improvements validated by subagent reviews

**Step 1: Constitutional Constraints Layer (30 minutes)**
- File: candidate_generation_system.md
- Add "Constitutional Constraints (Non-Negotiable)" section at TOP (lines 1-50)
- Move all AUTO-REJECT rules to highest priority window
- Establish hierarchy: Constraints → Task → Context → Examples

**Step 2: Post-Validation Retry with RSIP (90 minutes)**
- File: candidate_generator.py (~75 min code)
  - Add validate_semantics() function (~50 lines)
  - Add create_surgical_fix_prompt() with asset preservation (~40 lines)
  - Add retry_failed_strategies() with single retry (~30 lines)
  - Update generate() orchestration (~15 lines)
- File: candidate_generation.md (~15 min RSIP prompts)
  - Add Post-Generation Self-Critique checklist
  - Add Pre-Submission Validation Summary

**Step 3: Alpha vs Beta Framework (120 minutes)**
- File: candidate_generation_system.md (~60 min framework)
  - Add "Alpha Generation vs Beta Exposure" section (~100 lines)
  - Add decision matrix for archetype-security level mapping
  - Add security selection workflow (universe → screening → analysis)
- File: candidate_generation.md (~60 min example)
  - Add Mean Reversion example WITH individual stock selection (~75 lines)
  - Include fundamental analysis workflow demonstration

**Step 4: Four Archetype Examples (180 minutes)**
- File: candidate_generation.md after line 429
- Add Momentum example with conditional logic (~60 lines) - 45 min
- Mean Reversion already added in Step 3 - skip
- Add Carry example with regime triggers (~60 lines) - 45 min
- Add Multi-Factor example with dynamic allocation (~60 lines) - 45 min
- Each includes Context → Edge → Planning → Strategy → Coherence validation

**Step 5: Planning Matrix with RSIP (25 minutes)**
- File: candidate_generation.md after line 148
- Add Pre-Generation Planning Matrix (5 rows × 8 columns) - 15 min
- Add validation checkpoint (if Conditional=YES with empty Triggers → STOP) - 10 min

**Validation:**
- Read modified prompts, verify structure and completeness
- Check line counts match estimates
- Verify RSIP checkpoints logically positioned (pre/post/final)
- Verify Alpha vs Beta framework includes decision matrix + workflow

---

#### Phase 2: Validation & Polish (45 minutes)
**Files:** candidate_generation_system.md, models.py
**Purpose:** Add remaining validation rules and fix minor issues

**Step 1: Backtesting Validation (20 minutes)**
- File: candidate_generation_system.md after line 638
- Add quantitative claims validation rule
- Require backtesting evidence OR hypothesis language for % claims

**Step 2: Reporting Bug Fix (15 minutes)**
- Grep for summary generation code in models.py or candidate_generator.py
- Fix logic_tree check (ensure checking logic_tree not weights)
- Test with mock data

**Step 3: Diversity Revision (10 minutes)**
- File: candidate_generation_system.md lines 345-369
- Update diversity requirements to allow duplicate archetypes with different assets/theses

**Validation:**
- Test summary generation with mock data (verify bug fixed)
- Read diversity section, verify updated correctly

---

#### Phase 3: Integration Testing (1-2 hours)
**Files:** All modified files
**Purpose:** End-to-end validation of complete system

**Steps:**
1. Run pytest on all modified files (10 min)
2. Manual test: Generate 5 candidates with test context pack (20 min)
3. Verify RSIP checkpoints appear in output (10 min)
   - Planning Matrix completed
   - Post-Generation Self-Critique present
   - Pre-Submission Validation Summary present
4. Verify validation catches violations (15 min)
   - Empty logic_tree with conditional keywords
   - Momentum + quarterly frequency
   - Unvalidated quantitative claims
5. Verify retry mechanism works (15 min)
   - Inject failing strategy
   - Verify assets preserved in retry
   - Verify surgical fix (only thesis revised)
6. Verify Phase 0 fixes stable (15 min)
   - Edge Scorecard filters overall_pass=False
   - Charter completes all sections
7. Verify Alpha vs Beta framework applied (20 min)
   - Mean reversion strategy uses individual stocks [WFC, BAC, JPM]
   - NOT sector ETFs [XLF]
   - Fundamental analysis demonstrated in thesis

**Success Criteria:**
- All pytest tests pass
- RSIP checkpoints present and logically positioned
- Validation catches known violations
- Retry preserves asset structure
- Mean reversion uses individual stocks (not ETFs)
- Charter completes without truncation
- Edge Scorecard enforces quality gate

**Estimated Total Time:** 8-12 hours
- Phase 0: 35 minutes
- Phase 1: 6-8 hours
- Phase 2: 45 minutes
- Phase 3: 1-2 hours

### Validation Plan

**🆕 After Phase 0 (Critical Blocker Fixes):**
- Run `pytest tests/agent/` to verify no regressions
- **Fix #7 (Asset Drift):** Generate strategy, trigger retry, verify assets [XLK, XLY, XLF] preserved
- **Fix #8 (Edge Scorecard):** Generate strategy with overall_pass=False, verify it's filtered out
- **Fix #9 (Charter Truncation):** Generate charter, verify all sections complete (no mid-sentence cutoff)
- **Fix #10 (Stock Selection):** Generate mean reversion strategy, verify individual stocks [WFC, BAC, JPM] not ETFs [XLF]
- Pass criteria: All 4 blockers resolved, tests pass, manual verification complete

**After Phase 2 (Prompt Enhancements):**
- Read candidate_generation.md
- Verify planning matrix template present
- Verify 4 examples present with correct structure
- Verify references correctly placed
- Pass criteria: All 5 additions present, no markdown syntax errors

**After Phase 3 (Code Enforcement):**
- Run `ruff check src/agent/`
- Run `mypy src/agent/`
- Ensure imports resolve
- Check function type signatures
- Pass criteria: No linter errors, type checking passes

**After Phase 4 (Bug Fix):**
- Create mock Strategy with logic_tree populated
- Verify summary generation correct
- Pass criteria: Summary shows "conditional" not "static" when logic_tree present

**After Phase 5 (Integration):**
- Run full workflow with test context pack
- Review generated candidates
- Pass criteria: Planning matrix in thinking, validation triggers, retry invoked on failure, all Phase 0 fixes working in production

### Potential Failures & Mitigations

1. **Kimi K2 ignores planning matrix**
   - Mitigation: Matrix validation checkpoint - if empty, halt with error
   - Likelihood: MEDIUM (model known to bypass constraints)

2. **4 examples create prompt bloat**
   - Mitigation: Keep examples concise (~60-75 lines each), use progressive complexity
   - Likelihood: LOW (total addition ~350 lines, still under 1100 lines total)

3. **Retry mechanism doesn't improve quality**
   - Mitigation: Limit to 1 retry, fail fast if second attempt invalid
   - Likelihood: MEDIUM (depends on prompt quality)
   - Fallback: Return partial results with warning, log for analysis

4. **Pydantic validator too strict**
   - Mitigation: Use comprehensive keyword list, allow edge cases
   - Likelihood: LOW (careful keyword selection)

5. **Reporting bug not in expected location**
   - Mitigation: Systematic grep for 'logic_tree', 'static', 'conditional'
   - Likelihood: LOW (code is well-structured)

6. **Validation functions have bugs**
   - Mitigation: Unit tests for each validation function with pass/fail cases
   - Likelihood: MEDIUM (new code always risky)
   - Prevention: Write tests during Phase 2 implementation

---

## ARTIFACT 4: YAGNI Declaration

### Explicitly Excluding

1. **Cross-run diversity tracking with historical database (Doc Fix #4)**
   - **Why not:** User explicitly rejected: "I do not want to persist with cross-run diversity"
   - **Cost:** 2-3 hours (database schema, JSON persistence, query logic, prompt injection)
   - **User guidance:** Instead allow duplicate strategy types with different assets/theses

2. **Threshold guidance in context pack (Doc RC-6)**
   - **Why not:** User: "not entirely sure what this means, lower priority, ignore for now"
   - **Cost:** 1-2 hours (threshold calibration for SPY vs MA, sector dispersion, momentum premium)

3. **Pure one-at-a-time sequential generation**
   - **Why not:** 5x API calls, 5x cost ($0.10 vs $0.02 per run for Kimi K2) - inefficient
   - **Alternative:** Batch + post-validation retry (1-3 calls) achieves same enforcement

4. **Static analysis or AST parsing for validation**
   - **Why not:** User: "This is purely a prompting issue. I do not want to implement any static analysis"
   - **Cost:** 4-6 hours
   - **Alternative:** Pydantic validators as safety net only, prompt-first enforcement

5. **Correlation coefficient calculation for diversity check**
   - **Why not:** Complex - requires historical price data, correlation matrix computation
   - **Cost:** 3-4 hours
   - **Alternative:** Explicit anti-pattern examples (QQQ+TQQQ+XLK warning) sufficient

6. **Forcing 80%+ conditional logic universally**
   - **Why not:** Doc Alternative Hypothesis: Industry uses 40-50% static successfully
   - **Risk:** Over-engineering may reduce performance via overfitting + transaction costs
   - **Alternative:** Target 90%+ coherence (if thesis says conditional, must implement) not universal conditional

7. **Model comparison testing across 7 models**
   - **Why not:** Not immediate priority
   - **Cost:** 6-8 hours
   - **When:** After validating fixes work for Kimi K2

8. **Human baseline comparison**
   - **Why not:** Interesting but not actionable now
   - **Cost:** N/A (requires recruiting 5 professional quant traders)

### Future Considerations

1. **Cross-run diversity tracking**
   - **When:** After 50+ cohorts, if analysis shows value
   - **Current decision:** User deferred - allow duplicates with different assets

2. **Threshold guidance for non-VIX metrics**
   - **When:** If strategies struggle to design conditional triggers
   - **Current decision:** Ignored per user, lower priority

3. **Model comparison (Kimi K2 vs GPT-4o vs Opus 4)**
   - **When:** After validating fixes work
   - **Hypothesis:** Opus 4: 85-90%, GPT-4o: 80-85%, Kimi K2: 70-80% (post-fix)

4. **Backtesting all generated strategies**
   - **When:** To validate if conditional strategies outperform static
   - **Value:** Would validate industry practice hypothesis

5. **Multi-model workflow (Kimi ideation → GPT-4o implementation)**
   - **When:** After single-model results validated
   - **Expected:** 90% of GPT-4o quality at 40% of cost

---

## 🆕 Lessons Learned from November 3, 2024 Run

### What We Validated

**✅ Post-Validation Retry Works**
- The retry mechanism successfully caught 3/5 failed candidates
- Fixed candidates passed validation on second attempt
- **Implication:** Solution C's post-validation approach is sound architecture

**✅ Pipeline Orchestration Stable**
- Full Phase 5 workflow completed: Candidate Gen → Edge Scoring → Winner Selection → Charter Generation
- All 4 stages integrated successfully with MCP tools (FRED, Composer)
- **Implication:** No fundamental architecture changes needed

**✅ Narrative Quality Strong (7.5/10)**
- Kimi K2 generated coherent market thesis and strategic reasoning
- Charter sections well-structured and comprehensive (where not truncated)
- **Implication:** Model capable of high-level strategic thinking

### What We Discovered (4 Critical Blockers)

**❌ RC-RETRY-1: Asset Drift in Retry**
- **Problem:** Retry changed strategy assets [XLK, XLY, XLF] → [XLK, XLV, XLU]
- **Impact:** Invalidates the entire retry (different strategy, not fixed strategy)
- **Root Cause:** create_fix_prompt() doesn't preserve structure, regenerates from scratch
- **Fix Required:** Update retry to preserve assets, weights, logic_tree - only revise thesis text

**❌ RC-EDGE-1: Edge Scorecard Bypass**
- **Problem:** Strategies with overall_pass=False passed through to winner selection
- **Impact:** Failing strategies can win and get deployed (quality control failure)
- **Root Cause:** Missing filter between edge_scorer and winner_selector
- **Fix Required:** Add explicit overall_pass=True filter before winner selection

**❌ RC-CHARTER-1: Charter Truncation**
- **Problem:** Charter generation cuts off mid-sentence, missing "Final Verdict" section
- **Impact:** Incomplete strategic documentation, missing key justification
- **Root Cause:** max_tokens too low OR model hitting limits
- **Fix Required:** Increase max_tokens to 8000+ OR add truncation detection + retry

**❌ RC-SECTOR-1: Sector ETF Default (CRITICAL STRATEGIC GAP)**
- **Problem:** ALL 5 candidates used sector ETFs [XLF, XLC, XLB] instead of individual stocks
- **Impact:** Mean reversion thesis requires individual stock selection with fundamentals
- **Root Cause:** No explicit security selection requirements by strategy archetype
- **Strategic Implication:** System generating beta plays (sector rotation) instead of alpha generation (stock selection)
- **Fix Required:**
  1. Add "Security Selection Requirements by Archetype" to system prompt
  2. Require individual stocks for mean reversion, value, fundamental strategies
  3. Add worked example showing individual stock selection [WFC, BAC, JPM]
  4. Make fundamental analysis tools MANDATORY for applicable archetypes

### Strategic Insights

**1. Implementation-Thesis Coherence More Critical Than Expected**
- Original analysis focused on conditional vs static logic
- November 3 run revealed DEEPER issue: security selection sophistication
- Mean reversion thesis requires individual stock analysis, not sector ETFs
- **Learning:** "Coherence" includes security selection level, not just rebalancing logic

**2. Retry Mechanism is Double-Edged**
- ✅ Catches validation failures
- ❌ Can make things worse if poorly designed (asset drift)
- **Learning:** Retry must be surgical (fix specific issue) not wholesale (regenerate)

**3. Quality Gates Need Enforcement**
- Edge Scorecard designed correctly, but not enforced
- overall_pass=False strategies slipped through
- **Learning:** Design ≠ Enforcement. Add explicit filtering, not just scoring.

**4. Truncation is Insidious**
- Charter looked complete at first glance
- Only detailed review revealed missing "Final Verdict" section
- **Learning:** Need automated truncation detection (check for incomplete sections)

### Updated Success Criteria

**Pre-November 3 Target:**
- 8.0+/10 overall quality
- 90%+ implementation-thesis coherence
- 70%+ conditional logic adoption

**Post-November 3 Target:**
- 8.0+/10 overall quality (unchanged)
- 90%+ implementation-thesis coherence (unchanged, but deeper definition)
- 70%+ conditional logic adoption (unchanged)
- **🆕 100% blocker resolution rate** (all 4 blockers must be fixed)
- **🆕 Security selection sophistication:** Individual stocks for mean reversion/value, not ETFs
- **🆕 Retry fidelity:** 100% asset/weight preservation in retry (surgical fixes only)
- **🆕 Charter completeness:** 100% of charters must have all sections (no truncation)

### Impact on Original Root Cause Analysis

**Validated Root Causes:**
- ✅ RC-1 (Validation Timing): Confirmed - retry caught failures
- ✅ RC-2B (One Example): Partially confirmed - narrative strong, implementation weak
- ✅ RC-4B (ETF-Heavy Examples): Confirmed - ETF-heavy examples anchored outputs; stock-selection example added to counterbalance

**New Root Causes Discovered:**
- 🆕 RC-RETRY-1: Asset drift in retry (not in original analysis)
- 🆕 RC-EDGE-1: Scorecard bypass (enforcement gap)
- 🆕 RC-CHARTER-1: Truncation (token limit or generation issue)
- 🆕 RC-SECTOR-1: Security selection gap (deeper coherence issue)

**Overall Assessment:**
- Original analysis: 70-80% accurate
- Missed: 4 critical implementation/enforcement gaps
- **Action:** Phase 0 fixes MUST precede original 6 fixes

---

## ARTIFACT 5: Pattern Selection Rationale

### Applying

1. **Doc Fix #1: Validation Timing**
   - **Source:** Analysis document lines 477-523
   - **Trust score:** ★★★★★ (doc-validated, 85% probability root cause)
   - **Why:** RC-1A/1B (85% prob): Validation after generation too late, agent rationalizes
   - **Where:** candidate_generator.py post-validation with retry loop
   - **Adaptation:** Batch+retry (1-3 calls) vs pure sequential (5 calls) for cost efficiency

2. **Doc Fix #2: Add 4 Detailed Examples**
   - **Source:** Analysis document lines 526-544
   - **Trust score:** ★★★★★ (doc-validated, 80% probability root cause)
   - **Why:** VIX proves model CAN do it, needs templates for other archetypes
   - **Where:** candidate_generation.md after line 429
   - **Examples:** Momentum, Mean-reversion, Carry, Multi-factor (4 × 60-75 lines each)

3. **Doc Fix #3: Mandatory Planning Step**
   - **Source:** Analysis document lines 546-575
   - **Trust score:** ★★★★☆ (doc-validated, 60% probability)
   - **Why:** Forces conscious decision about conditional logic before generation
   - **Where:** candidate_generation.md after line 148, before Step 2.2
   - **Format:** 5 rows × 8 columns table with commitments

4. **Doc Fix #5 → Fix #4: Backtesting Validation**
   - **Source:** Analysis document lines 652-714 (NEW issue #6)
   - **Trust score:** ★★★★★ (doc-identified gap, 80% probability)
   - **Why:** Kimi K2 makes confident % assertions without evidence
   - **Where:** candidate_generation_system.md after line 638
   - **Enforcement:** AUTO-REJECT % claims without backtesting OR hypothesis language

5. **Doc RC-7 → Fix #5: Reporting Bug Fix**
   - **Source:** Analysis document lines 413-422
   - **Trust score:** ★★★☆☆ (30% probability but easy fix)
   - **Why:** Incorrect reporting confuses quality assessment
   - **Where:** Search for summary generation code, fix logic_tree check

6. **User Correction → Fix #6: Diversity Revision**
   - **Source:** User message: "allow duplicate types, but with different stocks... articulating different theses"
   - **Trust score:** ★★★★★ (user requirement)
   - **Why:** User explicitly rejected cross-run diversity database
   - **Where:** candidate_generation_system.md lines 345-369

7. **Pydantic Strict Validation (Safety Net)**
   - **Source:** Code flow tracing found missing validator + Kimi K2 research
   - **Trust score:** ★★★★☆ (addresses Kimi K2 known weakness)
   - **Why:** User wants prompt-first but Kimi K2 bypasses constraints
   - **Where:** models.py after line 268 (validate_conditional_logic_required)
   - **Scope:** ONE validator only, not all matrix rules

8. **Constitutional AI (Retry Loop Pattern)**
   - **Source:** Web research + doc Fix #1 implementation
   - **Trust score:** ★★★★☆ (research-validated)
   - **Why:** Critique (validation errors) → Revise (fix prompt) cycle
   - **Where:** candidate_generator.py validation + retry functions

9. **Doc Alternative Hypothesis: Coherence > Complexity**
   - **Source:** Analysis document lines 815-907 (Industry Practice Benchmark)
   - **Trust score:** ★★★★☆ (evidence-based recalibration)
   - **Why:** Forcing 80%+ conditional may be over-engineering
   - **Where:** Success criteria: 90%+ coherence (not 80%+ conditional)
   - **Evidence:** Fama-French, AQR, DFA all use simple periodic rebalancing

### Not Using

1. **Cross-Run Diversity Tracking (Doc Fix #4)**
   - **Why not:** User explicitly rejected
   - **Alternative:** Allow duplicate archetypes with different assets

2. **Threshold Guidance (Doc RC-6)**
   - **Why not:** User said ignore, lower priority
   - **Alternative:** VIX thresholds in example; others use relative comparisons

3. **Pure Sequential One-at-a-Time**
   - **Why not:** 5x API calls, 5x cost - inefficient
   - **Using instead:** Batch + retry hybrid

4. **Model Comparison Testing**
   - **Why not:** Need to validate fixes work first
   - **When:** After implementation complete

---

## Implementation Roadmap

### Phase 1: Prompt Enhancements (90 minutes)

**File:** `src/agent/prompts/candidate_generation.md`

**Step 1.1: Planning Matrix (20 min)**
- Insert after line 148, before Step 2.1
- Format: Markdown table 5 rows × 8 columns
- Validation checkpoint: If Conditional=YES with empty Triggers → STOP

**Step 1.2: Four Examples (60 min)**
- Insert after line 429 (after VIX)
- Section: "Additional Worked Examples by Archetype"
- Examples: Momentum, Mean-reversion, Carry, Multi-factor
- Each: ~60-75 lines with Context→Edge→Planning→Strategy→Validation

**Step 1.3: Reference Integrations (10 min)**
- Step 2.1: Add edge-frequency matrix reference
- Step 2.2: Add weight derivation methods reference
- Step 2.3: Add correlation anti-pattern warning

### Phase 2: Code Enforcement (60 minutes)

**File:** `src/agent/models.py` (15 min)
- Add `validate_conditional_logic_required()` after line 268
- Checks: thesis keywords → logic_tree not empty

**File:** `src/agent/stages/candidate_generator.py` (45 min)
- Add `validate_semantics()`: checks coherence, alignment, % claims
- Add `create_fix_prompt()`: generates targeted error messages
- Add `retry_failed_strategies()`: single retry with fixes
- Update `generate()`: orchestrate validation + retry

### Phase 3: Fixes & Clarifications (30 minutes)

**Backtesting Validation (15 min)**
- File: `src/agent/prompts/system/candidate_generation_system.md`
- Insert after line 638
- Rule: % claims require validation OR hypothesis language

**Reporting Bug (10 min)**
- Grep for summary generation code
- Fix logic_tree check
- Test with mock data

**Diversity Revision (5 min)**
- File: `candidate_generation_system.md` lines 345-369
- Add: "ACCEPTABLE: duplicate archetypes with different assets/theses"

### Phase 4: Validation (Integrated)

**Checkpoints:**
- ✅ Planning matrix template present
- ✅ 4 examples with correct structure
- ✅ Validation functions pass linting/type checking
- ✅ Bug fix verified with mock data
- ✅ Integration test with full workflow

---

## Success Metrics

### Primary Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Implementation-thesis coherence | 40% | 90%+ | Manual review of thesis vs logic_tree |
| Conditional logic rate | 20% | 40-60% | Count populated logic_tree |
| Overall quality score | 6.1/10 | 8.0+/10 | Doc rubric evaluation |
| Validation pass rate | Unknown | 80%+ | Track failures + retries |
| Quantitative claims validated | 0% | 100% | Check evidence or hedge language |

### Secondary Metrics

- Template diversity: Monitor archetype distribution
- Token efficiency: Track usage vs budget
- Retry rate: % of runs requiring retry
- Quality by archetype: Ensure non-VIX improve

### Regression Detection

**Alert if:**
- Coherence drops below 70%
- Quality score drops >1.5 points
- Validation failure rate >20%

**Success if:**
- Coherence >90% for 5 consecutive runs
- Quality score >8.0 sustained
- Retry fixes >90% of validation failures

---

## Appendix: Detailed Example Templates

### Example Structure (Each 60-75 lines)

```markdown
### Example: [Archetype Name]

**Context Pack Data:**
- Regime: [Current state]
- Key metrics: [Relevant data]
- Leadership: [Sectors/factors]

**Edge:**
[1-2 sentence specific inefficiency]

**Implementation Planning:**
1. Requires conditional logic? [YES/NO + reasoning]
2. Triggers identified: [List conditions]
3. Weight derivation: [Method + formula]
4. Rebalancing frequency: [Frequency + justification]

**Complete Strategy Object:**
```python
Strategy(
  name="...",
  thesis_document="""...""",
  rebalancing_rationale="""...""",
  assets=[...],
  weights={} or {...},
  rebalance_frequency="...",
  logic_tree={...}
)
```

**Coherence Validation Checklist:**
✅ Logic Tree Completeness: [Explanation]
✅ Rebalancing Alignment: [Explanation]
✅ Weight Derivation: [Explanation]
✅ Internal Consistency: [Checks]
✅ No Contradictions: [Checks]

**Why This Implementation Is Coherent:**
- [Design decision 1]
- [Design decision 2]
- [Comparison to common mistakes]
```

---

## Key Changes Based on Subagent Reviews

### From Architecture Validation Review:
- **✅ Restructured Phase 0:** Only 2 TRUE blockers (35 min), not 4 (105 min)
  - RC-EDGE-1 (Edge Scorecard): TRUE blocker - prevents deployment
  - RC-CHARTER-1 (Truncation): TRUE blocker - prevents deployment
  - RC-RETRY-1 (Asset Drift): Merged into Fix #2 (retry implementation)
  - RC-SECTOR-1 (Stock Selection): Merged into Fix #3 (Alpha vs Beta framework)

### From Prompt Engineering Review:
- **✅ Added Constitutional Constraints Layer:** Move validation rules to top priority window
- **✅ Added RSIP Checkpoints:** Pre-generation reasoning → Post-generation reflection → Pre-submission validation
- **✅ Removed Pydantic Validators:** Per user request, pure prompt engineering approach
- **✅ Hierarchical Context Management:** Constraints → Task → Context → Examples

### From Strategic Sophistication Analysis:
- **✅ Added Alpha vs Beta Framework:** Conceptual foundation for security selection
- **✅ Added Security Selection Workflow:** Universe → Screening → Fundamental Analysis → Ranking
- **✅ Added Coherence-Based Requirements:** Not universal "require stocks" - match archetype needs
- **✅ Dual-Sophistication Examples:** VIX conditional logic + Mean reversion stock selection

### From Risk Assessment:
- **✅ Realistic Time Estimates:** 8-12 hours (not 4.5 hours optimistic)
- **✅ Incremental Deployment:** Phase 0 → Pause → Validate → Phase 1
- **✅ Testing Buffer:** 1-2 hours integration testing explicitly included
- **✅ Go/No-Go Checkpoints:** Phase 0 must deploy end-to-end before Phase 1

## Next Steps

1. **Review & Approval** - User reviews updated architecture plan
2. **Phase 0: DEPLOYMENT BLOCKERS** - Implement 2 critical fixes (35 min)
   - Edge Scorecard enforcement
   - Charter truncation fix
3. **Checkpoint: Validate Phase 0** - System must deploy end-to-end
4. **Phase 1: CORE ARCHITECTURE** - Implement prompt improvements (6-8 hours)
   - Constitutional constraints layer
   - RSIP reflection checkpoints
   - Alpha vs Beta framework
   - Four archetype examples
   - Planning matrix with RSIP
5. **Phase 2: POLISH** - Validation rules + bug fix (45 min)
6. **Phase 3: INTEGRATION TESTING** - End-to-end validation (1-2 hours)
7. **DOCUMENTER Phase** - Update docs and capture learnings

**Estimated Total Time:** 8-12 hours (realistic)
- Phase 0: 35 minutes
- Phase 1: 6-8 hours
- Phase 2: 45 minutes
- Phase 3: 1-2 hours

**Expected Quality Improvement:** 6.1/10 → 8.5+/10 (+39%)
- Implementation-thesis coherence: 40% → 90%+
- Conditional logic rate: 20% → 60-80%
- Security selection sophistication: 0% → 80%+ (for applicable archetypes)
- Blocker resolution: 100% (all deployment blockers fixed)

---

**Document Version:** 1.2
**Last Updated:** November 3, 2024 (Revised with Subagent Review Insights)
**Status:** Restructured based on 4 specialized subagent reviews - Ready for Implementation
**Change Log:**
- v1.2 (Nov 3, 2024): Restructured based on subagent reviews - separated true blockers from quality improvements, added RSIP checkpoints, added Alpha vs Beta framework, removed Pydantic validators per user request, realistic time estimates (8-12 hours)
- v1.1 (Nov 3, 2024): Added Phase 0 blocker fixes from production run, expanded to 10 total fixes, added Lessons Learned section
- v1.0 (Nov 2, 2024): Initial architecture plan with 6 fixes
**Next Phase:** BUILDER (Phase 0 first, then Phase 1-3)
