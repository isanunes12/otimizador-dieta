import { useEffect, useState } from 'react';
import { fetchRuns } from '../services/api';
import type { RunListItem, Stratum } from '../types/diet';
import { brl, dataHora, fmt, rotuloExtrato } from '../utils';

interface Props {
  strata: Stratum[];
  onOpen: (id: string) => void;
  onNew: () => void;
}

export function RunHistory({ strata, onOpen, onNew }: Props) {
  const [runs, setRuns] = useState<RunListItem[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    fetchRuns()
      .then(setRuns)
      .catch((e: Error) => setErro(e.message));
  }, []);

  if (erro) return <div className="alert error">{erro}</div>;
  if (!runs) return <p className="muted">Carregando histórico…</p>;
  if (runs.length === 0)
    return (
      <div className="card empty">
        <p>Você ainda não executou nenhuma otimização.</p>
        <button className="btn primary" onClick={onNew}>Fazer a primeira</button>
      </div>
    );

  return (
    <section className="card">
      <h2>Histórico de execuções</h2>
      <div className="table-wrap">
        <table className="table clickable">
          <thead>
            <tr>
              <th>Data</th>
              <th>Nome</th>
              <th>Extrato</th>
              <th className="num">FO</th>
              <th className="num">PHDI</th>
              <th className="num">kcal</th>
              <th className="num">Custo</th>
              <th className="num">Ger. × pop.</th>
              <th>Penalizada</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.id} onClick={() => onOpen(r.id)} tabIndex={0} onKeyDown={(e) => e.key === 'Enter' && onOpen(r.id)}>
                <td>{dataHora(r.created_at)}</td>
                <td>{r.name || <span className="muted">sem nome</span>}</td>
                <td>{rotuloExtrato(r.uf, r.faixa, strata)}</td>
                <td className="num">{fmt(r.summary?.fitness)}</td>
                <td className="num">{fmt(r.summary?.phdi_total)}</td>
                <td className="num">{fmt(r.summary?.total_calories, 0)}</td>
                <td className="num">{brl(r.summary?.total_cost)}</td>
                <td className="num">{r.params?.generations} × {r.params?.population_size}</td>
                <td>{r.summary?.is_penalized ? <span className="tag warn">sim</span> : <span className="tag ok">não</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
