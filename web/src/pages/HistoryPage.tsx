import { useEffect, useRef, useState, useMemo } from 'react';
import { createChart, type IChartApi, type ISeriesApi, LineSeries, AreaSeries } from 'lightweight-charts';
import { useCompositeHistory } from '../hooks/useSentimentData';

type RangeKey = '30d' | '90d' | '180d' | '1y' | 'all';

function getStartDate(range: RangeKey): string | undefined {
  if (range === 'all') return undefined;
  const d = new Date();
  const days = { '30d': 30, '90d': 90, '180d': 180, '1y': 365 }[range];
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

export default function HistoryPage() {
  const [range, setRange] = useState<RangeKey>('90d');
  const startDate = useMemo(() => getStartDate(range), [range]);
  const { data, isLoading } = useCompositeHistory(startDate);

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const compositeSeriesRef = useRef<ISeriesApi<'Area'> | null>(null);
  const sentimentSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const macroSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const goldSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  // Create chart once
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#ffffff' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 500,
      rightPriceScale: {
        visible: true,
        borderColor: '#ddd',
      },
      leftPriceScale: {
        visible: true,
        borderColor: '#ddd',
      },
      timeScale: {
        borderColor: '#ddd',
      },
    });

    const compositeSeries = chart.addSeries(AreaSeries, {
      lineColor: '#d97706',
      topColor: 'rgba(217, 119, 6, 0.4)',
      bottomColor: 'rgba(217, 119, 6, 0.05)',
      lineWidth: 2,
      priceScaleId: 'right',
      title: 'Composite',
    });

    const sentimentSeries = chart.addSeries(LineSeries, {
      color: '#3b82f6',
      lineWidth: 1,
      priceScaleId: 'right',
      title: 'Sentiment',
      lineStyle: 2,
    });

    const macroSeries = chart.addSeries(LineSeries, {
      color: '#8b5cf6',
      lineWidth: 1,
      priceScaleId: 'right',
      title: 'Macro',
      lineStyle: 2,
    });

    const goldSeries = chart.addSeries(LineSeries, {
      color: '#eab308',
      lineWidth: 2,
      priceScaleId: 'left',
      title: 'Gold $',
    });

    chartRef.current = chart;
    compositeSeriesRef.current = compositeSeries;
    sentimentSeriesRef.current = sentimentSeries;
    macroSeriesRef.current = macroSeries;
    goldSeriesRef.current = goldSeries;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, []);

  // Update data
  useEffect(() => {
    if (!data || !compositeSeriesRef.current) return;

    const compositeData = data.map(d => ({
      time: d.date as string,
      value: d.composite_score,
    }));

    const sentimentData = data.map(d => ({
      time: d.date as string,
      value: d.sentiment_layer,
    }));

    const macroData = data.map(d => ({
      time: d.date as string,
      value: d.macro_layer,
    }));

    const goldData = data
      .filter(d => d.gold_price != null)
      .map(d => ({
        time: d.date as string,
        value: d.gold_price!,
      }));

    compositeSeriesRef.current.setData(compositeData);
    sentimentSeriesRef.current?.setData(sentimentData);
    macroSeriesRef.current?.setData(macroData);
    goldSeriesRef.current?.setData(goldData);

    chartRef.current?.timeScale().fitContent();
  }, [data]);

  const ranges: { key: RangeKey; label: string }[] = [
    { key: '30d', label: '30D' },
    { key: '90d', label: '90D' },
    { key: '180d', label: '180D' },
    { key: '1y', label: '1Y' },
    { key: 'all', label: 'All' },
  ];

  return (
    <div className="space-y-4">
      {/* Range selector */}
      <div className="flex items-center gap-2">
        {ranges.map(r => (
          <button
            key={r.key}
            onClick={() => setRange(r.key)}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              range === r.key
                ? 'bg-amber-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {r.label}
          </button>
        ))}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-sm">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-amber-600" /> Composite (0-100)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-blue-500" /> Sentiment Layer
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-purple-500" /> Macro Layer
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-yellow-500" /> Gold Price (left axis)
        </span>
      </div>

      {/* Color band legend */}
      <div className="flex flex-wrap gap-3 text-xs text-gray-500">
        <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-red-400 rounded" /> Bearish (0-35)</span>
        <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-gray-300 rounded" /> Neutral (35-65)</span>
        <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-green-400 rounded" /> Bullish (65-100)</span>
      </div>

      {/* Chart */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        {isLoading && (
          <div className="flex items-center justify-center h-[500px]">
            <div className="animate-spin rounded-full h-10 w-10 border-4 border-amber-500 border-t-transparent" />
          </div>
        )}
        <div ref={chartContainerRef} className={isLoading ? 'invisible h-0' : ''} />
        {!isLoading && (!data || data.length === 0) && (
          <div className="flex items-center justify-center h-[500px] text-gray-400">
            No historical data available for this range
          </div>
        )}
      </div>
    </div>
  );
}
