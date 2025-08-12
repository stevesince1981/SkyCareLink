import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { RoleKey, RequestRow, Quote } from '../data/types';
import { data } from '../data/quotes';
import RoleToggle from '../components/RoleToggle';
import DashboardFull from '../components/DashboardFull';
import DashboardSimple from '../components/DashboardSimple';
import ConfirmationModal from '../components/ConfirmationModal';

export default function PhaseOne() {
  const [sp] = useSearchParams();
  const role = (sp.get('role') as RoleKey) || 'provider';
  
  const [confirmationModal, setConfirmationModal] = useState({
    isOpen: false,
    request: null as RequestRow | null,
    quote: null as Quote | null
  });

  const roleData = useMemo(() => data[role] || [], [role]);

  const handleAccept = (request: RequestRow, quote: Quote) => {
    // Generate booking reference
    const bookingRef = `MF-${Math.random().toString(36).substr(2, 6).toUpperCase()}`;
    
    // Show toast notification
    const toast = document.createElement('div');
    toast.className = 'fixed top-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    toast.textContent = `Accepted — Ref #${bookingRef}`;
    document.body.appendChild(toast);
    
    // Remove toast after 3 seconds
    setTimeout(() => {
      document.body.removeChild(toast);
    }, 3000);

    // Open confirmation modal
    setConfirmationModal({
      isOpen: true,
      request,
      quote
    });
  };

  const closeConfirmationModal = () => {
    setConfirmationModal({
      isOpen: false,
      request: null,
      quote: null
    });
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Sticky Header */}
      <header className="sticky top-0 bg-white border-b border-gray-200 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Phase 1 Dashboard Preview</h1>
              <p className="text-sm text-gray-600">Role-based medical transport dashboard</p>
            </div>
            <RoleToggle />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Panel - Full View */}
          <div>
            <DashboardFull 
              data={roleData}
              role={role}
              onAccept={handleAccept}
            />
          </div>

          {/* Right Panel - Simplified View */}
          <div>
            <DashboardSimple 
              data={roleData}
              role={role}
              onAccept={handleAccept}
            />
          </div>
        </div>

        {/* Role Information */}
        <div className="mt-8 bg-white rounded-lg border p-4">
          <h3 className="font-medium text-gray-900 mb-2">Current Role: {role.charAt(0).toUpperCase() + role.slice(1)}</h3>
          <div className="text-sm text-gray-600">
            {role === 'provider' && (
              <p>Provider view shows comprehensive request management with {roleData.length} active requests, advanced filtering, and detailed quote analysis.</p>
            )}
            {role === 'affiliate' && (
              <p>Affiliate view displays {roleData.length} referral opportunities with incentive indicators and streamlined acceptance workflow.</p>
            )}
            {role === 'individual' && (
              <p>Individual view shows {roleData.length} personal transport requests with simplified interface and clear status tracking.</p>
            )}
          </div>
        </div>
      </main>

      {/* Confirmation Modal */}
      <ConfirmationModal
        isOpen={confirmationModal.isOpen}
        onClose={closeConfirmationModal}
        request={confirmationModal.request}
        quote={confirmationModal.quote}
      />
    </div>
  );
}