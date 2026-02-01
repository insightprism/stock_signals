import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export interface CompositeData {
  id: number;
  date: string;
  composite_score: number;
  label: string;
  sentiment_layer: number;
  macro_layer: number;
  driver_breakdown: Record<string, { sentiment: number; macro: number; weighted: number }>;
  gold_price: number | null;
  gold_return: number | null;
}

export interface DriverScore {
  id: number;
  date: string;
  driver: string;
  sentiment_score: number | null;
  macro_score: number | null;
}

export interface RawSignal {
  id: number;
  date: string;
  driver: string;
  layer: string;
  source: string;
  series_name: string;
  raw_value: number;
  normalized_value: number | null;
  metadata: string | null;
}

export interface StatsData {
  total_dates: number;
  min_date: string | null;
  max_date: string | null;
  signal_count: number;
  sources: string[];
  drivers: string[];
  layers: string[];
}

export interface ConfigData {
  driver_weights: Record<string, number>;
  layer_weights: Record<string, number>;
  driver_names: string[];
}

export const fetchCompositeLatest = () =>
  api.get<{ data: CompositeData | null }>('/composite/latest').then(r => r.data.data);

export const fetchCompositeHistory = (startDate?: string, endDate?: string) => {
  const params: Record<string, string> = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  return api.get<{ data: CompositeData[] }>('/composite/history', { params }).then(r => r.data.data);
};

export const fetchDriversLatest = () =>
  api.get<{ data: DriverScore[]; date: string | null }>('/drivers/latest').then(r => r.data);

export const fetchDriversHistory = (startDate?: string, endDate?: string) => {
  const params: Record<string, string> = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  return api.get<{ data: DriverScore[] }>('/drivers/history', { params }).then(r => r.data.data);
};

export const fetchSignals = (filters: {
  driver?: string;
  layer?: string;
  source?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}) =>
  api.get<{
    data: RawSignal[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  }>('/signals', { params: filters }).then(r => r.data);

export const fetchConfig = () =>
  api.get<ConfigData>('/config').then(r => r.data);

export const fetchStats = () =>
  api.get<StatsData>('/stats').then(r => r.data);

export interface PipelineStatus {
  running: boolean;
  last_error: string | null;
  last_result: { date: string; composite_score: number; label: string } | null;
}

export const runPipeline = (targetDate?: string) => {
  const params: Record<string, string> = {};
  if (targetDate) params.target_date = targetDate;
  return api.post<{ status: string; date?: string }>('/pipeline/run', null, { params }).then(r => r.data);
};

export const fetchPipelineStatus = () =>
  api.get<PipelineStatus>('/pipeline/status').then(r => r.data);
