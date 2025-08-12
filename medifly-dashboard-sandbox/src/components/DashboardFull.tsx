import { useState } from 'react';
import { RequestRow, Quote } from '../data/types';
import MiniCards from './MiniCards';
import FiltersBar from './FiltersBar';
import Table from './Table';

type Props = {
  data: RequestRow[];
  role: string;
  onAccept: (row: RequestRow, quote: Quote) => void;
};

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

const defaultFilters: Filters = {
  search: '',
  status: [],
  priceMin: '',
  priceMax: '',
  etaMin: '',
  etaMax: '',
  dateStart: '',
  dateEnd: '',
};

export default function DashboardFull({ data, role, onAccept }: Props) {
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [viewModalOpen, setViewModalOpen] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState<RequestRow | null>(null);

  const filteredData = data.filter(row => {
    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      const matchesSearch = 
        row.requestedBy.toLowerCase().includes(searchLower) ||
        row.caseRef.toLowerCase().includes(searchLower) ||
        row.from.toLowerCase().includes(searchLower) ||
        row.to.toLowerCase().includes(searchLower);
      if (!matchesSearch) return false;
    }

    // Status filter
    if (filters.status.length > 0 && !filters.status.includes(row.status)) {
      return false;
    }

    // Price filter
    if (filters.priceMin || filters.priceMax) {
      const minPrice = row.quotes.reduce((min, q) => Math.min(min, q.price), Infinity);
      if (filters.priceMin && minPrice < parseInt(filters.priceMin)) return false;
      if (filters.priceMax && minPrice > parseInt(filters.priceMax)) return false;
    }

    // ETA filter
    if (filters.etaMin || filters.etaMax) {
      const minEta = row.quotes.reduce((min, q) => Math.min(min, q.etaMinutes), Infinity);
      if (filters.etaMin && minEta < parseInt(filters.etaMin)) return false;
      if (filters.etaMax && minEta > parseInt(filters.etaMax)) return false;
    }

    // Date filter
    if (filters.dateStart || filters.dateEnd) {
      const rowDate = new Date(row.updatedAt).toISOString().split('T')[0];
      if (filters.dateStart && rowDate < filters.dateStart) return false;
      if (filters.dateEnd && rowDate > filters.dateEnd) return false;
    }

    return true;
  });

  const handleView = (row: RequestRow) => {
    setSelectedRequest(row);
    setViewModalOpen(true);
  };

  const handleClearFilters = () => {
    setFilters(defaultFilters);
  };

  return (
    <div className="bg-gray-50 rounded-lg p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Dashboard — Full View</h2>
      
      <MiniCards data={filteredData} />
      
      <FiltersBar 
        filters={filters}
        onFiltersChange={setFilters}
        onClear={handleClearFilters}
      />

      <div className="bg-white rounded-lg border overflow-hidden">
        <Table
          rows={filteredData}
          onAccept={onAccept}
          onView={handleView}
          showIncentive={role === 'affiliate'}
        />
      </div>

      {/* View Modal */}
      {viewModalOpen && selectedRequest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-gray-900">Request Details</h3>
                <button
                  onClick={() => setViewModalOpen(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                  aria-label="Close">
                  ×
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Request Information</h4>
                  <div className="space-y-2 text-sm">
                    <div><span className="text-gray-600">Case Reference:</span> <span className="font-mono">{selectedRequest.caseRef}</span></div>
                    <div><span className="text-gray-600">Requested by:</span> {selectedRequest.requestedBy}</div>
                    <div><span className="text-gray-600">Route:</span> {selectedRequest.from} → {selectedRequest.to}</div>
                    <div><span className="text-gray-600">Equipment needed:</span> {selectedRequest.needs.join(', ')}</div>
                    <div><span className="text-gray-600">Status:</span> 
                      <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
                        selectedRequest.status === 'quotes_ready' ? 'bg-green-100 text-green-800' :
                        selectedRequest.status === 'collecting_quotes' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {selectedRequest.status.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Schedule</h4>
                  <div className="space-y-2 text-sm">
                    <div><span className="text-gray-600">Window start:</span> {new Date(selectedRequest.windowStart).toLocaleString()}</div>
                    <div><span className="text-gray-600">Window end:</span> {new Date(selectedRequest.windowEnd).toLocaleString()}</div>
                    <div><span className="text-gray-600">Last updated:</span> {new Date(selectedRequest.updatedAt).toLocaleString()}</div>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-3">Available Quotes</h4>
                <Table
                  rows={[selectedRequest]}
                  onAccept={(row, quote) => {
                    onAccept(row, quote);
                    setViewModalOpen(false);
                  }}
                  showIncentive={role === 'affiliate'}
                />
              </div>

              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setViewModalOpen(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700">
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}