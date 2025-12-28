'use client';

import ReactMarkdown from 'react-markdown';
import type { WorkflowResult } from '../lib/types';

interface StrategyDetailProps {
  result: WorkflowResult;
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="font-sans text-xs font-medium text-muted tracking-wide mb-3">
      {children}
    </h3>
  );
}

function Markdown({ children }: { children: string }) {
  return (
    <div className="font-serif text-lg leading-[1.65] text-foreground prose prose-stone max-w-none prose-headings:font-sans prose-headings:text-foreground prose-p:my-4 prose-ul:my-4 prose-li:my-1 prose-code:font-mono prose-code:text-sm prose-code:bg-stone-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded">
      <ReactMarkdown>{children}</ReactMarkdown>
    </div>
  );
}

interface LogicTreeNode {
  condition?: string;
  if_true?: { assets: string[]; weights: Record<string, number> };
  if_false?: { assets: string[]; weights: Record<string, number> };
}

function renderWeights(weights: Record<string, number>): React.ReactNode {
  return (
    <div className="font-mono text-sm space-y-1 ml-4">
      {Object.entries(weights).map(([asset, weight]) => (
        <div key={asset}>
          <span className="text-foreground">{asset}</span>
          <span className="text-muted">: </span>
          <span className="text-foreground">{(weight * 100).toFixed(0)}%</span>
        </div>
      ))}
    </div>
  );
}

function renderLogicTree(tree: Record<string, unknown>): React.ReactNode {
  if (!tree || typeof tree !== 'object') return null;

  const node = tree as LogicTreeNode;

  if (node.condition && node.if_true && node.if_false) {
    return (
      <div className="font-mono text-sm space-y-2">
        <div>
          <span className="text-vermillion">if</span>{' '}
          <span className="text-foreground">{node.condition}</span>
        </div>
        {renderWeights(node.if_true.weights)}
        <div>
          <span className="text-vermillion">else</span>
        </div>
        {renderWeights(node.if_false.weights)}
      </div>
    );
  }

  return (
    <pre className="font-mono text-sm text-foreground bg-stone-100 p-4 rounded overflow-x-auto">
      {JSON.stringify(tree, null, 2)}
    </pre>
  );
}

export function StrategyDetail({ result }: StrategyDetailProps) {
  const { strategy, charter, selection_reasoning } = result;
  const hasLogicTree = strategy.logic_tree && Object.keys(strategy.logic_tree).length > 0;
  const hasWeights = strategy.weights && Object.keys(strategy.weights).length > 0;

  return (
    <div className="px-8 py-8 md:px-16 lg:px-24">
      <div className="max-w-prose space-y-10">
        {/* Assets & Allocation */}
        <section>
          <SectionHeader>Assets & Allocation</SectionHeader>
          <div className="flex flex-wrap gap-2 mb-4">
            {strategy.assets.map((asset) => (
              <span
                key={asset}
                className="px-3 py-1 bg-border rounded font-mono text-sm text-foreground"
              >
                {asset}
              </span>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm mb-6">
            <div>
              <span className="font-sans text-muted">Rebalance:</span>{' '}
              <span className="font-mono text-foreground">{strategy.rebalance_frequency}</span>
            </div>
            <div>
              <span className="font-sans text-muted">Archetype:</span>{' '}
              <span className="font-mono text-foreground">{strategy.archetype}</span>
            </div>
            <div>
              <span className="font-sans text-muted">Edge Type:</span>{' '}
              <span className="font-mono text-foreground">{strategy.edge_type}</span>
            </div>
            <div>
              <span className="font-sans text-muted">Concentration:</span>{' '}
              <span className="font-mono text-foreground">{strategy.concentration_intent}</span>
            </div>
          </div>

          {/* Logic Tree */}
          {hasLogicTree && (
            <div className="mt-4">
              <p className="font-sans text-sm text-muted mb-2">Logic Tree:</p>
              <div className="bg-stone-50 border border-border rounded p-4 overflow-x-auto">
                {renderLogicTree(strategy.logic_tree)}
              </div>
            </div>
          )}

          {/* Static Weights */}
          {hasWeights && !hasLogicTree && (
            <div className="mt-4">
              <p className="font-sans text-sm text-muted mb-2">Weights:</p>
              <div className="bg-stone-50 border border-border rounded p-4">
                <div className="font-mono text-sm space-y-1">
                  {Object.entries(strategy.weights).map(([asset, weight]) => (
                    <div key={asset}>
                      <span className="text-foreground">{asset}</span>
                      <span className="text-muted">: </span>
                      <span className="text-foreground">{(weight * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Market Thesis */}
        <section>
          <SectionHeader>Market Thesis</SectionHeader>
          <Markdown>{charter.market_thesis}</Markdown>
        </section>

        {/* Selection Reasoning */}
        <section>
          <SectionHeader>Selection Reasoning</SectionHeader>
          <Markdown>{selection_reasoning.why_selected}</Markdown>
          {selection_reasoning.tradeoffs_accepted && (
            <div className="mt-4 pt-4 border-t border-border">
              <p className="font-sans text-sm text-muted mb-2">Tradeoffs Accepted:</p>
              <Markdown>{selection_reasoning.tradeoffs_accepted}</Markdown>
            </div>
          )}
          <div className="mt-4 flex items-center gap-4">
            <span className="font-sans text-sm text-muted">Conviction:</span>
            <span className="font-mono text-sm text-foreground">
              {(selection_reasoning.conviction_level * 100).toFixed(0)}%
            </span>
          </div>
        </section>

        {/* Failure Modes */}
        {charter.failure_modes && charter.failure_modes.length > 0 && (
          <section>
            <SectionHeader>Failure Modes</SectionHeader>
            <ul className="space-y-3">
              {charter.failure_modes.map((mode, i) => (
                <li key={i} className="flex gap-3">
                  <span className="text-muted shrink-0">•</span>
                  <span className="font-serif text-lg leading-[1.65] text-foreground">
                    {mode}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Expected Behavior */}
        {charter.expected_behavior && (
          <section>
            <SectionHeader>Expected Behavior</SectionHeader>
            <Markdown>{charter.expected_behavior}</Markdown>
          </section>
        )}
      </div>
    </div>
  );
}
