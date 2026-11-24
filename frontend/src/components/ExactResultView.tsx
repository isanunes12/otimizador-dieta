import { useState } from 'react';
import { ConsumoIntervalo, LegendaIntervalo } from './ConsumoIntervalo';
import type { ExactResult, ExactSolution } from '../types/diet';
import { brl, fmt, tipoPorChave } from '../utils';
import { SeloTipo } from './TipoComponente';
import { ticks } from './LineChart';

const W = 640;
const H = 320;
const PAD = { top: 16, right: 20, bottom: 40, left: 56 };
const COR_PONTO = '#16a34a';
const COR_SELECIONADO = '#2563eb';

function dominio(valores: number[]): [number, number] {
  const lo = Math.min(...valores);
  const hi = Math.max(...valores);
  const folga = hi === lo ? 1 : (hi - lo) * 0.08;
  return [lo - folga, hi + folga];
}

function FronteiraPareto({ solucoes, selecionada, onSelect }: { solucoes: ExactSolution[]; selecionada: number; onSelect: (i: number) => void }) {
  const [xMin, xMax] = dominio(solucoes.map((s) => s.phdi));
  const [yMin, yMax] = dominio(solucoes.map((s) => s.acceptability));
  const iw = W - PAD.left - PAD.right;
  const ih = H - PAD.top - PAD.bottom;
  const x = (v: number) => PAD.left + ((v - xMin) / (xMax - xMin)) * iw;
  const y = (v: number) => PAD.top + ih - ((v - yMin) / (yMax - yMin)) * ih;
  const casas = (a: number, b: number) => (Math.abs(b - a) < 5 ? 1 : 0);

  return (
    <figure className="chart">
      <figcaption>Fronteira de Pareto</figcaption>
      <div className="chart-legend">
        <span className="muted">Clique em um ponto para ver a dieta correspondente.</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Fronteira de Pareto: PHDI por aceitabilidade cultural">
        {ticks(yMin, yMax).map((v) => (
          <g key={v}>
            <line x1={PAD.left} x2={W - PAD.right} y1={y(v)} y2={y(v)} className="grid" />
            <text x={PAD.left - 8} y={y(v)} className="tick" textAnchor="end" dominantBaseline="middle">
              {fmt(v, casas(yMin, yMax))}
            </text>
          </g>
        ))}
        {ticks(xMin, xMax).map((v) => (
          <text key={v} x={x(v)} y={H - PAD.bottom + 16} className="tick" textAnchor="middle">
            {fmt(v, casas(xMin, xMax))}
          </text>
        ))}
        <text x={PAD.left + iw / 2} y={H - 6} className="tick" textAnchor="middle">PHDI</text>
        <text transform={`translate(13 ${PAD.top + ih / 2}) rotate(-90)`} className="tick" textAnchor="middle">Aceitabilidade cultural</text>
        <polyline fill="none" stroke={COR_PONTO} strokeWidth={1.5} points={solucoes.map((s) => `${x(s.phdi)},${y(s.acceptability)}`).join(' ')} />
        {solucoes.map((s, i) => (
          <g key={i} className="pareto-point" onClick={() => onSelect(i)}>
            <title>{`Solução ${i + 1}: PHDI ${fmt(s.phdi)} · aceitabilidade ${fmt(s.acceptability)}`}</title>
            <circle cx={x(s.phdi)} cy={y(s.acceptability)} r={11} fill="transparent" />
            <circle cx={x(s.phdi)} cy={y(s.acceptability)} r={i === selecionada ? 6.5 : 4} fill={i === selecionada ? COR_SELECIONADO : COR_PONTO} />
          </g>
        ))}
      </svg>
    </figure>
  );
}

export function ExactResultView({ exact }: { exact?: ExactResult | null }) {
  const [selecionada, setSelecionada] = useState(0);

  if (!exact) {
    return <div className="alert info">Esta execução foi feita antes da inclusão do método exato. Rode novamente para ver este resultado.</div>;
  }
  if (exact.status === 'error') {
    return <div className="alert error">{exact.message}</div>;
  }

  const solucoes = exact.solutions;
  const sol = solucoes[selecionada];
  const maxKcal = Math.max(...sol.items.map((i) => Math.max(i.calories, i.acceptability_max)), 1);

  return (
    <div className="stack">
      <p className="muted">
        ε-restrição · {solucoes.length} soluções na fronteira · {fmt(exact.duration_s, 1)} s. Este método usa as metas do próprio extrato
        ({fmt(exact.target_calories, 0)} kcal e até {brl(exact.target_cost)} por dia), limites culturais próprios e 14 componentes no PHDI,
        por isso os valores não são diretamente comparáveis aos do algoritmo genético.
      </p>

      {exact.skipped_points > 0 && (
        <div className="alert warn">{exact.skipped_points} ponto(s) da fronteira ficaram de fora porque o solver não provou uma solução ótima.</div>
      )}

      <div className="kpis">
        <div className="kpi">
          <span>PHDI</span>
          <strong>{fmt(sol.phdi)}</strong>
          <small className="muted">de 140</small>
        </div>
        <div className="kpi">
          <span>Aceitabilidade cultural</span>
          <strong>{fmt(sol.acceptability)}</strong>
          <small className="muted">de 150</small>
        </div>
        <div className="kpi">
          <span>Calorias</span>
          <strong>{fmt(sol.total_calories, 0)}</strong>
          <small className="muted">meta {fmt(exact.target_calories, 0)} kcal</small>
        </div>
        <div className="kpi">
          <span>Custo diário</span>
          <strong>{brl(sol.total_cost)}</strong>
          <small className="muted">limite {brl(exact.target_cost)}</small>
        </div>
      </div>

      <div className="grid-charts">
        <section className="card">
          <FronteiraPareto solucoes={solucoes} selecionada={selecionada} onSelect={setSelecionada} />
        </section>
        <section className="card">
          <h3>Soluções</h3>
          <div className="table-wrap exact-solutions">
            <table className="table clickable">
              <thead>
                <tr>
                  <th>#</th>
                  <th className="num">PHDI</th>
                  <th className="num">Aceitabilidade</th>
                  <th className="num">Custo</th>
                </tr>
              </thead>
              <tbody>
                {solucoes.map((s, i) => (
                  <tr
                    key={i}
                    className={i === selecionada ? 'selected' : ''}
                    aria-selected={i === selecionada}
                    tabIndex={0}
                    onClick={() => setSelecionada(i)}
                    onKeyDown={(e) => e.key === 'Enter' && setSelecionada(i)}
                  >
                    <td>{i + 1}</td>
                    <td className="num">{fmt(s.phdi)}</td>
                    <td className="num">{fmt(s.acceptability)}</td>
                    <td className="num">{brl(s.total_cost)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <section className="card">
        <h3>Composição da dieta: solução {selecionada + 1} de {solucoes.length}</h3>
        <p className="hint">
          O ponto mostra as kcal do componente e a faixa cinza é o intervalo de aceitabilidade cultural. A coluna Desvio indica quantas kcal
          ficaram abaixo (−) ou acima (+) desse intervalo.
        </p>
        <LegendaIntervalo />
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Componente</th>
                <th className="num">kcal</th>
                <th className="bar-col">Consumo × intervalo cultural</th>
                <th className="num">% VCT</th>
                <th className="num">PHDI</th>
                <th className="num">Aceitab.</th>
                <th className="num">Custo</th>
                <th className="num">Desvio</th>
              </tr>
            </thead>
            <tbody>
              {sol.items.map((i) => {
                const desvio = i.gap_lower > 0.005 ? `−${fmt(i.gap_lower, 1)}` : i.gap_upper > 0.005 ? `+${fmt(i.gap_upper, 1)}` : null;
                return (
                  <tr key={i.key} className={desvio ? 'penalized' : ''}>
                    <td><SeloTipo tipo={tipoPorChave(i.key)} /></td>
                    <td>{i.group_pt}</td>
                    <td className="num">{fmt(i.calories, 1)}</td>
                    <td className="bar-col">
                      <ConsumoIntervalo valor={i.calories} min={i.acceptability_min} max={i.acceptability_max} escala={maxKcal} />
                    </td>
                    <td className="num">{fmt(i.percentage, 1)}%</td>
                    <td className="num">{i.phdi_score === null ? '—' : fmt(i.phdi_score, 1)}</td>
                    <td className="num">{fmt(i.acceptability_score, 1)}</td>
                    <td className="num">{brl(i.cost)}</td>
                    <td className="num">{desvio ?? '—'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
