import { useEffect, useState } from 'react';
import { AuthForm } from './components/AuthForm';
import { ExactResultView } from './components/ExactResultView';
import { ParameterForm, type FormPreset } from './components/ParameterForm';
import { ResultView } from './components/ResultView';
import { RunHistory } from './components/RunHistory';
import { deleteRun, fetchRun, fetchStrata, runOptimization } from './services/api';
import { currentSession, onSessionChange, signOut, type Session } from './services/auth';
import type { Adjustment, EditableField, RunDetail, Stratum } from './types/diet';
import './App.css';

type Tela = { nome: 'nova' } | { nome: 'historico' } | { nome: 'detalhe'; id: string };

interface ResultadosProps {
  run: RunDetail;
  strata: Stratum[];
  onRepeat: () => void;
  onDelete: () => void;
}

function Resultados({ run, strata, onRepeat, onDelete }: ResultadosProps) {
  return (
    <div className="stack">
      <section className="method-block">
        <h2 className="method-label">Algoritmo genético</h2>
        <ResultView run={run} strata={strata} onRepeat={onRepeat} onDelete={onDelete} />
      </section>
      <section className="method-block">
        <h2 className="method-label">Método exato</h2>
        <ExactResultView key={run.id} exact={run.exact} />
      </section>
    </div>
  );
}

function presetDe(run: RunDetail): FormPreset {
  const campos: EditableField[] = ['min_kcal', 'max_kcal', 'cultural_min', 'cultural_max', 'price_per_kcal'];
  const adjustments: Adjustment[] = (run.inputs ?? [])
    .filter((g) => g.adjusted)
    .map((g) => {
      const a: Adjustment = { phdi_index: g.phdi_index };
      campos.forEach((c) => (a[c] = g[c]));
      return a;
    });
  return { name: run.name, uf: run.uf, faixa: run.faixa, params: run.params, adjustments };
}

export default function App() {
  const [session, setSession] = useState<Session | null>(currentSession());
  const [tela, setTela] = useState<Tela>({ nome: 'nova' });
  const [strata, setStrata] = useState<Stratum[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [resultado, setResultado] = useState<RunDetail | null>(null);
  const [detalhe, setDetalhe] = useState<RunDetail | null>(null);
  const [preset, setPreset] = useState<FormPreset | null>(null);

  useEffect(() => onSessionChange(setSession), []);

  useEffect(() => {
    if (!session) return;
    fetchStrata()
      .then(setStrata)
      .catch((e: Error) => setErro(e.message));
  }, [session]);

  useEffect(() => {
    if (tela.nome !== 'detalhe') return;
    setDetalhe(null);
    fetchRun(tela.id)
      .then(setDetalhe)
      .catch((e: Error) => setErro(e.message));
  }, [tela]);

  if (!session) return <AuthForm />;

  const ir = (t: Tela) => {
    setErro(null);
    setTela(t);
    window.scrollTo({ top: 0 });
  };

  const otimizar = async (p: FormPreset) => {
    setCarregando(true);
    setErro(null);
    setResultado(null);
    try {
      const r = await runOptimization(p);
      setResultado(r);
      setTimeout(() => document.getElementById('resultado')?.scrollIntoView({ behavior: 'smooth' }), 50);
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setCarregando(false);
    }
  };

  const repetir = (run: RunDetail) => {
    setPreset(presetDe(run));
    setResultado(null);
    ir({ nome: 'nova' });
  };

  const excluir = async (run: RunDetail) => {
    if (!window.confirm('Excluir esta execução do histórico?')) return;
    try {
      await deleteRun(run.id);
      if (resultado?.id === run.id) setResultado(null);
      ir({ nome: 'historico' });
    } catch (e) {
      setErro((e as Error).message);
    }
  };

  return (
    <div className="app">
      <header className="topbar">
        <strong className="brand">Otimizador de Dieta · AG</strong>
        <nav>
          <button className={tela.nome === 'nova' ? 'tab active' : 'tab'} onClick={() => ir({ nome: 'nova' })}>
            Nova execução
          </button>
          <button className={tela.nome !== 'nova' ? 'tab active' : 'tab'} onClick={() => ir({ nome: 'historico' })}>
            Histórico
          </button>
        </nav>
        <div className="user">
          <span className="muted">{session.displayName || session.email}</span>
          <button className="btn ghost small" onClick={() => signOut()}>Sair</button>
        </div>
      </header>

      <main className="container">
        {erro && <div className="alert error">{erro}</div>}

        {tela.nome === 'nova' && (
          <>
            <ParameterForm strata={strata} preset={preset} isLoading={carregando} onSubmit={otimizar} />
            {resultado && (
              <div id="resultado" className="result-block">
                <Resultados
                  run={resultado}
                  strata={strata}
                  onRepeat={() => repetir(resultado)}
                  onDelete={() => excluir(resultado)}
                />
              </div>
            )}
          </>
        )}

        {tela.nome === 'historico' && (
          <RunHistory strata={strata} onOpen={(id) => ir({ nome: 'detalhe', id })} onNew={() => ir({ nome: 'nova' })} />
        )}

        {tela.nome === 'detalhe' && (
          <>
            <button className="btn ghost small" onClick={() => ir({ nome: 'historico' })}>← Voltar ao histórico</button>
            {detalhe ? (
              <Resultados run={detalhe} strata={strata} onRepeat={() => repetir(detalhe)} onDelete={() => excluir(detalhe)} />
            ) : (
              !erro && <p className="muted">Carregando…</p>
            )}
          </>
        )}
      </main>
    </div>
  );
}
