import { useState } from 'react';
import { RequestRow, Quote } from '../data/types';
import Table from './Table';

type Props = {
  data: RequestRow[];
  role: string;
  onAccept: (row: RequestRow, quote: Quote) => void;
};

export default function DashboardSimple({ data, role, onAccept }: Props) {
  const [search, setSearch] = useState('');

  const filteredData = data.filter(row => {
    if (!search) return true;
    
    const searchLower = search.toLowerCase();
    return (
      row.requestedBy.toLowerCase().includes(searchLower) ||
      row.caseRef.toLowerCase().includes(searchLower) ||
      row.from.toLowerCase().includes(searchLower) ||
      row.to.toLowerCase().includes(searchLower)
    );
  });

  return (
    <div className="bg-gray-50 rounded-lg p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Dashboard — Simplified View</h2>
      
      {/* Simple Search */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search requests..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Simplified Table */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <Table
          rows={filteredData}
          simplified={true}
          onAccept={onAccept}
          showIncentive={role === 'affiliate'}
        />
      </div>

      {/* Summary Stats */}
      <div className="mt-6 text-center text-sm text-gray-600">
        Showing {filteredData.length} of {data.length} requests
      </div>
    </div>
  );
}