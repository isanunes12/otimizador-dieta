/**
 * Login com Firebase Authentication (e-mail e senha) usando a API REST oficial do Firebase,
 * sem precisar do pacote `firebase`. O backend valida o ID token com o Firebase Admin SDK.
 *
 * Requer VITE_FIREBASE_API_KEY (Console do Firebase > Configurações do projeto > Chave de API da Web)
 * e o provedor "E-mail/senha" ativado em Authentication > Sign-in method.
 */

const API_KEY = import.meta.env.VITE_FIREBASE_API_KEY as string | undefined;
const IDENTITY = 'https://identitytoolkit.googleapis.com/v1/accounts';
const SECURE_TOKEN = 'https://securetoken.googleapis.com/v1/token';
const STORAGE_KEY = 'dieta-ag:session';

export interface Session {
  uid: string;
  email: string;
  displayName: string;
  idToken: string;
  refreshToken: string;
  /** epoch em ms */
  expiresAt: number;
}

type Listener = (s: Session | null) => void;
const listeners = new Set<Listener>();
let session: Session | null = load();
let motivoSaida: string | null = null;

function load(): Session | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null;
  }
}

function save(s: Session | null) {
  session = s;
  if (s) motivoSaida = null;
  try {
    if (s) localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* navegação privada: segue só em memória */
  }
  listeners.forEach((l) => l(s));
}

export function onSessionChange(l: Listener): () => void {
  listeners.add(l);
  return () => listeners.delete(l);
}

export function currentSession(): Session | null {
  return session;
}

export function isAuthConfigured(): boolean {
  return Boolean(API_KEY);
}

const MENSAGENS: Record<string, string> = {
  EMAIL_EXISTS: 'Já existe uma conta com este e-mail.',
  EMAIL_NOT_FOUND: 'E-mail ou senha incorretos.',
  INVALID_PASSWORD: 'E-mail ou senha incorretos.',
  INVALID_LOGIN_CREDENTIALS: 'E-mail ou senha incorretos.',
  INVALID_EMAIL: 'E-mail inválido.',
  USER_DISABLED: 'Esta conta foi desativada.',
  TOO_MANY_ATTEMPTS_TRY_LATER: 'Muitas tentativas. Tente de novo em alguns minutos.',
  OPERATION_NOT_ALLOWED: 'Login por e-mail/senha não está ativado no Firebase.',
  MISSING_PASSWORD: 'Informe a senha.',
};

async function post<T>(url: string, body: unknown): Promise<T> {
  if (!API_KEY) throw new Error('VITE_FIREBASE_API_KEY não configurada (veja o README).');
  const res = await fetch(`${url}?key=${API_KEY}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const codigo: string = data?.error?.message ?? 'ERRO';
    if (codigo.startsWith('WEAK_PASSWORD')) throw new Error('A senha precisa ter pelo menos 6 caracteres.');
    throw new Error(MENSAGENS[codigo.split(' ')[0]] ?? `Erro de autenticação (${codigo})`);
  }
  return data as T;
}

interface AuthResponse {
  localId: string;
  email: string;
  displayName?: string;
  idToken: string;
  refreshToken: string;
  expiresIn: string;
}

function fromAuth(r: AuthResponse, displayName?: string): Session {
  return {
    uid: r.localId,
    email: r.email,
    displayName: displayName ?? r.displayName ?? '',
    idToken: r.idToken,
    refreshToken: r.refreshToken,
    expiresAt: Date.now() + Number(r.expiresIn) * 1000,
  };
}

export async function signIn(email: string, password: string): Promise<void> {
  const r = await post<AuthResponse>(`${IDENTITY}:signInWithPassword`, { email, password, returnSecureToken: true });
  save(fromAuth(r));
}

export async function signUp(name: string, email: string, password: string): Promise<void> {
  const r = await post<AuthResponse>(`${IDENTITY}:signUp`, { email, password, returnSecureToken: true });
  if (name.trim()) {
    await post(`${IDENTITY}:update`, { idToken: r.idToken, displayName: name.trim(), returnSecureToken: false });
  }
  save(fromAuth(r, name.trim()));
}

export async function sendPasswordReset(email: string): Promise<void> {
  await post(`${IDENTITY}:sendOobCode`, { requestType: 'PASSWORD_RESET', email });
}

/** Sai da conta. `motivo` (opcional) é mostrado na tela de login, para o usuário saber por que saiu. */
export function signOut(motivo?: unknown): void {
  motivoSaida = typeof motivo === 'string' ? motivo : null;
  save(null);
}

/** Motivo da última saída automática (é apagado no próximo login). */
export function consumeSignOutReason(): string | null {
  return motivoSaida;
}

let refreshing: Promise<string> | null = null;

/** Devolve um ID token válido, renovando-o se faltar menos de 1 minuto para expirar. */
export async function getIdToken(): Promise<string> {
  const s = session;
  if (!s) throw new Error('Faça login para continuar');
  if (s.expiresAt - Date.now() > 60_000) return s.idToken;
  if (!refreshing) {
    refreshing = (async () => {
      const res = await fetch(`${SECURE_TOKEN}?key=${API_KEY}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ grant_type: 'refresh_token', refresh_token: s.refreshToken }),
      });
      if (!res.ok) {
        signOut('Sua sessão expirou. Entre novamente.');
        throw new Error('Sua sessão expirou. Entre novamente.');
      }
      const d = (await res.json()) as { id_token: string; refresh_token: string; expires_in: string };
      save({ ...s, idToken: d.id_token, refreshToken: d.refresh_token, expiresAt: Date.now() + Number(d.expires_in) * 1000 });
      return d.id_token;
    })().finally(() => {
      refreshing = null;
    });
  }
  return refreshing;
}
