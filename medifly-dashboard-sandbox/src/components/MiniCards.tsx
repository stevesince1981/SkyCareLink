import { RequestRow } from '../data/types';

type Props = {
  data: RequestRow[];
};

export default function MiniCards({ data }: Props) {
  const requestsToday = data.filter(r => {
    const today = new Date().toDateString();
    const updated = new Date(r.updatedAt).toDateString();
    return today === updated;
  }).length;

  const quotesSent = data.reduce((acc, r) => acc + r.quotes.length, 0);
  
  const acceptanceRate = data.length > 0 
    ? Math.round((data.filter(r => r.status === 'booked').length / data.length) * 100)
    : 0;

  const cards = [
    {
      title: 'Requests Today',
      value: requestsToday,
      change: '+12%',
      changeType: 'positive' as const
    },
    {
      title: 'Quotes Sent',
      value: quotesSent,
      change: '+8%',
      changeType: 'positive' as const
    },
    {
      title: 'Acceptance Rate',
      value: `${acceptanceRate}%`,
      change: '+5%',
      changeType: 'positive' as const
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      {cards.map((card, index) => (
        <div key={index} className="bg-white rounded-lg border p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">{card.title}</p>
              <p className="text-2xl font-bold text-gray-900">{card.value}</p>
            </div>
            <div className={`text-sm font-medium ${
              card.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
            }`}>
              {card.change}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}