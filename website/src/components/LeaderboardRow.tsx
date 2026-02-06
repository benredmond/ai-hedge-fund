'use client';

import Image from 'next/image';
import type { WorkflowResult } from '../lib/types';
import { StrategyDetail } from './StrategyDetail';

interface Metrics {
  return: number;
  alpha: number;
  sharpe: number;
  maxDrawdown: number;
}

interface BenchmarkInfo {
  ticker: string;
  description: string;
}

interface LeaderboardRowProps {
  result: WorkflowResult;
  rank: number;
  isWinner: boolean;
  isExpanded: boolean;
  showDetail: boolean;
  onToggleExpand: () => void;
  onToggleDetail: () => void;
  metrics?: Metrics;
  isMobile: boolean;
  benchmark?: BenchmarkInfo;
}

function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${(value * 100).toFixed(1)}%`;
}

function formatSharpe(value: number): string {
  return value.toFixed(2);
}

function ChevronDown({ className }: { className?: string }) {
  return (
    <svg className={className} width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 4.5L6 7.5L9 4.5" />
    </svg>
  );
}

function ChevronRight({ className }: { className?: string }) {
  return (
    <svg className={className} width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4.5 3L7.5 6L4.5 9" />
    </svg>
  );
}

function ChevronUp({ className }: { className?: string }) {
  return (
    <svg className={className} width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 7.5L6 4.5L9 7.5" />
    </svg>
  );
}

function ArrowRight({ className }: { className?: string }) {
  return (
    <svg className={className} width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2.5 6H9.5M6.5 3L9.5 6L6.5 9" />
    </svg>
  );
}

function ArrowUpRight({ className }: { className?: string }) {
  return (
    <svg className={className} width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3.5 8.5L8.5 3.5M8.5 3.5H4.5M8.5 3.5V7.5" />
    </svg>
  );
}

function extractSummary(text: string, maxSentences = 2): string {
  // Fallback: extract first N sentences from thesis_document
  const sentences = text.split(/(?<=[.!?])\s+/);
  return sentences.slice(0, maxSentences).join(' ');
}

function getSummary(result: WorkflowResult): string {
  // Prefer AI-generated summary from Composer deployment, fall back to extraction
  if (result.strategy_summary) {
    return result.strategy_summary;
  }
  return extractSummary(result.strategy.thesis_document);
}

function formatModelName(model: string): string {
  // "openai:kimi-k2-thinking" -> "kimi-k2"
  const parts = model.split(':');
  const name = parts[parts.length - 1];
  return name.replace(/-thinking$/, '').replace(/-preview$/, '');
}

function getProviderLogo(model: string): string | null {
  const modelLower = model.toLowerCase();

  // Detect by model name first (handles openai: prefix for non-OpenAI models)
  if (modelLower.includes('kimi') || modelLower.includes('moonshot')) {
    return '/logos/moonshot.png';
  }
  if (modelLower.includes('deepseek')) {
    return '/logos/deepseek.png';
  }
  if (modelLower.includes('claude')) {
    return '/logos/anthropic.png';
  }
  if (modelLower.includes('gemini')) {
    return '/logos/google.png';
  }
  if (modelLower.includes('qwen')) {
    return '/logos/qwen.png';
  }
  if (modelLower.includes('grok')) {
    return '/logos/xai.png';
  }
  if (modelLower.includes('gpt') || modelLower.includes('o1') || modelLower.includes('o3')) {
    return '/logos/openai.svg';
  }

  // Fall back to prefix
  const prefix = model.split(':')[0];
  const logoMap: Record<string, string> = {
    openai: '/logos/openai.svg',
    anthropic: '/logos/anthropic.png',
  };

  return logoMap[prefix] || null;
}

interface LogicTreeNode {
  condition?: string;
  if_true?: LogicTreeNode;
  if_false?: LogicTreeNode;
  assets?: string[];
  weights?: Record<string, number>;
  filter?: Record<string, unknown>;
  weighting?: Record<string, unknown>;
}

function collectAssets(node?: LogicTreeNode): string[] {
  if (!node || typeof node !== 'object') return [];

  const assets: string[] = [];

  if (Array.isArray(node.assets)) {
    assets.push(...node.assets);
  }

  if (node.weights && typeof node.weights === 'object') {
    assets.push(...Object.keys(node.weights));
  }

  if (node.if_true) {
    assets.push(...collectAssets(node.if_true));
  }

  if (node.if_false) {
    assets.push(...collectAssets(node.if_false));
  }

  return Array.from(new Set(assets));
}

function formatLogicTreeCompact(tree: Record<string, unknown>): React.ReactNode {
  if (!tree || typeof tree !== 'object') return null;

  const node = tree as LogicTreeNode;

  if (node.condition && node.if_true && node.if_false) {
    const trueAssets = collectAssets(node.if_true);
    const falseAssets = collectAssets(node.if_false);
    const trueLabel = trueAssets.length > 0 ? trueAssets.join('/') : '—';
    const falseLabel = falseAssets.length > 0 ? falseAssets.join('/') : '—';

    return (
      <div className="font-mono text-sm text-muted flex items-center flex-wrap">
        <span className="text-vermillion">if</span>{' '}
        <span className="text-foreground">{node.condition}</span>
        <ArrowRight className="text-muted mx-2 inline-block" />
        <span className="text-foreground">{trueLabel}</span>
        <span className="text-muted mx-2">|</span>
        <span className="text-vermillion">else</span>
        <ArrowRight className="text-muted mx-2 inline-block" />
        <span className="text-foreground">{falseLabel}</span>
      </div>
    );
  }

  return null;
}

function formatWeightsCompact(weights: Record<string, number>): React.ReactNode {
  const entries = Object.entries(weights);
  if (entries.length === 0) return null;

  return (
    <div className="font-mono text-sm flex flex-wrap gap-x-4 gap-y-1">
      {entries.map(([asset, weight]) => (
        <span key={asset}>
          <span className="text-foreground">{asset}</span>
          <span className="text-muted">: </span>
          <span className="text-foreground">{(weight * 100).toFixed(0)}%</span>
        </span>
      ))}
    </div>
  );
}

export function LeaderboardRow({
  result,
  rank,
  isWinner,
  isExpanded,
  showDetail,
  onToggleExpand,
  onToggleDetail,
  metrics,
  isMobile,
  benchmark,
}: LeaderboardRowProps) {
  // Benchmark rows: simplified rendering
  if (benchmark) {
    if (isMobile) {
      return (
        <div className="border border-dashed border-border rounded-lg opacity-60">
          <div className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="font-mono text-sm text-muted">&mdash;</span>
              <span className="font-mono text-sm text-muted">{benchmark.ticker}</span>
            </div>
            <p className="font-sans text-sm text-muted mb-3">{benchmark.description}</p>
            <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-sm">
              {metrics ? (
                <>
                  <span className={metrics.return >= 0 ? 'text-vermillion' : 'text-negative'}>
                    {formatPercent(metrics.return)}
                  </span>
                  <span className="text-muted">Sharpe {formatSharpe(metrics.sharpe)}</span>
                  <span className="text-muted">DD {formatPercent(metrics.maxDrawdown)}</span>
                </>
              ) : (
                <span className="text-muted">Performance pending</span>
              )}
            </div>
          </div>
        </div>
      );
    }

    return (
      <tr className="border-b border-dashed border-border last:border-b-0">
        <td className="px-4 py-3 font-mono text-sm text-muted w-12">&mdash;</td>
        <td className="px-4 py-3 font-mono text-sm text-muted">{benchmark.ticker}</td>
        <td className="px-4 py-3 font-sans text-sm text-muted">{benchmark.description}</td>
        <td className="px-4 py-3"></td>
        <td className={`px-4 py-3 text-right font-mono text-sm ${metrics && metrics.return >= 0 ? 'text-vermillion' : metrics ? 'text-negative' : 'text-muted'}`}>
          {metrics ? formatPercent(metrics.return) : '—'}
        </td>
        <td className="px-4 py-3 text-right font-mono text-sm text-muted">&mdash;</td>
        <td className="px-4 py-3 text-right font-mono text-sm text-muted">
          {metrics ? formatSharpe(metrics.sharpe) : '—'}
        </td>
        <td className="px-4 py-3 text-right font-mono text-sm text-negative">
          {metrics ? formatPercent(metrics.maxDrawdown) : '—'}
        </td>
      </tr>
    );
  }

  const modelName = formatModelName(result.model || 'Unknown');
  const providerLogo = getProviderLogo(result.model || '');
  const summary = getSummary(result);
  const hasLogicTree = result.strategy.logic_tree && Object.keys(result.strategy.logic_tree).length > 0;
  const hasWeights = result.strategy.weights && Object.keys(result.strategy.weights).length > 0;

  const allocationCompact = hasLogicTree
    ? formatLogicTreeCompact(result.strategy.logic_tree)
    : hasWeights
      ? formatWeightsCompact(result.strategy.weights)
      : null;

  // Shared Level 1 Summary content
  const Level1Content = () => (
    <div className="max-w-2xl">
      <p className="font-serif text-lg leading-relaxed text-foreground mb-4">
        {summary}
      </p>

      {allocationCompact && (
        <div className="mb-4 p-3 bg-white border border-border rounded overflow-x-auto">
          <div className="min-w-0 break-words">
            {allocationCompact}
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggleDetail();
          }}
          className="font-sans text-sm text-vermillion hover:underline py-2 sm:py-0 text-left inline-flex items-center gap-1"
        >
          {showDetail ? (
            <>Hide full thesis <ChevronUp className="inline-block" /></>
          ) : (
            <>Show full thesis <ChevronDown className="inline-block" /></>
          )}
        </button>

        {result.symphony_id && (
          <a
            href={`https://app.composer.trade/symphony/${result.symphony_id}/details`}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="font-sans text-sm text-vermillion hover:underline py-2 sm:py-0 inline-flex items-center gap-1"
          >
            View on Composer <ArrowUpRight className="inline-block" />
          </a>
        )}
      </div>
    </div>
  );

  // Mobile Card Layout
  if (isMobile) {
    return (
      <div
        onClick={onToggleExpand}
        className={`
          border border-border rounded-lg cursor-pointer
          transition-colors duration-150
          ${isWinner ? 'border-l-4 border-l-vermillion' : ''}
          ${isExpanded ? 'bg-stone-50' : 'hover:bg-stone-50/50'}
        `}
      >
        {/* Card Header */}
        <div className="p-4">
          <div className="flex items-start justify-between gap-3 mb-2">
            <div className="flex items-center gap-2 min-w-0">
              <span className="font-mono text-sm text-muted">#{rank}</span>
              {isWinner && <span>👑</span>}
              {providerLogo && (
                <Image
                  src={providerLogo}
                  alt=""
                  width={16}
                  height={16}
                  className="opacity-60 shrink-0"
                />
              )}
              <span className="font-mono text-sm font-medium text-foreground">{modelName}</span>
            </div>
            {isExpanded ? <ChevronDown className="text-muted" /> : <ChevronRight className="text-muted" />}
          </div>

          <p className="font-sans text-sm text-foreground mb-3">
            {result.strategy.name}
          </p>

          {/* Metrics Row */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 mb-3 font-mono text-sm">
            {metrics ? (
              <>
                <span className={metrics.return >= 0 ? 'text-vermillion' : 'text-negative'}>
                  {formatPercent(metrics.return)}
                </span>
                <span className="text-muted">
                  Sharpe {formatSharpe(metrics.sharpe)}
                </span>
                <span className="text-muted">
                  DD {formatPercent(metrics.maxDrawdown)}
                </span>
              </>
            ) : (
              <span className="text-muted">Performance pending</span>
            )}
          </div>

          {/* Asset Pills */}
          <div className="flex flex-wrap gap-1">
            {result.strategy.assets.slice(0, 5).map((asset) => (
              <span
                key={asset}
                className="px-1.5 py-0.5 bg-border rounded text-xs font-mono text-muted"
              >
                {asset}
              </span>
            ))}
            {result.strategy.assets.length > 5 && (
              <span className="px-1.5 py-0.5 text-xs font-mono text-muted">
                +{result.strategy.assets.length - 5}
              </span>
            )}
          </div>
        </div>

        {/* Level 1: Expanded Summary */}
        {isExpanded && (
          <div className="border-t border-border bg-stone-100 p-4">
            <Level1Content />
          </div>
        )}

        {/* Level 2: Full Detail */}
        {isExpanded && showDetail && (
          <div className="border-t border-border bg-stone-100">
            <StrategyDetail result={result} />
          </div>
        )}
      </div>
    );
  }

  // Desktop Table Layout
  return (
    <>
      {/* Level 0: Table Row */}
      <tr
        onClick={onToggleExpand}
        className={`
          border-b border-border last:border-b-0 cursor-pointer
          transition-colors duration-150
          ${isWinner ? 'border-l-2 border-l-vermillion' : ''}
          ${isExpanded ? 'bg-stone-50' : 'hover:bg-stone-50/50'}
        `}
      >
        <td className="px-4 py-3 font-mono text-sm text-muted w-12">
          {rank}
        </td>
        <td className="px-4 py-3 font-mono text-sm text-foreground">
          <span className="inline-flex items-center gap-1.5">
            {isWinner && <span>👑</span>}
            {providerLogo && (
              <Image
                src={providerLogo}
                alt=""
                width={14}
                height={14}
                className="opacity-60"
              />
            )}
            {modelName}
          </span>
        </td>
        <td className="px-4 py-3 font-sans text-sm text-foreground">
          {result.strategy.name}
        </td>
        <td className="px-4 py-3">
          <div className="flex flex-wrap gap-1">
            {result.strategy.assets.slice(0, 5).map((asset) => (
              <span
                key={asset}
                className="px-1.5 py-0.5 bg-border rounded text-xs font-mono text-muted"
              >
                {asset}
              </span>
            ))}
            {result.strategy.assets.length > 5 && (
              <span className="px-1.5 py-0.5 text-xs font-mono text-muted">
                +{result.strategy.assets.length - 5}
              </span>
            )}
          </div>
        </td>
        <td className={`px-4 py-3 text-right font-mono text-sm ${metrics && metrics.return >= 0 ? 'text-vermillion' : metrics ? 'text-negative' : 'text-muted'}`}>
          {metrics ? formatPercent(metrics.return) : '—'}
        </td>
        <td className={`px-4 py-3 text-right font-mono text-sm ${metrics && metrics.alpha >= 0 ? 'text-vermillion' : metrics ? 'text-negative' : 'text-muted'}`}>
          {metrics ? formatPercent(metrics.alpha) : '—'}
        </td>
        <td className="px-4 py-3 text-right font-mono text-sm text-foreground">
          {metrics ? formatSharpe(metrics.sharpe) : '—'}
        </td>
        <td className="px-4 py-3 text-right font-mono text-sm text-negative">
          {metrics ? formatPercent(metrics.maxDrawdown) : '—'}
        </td>
      </tr>

      {/* Level 1: Summary */}
      {isExpanded && (
        <tr>
          <td colSpan={8} className="bg-stone-100 px-6 py-5">
            <Level1Content />
          </td>
        </tr>
      )}

      {/* Level 2: Full Detail */}
      {isExpanded && showDetail && (
        <tr>
          <td colSpan={8} className="bg-stone-100 border-t border-border">
            <StrategyDetail result={result} />
          </td>
        </tr>
      )}
    </>
  );
}
