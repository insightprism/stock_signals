import { useAsset } from '../context/AssetContext';

const CATEGORY_COLORS: Record<string, string> = {
  metal: 'bg-amber-100 text-amber-800',
  energy: 'bg-blue-100 text-blue-800',
  other: 'bg-gray-100 text-gray-600',
};

export function AssetSelector() {
  const { selectedAsset, setSelectedAsset, assets, assetsLoading } = useAsset();

  if (assetsLoading || assets.length === 0) return null;

  return (
    <div className="flex items-center gap-2">
      <select
        value={selectedAsset}
        onChange={e => setSelectedAsset(e.target.value)}
        className="bg-amber-800 text-white border border-amber-600 rounded-md px-3 py-1.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-amber-400 appearance-none cursor-pointer"
        style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3E%3Cpath stroke='%23ffffff' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3E%3C/svg%3E")`, backgroundPosition: 'right 0.5rem center', backgroundRepeat: 'no-repeat', backgroundSize: '1.2em 1.2em', paddingRight: '2rem' }}
      >
        {assets.map(a => (
          <option key={a.asset_id} value={a.asset_id}>
            {a.display_name}
          </option>
        ))}
      </select>
      {(() => {
        const current = assets.find(a => a.asset_id === selectedAsset);
        if (!current) return null;
        const cat = current.category || 'other';
        return (
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${CATEGORY_COLORS[cat] ?? CATEGORY_COLORS.other}`}>
            {cat.charAt(0).toUpperCase() + cat.slice(1)}
          </span>
        );
      })()}
    </div>
  );
}
