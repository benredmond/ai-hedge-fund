---
id: P9T8hWAex8AOQ41cMPLsf
identifier: docs-plans-consolidation
title: Docs/Plans Consolidation Review
created: 2026-01-04T21:07:06Z
updated: 2026-01-04T21:07:06Z
phase: research
status: active
---

# Docs/Plans Consolidation Review

<research>
original_prompt: "search through ./docs and ./plans to see what we can consolidate / remove. plans should be human-gen, docs is ai-gen. the new source for \"task\" information is .apex/"
enhanced_prompt:
  intent: "Identify duplicative or outdated documentation in docs/ and plan/, and recommend consolidation/removal; move task-tracking content into .apex/"
  scope:
    in: ["docs/", "plan/", ".apex/tasks/"]
    out: ["src/", "tests/", "website/"]
  acceptance_criteria:
    - "List doc files that are task-oriented and should move to .apex or be removed"
    - "List overlapping docs and suggest a single canonical doc for each topic"
    - "Note overlaps inside plan/ that could be collapsed"
  success_metrics:
    - "Clear keep/consolidate/remove list with file paths"
  related_patterns: ["APEX.SYSTEM:PAT:AUTO:ImFaZC3j (not relevant)"]

inventory:
  docs_files: 23
  plan_files: 8
  task_info_source: ".apex/tasks/ (existing)"

findings:
  task_oriented_docs_with_ids:
    - docs/BYTECODE_CACHE_FIX_SPEC.md (Task ID)
    - docs/MCP_COMPRESSION_ARCHITECTURE_ANALYSIS.md (Task ID + task lists)
    - docs/prompt_engineering_architecture_plan.md (Task ID)
    - docs/SYMPHONY_LOGIC_AUDIT_INDEX.md (Task ID)
    - docs/RESEARCH_SUMMARY.md (Task + Task ID)
    - docs/PROFESSIONAL_VALIDATION_DEPLOYMENT.md (Task)
    - docs/REFINED_WORKFLOW_ARCHITECTURE_PLAN.md (Tasks list)
  task_adjacent_docs_no_ids_but_plan_like:
    - docs/CANDIDATE_GENERATION_FIX_PLAN.md
    - docs/candidate_quality_improvement_plan.md
    - docs/prompt_engineering_analysis_nov2024.md
    - docs/SYSTEMS_ANALYSIS_VALIDATION_FLOW.md
    - docs/VALIDATION_FLOW_DIAGRAM.md
    - docs/EXECUTION_FLOW_DETAILED.md
    - docs/SYMPHONY_LOGIC_AUDIT_INTEGRATION.md

  overlap_clusters:
    validation_flow:
      - docs/VALIDATION_FLOW_DIAGRAM.md
      - docs/SYSTEMS_ANALYSIS_VALIDATION_FLOW.md
      - docs/EXECUTION_FLOW_DETAILED.md
      - docs/RESEARCH_SUMMARY.md
      note: "Same flow described multiple ways; consolidate to a single canonical doc or move to .apex if tied to a task."
    symphony_logic_audit:
      - docs/SYMPHONY_LOGIC_AUDIT_INDEX.md
      - docs/SYMPHONY_LOGIC_AUDIT_INTEGRATION.md
      - docs/RESEARCH_SUMMARY.md
      note: "Index + integration guide overlap; consider keeping only integration guide or folding into one file."
    mcp_research:
      - docs/README_MCP_RESEARCH.md
      - docs/multi_provider_mcp_comparison.md
      - docs/quick_reference_mcp_providers.md
      - docs/mcp_provider_code_examples.md
      - docs/mcp_setup.md
      note: "Summary + quick ref + code examples are redundant; consider keeping quick ref + setup, and archiving large comparison + summary."
    token_management:
      - docs/TOKEN_MANAGEMENT.md
      - docs/STAGE_TOKEN_ANALYSIS.md
      note: "Stage analysis overlaps token management; merge and keep one canonical doc."
    market_context:
      - docs/market_context_schema.md
      - docs/MARKET_CONTEXT_V2_SPEC.md
      - plan/README.md
      - plan/MARKET_CONTEXT.md
      - plan/CONTEXT_PACK.md
      note: "Multiple specs/overviews; decide canonical v1 schema + current implementation vs future v2 spec."

  plan_internal_overlap:
    - plan/CONTEXT_PACK.md (includes a mini strategy-guidelines section)
    - plan/INVESTING_STRATEGY_GUIDELINES.md (full guidelines)
    note: "Context pack could reference the full guidelines doc instead of duplicating content."
    - plan/README.md vs plan/MARKET_CONTEXT.md (both describe context pack generation)

risks_and_gotchas:
  - "docs/mcp_setup.md embeds local paths and API keys; consider scrubbing or relocating to .env.example."
  - "docs/TOKEN_MANAGEMENT.md uses 4-stage language while STAGE_TOKEN_ANALYSIS covers 5 stages; ensure canonical doc matches current workflow."

recommendations_summary:
  move_to_apex_or_archive:
    - docs/BYTECODE_CACHE_FIX_SPEC.md
    - docs/MCP_COMPRESSION_ARCHITECTURE_ANALYSIS.md
    - docs/prompt_engineering_architecture_plan.md
    - docs/SYMPHONY_LOGIC_AUDIT_INDEX.md
    - docs/RESEARCH_SUMMARY.md
    - docs/PROFESSIONAL_VALIDATION_DEPLOYMENT.md
    - docs/REFINED_WORKFLOW_ARCHITECTURE_PLAN.md
  consolidate:
    - validation flow cluster → single canonical doc
    - symphony logic audit cluster → single canonical doc
    - token management → merge STAGE_TOKEN_ANALYSIS into TOKEN_MANAGEMENT
    - MCP research → keep quick reference + setup (or code examples), archive summary/comparison
  plan_cleanup_candidates:
    - plan/CONTEXT_PACK.md: remove duplicated guideline section, link to plan/INVESTING_STRATEGY_GUIDELINES.md
    - plan/README.md vs plan/MARKET_CONTEXT.md: choose one as primary
</research>

<plan>
<!-- Populated by /apex:plan -->
</plan>

<implementation>
<!-- Populated by /apex:implement -->
</implementation>

<ship>
<!-- Populated by /apex:ship -->
</ship>
