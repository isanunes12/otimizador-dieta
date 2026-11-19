import { useMemo, useState, type MouseEvent } from 'react';
import { fmt } from '../utils';

export interface Series {
  label: string;
  color: string;
  values: number[];
  dashed?: boolean;
}

interface Props {
  title: string;
  series: Series[];
  xLabel?: string;
  height?: number;
}

const W = 640;
const PAD = { top: 16, right: 16, bottom: 34, left: 52 };

export function ticks(min: number, max: number, n = 5): number[] {
  if (min === max) return [min];
  const passoBruto = (max - min) / n;
  const mag = 10 ** Math.floor(Math.log10(passoBruto));
  const passo = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((p) => p >= passoBruto) ?? passoBruto;
  const out: number[] = [];
  for (let v = Math.ceil(min / passo) * passo; v <= max + 1e-9; v += passo) out.push(Number(v.toFixed(10)));
  return out;
}

/** Gráfico de linhas em SVG puro (sem dependências), com legenda e leitura ao passar o mouse. */
export function LineChart({ title, series, xLabel = 'Geração', height = 260 }: Props) {
  const [hover, setHover] = useState<number | null>(null);
  const n = Math.max(0, ...series.map((s) => s.values.length));
  const H = height;
  const iw = W - PAD.left - PAD.right;
  const ih = H - PAD.top - PAD.bottom;

  const { yMin, yMax } = useMemo(() => {
    const todos = series.flatMap((s) => s.values).filter((v) => Number.isFinite(v));
    let lo = Math.min(0, ...todos);
    let hi = Math.max(...todos, 1);
    if (hi === lo) hi = lo + 1;
    const folga = (hi - lo) * 0.05;
    return { yMin: lo === 0 ? 0 : lo - folga, yMax: hi + folga };
  }, [series]);

  if (n === 0) return null;

  const x = (i: number) => PAD.left + (n === 1 ? iw / 2 : (i / (n - 1)) * iw);
  const y = (v: number) => PAD.top + ih - ((v - yMin) / (yMax - yMin)) * ih;
  const yt = ticks(yMin, yMax);
  const xt = ticks(0, n - 1, 6).filter((v) => Number.isInteger(v));

  const onMove = (e: MouseEvent<SVGSVGElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - r.left) / r.width) * W;
    const i = Math.round(((px - PAD.left) / iw) * (n - 1));
    setHover(i >= 0 && i < n ? i : null);
  };

  return (
    <figure className="chart">
      <figcaption>{title}</figcaption>
      <div className="chart-legend">
        {series.map((s) => (
          <span key={s.label}>
            <i style={{ background: s.color }} /> {s.label}
            {hover !== null && <b> {fmt(s.values[hover])}</b>}
          </span>
        ))}
        {hover !== null && <span className="muted">{xLabel} {hover}</span>}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={title} onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
        {yt.map((v) => (
          <g key={v}>
            <line x1={PAD.left} x2={W - PAD.right} y1={y(v)} y2={y(v)} className="grid" />
            <text x={PAD.left - 8} y={y(v)} className="tick" textAnchor="end" dominantBaseline="middle">
              {fmt(v, Math.abs(yMax - yMin) < 5 ? 1 : 0)}
            </text>
          </g>
        ))}
        {xt.map((v) => (
          <text key={v} x={x(v)} y={H - PAD.bottom + 16} className="tick" textAnchor="middle">
            {v}
          </text>
        ))}
        <text x={PAD.left + iw / 2} y={H - 4} className="tick" textAnchor="middle">
          {xLabel}
        </text>
        {series.map((s) => (
          <polyline
            key={s.label}
            fill="none"
            stroke={s.color}
            strokeWidth={2}
            strokeDasharray={s.dashed ? '5 4' : undefined}
            strokeLinejoin="round"
            points={s.values.map((v, i) => `${x(i)},${y(v)}`).join(' ')}
          />
        ))}
        {hover !== null && (
          <g>
            <line x1={x(hover)} x2={x(hover)} y1={PAD.top} y2={PAD.top + ih} className="cursor" />
            {series.map((s) => (
              <circle key={s.label} cx={x(hover)} cy={y(s.values[hover])} r={3.5} fill={s.color} />
            ))}
          </g>
        )}
      </svg>
    </figure>
  );
}
