import { RequestRow } from './types';

const base: RequestRow = {
  id: 'REQ-1201',
  requestedBy: 'Maria Gomez',
  caseRef: 'ER-2025-0145',
  from: 'Orlando, FL',
  to: 'New York, NY',
  windowStart: '2025-08-12T15:00:00Z',
  windowEnd: '2025-08-12T19:00:00Z',
  needs: ['vent','monitor'],
  quotes: [
    { providerName: 'Concierge (SkyCareLink)', price: 12000, etaMinutes: 180, expiresAt: '2025-08-12T20:00:00Z', notes: 'All-inclusive concierge', concierge: true, incentive: true },
    { providerName: 'DP-Air', price: 11500, etaMinutes: 165, expiresAt: '2025-08-12T19:30:00Z' },
    { providerName: 'Sky Rescue', price: 13000, etaMinutes: 210, expiresAt: '2025-08-12T21:00:00Z' },
    { providerName: 'HealthLink', price: 14500, etaMinutes: 195, expiresAt: '2025-08-12T20:30:00Z' }
  ],
  status: 'quotes_ready',
  updatedAt: '2025-08-12T16:00:00Z'
};

function clone(id: number, overrides: Partial<RequestRow> = {}): RequestRow {
  return { ...base, id: `REQ-${1200+id}`, caseRef: `ER-2025-${1400+id}`, ...overrides };
}

// Generate more varied data
const locations = [
  ['Miami, FL', 'Atlanta, GA'],
  ['Los Angeles, CA', 'Phoenix, AZ'],
  ['Chicago, IL', 'Detroit, MI'],
  ['Houston, TX', 'Dallas, TX'],
  ['Boston, MA', 'Portland, ME'],
  ['Seattle, WA', 'Denver, CO']
];

const names = [
  'Alex Chen', 'Jamie Patel', 'Sarah Wilson', 'Michael Torres', 'Lisa Johnson',
  'David Kim', 'Emma Rodriguez', 'Ryan O\'Connor', 'Nina Sharma', 'Carlos Martinez'
];

const equipment = [
  ['vent', 'monitor'], ['ecmo'], ['vent'], ['monitor', 'pump'], ['defibrillator'],
  ['vent', 'ecmo'], ['monitor'], ['pump'], ['vent', 'monitor', 'ecmo']
];

const statuses = ['quotes_ready', 'collecting_quotes', 'submitted', 'booked'] as const;

function generateRequest(id: number, role: 'provider' | 'affiliate' | 'individual'): RequestRow {
  const locationPair = locations[id % locations.length];
  const name = role === 'affiliate' ? (id % 2 ? 'Client Lead' : 'Referral Office') :
                role === 'individual' ? (id % 2 ? 'Family Contact' : 'Patient Rep') :
                names[id % names.length];
  
  const basePrice = 10000 + (id % 5) * 2000;
  const equipment_set = equipment[id % equipment.length];
  
  return clone(id, {
    requestedBy: name,
    from: locationPair[0],
    to: locationPair[1],
    needs: equipment_set,
    status: statuses[id % statuses.length],
    quotes: [
      { 
        providerName: 'Concierge (SkyCareLink)', 
        price: basePrice + 1000, 
        etaMinutes: 150 + (id % 4) * 30, 
        expiresAt: '2025-08-12T20:00:00Z', 
        notes: 'All-inclusive concierge', 
        concierge: true, 
        incentive: true 
      },
      { 
        providerName: 'DP-Air', 
        price: basePrice - 500, 
        etaMinutes: 140 + (id % 3) * 25, 
        expiresAt: '2025-08-12T19:30:00Z' 
      },
      { 
        providerName: 'Sky Rescue', 
        price: basePrice + 2000, 
        etaMinutes: 180 + (id % 5) * 20, 
        expiresAt: '2025-08-12T21:00:00Z' 
      },
      { 
        providerName: 'HealthLink', 
        price: basePrice + 3500, 
        etaMinutes: 160 + (id % 4) * 35, 
        expiresAt: '2025-08-12T20:30:00Z' 
      }
    ]
  });
}

export const data = {
  provider: Array.from({length: 25}, (_, i) => generateRequest(i, 'provider')),
  affiliate: Array.from({length: 12}, (_, i) => generateRequest(i, 'affiliate')),
  individual: Array.from({length: 6}, (_, i) => generateRequest(i, 'individual'))
};