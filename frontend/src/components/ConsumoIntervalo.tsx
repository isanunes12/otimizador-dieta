import { fmt } from '../utils';

// Folga para arredondamentos numéricos do otimizador (kcal)
const TOLERANCIA = 0.005;

type Situacao = 'abaixo' | 'dentro' | 'acima';

const ROTULOS: Record<Situacao, string> = {
  abaixo: 'Abaixo do intervalo',
  dentro: 'Dentro do intervalo',
  acima: 'Acima do intervalo',
};

function situacao(valor: number, min: number, max: number): Situacao {
  if (valor < min - TOLERANCIA) return 'abaixo';
  if (valor > max + TOLERANCIA) return 'acima';
  return 'dentro';
}

interface Props {
  valor: number;
  min: number;
  max: number;
  escala: number;
}

/** Faixa cinza = intervalo de aceitabilidade cultural; ponto colorido = consumo da dieta. */
export function ConsumoIntervalo({ valor, min, max, escala }: Props) {
  const lo = Math.min(min, max);
  const hi = Math.max(min, max);
  const s = situacao(valor, lo, hi);
  const pct = (v: number) => `${Math.min(100, Math.max(0, (v / escala) * 100))}%`;
  const titulo = `${ROTULOS[s]}: ${fmt(valor, 1)} kcal (intervalo ${fmt(lo, 1)}–${fmt(hi, 1)} kcal)`;

  return (
    <div className="bar" role="img" aria-label={titulo} title={titulo}>
      <div className="bar-range" style={{ left: pct(lo), width: `max(2px, ${((hi - lo) / escala) * 100}%)` }} />
      <span className={`bar-dot ${s}`} style={{ left: pct(valor) }} />
    </div>
  );
}

export function LegendaIntervalo() {
  return (
    <div className="bar-legend" aria-label="Legenda">
      <span><i className="bar-legend-range" /> Intervalo de aceitabilidade cultural</span>
      {(['abaixo', 'dentro', 'acima'] as Situacao[]).map((s) => (
        <span key={s}><i className={`bar-dot static ${s}`} /> {ROTULOS[s]}</span>
      ))}
    </div>
  );
}
