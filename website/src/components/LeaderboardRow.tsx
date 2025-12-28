'use client';

import Image from 'next/image';
import type { WorkflowResult } from '../lib/types';
import { StrategyDetail } from './StrategyDetail';

interface LeaderboardRowProps {
  result: WorkflowResult;
  rank: number;
  isWinner: boolean;
  isExpanded: boolean;
  showDetail: boolean;
  onToggleExpand: () => void;
  onToggleDetail: () => void;
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
  if_true?: { assets: string[]; weights: Record<string, number> };
  if_false?: { assets: string[]; weights: Record<string, number> };
}

function formatLogicTreeCompact(tree: Record<string, unknown>): React.ReactNode {
  const node = tree as LogicTreeNode;

  if (node.condition && node.if_true && node.if_false) {
    const trueAssets = node.if_true.assets.join('/');
    const falseAssets = node.if_false.assets.join('/');

    return (
      <div className="font-mono text-sm text-muted">
        <span className="text-vermillion">if</span>{' '}
        <span className="text-foreground">{node.condition}</span>
        <span className="text-muted mx-2">→</span>
        <span className="text-foreground">{trueAssets}</span>
        <span className="text-muted mx-2">|</span>
        <span className="text-vermillion">else</span>
        <span className="text-muted mx-2">→</span>
        <span className="text-foreground">{falseAssets}</span>
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
}: LeaderboardRowProps) {
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
        <td className="px-4 py-3 text-right font-mono text-sm text-muted/40">
          ···
        </td>
        <td className="px-4 py-3 text-right font-mono text-sm text-muted/40">
          ···
        </td>
        <td className="px-4 py-3 text-right font-mono text-sm text-muted/40">
          ···
        </td>
        <td className="px-4 py-3 text-right font-mono text-sm text-muted/40">
          ···
        </td>
      </tr>

      {/* Level 1: Summary */}
      {isExpanded && (
        <tr>
          <td colSpan={8} className="bg-stone-50 px-6 py-5">
            <div className="max-w-2xl">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-muted">▼</span>
                <span className="inline-flex items-center gap-1.5">
                  {providerLogo && (
                    <Image
                      src={providerLogo}
                      alt=""
                      width={14}
                      height={14}
                      className="opacity-60"
                    />
                  )}
                  <span className="font-mono text-sm text-foreground">{modelName}</span>
                </span>
                <span className="text-muted">—</span>
                <span className="font-sans text-sm text-foreground">&ldquo;{result.strategy.name}&rdquo;</span>
              </div>

              <p className="font-serif text-lg leading-relaxed text-foreground mb-4">
                {summary}
              </p>

              {allocationCompact && (
                <div className="mb-4 p-3 bg-stone-50 border border-border rounded">
                  {allocationCompact}
                </div>
              )}

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleDetail();
                }}
                className="font-sans text-sm text-vermillion hover:underline"
              >
                {showDetail ? 'Hide full thesis ↑' : 'View full thesis →'}
              </button>
            </div>
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
