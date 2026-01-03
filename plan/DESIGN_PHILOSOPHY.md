# Design Philosophy: Cohort Tracking Website

## Core Concept

**Leaderboard + Longform**

A data-forward surface with readable drill-in. The leaderboard shows who's winning at a glance; clicking in reveals reasoning in readable prose.

This tension—compressed data vs. expansive narrative—is the heart of the design. Neither dominates; they complement.

## Audience & Vibe

**Audience**: Technical crowd (researchers, builders, quantitatively literate)

**Vibe**: Toy project with serious data. Precise but not cold. The design should feel like a well-maintained research notebook—functional, clear, with personality in the details rather than decoration.

**Anti-patterns to avoid**:
- Gratuitous dashboards with meaningless charts
- "Fintech blue" corporate aesthetic
- Overly playful/whimsical elements that undermine data credibility
- Dense, impersonal data walls

## Typography System

Three fonts, each with a distinct role:

| Role | Font | Weight | Usage |
|------|------|--------|-------|
| **Data/Numbers** | Commit Mono | 400-700 | Returns, percentages, metrics, code |
| **UI/Headers** | Satoshi | 400-700 | Section labels, navigation, buttons |
| **Reasoning/Prose** | Sentient | 400 | Thesis text, explanations, narratives |

### Type Scale

```
Data numbers:     16-24px, Commit Mono
Section headers:  14-20px, Satoshi, weight 500-600
Body prose:       18px, Sentient, line-height 1.65
Labels/meta:      12px, Satoshi, uppercase, letter-spacing: 0.05em
```

### Rationale

- **Commit Mono** for data creates visual consistency across all numbers. Monospace ensures columns align naturally.
- **Satoshi** is geometric but warm—technical without being sterile.
- **Sentient** as a serif for long-form reading signals "slow down, read this carefully." It elevates the AI's reasoning from raw output to considered analysis.

## Color Palette

```css
/* Neutrals */
--background:     #fafaf9   /* Warm white, not sterile */
--foreground:     #1a1a1a   /* Near-black, high contrast */
--muted:          #6b6b6b   /* Secondary text */
--border:         #e5e5e5   /* Subtle dividers */

/* Semantic */
--vermillion:     #ff3a2d   /* Winner accent, positive returns, CTAs */
--negative:       #9b2c2c   /* Negative returns, warnings */
--benchmark:      #a3a3a3   /* SPY/QQQ/60-40 chart lines */
```

### Color Usage Principles

1. **Vermillion is earned.** Only the winner gets a vermillion left-border. Positive returns get vermillion text. CTAs get vermillion. Don't dilute it.

2. **Benchmarks are quiet.** They exist for comparison, not attention. Gray keeps them in the background.

3. **Backgrounds stay warm.** The `#fafaf9` warm white prevents the clinical feel of pure white against data-heavy tables.

4. **No gratuitous color.** If something doesn't need color to communicate, it doesn't get color.

5. **Accents with restraint.** Small visual flourishes (LIVE badge, winner emoji 👑) are OK when they add information or personality—but use sparingly. One or two per view, not scattered throughout.

## Information Architecture

### Progressive Disclosure (3 Levels)

The leaderboard is a compressed view. Each row can expand to reveal more context, but users control the depth.

```
Level 0: Table Row (default view)
├── Rank, Model, Strategy Name, Assets, Return, Alpha, Sharpe, Drawdown
├── Monospace numbers, asset pills, minimal chrome
└── Winner: vermillion left border

Level 1: Summary (first click)
├── Model name + strategy name header
├── 2-sentence summary in Sentient serif
├── Allocation preview (logic tree or weights)
└── "View full thesis →" link

Level 2: Full Detail (second click)
├── Assets & Allocation (all assets, logic tree, metadata)
├── Market Thesis (full prose)
├── Selection Reasoning (why this beat 4 alternatives)
├── Failure Modes (bulleted list)
└── Expected Behavior (prose)
```

### Default State

On page load:
- Leaderboard table visible
- **Winner (rank #1) has Level 1 expanded by default**
- All other rows collapsed

This immediately surfaces the most interesting content without overwhelming.

### Why This Works

1. **Respects attention**: Users scanning get the table. Users investigating get the drill-in.
2. **Preserves context**: Expanding in-place (accordion) keeps the table visible for comparison.
3. **Rewards curiosity**: Each level reveals more depth, creating a "pull" rather than "push" information flow.

## Component Patterns

### Leaderboard Table

```
┌──────────────────────────────────────────────────────────────────┐
│ #    Model      Strategy           Assets       Return  Sharpe  │
├──────────────────────────────────────────────────────────────────┤
│ ▐1   kimi-k2    Momentum Rotation  QQQ TLT...   +4.21%   1.42   │  ← vermillion border
│  2   gpt-4o     Defensive Value    VTV AGG...   +2.15%   0.98   │
│  3   deepseek   Risk Parity Tilt   SPY TLT...   +1.82%   0.87   │
└──────────────────────────────────────────────────────────────────┘
```

**Rules:**
- No zebra striping (clean white rows)
- Subtle bottom borders only (`border-b border-border`)
- Model name left-aligned, metrics right-aligned
- Positive returns in vermillion, negative in `--negative`
- Winner row: 2px vermillion left border
- Hover state: subtle warm gray background (`bg-stone-50/50`)
- **Pending metrics**: Single em-dash `—` in muted color (not triple dots or "N/A")

### Asset Pills

```
┌─────┐ ┌─────┐ ┌─────┐ ┌────┐
│ QQQ │ │ TLT │ │ GLD │ │ +3 │
└─────┘ └─────┘ └─────┘ └────┘
```

- Show first 5 assets, then "+N" overflow
- `bg-border` background, `font-mono text-xs`
- Rounded corners (4px)

### Level 1 Summary

```
┌────────────────────────────────────────────────────────────────────────┐
│ ▼ kimi-k2 — "Momentum Rotation with Vol Dampening"                     │
│                                                                        │
│ A momentum-based strategy that rotates between growth and              │
│ defensive assets based on VIX thresholds. Designed for late-cycle      │
│ bull markets with elevated uncertainty.                                │
│                                                                        │
│ ┌──────────────────────────────────────────────────────┐               │
│ │ if VIX > 20 → QQQ/TLT | else → QQQ/GLD              │               │
│ └──────────────────────────────────────────────────────┘               │
│                                                                        │
│ View full thesis →                                                     │
└────────────────────────────────────────────────────────────────────────┘
```

- `bg-stone-100` background to differentiate from table
- Sentient serif for summary paragraph
- Allocation preview in monospace (logic tree syntax or weight breakdown)
- **Allocation block**: `bg-white` with border to pop against the stone-100 panel
- Vermillion link to Level 2

### Level 2 Full Detail

- Wide margins (responsive: `px-8 md:px-16 lg:px-24`)
- Max-width for prose: `max-w-prose` (~65ch)
- Clear section headers: Satoshi, uppercase, tracked, muted color
- Section spacing: `space-y-10`
- Prose rendering: Sentient at 18px, line-height 1.65

### Performance Chart

The cumulative returns chart sits above the leaderboard, providing visual context before the rankings.

```
┌────────────────────────────────────────────────────────────────────────┐
│ Cumulative Returns                                      Day 64 of 90   │
│                                                                        │
│     40% ─┬─────────────────────────────────────────                    │
│          │                           ╱──── kimi-k2 (winner, vermillion)│
│     20% ─┤                    ╱─────╱                                  │
│          │             ╱─────╱                                         │
│      0% ─┼────────────────────────────────── SPY (gray)                │
│          │                                                             │
│    -20% ─┤                                                             │
│          └─────────┬─────────────┬───────────┬─────────                │
│                  Jan 15       Feb 27       Apr 10                      │
│                                                                        │
│         — QQQ  — SPY  — kimi-k2  — kimi-k2  — kimi-k2  — kimi-k2       │
└────────────────────────────────────────────────────────────────────────┘
```

**Rules:**
- **Legend**: Model names only (not full strategy names). Full names appear in tooltip on hover.
- **Tooltip**: Sorted by return, highest first. Shows full "model: strategy name" format.
- **Line colors**: Winner gets vermillion; other strategies get a coherent palette (blue family); benchmarks (SPY/QQQ) in muted gray.
- **Line weights**: Winner 2.5px, strategies 1.5px, benchmarks 1px.
- **Endpoint logos**: Provider logo appears at line endpoint for visual identification.
- **X-axis**: Show first, middle, and last dates only (avoid clutter).
- **Y-axis**: Percentage format with Commit Mono.
- **Day counter**: "Day N of 90" in top-right corner.

## Interaction Patterns

### Click Behaviors

| Action | Result |
|--------|--------|
| Click row | Toggle Level 1 (collapses if open, expands if closed) |
| Click "View full thesis" | Expand Level 2 (Level 1 stays visible) |
| Click different row | Collapse current expansion, expand new row to Level 1 |

### Transitions

- Expand/collapse: `transition-colors duration-150` on hover
- Content appearance: No animation (instant expand, keeps it snappy)
- Consider slide animation for Level 2 if it feels abrupt

### Cursor

- Rows: `cursor-pointer` (entire row clickable)
- Links: Standard link behavior

## Responsive Considerations

### Mobile (< 768px)

**Deferred decision**: Table could either:
1. Horizontal scroll (preserves table structure)
2. Card stack (transforms each row into a card)

For MVP: horizontal scroll is simpler and preserves the data comparison affordance.

### Tablet (768-1024px)

- Reduce padding
- Keep table structure
- Level 2 detail spans full width

### Desktop (> 1024px)

- Generous margins on Level 2 detail
- Consider sidebar for navigation if multi-cohort switching added

## Future Considerations

These are explicitly **not** designed yet:

1. **Cohort switching UI**: Will need tabs or dropdown when multiple cohorts exist
2. **Empty/loading states**: Need design when data is unavailable
3. **Board meeting integration**: Day 30/60/90 decision points need UI treatment
4. **"What is this?" auto-collapse**: Consider collapsing intro section after first visit (localStorage)

## Design Principles Summary

1. **Data first, prose second**: Surface numbers immediately, reveal narrative on demand
2. **Earned emphasis**: Vermillion is for winners and positive outcomes only
3. **Typography does the work**: Three distinct fonts create hierarchy without decoration
4. **Progressive disclosure**: Users control depth; don't overwhelm
5. **Warm precision**: Technical but human—the warm white background, the serif for reasoning
6. **Restraint**: When in doubt, remove. Every element should justify its existence.
