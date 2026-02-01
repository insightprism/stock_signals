import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { fetchAssets, type AssetInfo } from '../api/sentimentApi';

interface AssetContextType {
  selectedAsset: string;
  setSelectedAsset: (asset: string) => void;
  assets: AssetInfo[];
  assetsLoading: boolean;
  currentAssetName: string;
}

const AssetContext = createContext<AssetContextType>({
  selectedAsset: 'gold',
  setSelectedAsset: () => {},
  assets: [],
  assetsLoading: true,
  currentAssetName: 'Gold',
});

export function AssetProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [selectedAsset, setSelectedAssetRaw] = useState('gold');
  const [assets, setAssets] = useState<AssetInfo[]>([]);
  const [assetsLoading, setAssetsLoading] = useState(true);

  useEffect(() => {
    fetchAssets()
      .then(setAssets)
      .catch(() => {})
      .finally(() => setAssetsLoading(false));
  }, []);

  const setSelectedAsset = (asset: string) => {
    setSelectedAssetRaw(asset);
    queryClient.invalidateQueries();
  };

  const currentAssetName =
    assets.find(a => a.asset_id === selectedAsset)?.display_name ?? selectedAsset;

  return (
    <AssetContext.Provider
      value={{ selectedAsset, setSelectedAsset, assets, assetsLoading, currentAssetName }}
    >
      {children}
    </AssetContext.Provider>
  );
}

export function useAsset() {
  return useContext(AssetContext);
}
