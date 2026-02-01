import { useQuery } from '@tanstack/react-query';
import {
  fetchCompositeLatest,
  fetchCompositeHistory,
  fetchDriversLatest,
  fetchDriversHistory,
  fetchSignals,
  fetchConfig,
  fetchStats,
  fetchAssets,
} from '../api/sentimentApi';

export function useAssets() {
  return useQuery({
    queryKey: ['assets'],
    queryFn: fetchAssets,
    staleTime: Infinity,
  });
}

export function useCompositeLatest(asset: string) {
  return useQuery({
    queryKey: ['composite', 'latest', asset],
    queryFn: () => fetchCompositeLatest(asset),
  });
}

export function useCompositeHistory(asset: string, startDate?: string, endDate?: string) {
  return useQuery({
    queryKey: ['composite', 'history', asset, startDate, endDate],
    queryFn: () => fetchCompositeHistory(asset, startDate, endDate),
  });
}

export function useDriversLatest(asset: string) {
  return useQuery({
    queryKey: ['drivers', 'latest', asset],
    queryFn: () => fetchDriversLatest(asset),
  });
}

export function useDriversHistory(asset: string, startDate?: string, endDate?: string) {
  return useQuery({
    queryKey: ['drivers', 'history', asset, startDate, endDate],
    queryFn: () => fetchDriversHistory(asset, startDate, endDate),
  });
}

export function useSignals(asset: string, filters: {
  driver?: string;
  layer?: string;
  source?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: ['signals', asset, filters],
    queryFn: () => fetchSignals(asset, filters),
  });
}

export function useConfig(asset: string) {
  return useQuery({
    queryKey: ['config', asset],
    queryFn: () => fetchConfig(asset),
    staleTime: Infinity,
  });
}

export function useStats(asset: string) {
  return useQuery({
    queryKey: ['stats', asset],
    queryFn: () => fetchStats(asset),
  });
}
