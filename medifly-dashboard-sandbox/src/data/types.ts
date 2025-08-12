export type Quote = {
  providerName: string;
  price: number;
  etaMinutes: number;
  expiresAt: string;
  notes?: string;
  concierge?: boolean;
  incentive?: boolean;
};

export type RequestRow = {
  id: string;
  requestedBy: string;
  caseRef: string;
  from: string;
  to: string;
  windowStart: string;
  windowEnd: string;
  needs: string[];
  quotes: Quote[];
  status: 'draft'|'submitted'|'collecting_quotes'|'quotes_ready'|'booked'|'expired';
  updatedAt: string;
};

export type RoleKey = 'affiliate'|'provider'|'individual';