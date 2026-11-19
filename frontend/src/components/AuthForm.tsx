import { useState, type FormEvent } from 'react';
import { consumeSignOutReason, isAuthConfigured, sendPasswordReset, signIn, signUp } from '../services/auth';

type Modo = 'login' | 'cadastro' | 'recuperar';

export function AuthForm() {
  const [modo, setModo] = useState<Modo>('login');
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [mostrarSenha, setMostrarSenha] = useState(false);
  // Se o usuário foi deslogado automaticamente, mostra o motivo em vez de só voltar para o login
  const [erro, setErro] = useState<string | null>(() => consumeSignOutReason());
  const [aviso, setAviso] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  const enviar = async (e: FormEvent) => {
    e.preventDefault();
    setErro(null);
    setAviso(null);
    setCarregando(true);
    try {
      if (modo === 'login') await signIn(email, senha);
      else if (modo === 'cadastro') await signUp(nome, email, senha);
      else {
        await sendPasswordReset(email);
        setAviso('Se o e-mail estiver cadastrado, você vai receber um link para redefinir a senha.');
      }
    } catch (err) {
      setErro((err as Error).message);
    } finally {
      setCarregando(false);
    }
  };

  const trocar = (m: Modo) => {
    setModo(m);
    setMostrarSenha(false);
    setErro(null);
    setAviso(null);
  };

  return (
    <div className="auth">
      <div className="auth-intro">
        <h1>Otimizador de Dieta</h1>
        <p>
          Algoritmo genético para compor dietas com alta pontuação no PHDI, respeitando custo, meta calórica e
          aceitabilidade cultural de cada UF e faixa de renda.
        </p>
      </div>

      <form className="card auth-card" onSubmit={enviar}>
        <h2>{modo === 'login' ? 'Entrar' : modo === 'cadastro' ? 'Criar conta' : 'Recuperar senha'}</h2>

        {!isAuthConfigured() && (
          <div className="alert error">
            Falta configurar <code>FIREBASE_WEB_API_KEY</code> no arquivo <code>.env</code> (veja o README).
          </div>
        )}

        {modo === 'cadastro' && (
          <label>
            Nome
            <input value={nome} onChange={(e) => setNome(e.target.value)} autoComplete="name" required />
          </label>
        )}
        <label>
          E-mail
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
        </label>
        {modo !== 'recuperar' && (
          <label>
            Senha
            <div className="senha-campo">
              <input
                type={mostrarSenha ? 'text' : 'password'}
                aria-label="Senha"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                autoComplete={modo === 'login' ? 'current-password' : 'new-password'}
                minLength={6}
                required
              />
              <button
                type="button"
                className="senha-toggle"
                onClick={() => setMostrarSenha((v) => !v)}
                aria-label={mostrarSenha ? 'Ocultar senha' : 'Mostrar senha'}
                title={mostrarSenha ? 'Ocultar senha' : 'Mostrar senha'}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
                  <circle cx="12" cy="12" r="3" />
                  {mostrarSenha && <path d="M4 4l16 16" />}
                </svg>
              </button>
            </div>
          </label>
        )}

        {erro && <div className="alert error">{erro}</div>}
        {aviso && <div className="alert info">{aviso}</div>}

        <button className="btn primary" disabled={carregando}>
          {carregando ? 'Aguarde…' : modo === 'login' ? 'Entrar' : modo === 'cadastro' ? 'Criar conta' : 'Enviar link'}
        </button>

        <div className="auth-links">
          {modo !== 'login' && (
            <button type="button" className="link" onClick={() => trocar('login')}>
              Já tenho conta
            </button>
          )}
          {modo !== 'cadastro' && (
            <button type="button" className="link" onClick={() => trocar('cadastro')}>
              Criar conta
            </button>
          )}
          {modo === 'login' && (
            <button type="button" className="link" onClick={() => trocar('recuperar')}>
              Esqueci a senha
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
