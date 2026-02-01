import { useQuery } from '@tanstack/react-query';
import {
  fetchCompositeLatest,
  fetchCompositeHistory,
  fetchDriversLatest,
  fetchDriversHistory,
  fetchSignals,
  fetchConfig,
  fetchStats,
} from '../api/sentimentApi';

export function useCompositeLatest() {
  return useQuery({
    queryKey: ['composite', 'latest'],
    queryFn: fetchCompositeLatest,
  });
}

export function useCompositeHistory(startDate?: string, endDate?: string) {
  return useQuery({
    queryKey: ['composite', 'history', startDate, endDate],
    queryFn: () => fetchCompositeHistory(startDate, endDate),
  });
}

export function useDriversLatest() {
  return useQuery({
    queryKey: ['drivers', 'latest'],
    queryFn: fetchDriversLatest,
  });
}

export function useDriversHistory(startDate?: string, endDate?: string) {
  return useQuery({
    queryKey: ['drivers', 'history', startDate, endDate],
    queryFn: () => fetchDriversHistory(startDate, endDate),
  });
}

export function useSignals(filters: {
  driver?: string;
  layer?: string;
  source?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: ['signals', filters],
    queryFn: () => fetchSignals(filters),
  });
}

export function useConfig() {
  return useQuery({
    queryKey: ['config'],
    queryFn: fetchConfig,
    staleTime: Infinity,
  });
}

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
  });
}
