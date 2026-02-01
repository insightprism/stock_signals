import { useDriversLatest, useConfig } from '../hooks/useSentimentData';

const DRIVER_LABELS: Record<string, string> = {
  monetary_policy: 'Monetary Policy',
  us_dollar: 'US Dollar',
  inflation_expect: 'Inflation Expectations',
  geopolitical_risk: 'Geopolitical Risk',
  investment_demand: 'Investment Demand',
  spec_positioning: 'Speculative Positioning',
  risk_appetite: 'Risk Appetite',
};

const DRIVER_DESCRIPTIONS: Record<string, string> = {
  monetary_policy: 'Federal Reserve policy, interest rates, real yields',
  us_dollar: 'Dollar index strength/weakness (inverse relationship)',
  inflation_expect: 'Breakeven inflation rates and expectations',
  geopolitical_risk: 'Wars, sanctions, global conflicts',
  investment_demand: 'Gold ETF flows, central bank buying',
  spec_positioning: 'COMEX futures net managed money positioning',
  risk_appetite: 'VIX, equity markets, safe haven demand',
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

function scoreLabel(score: number): string {
  if (score < 20) return 'Strongly Bearish';
  if (score < 35) return 'Bearish';
  if (score < 45) return 'Slightly Bearish';
  if (score < 55) return 'Neutral';
  if (score < 65) return 'Slightly Bullish';
  if (score < 80) return 'Bullish';
  return 'Strongly Bullish';
}

function cardBorder(score: number): string {
  if (score < 35) return 'border-l-red-500';
  if (score < 45) return 'border-l-orange-400';
  if (score < 55) return 'border-l-gray-400';
  if (score < 65) return 'border-l-lime-500';
  return 'border-l-green-500';
}

export default function DriversPage() {
  const { data: driversData, isLoading: drvLoading } = useDriversLatest();
  const { data: config, isLoading: cfgLoading } = useConfig();

  if (drvLoading || cfgLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-amber-500 border-t-transparent" />
      </div>
    );
  }

  const drivers = driversData?.data ?? [];
  const date = driversData?.date;
  const driverNames = config?.driver_names ?? [];
  const weights = config?.driver_weights ?? {};
  const layerWeights = config?.layer_weights ?? { sentiment: 0.4, macro: 0.6 };

  if (drivers.length === 0) {
    return (
      <div className="text-center py-20 text-gray-500">
        <p className="text-xl font-medium mb-2">No driver data available</p>
        <p>Run the pipeline to generate driver scores.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {date && (
        <p className="text-sm text-gray-500">
          Showing scores for <span className="font-medium text-gray-700">{date}</span>
        </p>
      )}

      {/* Score scale legend */}
      <div className="flex flex-wrap gap-3 text-xs">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-500" /> Bearish (&lt;35)</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-orange-400" /> Slightly Bearish (35-45)</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-gray-400" /> Neutral (45-55)</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-lime-500" /> Slightly Bullish (55-65)</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-green-500" /> Bullish (&gt;65)</span>
      </div>

      {/* Driver cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {driverNames.map(driverKey => {
          const driverData = drivers.find(d => d.driver === driverKey);
          const sentimentScore = driverData?.sentiment_score ?? 50;
          const macroScore = driverData?.macro_score ?? 50;
          const weight = weights[driverKey] ?? 0;
          const weighted = weight * (sentimentScore * layerWeights.sentiment + macroScore * layerWeights.macro);
          const blended = sentimentScore * layerWeights.sentiment + macroScore * layerWeights.macro;

          return (
            <div
              key={driverKey}
              className={`bg-white rounded-xl shadow-sm border border-gray-200 border-l-4 ${cardBorder(blended)} p-5`}
            >
              <div className="flex items-start justify-between mb-1">
                <h3 className="font-semibold text-gray-800">
                  {DRIVER_LABELS[driverKey] ?? driverKey}
                </h3>
                <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
                  Weight: {(weight * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-xs text-gray-400 mb-4">
                {DRIVER_DESCRIPTIONS[driverKey] ?? ''}
              </p>

              {/* Sentiment score */}
              <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-500">Sentiment Score</span>
                  <span className={`text-sm font-bold ${scoreColor(sentimentScore)}`}>
                    {sentimentScore.toFixed(1)} - {scoreLabel(sentimentScore)}
                  </span>
                </div>
                <div className="bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${scoreBg(sentimentScore)}`}
                    style={{ width: `${Math.max(sentimentScore, 2)}%` }}
                  />
                </div>
              </div>

              {/* Macro score */}
              <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-500">Macro Score</span>
                  <span className={`text-sm font-bold ${scoreColor(macroScore)}`}>
                    {macroScore.toFixed(1)} - {scoreLabel(macroScore)}
                  </span>
                </div>
                <div className="bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all ${scoreBg(macroScore)}`}
                    style={{ width: `${Math.max(macroScore, 2)}%` }}
                  />
                </div>
              </div>

              {/* Weighted contribution */}
              <div className="pt-3 border-t border-gray-100 flex items-center justify-between">
                <span className="text-xs text-gray-400">Weighted contribution to composite</span>
                <span className="text-sm font-semibold text-gray-700">
                  {weighted.toFixed(1)} pts
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
