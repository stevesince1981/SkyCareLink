export const fmtMoney = (n: number) => `$${n.toLocaleString()}`;
export const fmtETA = (m: number) => `${Math.floor(m/60)}h ${m%60}m`;
export const fmtDate = (iso: string) => new Date(iso).toLocaleString();