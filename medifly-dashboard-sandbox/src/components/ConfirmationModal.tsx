import { Quote, RequestRow } from '../data/types';
import { fmtMoney, fmtETA } from '../utils/format';

type Props = {
  isOpen: boolean;
  onClose: () => void;
  request: RequestRow | null;
  quote: Quote | null;
};

export default function ConfirmationModal({ isOpen, onClose, request, quote }: Props) {
  if (!isOpen || !request || !quote) return null;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-gray-900">Booking Confirmation</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
              aria-label="Close">
              ×
            </button>
          </div>

          <div className="space-y-6">
            {/* Booking Summary */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-800 mb-2">✓ Booking Confirmed</h3>
              <p className="text-green-700">
                Your transport request has been accepted and confirmed with {quote.providerName}.
              </p>
            </div>

            {/* Request Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Request Details</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="text-gray-600">Case Reference:</span> <span className="font-mono">{request.caseRef}</span></div>
                  <div><span className="text-gray-600">Requested by:</span> {request.requestedBy}</div>
                  <div><span className="text-gray-600">Route:</span> {request.from} → {request.to}</div>
                  <div><span className="text-gray-600">Equipment:</span> {request.needs.join(', ')}</div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Provider Details</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="text-gray-600">Provider:</span> {quote.providerName}</div>
                  <div><span className="text-gray-600">Price:</span> <span className="font-semibold">{fmtMoney(quote.price)}</span></div>
                  <div><span className="text-gray-600">ETA:</span> {fmtETA(quote.etaMinutes)}</div>
                  <div><span className="text-gray-600">Notes:</span> {quote.notes || 'None'}</div>
                </div>
              </div>
            </div>

            {/* Terms */}
            <div className="border-t pt-4">
              <h4 className="font-medium text-gray-900 mb-2">Terms & Conditions</h4>
              <div className="text-sm text-gray-600 space-y-1">
                <p>• Payment is due upon completion of transport service</p>
                <p>• Cancellation fees may apply within 2 hours of scheduled pickup</p>
                <p>• All medical equipment and staffing included as specified</p>
                <p>• 24/7 support available during transport</p>
                {quote.concierge && <p>• Full concierge service includes ground coordination</p>}
              </div>
            </div>

            {/* Print Area */}
            <div className="print-area print-header" data-ref={request.caseRef}>
              <div className="hidden print:block">
                <h2>SkyCareLink Medical Transport - Booking Confirmation</h2>
                <div className="mt-4">
                  <div><strong>Case Reference:</strong> {request.caseRef}</div>
                  <div><strong>Route:</strong> {request.from} → {request.to}</div>
                  <div><strong>Provider:</strong> {quote.providerName}</div>
                  <div><strong>Price:</strong> {fmtMoney(quote.price)}</div>
                  <div><strong>ETA:</strong> {fmtETA(quote.etaMinutes)}</div>
                </div>
                <div className="print-footer" data-ref={request.caseRef}></div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <button
              onClick={handlePrint}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-sm">
              Print Confirmation
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}