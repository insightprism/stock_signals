import { lazy, type ComponentType } from 'react';

interface RouteConfig {
  path: string;
  label: string;
  component: ComponentType;
}

const HomePage = lazy(() => import('../pages/HomePage'));
const HistoryPage = lazy(() => import('../pages/HistoryPage'));
const DriversPage = lazy(() => import('../pages/DriversPage'));
const SignalsPage = lazy(() => import('../pages/SignalsPage'));

export const routes: RouteConfig[] = [
  { path: '/', label: 'Dashboard', component: HomePage },
  { path: '/history', label: 'History', component: HistoryPage },
  { path: '/drivers', label: 'Drivers', component: DriversPage },
  { path: '/signals', label: 'Signals', component: SignalsPage },
];
