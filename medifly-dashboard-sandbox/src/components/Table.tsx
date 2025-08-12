import { Quote, RequestRow } from '../data/types';
import { fmtMoney, fmtETA, fmtDate } from '../utils/format';

type Props = {
  rows: RequestRow[];
  simplified?: boolean;
  onAccept: (row: RequestRow, q: Quote)=>void;
  onView?: (row: RequestRow)=>void;
  showIncentive?: boolean;
};

export default function Table({ rows, simplified, onAccept, onView, showIncentive }: Props){
  return (
    <div className="table-container">
      <table className="w-full text-sm">
        <thead className="text-left text-gray-500 bg-gray-50 sticky top-0">
          <tr>
            <th className="py-3 px-4 font-medium">Requested By</th>
            <th className="py-3 px-4 font-medium">Case Ref</th>
            <th className="py-3 px-4 font-medium">From → To</th>
            <th className="py-3 px-4 font-medium">{simplified ? 'ETA' : 'Window'}</th>
            <th className="py-3 px-4 font-medium">Top Quotes</th>
            <th className="py-3 px-4 font-medium actions no-print">Actions</th>
          </tr>
        </thead>
        <tbody>
        {rows.map(row=>{
          const concierge = row.quotes.find(q=>q.concierge);
          const others = row.quotes.filter(q=>!q.concierge);
          const quotesOrdered = concierge ? [concierge, ...others] : row.quotes;

          return (
            <tr key={row.id} className="border-t hover:bg-gray-50">
              <td className="py-3 px-4">{row.requestedBy}</td>
              <td className="py-3 px-4 font-mono text-xs">{row.caseRef}</td>
              <td className="py-3 px-4">{row.from} → {row.to}</td>
              <td className="py-3 px-4">
                { simplified ? fmtETA(quotesOrdered[0].etaMinutes) 
                              : `${fmtDate(row.windowStart)} — ${fmtDate(row.windowEnd)}` }
              </td>
              <td className="py-3 px-4">
                <div className="flex flex-col gap-2">
                  {quotesOrdered.slice(0, simplified?3:4).map((q,i)=>(
                    <div key={i} className="flex items-center gap-3">
                      <span className={`px-2 py-1 rounded-md text-xs font-medium ${
                        q.concierge
                          ? 'border-2 border-blue-600 text-blue-700 bg-blue-50 quote-badge'
                          : 'bg-gray-100 text-gray-700'
                      }`}>
                        {q.providerName}
                        {q.concierge && <span className="ml-1 text-xs">★</span>}
                      </span>
                      <span className="text-gray-600">{fmtETA(q.etaMinutes)}</span>
                      <span className="font-semibold">{fmtMoney(q.price)}</span>
                      {q.concierge && showIncentive && (
                        <span className="text-xs text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                          Incentive applies
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </td>
              <td className="py-3 px-4 no-print">
                <div className="flex gap-2">
                  {!simplified && onView && (
                    <button 
                      className="px-3 py-1 border border-gray-300 rounded-md hover:bg-gray-50 text-sm" 
                      onClick={()=>onView(row)} 
                      data-test="btn-view">
                      View
                    </button>
                  )}
                  <button 
                    className={`px-3 py-1 rounded-md text-sm font-medium text-white transition-colors ${
                      simplified 
                        ? 'bg-blue-600 hover:bg-blue-700 px-6 py-2' 
                        : 'bg-blue-600 hover:bg-blue-700'
                    }`}
                    onClick={()=>onAccept(row, quotesOrdered[0])}
                    data-test="btn-accept">
                    Accept
                  </button>
                  <button 
                    className="px-3 py-1 border border-gray-300 rounded-md hover:bg-gray-50 text-sm" 
                    onClick={()=>window.print()} 
                    data-test="btn-print">
                    Print
                  </button>
                </div>
              </td>
            </tr>
          );
        })}
        </tbody>
      </table>
    </div>
  );
}