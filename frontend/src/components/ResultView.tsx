import type { RunDetail, Stratum } from '../types/diet';
import { baixarCsvDieta, baixarCsvHistorico, brl, dataHora, fmt, rotuloExtrato } from '../utils';
import { LineChart } from './LineChart';

interface Props {
  run: RunDetail;
  strata: Stratum[];
  onRepeat?: () => void;
  onDelete?: () => void;
}

const CORES = {
  fo: '#2563eb',
  phdi: '#16a34a',
  total: '#dc2626',
  calorias: '#f59e0b',
  custo: '#7c3aed',
  cultural: '#0891b2',
};

export function ResultView({ run, strata, onRepeat, onDelete }: Props) {
  const s = run.summary;
  const h = run.history;
  const p = run.params;
  const maxKcal = Math.max(...run.items.filter((i) => i.group !== 'DGV' && i.group !== 'REV').map((i) => Math.max(i.calories, i.cultural_max)), 1);

  return (
    <div className="stack">
      <div className="row-between">
        <div>
          <h2 className="title">{run.name || 'Execução sem nome'}</h2>
          <p className="muted">
            {rotuloExtrato(run.uf, run.faixa, strata)} · {dataHora(run.created_at)} · semente <code>{p.seed}</code> ·{' '}
            {fmt(s.duration_s, 1)} s
          </p>
        </div>
        <div className="actions">
          {onRepeat && (
            <button className="btn ghost" onClick={onRepeat}>
              Repetir com estes parâmetros
            </button>
          )}
          <button className="btn ghost" onClick={() => baixarCsvDieta(run)}>CSV da dieta</button>
          <button className="btn ghost" onClick={() => baixarCsvHistorico(run)}>CSV da convergência</button>
          {onDelete && (
            <button className="btn danger" onClick={onDelete}>
              Excluir
            </button>
          )}
        </div>
      </div>

      <div className="kpis">
        <div className="kpi">
          <span>Função objetivo</span>
          <strong>{fmt(s.fitness)}</strong>
        </div>
        <div className="kpi">
          <span>PHDI</span>
          <strong>{fmt(s.phdi_total)}</strong>
          <small className="muted">de 150</small>
        </div>
        <div className="kpi">
          <span>Calorias</span>
          <strong>{fmt(s.total_calories, 0)}</strong>
          <small className="muted">meta {fmt(p.target_calories, 0)} kcal</small>
        </div>
        <div className="kpi">
          <span>Custo diário</span>
          <strong>{brl(s.total_cost)}</strong>
          <small className="muted">alvo {brl(p.target_cost)}</small>
        </div>
        <div className={s.is_penalized ? 'kpi warn' : 'kpi ok'}>
          <span>Penalização</span>
          <strong>{fmt(s.penalty_total)}</strong>
          <small className="muted">
            kcal {fmt(s.penalty_calories)} · custo {fmt(s.penalty_cost)} · cultural {fmt(s.penalty_cultural)}
          </small>
        </div>
      </div>

      {run.warnings?.length > 0 && (
        <div className="alert warn">
          <strong>Atenção aos dados de entrada:</strong>
          <ul>
            {run.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid-charts">
        <section className="card">
          <LineChart
            title="Convergência: melhor indivíduo por geração"
            series={[
              { label: 'FO', color: CORES.fo, values: h.map((g) => g.fo) },
              { label: 'PHDI', color: CORES.phdi, values: h.map((g) => g.phdi), dashed: true },
            ]}
          />
        </section>
        <section className="card">
          <LineChart
            title="Penalizações do melhor indivíduo"
            series={[
              { label: 'Total', color: CORES.total, values: h.map((g) => g.penalty_total) },
              { label: 'Calorias', color: CORES.calorias, values: h.map((g) => g.penalty_calories) },
              { label: 'Custo', color: CORES.custo, values: h.map((g) => g.penalty_cost) },
              { label: 'Cultural', color: CORES.cultural, values: h.map((g) => g.penalty_cultural) },
            ]}
          />
        </section>
      </div>

      <section className="card">
        <h3>Composição da dieta</h3>
        <p className="hint">
          A barra mostra as kcal do componente; a faixa clara é o intervalo de aceitabilidade cultural do extrato.
          DGV e REV são proporções dos vegetais e não somam nas calorias totais.
        </p>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Componente</th>
                <th className="num">kcal</th>
                <th className="bar-col">Consumo × faixa cultural</th>
                <th className="num">% VCT</th>
                <th className="num">PHDI</th>
                <th className="num">Custo</th>
                <th className="num">Penalização</th>
              </tr>
            </thead>
            <tbody>
              {run.items.map((i) => {
                const proporcao = i.group === 'DGV' || i.group === 'REV';
                const lo = Math.min(i.cultural_min, i.cultural_max);
                const hi = Math.max(i.cultural_min, i.cultural_max);
                return (
                  <tr key={i.phdi_index} className={i.is_penalized ? 'penalized' : ''}>
                    <td>
                      {i.group_pt}
                      {i.other_vegetables_calories !== null && (
                        <small className="muted block">outros vegetais: {fmt(i.other_vegetables_calories, 1)} kcal</small>
                      )}
                    </td>
                    <td className="num">{fmt(i.calories, 1)}</td>
                    <td className="bar-col">
                      {!proporcao && (
                        <div className="bar">
                          <div className="bar-range" style={{ left: `${(lo / maxKcal) * 100}%`, width: `${Math.max(0.5, ((hi - lo) / maxKcal) * 100)}%` }} />
                          <div className="bar-fill" style={{ width: `${(i.calories / maxKcal) * 100}%` }} />
                        </div>
                      )}
                      {proporcao && <small className="muted">{fmt(i.percentage, 1)}% dos vegetais</small>}
                    </td>
                    <td className="num">{proporcao ? '—' : `${fmt(i.percentage, 1)}%`}</td>
                    <td className="num">{i.phdi_score === null ? '—' : fmt(i.phdi_score, 1)}</td>
                    <td className="num">{brl(i.cost)}</td>
                    <td className="num">{i.is_penalized ? fmt(i.penalty) : '—'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <details className="card">
        <summary>Parâmetros usados</summary>
        <dl className="params">
          <dt>Gerações</dt><dd>{p.generations}</dd>
          <dt>População</dt><dd>{p.population_size}</dd>
          <dt>Cruzamento</dt><dd>{p.crossover_rate}</dd>
          <dt>Mutação</dt><dd>{p.mutation_rate}</dd>
          <dt>Elites</dt><dd>{p.elite_ratio}</dd>
          <dt>Torneio</dt><dd>{p.tournament_ratio}</dd>
          <dt>Zebra</dt><dd>{p.tournament_upset}</dd>
          <dt>BLX α / β</dt><dd>{p.blx_alpha} / {p.blx_beta}</dd>
          <dt>Semente</dt><dd>{p.seed}</dd>
          <dt>Componentes ajustados</dt>
          <dd>{run.inputs?.filter((g) => g.adjusted).map((g) => g.name_pt).join(', ') || 'nenhum'}</dd>
        </dl>
      </details>
    </div>
  );
}
