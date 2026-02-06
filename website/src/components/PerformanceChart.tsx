'use client';

import Image from 'next/image';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { PerformanceData } from '../lib/types';

// Strategy color palette (excluding vermillion which is reserved for winner)
const STRATEGY_COLORS = [
  '#2563eb', // blue
  '#7c3aed', // violet
  '#0891b2', // cyan
  '#059669', // emerald
  '#ca8a04', // yellow
];

interface PerformanceEntry {
  key: string;
  model: string;
  strategyName: string;
  isWinner: boolean;
  data: PerformanceData;
}

interface PerformanceChartProps {
  performances: PerformanceEntry[];
}

interface ChartDataPoint {
  date: string;
  displayDate: string;
  spy: number;
  qqq: number;
  [key: string]: string | number;
}

function formatModelName(model: string): string {
  const parts = model.split(':');
  return parts[parts.length - 1].replace(/-thinking$/, '').replace(/-preview$/, '');
}

function getProviderLogo(model: string): string | null {
  const modelLower = model.toLowerCase();
  if (modelLower.includes('kimi') || modelLower.includes('moonshot')) return '/logos/moonshot.png';
  if (modelLower.includes('deepseek')) return '/logos/deepseek.png';
  if (modelLower.includes('claude')) return '/logos/anthropic.png';
  if (modelLower.includes('gemini')) return '/logos/google.png';
  if (modelLower.includes('qwen')) return '/logos/qwen.png';
  if (modelLower.includes('grok')) return '/logos/xai.png';
  if (modelLower.includes('gpt') || modelLower.includes('o1') || modelLower.includes('o3')) return '/logos/openai.svg';
  const prefix = model.split(':')[0];
  if (prefix === 'openai') return '/logos/openai.svg';
  if (prefix === 'anthropic') return '/logos/anthropic.png';
  return null;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatPercentCompact(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function PerformanceChart({ performances }: PerformanceChartProps) {
  if (performances.length === 0) {
    return (
      <div className="bg-stone-50 border border-border rounded-lg p-8 text-center">
        <p className="font-sans text-sm text-muted">
          Performance data not yet available
        </p>
      </div>
    );
  }

  // Transform data: merge all strategies into single data points per date
  const dateMap = new Map<string, ChartDataPoint>();

  // Use first performance's data for benchmark values and dates
  const firstPerf = performances[0];
  for (const daily of firstPerf.data.daily) {
    dateMap.set(daily.date, {
      date: daily.date,
      displayDate: new Date(daily.date + 'T12:00:00').toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      }),
      spy: daily.spy_cumulative,
      qqq: daily.qqq_cumulative,
    });
  }

  // Add each strategy's returns (use unique key as data key)
  for (const perf of performances) {
    for (const daily of perf.data.daily) {
      const point = dateMap.get(daily.date);
      if (point) {
        point[perf.key] = daily.cumulative_return;
      }
    }
  }

  const chartData = Array.from(dateMap.values()).sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  // Calculate days elapsed from chart data
  const daysElapsed = chartData.length;

  // Assign colors: winner gets vermillion, others get palette colors
  // Use perf.key for dataKey (unique) but formatModelName + strategyName for display name
  let colorIndex = 0;
  const strategyLines = performances.map((perf) => {
    // Legend shows just model name - full strategy name visible on hover/tooltip
    const displayName = formatModelName(perf.model);
    const color = perf.isWinner ? '#ff3a2d' : STRATEGY_COLORS[colorIndex++ % STRATEGY_COLORS.length];
    const logo = getProviderLogo(perf.model);
    return { dataKey: perf.key, name: displayName, color, isWinner: perf.isWinner, logo, model: perf.model, fullName: `${formatModelName(perf.model)}: ${perf.strategyName}` };
  });

  // Create lookup map for tooltip/legend (keyed by both dataKey and name for legend clicks)
  const lineInfoMap = new Map(strategyLines.map(l => [l.dataKey, l]));
  const lineInfoByName = new Map(strategyLines.map(l => [l.name, l]));

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: {
    active?: boolean;
    payload?: Array<{ name: string; value: number; color: string; dataKey: string }>;
    label?: string;
  }) => {
    if (!active || !payload?.length) return null;

    // Sort by return value, highest first
    const sortedPayload = [...payload].sort((a, b) => b.value - a.value);

    return (
      <div className="bg-background border border-border rounded shadow-lg p-3">
        <p className="font-mono text-xs text-muted mb-2">{label}</p>
        {sortedPayload.map((entry) => {
          const lineInfo = lineInfoMap.get(entry.dataKey) || lineInfoByName.get(entry.name);
          // Show full strategy name in tooltip, not abbreviated legend name
          const displayName = lineInfo?.fullName || entry.name;
          return (
            <div key={entry.dataKey} className="flex items-center gap-2">
              <span
                className="w-3 h-0.5"
                style={{ backgroundColor: entry.color }}
              />
              {lineInfo?.logo && (
                <Image src={lineInfo.logo} alt="" width={12} height={12} className="opacity-60" />
              )}
              <span className="font-sans text-xs text-foreground">{displayName}</span>
              <span className="font-mono text-xs text-foreground ml-auto">
                {formatPercent(entry.value)}
              </span>
            </div>
          );
        })}
      </div>
    );
  };

  // X-axis tick formatter: show only first, middle, and last dates
  const tickFormatter = (value: string, index: number) => {
    const total = chartData.length;
    if (index === 0 || index === total - 1 || index === Math.floor(total / 2)) {
      return value;
    }
    return '';
  };

  // Custom dot that renders logo at the end of each line
  const lastIndex = chartData.length - 1;
  const createEndpointDot = (logo: string | null) => {
    function EndpointDot({ cx, cy, index }: { cx?: number; cy?: number; index?: number }) {
      if (index !== lastIndex || !logo || cx === undefined || cy === undefined) return null;
      return (
        <image
          x={cx + 4}
          y={cy - 8}
          width={16}
          height={16}
          href={logo}
          style={{ opacity: 0.7 }}
        />
      );
    }
    return EndpointDot;
  };

  return (
    <div className="bg-stone-50 border border-border rounded-lg p-4 sm:px-6 sm:pt-5 sm:pb-3">
      <div className="flex items-baseline justify-between mb-4">
        <h2 className="font-sans text-xs font-medium text-muted tracking-wide">
          Cumulative Returns
        </h2>
        <span className="font-mono text-xs text-muted">
          Day {daysElapsed} of 90
        </span>
      </div>
      <ResponsiveContainer width="100%" height={240} className="sm:!h-[260px]">
        <LineChart data={chartData} margin={{ top: 5, right: 25, left: 0, bottom: 0 }}>
          <XAxis
            dataKey="displayDate"
            tick={{ fontSize: 10, fontFamily: 'var(--font-commit-mono)' }}
            tickLine={false}
            axisLine={{ stroke: '#e5e5e5' }}
            tickFormatter={tickFormatter}
          />
          <YAxis
            tickFormatter={(value) => formatPercentCompact(value)}
            tick={{ fontSize: 10, fontFamily: 'var(--font-commit-mono)' }}
            tickLine={false}
            axisLine={false}
            width={40}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* Benchmark lines (thinner, gray) */}
          <Line
            type="monotone"
            dataKey="spy"
            name="SPY"
            stroke="#a3a3a3"
            strokeWidth={1}
            dot={false}
            activeDot={{ r: 3, fill: '#a3a3a3' }}
          />
          <Line
            type="monotone"
            dataKey="qqq"
            name="QQQ"
            stroke="#8a8a8a"
            strokeWidth={1}
            dot={false}
            activeDot={{ r: 3, fill: '#8a8a8a' }}
          />

          {/* Strategy lines (winner more prominent) */}
          {strategyLines.map((line) => (
            <Line
              key={line.dataKey}
              type="monotone"
              dataKey={line.dataKey}
              name={line.name}
              stroke={line.color}
              strokeWidth={line.isWinner ? 2.5 : 1.5}
              strokeOpacity={line.isWinner ? 1 : 0.7}
              dot={createEndpointDot(line.logo)}
              activeDot={{ r: 4, fill: line.color }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {/* Custom legend outside chart for tighter spacing */}
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 mt-1 text-[11px] font-sans">
        <div className="flex items-center gap-1.5">
          <span className="h-[1px] w-3 bg-[#a3a3a3]" />
          <span className="text-muted">QQQ</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-[1px] w-3 bg-[#8a8a8a]" />
          <span className="text-muted">SPY</span>
        </div>
        {strategyLines.map((line) => (
          <div key={line.dataKey} className="flex items-center gap-1.5">
            <span className="h-[2px] w-3" style={{ backgroundColor: line.color }} />
            <span style={{ color: line.isWinner ? line.color : undefined }}>{line.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
