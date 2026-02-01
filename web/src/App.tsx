import { Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { AssetProvider } from './context/AssetContext';
import { routes } from './config/routeConfig';

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="animate-spin rounded-full h-12 w-12 border-4 border-amber-500 border-t-transparent"></div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AssetProvider>
        <Layout>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              {routes.map((route) => (
                <Route
                  key={route.path}
                  path={route.path}
                  element={<route.component />}
                />
              ))}
            </Routes>
          </Suspense>
        </Layout>
      </AssetProvider>
    </BrowserRouter>
  );
}

export default App;
