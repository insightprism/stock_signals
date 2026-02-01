import { useState, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table';
import { useSignals, useStats } from '../hooks/useSentimentData';
import type { RawSignal } from '../api/sentimentApi';

export default function SignalsPage() {
  const { data: stats } = useStats();

  const [driver, setDriver] = useState('');
  const [layer, setLayer] = useState('');
  const [source, setSource] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [page, setPage] = useState(1);
  const [sorting, setSorting] = useState<SortingState>([]);

  const filters = useMemo(() => ({
    driver: driver || undefined,
    layer: layer || undefined,
    source: source || undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
    page,
    page_size: 50,
  }), [driver, layer, source, startDate, endDate, page]);

  const { data: result, isLoading } = useSignals(filters);

  const columns = useMemo<ColumnDef<RawSignal>[]>(() => [
    { accessorKey: 'date', header: 'Date', size: 110 },
    { accessorKey: 'driver', header: 'Driver', size: 140 },
    { accessorKey: 'layer', header: 'Layer', size: 100 },
    { accessorKey: 'source', header: 'Source', size: 130 },
    { accessorKey: 'series_name', header: 'Series', size: 180 },
    {
      accessorKey: 'raw_value',
      header: 'Raw Value',
      size: 110,
      cell: info => {
        const v = info.getValue<number>();
        return v != null ? v.toFixed(4) : '---';
      },
    },
    {
      accessorKey: 'normalized_value',
      header: 'Normalized',
      size: 110,
      cell: info => {
        const v = info.getValue<number | null>();
        return v != null ? v.toFixed(1) : '---';
      },
    },
  ], []);

  const tableData = result?.data ?? [];

  const table = useReactTable({
    data: tableData,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Driver</label>
            <select
              value={driver}
              onChange={e => { setDriver(e.target.value); setPage(1); }}
              className="w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm"
            >
              <option value="">All</option>
              {(stats?.drivers ?? []).map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Layer</label>
            <select
              value={layer}
              onChange={e => { setLayer(e.target.value); setPage(1); }}
              className="w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm"
            >
              <option value="">All</option>
              {(stats?.layers ?? []).map(l => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Source</label>
            <select
              value={source}
              onChange={e => { setSource(e.target.value); setPage(1); }}
              className="w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm"
            >
              <option value="">All</option>
              {(stats?.sources ?? []).map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={e => { setStartDate(e.target.value); setPage(1); }}
              className="w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={e => { setEndDate(e.target.value); setPage(1); }}
              className="w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm"
            />
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>
          {result ? `${result.total.toLocaleString()} signals found` : 'Loading...'}
        </span>
        {(driver || layer || source || startDate || endDate) && (
          <button
            onClick={() => { setDriver(''); setLayer(''); setSource(''); setStartDate(''); setEndDate(''); setPage(1); }}
            className="text-amber-600 hover:text-amber-700 font-medium"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="table-container" style={{ maxHeight: '600px' }}>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0">
              {table.getHeaderGroups().map(hg => (
                <tr key={hg.id}>
                  {hg.headers.map(header => (
                    <th
                      key={header.id}
                      className="px-3 py-2.5 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer select-none hover:bg-gray-100"
                      style={{ width: header.getSize() }}
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      <div className="flex items-center gap-1">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {{ asc: ' ↑', desc: ' ↓' }[header.column.getIsSorted() as string] ?? ''}
                      </div>
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                <tr>
                  <td colSpan={columns.length} className="text-center py-10 text-gray-400">
                    <div className="animate-spin inline-block rounded-full h-8 w-8 border-4 border-amber-500 border-t-transparent" />
                  </td>
                </tr>
              ) : table.getRowModel().rows.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="text-center py-10 text-gray-400">
                    No signals found
                  </td>
                </tr>
              ) : (
                table.getRowModel().rows.map(row => (
                  <tr key={row.id} className="hover:bg-gray-50">
                    {row.getVisibleCells().map(cell => (
                      <td key={cell.id} className="px-3 py-2 text-sm text-gray-700 whitespace-nowrap">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {result && result.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">
            Page {result.page} of {result.total_pages}
          </span>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(p => p - 1)}
              className="px-3 py-1.5 rounded-md text-sm bg-gray-100 text-gray-600 hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              disabled={page >= result.total_pages}
              onClick={() => setPage(p => p + 1)}
              className="px-3 py-1.5 rounded-md text-sm bg-gray-100 text-gray-600 hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
