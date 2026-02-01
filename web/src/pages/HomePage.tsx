import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useCompositeLatest, useDriversLatest, useConfig, useStats } from '../hooks/useSentimentData';
import { runPipeline, fetchPipelineStatus } from '../api/sentimentApi';

const DRIVER_LABELS: Record<string, string> = {
  monetary_policy: 'Monetary Policy',
  us_dollar: 'US Dollar',
  inflation_expect: 'Inflation Expectations',
  geopolitical_risk: 'Geopolitical Risk',
  investment_demand: 'Investment Demand',
  spec_positioning: 'Speculative Positioning',
  risk_appetite: 'Risk Appetite',
};

function scoreColor(score: number): string {
  if (score < 35) return 'text-red-600';
  if (score < 45) return 'text-orange-500';
  if (score < 55) return 'text-gray-600';
  if (score < 65) return 'text-lime-600';
  return 'text-green-600';
}

function scoreBg(score: number): string {
  if (score < 35) return 'bg-red-500';
  if (score < 45) return 'bg-orange-400';
  if (score < 55) return 'bg-gray-400';
  if (score < 65) return 'bg-lime-500';
  return 'bg-green-500';
}

function scoreGradientBg(score: number): string {
  if (score < 35) return 'from-red-600 to-red-500';
  if (score < 45) return 'from-orange-500 to-orange-400';
  if (score < 55) return 'from-gray-500 to-gray-400';
  if (score < 65) return 'from-lime-600 to-lime-500';
  return 'from-green-600 to-green-500';
}

function ScoreBar({ score, label }: { score: number; label: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-gray-500 w-24 shrink-0">{label}</span>
      <div className="flex-1 bg-gray-200 rounded-full h-4 relative">
        <div
          className={`h-4 rounded-full ${scoreBg(score)}`}
          style={{ width: `${Math.max(score, 2)}%` }}
        />
      </div>
      <span className={`text-sm font-semibold w-12 text-right ${scoreColor(score)}`}>
        {score.toFixed(1)}
      </span>
    </div>
  );
}

function RunPipelineButton() {
  const queryClient = useQueryClient();
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const poll = useCallback(() => {
    const interval = setInterval(async () => {
      try {
        const status = await fetchPipelineStatus();
        if (!status.running) {
          clearInterval(interval);
          setRunning(false);
          if (status.last_error) {
            setError(status.last_error);
          } else {
            queryClient.invalidateQueries();
          }
        }
      } catch {
        // keep polling
      }
    }, 3000);
    return interval;
  }, [queryClient]);

  useEffect(() => {
    // Check if already running on mount
    fetchPipelineStatus().then(s => {
      if (s.running) {
        setRunning(true);
        poll();
      }
    }).catch(() => {});
  }, [poll]);

  const handleRun = async () => {
    setError(null);
    setRunning(true);
    try {
      const res = await runPipeline();
      if (res.status === 'already_running') {
        // just poll
      }
      poll();
    } catch (e: unknown) {
      setRunning(false);
      setError(e instanceof Error ? e.message : 'Failed to start pipeline');
    }
  };

  return (
    <div className="space-y-3">
      <button
        onClick={handleRun}
        disabled={running}
        className="px-6 py-3 bg-amber-600 text-white font-semibold rounded-lg hover:bg-amber-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
      >
        {running ? (
          <span className="flex items-center gap-2">
            <span className="animate-spin inline-block rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
            Pipeline Running...
          </span>
        ) : (
          'Run Pipeline (Today)'
        )}
      </button>
      {error && (
        <p className="text-sm text-red-600">Error: {error}</p>
      )}
      {running && (
        <p className="text-sm text-gray-400">
          Collecting signals and computing scores. This may take a few minutes.
        </p>
      )}
    </div>
  );
}

export default function HomePage() {
  const { data: composite, isLoading: compLoading } = useCompositeLatest();
  const { data: driversData, isLoading: drvLoading } = useDriversLatest();
  const { data: config } = useConfig();
  const { data: stats } = useStats();

  if (compLoading || drvLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-amber-500 border-t-transparent" />
      </div>
    );
  }

  if (!composite) {
    return (
      <div className="text-center py-20 text-gray-500">
        <p className="text-xl font-medium mb-2">No data available yet</p>
        <p className="mb-6">Run the pipeline to collect signals and generate composite scores.</p>
        <RunPipelineButton />
      </div>
    );
  }

  const drivers = driversData?.data ?? [];

  return (
    <div className="space-y-6">
      {/* Run Pipeline */}
      <div className="flex justify-end">
        <RunPipelineButton />
      </div>

      {/* Composite Score Hero */}
      <div className={`bg-gradient-to-br ${scoreGradientBg(composite.composite_score)} rounded-2xl p-8 text-white shadow-lg`}>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            <p className="text-white/80 text-sm font-medium uppercase tracking-wider">Composite Score</p>
            <p className="text-6xl font-bold mt-1">{composite.composite_score.toFixed(1)}</p>
            <p className="text-2xl font-medium mt-1">{composite.label}</p>
            <p className="text-white/70 text-sm mt-2">Date: {composite.date}</p>
          </div>
          {composite.gold_price != null && (
            <div className="text-right">
              <p className="text-white/80 text-sm font-medium uppercase tracking-wider">Gold Price</p>
              <p className="text-4xl font-bold mt-1">${composite.gold_price.toFixed(2)}</p>
              {composite.gold_return != null && (
                <p className={`text-lg font-medium mt-1 ${composite.gold_return >= 0 ? 'text-green-200' : 'text-red-200'}`}>
                  {composite.gold_return >= 0 ? '+' : ''}{(composite.gold_return * 100).toFixed(2)}%
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Layer Scores */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Layer Scores</h2>
        <div className="space-y-3">
          <ScoreBar score={composite.sentiment_layer} label="Sentiment (40%)" />
          <ScoreBar score={composite.macro_layer} label="Macro (60%)" />
        </div>
      </div>

      {/* Driver Breakdown */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Driver Breakdown</h2>
        <div className="space-y-3">
          {(config?.driver_names ?? Object.keys(composite.driver_breakdown)).map(driverKey => {
            const driverData = drivers.find(d => d.driver === driverKey);
            const weight = config?.driver_weights[driverKey] ?? 0;
            const sentimentScore = driverData?.sentiment_score ?? 50;
            const macroScore = driverData?.macro_score ?? 50;
            const blended = (sentimentScore + macroScore) / 2;
            return (
              <div key={driverKey} className="border border-gray-100 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-700">
                    {DRIVER_LABELS[driverKey] ?? driverKey}
                  </span>
                  <span className="text-xs text-gray-400">Weight: {(weight * 100).toFixed(0)}%</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400 w-16">Sentiment</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2.5">
                      <div className={`h-2.5 rounded-full ${scoreBg(sentimentScore)}`} style={{ width: `${Math.max(sentimentScore, 2)}%` }} />
                    </div>
                    <span className={`text-xs font-medium w-8 text-right ${scoreColor(sentimentScore)}`}>{sentimentScore.toFixed(0)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400 w-16">Macro</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2.5">
                      <div className={`h-2.5 rounded-full ${scoreBg(macroScore)}`} style={{ width: `${Math.max(macroScore, 2)}%` }} />
                    </div>
                    <span className={`text-xs font-medium w-8 text-right ${scoreColor(macroScore)}`}>{macroScore.toFixed(0)}</span>
                  </div>
                </div>
                <div className="mt-1 flex items-center gap-2">
                  <span className="text-xs text-gray-400 w-16">Blended</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2.5">
                    <div className={`h-2.5 rounded-full ${scoreBg(blended)}`} style={{ width: `${Math.max(blended, 2)}%` }} />
                  </div>
                  <span className={`text-xs font-semibold w-8 text-right ${scoreColor(blended)}`}>{blended.toFixed(0)}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Quick Links + Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link to="/history" className="bg-white rounded-xl p-5 shadow-sm border border-gray-200 hover:border-amber-300 hover:shadow-md transition-all">
          <h3 className="font-semibold text-gray-800">History</h3>
          <p className="text-sm text-gray-500 mt-1">View composite score time series and gold price chart</p>
        </Link>
        <Link to="/drivers" className="bg-white rounded-xl p-5 shadow-sm border border-gray-200 hover:border-amber-300 hover:shadow-md transition-all">
          <h3 className="font-semibold text-gray-800">Drivers</h3>
          <p className="text-sm text-gray-500 mt-1">Detailed breakdown of all 7 sentiment drivers</p>
        </Link>
        <Link to="/signals" className="bg-white rounded-xl p-5 shadow-sm border border-gray-200 hover:border-amber-300 hover:shadow-md transition-all">
          <h3 className="font-semibold text-gray-800">Signals</h3>
          <p className="text-sm text-gray-500 mt-1">Browse and filter raw signal data</p>
        </Link>
      </div>

      {/* Stats Row */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 text-center">
            <p className="text-2xl font-bold text-gray-800">{stats.total_dates}</p>
            <p className="text-xs text-gray-500 mt-1">Days Tracked</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 text-center">
            <p className="text-2xl font-bold text-gray-800">{stats.signal_count.toLocaleString()}</p>
            <p className="text-xs text-gray-500 mt-1">Signals Collected</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 text-center">
            <p className="text-sm font-bold text-gray-800">{stats.min_date ?? '---'}</p>
            <p className="text-xs text-gray-500 mt-1">Earliest Date</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 text-center">
            <p className="text-sm font-bold text-gray-800">{stats.max_date ?? '---'}</p>
            <p className="text-xs text-gray-500 mt-1">Latest Date</p>
          </div>
        </div>
      )}
    </div>
  );
}
