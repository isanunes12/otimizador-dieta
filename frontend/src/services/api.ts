import type { Adjustment, ComponentInput, GAParameters, RunDetail, RunListItem, Stratum } from '../types/diet';
import { getIdToken, signOut } from './auth';

const API_BASE = `${(import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:5000'}/api`;

async function request<T>(path: string, init: RequestInit = {}, auth = false): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body) headers.set('Content-Type', 'application/json');
  if (auth) headers.set('Authorization', `Bearer ${await getIdToken()}`);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch {
    throw new Error('Não foi possível falar com o servidor. O backend está rodando?');
  }
  if (res.status === 204) return undefined as T;

  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && auth) {
    const motivo = data?.error ?? 'O servidor recusou seu login. Entre novamente.';
    signOut(motivo);
    throw new Error(motivo);
  }
  if (!res.ok) throw new Error(data?.error ?? `Erro ${res.status}`);
  return data as T;
}

export const fetchStrata = () => request<Stratum[]>('/strata');

export const fetchStratum = (uf: number, faixa: number) => request<ComponentInput[]>(`/strata/${uf}/${faixa}`);

export const runOptimization = (payload: {
  name: string;
  uf: number;
  faixa: number;
  params: GAParameters;
  adjustments: Adjustment[];
}) => request<RunDetail>('/optimize', { method: 'POST', body: JSON.stringify(payload) }, true);

export const fetchRuns = () => request<RunListItem[]>('/runs', {}, true);

export const fetchRun = (id: string) => request<RunDetail>(`/runs/${encodeURIComponent(id)}`, {}, true);

export const deleteRun = (id: string) =>
  request<void>(`/runs/${encodeURIComponent(id)}`, { method: 'DELETE' }, true);
