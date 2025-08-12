import { useState } from 'react';

type Filters = {
  search: string;
  status: string[];
  priceMin: string;
  priceMax: string;
  etaMin: string;
  etaMax: string;
  dateStart: string;
  dateEnd: string;
};

type Props = {
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
  onClear: () => void;
};

const statusOptions = [
  'draft', 'submitted', 'collecting_quotes', 'quotes_ready', 'booked', 'expired'
];

const savedViews = ['Today', 'Last 7 Days', 'My Favorites'];

export default function FiltersBar({ filters, onFiltersChange, onClear }: Props) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleStatusToggle = (status: string) => {
    const newStatus = filters.status.includes(status)
      ? filters.status.filter(s => s !== status)
      : [...filters.status, status];
    onFiltersChange({ ...filters, status: newStatus });
  };

  const handleSavedView = (view: string) => {
    // Simple presets for demo
    const today = new Date().toISOString().split('T')[0];
    const week = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    switch (view) {
      case 'Today':
        onFiltersChange({ ...filters, dateStart: today, dateEnd: today });
        break;
      case 'Last 7 Days':
        onFiltersChange({ ...filters, dateStart: week, dateEnd: today });
        break;
      case 'My Favorites':
        onFiltersChange({ ...filters, status: ['quotes_ready', 'booked'] });
        break;
    }
  };

  return (
    <div className="bg-white rounded-lg border p-4 mb-4">
      <div className="flex flex-wrap items-center gap-4 mb-4">
        <input
          type="text"
          placeholder="Search requests..."
          value={filters.search}
          onChange={(e) => onFiltersChange({ ...filters, search: e.target.value })}
          className="flex-1 min-w-64 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50">
          {showAdvanced ? 'Hide' : 'Show'} Filters
        </button>
        <button
          onClick={onClear}
          className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800">
          Clear All
        </button>
      </div>

      {/* Saved Views */}
      <div className="flex gap-2 mb-4">
        <span className="text-sm text-gray-600 py-1">Quick views:</span>
        {savedViews.map(view => (
          <button
            key={view}
            onClick={() => handleSavedView(view)}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-full">
            {view}
          </button>
        ))}
      </div>

      {showAdvanced && (
        <div className="border-t pt-4 space-y-4">
          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <div className="flex flex-wrap gap-2">
              {statusOptions.map(status => (
                <button
                  key={status}
                  onClick={() => handleStatusToggle(status)}
                  className={`px-3 py-1 text-sm rounded-full border ${
                    filters.status.includes(status)
                      ? 'bg-blue-100 border-blue-300 text-blue-700'
                      : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}>
                  {status.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Price Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Price Range</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={filters.priceMin}
                  onChange={(e) => onFiltersChange({ ...filters, priceMin: e.target.value })}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                />
                <input
                  type="number"
                  placeholder="Max"
                  value={filters.priceMax}
                  onChange={(e) => onFiltersChange({ ...filters, priceMax: e.target.value })}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                />
              </div>
            </div>

            {/* ETA Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">ETA (minutes)</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={filters.etaMin}
                  onChange={(e) => onFiltersChange({ ...filters, etaMin: e.target.value })}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                />
                <input
                  type="number"
                  placeholder="Max"
                  value={filters.etaMax}
                  onChange={(e) => onFiltersChange({ ...filters, etaMax: e.target.value })}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                />
              </div>
            </div>

            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
              <input
                type="date"
                value={filters.dateStart}
                onChange={(e) => onFiltersChange({ ...filters, dateStart: e.target.value })}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
              <input
                type="date"
                value={filters.dateEnd}
                onChange={(e) => onFiltersChange({ ...filters, dateEnd: e.target.value })}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}