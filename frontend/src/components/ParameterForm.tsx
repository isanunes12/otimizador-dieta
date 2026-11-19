import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { fetchStratum } from '../services/api';
import type { Adjustment, ComponentInput, EditableField, GAParameters, Stratum } from '../types/diet';
import { fmt } from '../utils';

export const PARAMETROS_PADRAO: GAParameters = {
  generations: 100,
  population_size: 100,
  crossover_rate: 0.8,
  mutation_rate: 0.1,
  target_calories: 2000,
  target_cost: 20,
  elite_ratio: 0.01,
  tournament_ratio: 0.02,
  tournament_upset: 0.05,
  blx_alpha: 0.5,
  blx_beta: 0.25,
  seed: null,
};

export interface FormPreset {
  name: string;
  uf: number;
  faixa: number;
  params: GAParameters;
  adjustments: Adjustment[];
}

interface Props {
  strata: Stratum[];
  preset: FormPreset | null;
  isLoading: boolean;
  onSubmit: (p: FormPreset) => void;
}

const CAMPOS: { key: EditableField; label: string; casas: number }[] = [
  { key: 'min_kcal', label: 'Mín. kcal', casas: 1 },
  { key: 'max_kcal', label: 'Máx. kcal', casas: 1 },
  { key: 'cultural_min', label: 'Cult. mín.', casas: 1 },
  { key: 'cultural_max', label: 'Cult. máx.', casas: 1 },
  { key: 'price_per_kcal', label: 'R$/kcal', casas: 5 },
];

type NumParam = Exclude<keyof GAParameters, 'seed'>;

const BASICOS: { key: NumParam; label: string; step: number; min: number; max: number; ajuda?: string }[] = [
  { key: 'target_calories', label: 'Meta calórica (kcal)', step: 0.1, min: 500, max: 6000 },
  { key: 'target_cost', label: 'Custo alvo (R$/dia)', step: 0.01, min: 0.01, max: 10000 },
  { key: 'generations', label: 'Gerações', step: 1, min: 1, max: 2000 },
  { key: 'population_size', label: 'Tamanho da população', step: 1, min: 4, max: 2000 },
  { key: 'crossover_rate', label: 'Taxa de cruzamento', step: 0.01, min: 0, max: 1 },
  { key: 'mutation_rate', label: 'Taxa de mutação', step: 0.01, min: 0, max: 1 },
];

const AVANCADOS: { key: NumParam; label: string; step: number; min: number; max: number; ajuda: string }[] = [
  { key: 'elite_ratio', label: 'Proporção de elites', step: 0.01, min: 0, max: 0.5, ajuda: 'Fração da população que passa direto (mín. 1 indivíduo)' },
  { key: 'tournament_ratio', label: 'Participantes do torneio', step: 0.01, min: 0, max: 1, ajuda: 'Fração da população em cada torneio (mín. 2)' },
  { key: 'tournament_upset', label: 'Prob. de zebra no torneio', step: 0.01, min: 0, max: 1, ajuda: 'Chance do pior indivíduo vencer um confronto' },
  { key: 'blx_alpha', label: 'BLX α', step: 0.05, min: 0, max: 2, ajuda: 'Expansão do intervalo do lado do melhor pai' },
  { key: 'blx_beta', label: 'BLX β', step: 0.05, min: 0, max: 2, ajuda: 'Expansão do intervalo do lado do pior pai' },
];

export function ParameterForm({ strata, preset, isLoading, onSubmit }: Props) {
  const [nome, setNome] = useState('');
  const [extrato, setExtrato] = useState('99-99');
  const [params, setParams] = useState<GAParameters>(PARAMETROS_PADRAO);
  const [base, setBase] = useState<ComponentInput[]>([]);
  const [ajustes, setAjustes] = useState<Record<number, Partial<Record<EditableField, number>>>>({});
  const [erroBase, setErroBase] = useState<string | null>(null);

  // Preenche o formulário ao "repetir" uma execução do histórico
  useEffect(() => {
    if (!preset) return;
    setNome(preset.name ? `${preset.name} (cópia)` : '');
    setExtrato(`${preset.uf}-${preset.faixa}`);
    setParams({ ...PARAMETROS_PADRAO, ...preset.params });
    const a: Record<number, Partial<Record<EditableField, number>>> = {};
    preset.adjustments.forEach(({ phdi_index, ...resto }) => (a[phdi_index] = resto));
    setAjustes(a);
  }, [preset]);

  const [uf, faixa] = extrato.split('-').map(Number);

  // Metas padrão = consumo e custo atuais da população do extrato (como no método exato e na tabela da orientadora)
  const aplicaMetas = (chave: string) => {
    const s = strata.find((e) => `${e.uf}-${e.faixa}` === chave);
    if (s?.target_calories && s?.target_cost) {
      setParams((p) => ({ ...p, target_calories: s.target_calories!, target_cost: s.target_cost! }));
    }
  };

  // Na primeira carga (sem "repetir"), preenche as metas do extrato inicial
  const metasIniciais = useRef(false);
  useEffect(() => {
    if (metasIniciais.current || preset || strata.length === 0) return;
    metasIniciais.current = true;
    aplicaMetas(extrato);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [strata, preset]);

  useEffect(() => {
    let ativo = true;
    setErroBase(null);
    fetchStratum(uf, faixa)
      .then((g) => ativo && setBase(g))
      .catch((e: Error) => ativo && setErroBase(e.message));
    return () => {
      ativo = false;
    };
  }, [uf, faixa]);

  const porUf = useMemo(() => {
    const m = new Map<string, Stratum[]>();
    strata.forEach((s) => m.set(s.uf_nome, [...(m.get(s.uf_nome) ?? []), s]));
    return [...m.entries()];
  }, [strata]);

  const valor = (g: ComponentInput, k: EditableField) => ajustes[g.phdi_index]?.[k] ?? g[k];

  const editar = (idx: number, k: EditableField, texto: string, casas: number) => {
    setAjustes((prev) => {
      const linha = { ...prev[idx] };
      const original = base[idx]?.[k];
      const v = Number(texto.replace(',', '.'));
      // compara com o valor arredondado exibido, para não marcar como alterado só por sair do campo
      if (texto === '' || !Number.isFinite(v) || (original !== undefined && v === Number(original.toFixed(casas)))) delete linha[k];
      else linha[k] = v;
      const novo = { ...prev, [idx]: linha };
      if (Object.keys(linha).length === 0) delete novo[idx];
      return novo;
    });
  };

  const setNum = (k: NumParam, texto: string) => setParams((p) => ({ ...p, [k]: Number(texto) }));

  const avaliacoes = params.generations * params.population_size;

  const enviar = (e: FormEvent) => {
    e.preventDefault();
    const adjustments: Adjustment[] = Object.entries(ajustes).map(([idx, campos]) => ({ phdi_index: Number(idx), ...campos }));
    onSubmit({ name: nome, uf, faixa, params, adjustments });
  };

  return (
    <form className="stack" onSubmit={enviar}>
      <section className="card">
        <h2>1. Extrato da população</h2>
        <div className="grid-2">
          <label>
            UF e faixa de renda
            <select value={extrato} onChange={(e) => { setExtrato(e.target.value); setAjustes({}); aplicaMetas(e.target.value); }}>
              {porUf.map(([ufNome, lista]) => (
                <optgroup key={ufNome} label={ufNome}>
                  {lista.map((s) => (
                    <option key={`${s.uf}-${s.faixa}`} value={`${s.uf}-${s.faixa}`}>
                      {s.uf_nome} · {s.faixa_nome}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </label>
          <label>
            Nome da execução <span className="muted">(opcional)</span>
            <input value={nome} maxLength={80} onChange={(e) => setNome(e.target.value)} placeholder="Ex.: MG faixa 2, custo R$ 15" />
          </label>
        </div>
      </section>

      <section className="card">
        <h2>2. Metas e parâmetros do AG</h2>
        <p className="hint">
          A meta calórica e o custo alvo começam com o consumo e o custo atuais da população do extrato (os mesmos usados
          pelo método exato). Você pode alterá-los.
        </p>
        <div className="grid-3">
          {BASICOS.map((c) => (
            <label key={c.key}>
              {c.label}
              <input type="number" step={c.step} min={c.min} max={c.max} value={params[c.key]} onChange={(e) => setNum(c.key, e.target.value)} required />
            </label>
          ))}
          <label>
            Semente aleatória <span className="muted">(vazio = aleatória)</span>
            <input
              type="number"
              min={0}
              step={1}
              value={params.seed ?? ''}
              onChange={(e) => setParams((p) => ({ ...p, seed: e.target.value === '' ? null : Number(e.target.value) }))}
              placeholder="ex.: 42"
            />
          </label>
        </div>
        <p className={avaliacoes > 500_000 ? 'hint error-text' : 'hint'}>
          {fmt(avaliacoes, 0)} avaliações {avaliacoes > 500_000 ? '— o limite é 500.000' : avaliacoes > 100_000 ? '— pode levar alguns segundos' : ''}
        </p>

        <details>
          <summary>Parâmetros avançados</summary>
          <div className="grid-3">
            {AVANCADOS.map((c) => (
              <label key={c.key} title={c.ajuda}>
                {c.label}
                <input type="number" step={c.step} min={c.min} max={c.max} value={params[c.key]} onChange={(e) => setNum(c.key, e.target.value)} required />
                <small className="muted">{c.ajuda}</small>
              </label>
            ))}
          </div>
        </details>
      </section>

      <section className="card">
        <div className="row-between">
          <h2>3. Componentes do PHDI</h2>
          {Object.keys(ajustes).length > 0 && (
            <button type="button" className="btn ghost" onClick={() => setAjustes({})}>
              Restaurar valores do extrato
            </button>
          )}
        </div>
        <p className="hint">
          Valores do banco INA para o extrato escolhido. Edite uma célula para testar outro cenário; células alteradas
          ficam destacadas.
        </p>
        {erroBase && <div className="alert error">{erroBase}</div>}
        <div className="table-wrap">
          <table className="table compact">
            <thead>
              <tr>
                <th>#</th>
                <th>Componente</th>
                {CAMPOS.map((c) => (
                  <th key={c.key} className="num">{c.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {base.map((g) => {
                const invertido = valor(g, 'cultural_min') > valor(g, 'cultural_max');
                return (
                  <tr key={g.phdi_index}>
                    <td className="muted">{g.phdi_index}</td>
                    <td>
                      {g.name_pt}
                      {g.fixed && <span className="tag">fixo</span>}
                      {invertido && <span className="tag warn" title="Mínimo cultural maior que o máximo">⚠</span>}
                    </td>
                    {CAMPOS.map((c) => {
                      const alterado = ajustes[g.phdi_index]?.[c.key] !== undefined;
                      return (
                        <td key={c.key} className="num">
                          <input
                            className={alterado ? 'cell changed' : 'cell'}
                            type="number"
                            step="any"
                            min={0}
                            aria-label={`${c.label} — ${g.name_pt}`}
                            defaultValue={Number(valor(g, c.key).toFixed(c.casas))}
                            key={`${extrato}-${alterado}-${valor(g, c.key)}`}
                            onBlur={(e) => editar(g.phdi_index, c.key, e.target.value, c.casas)}
                          />
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <button type="submit" className="btn primary big" disabled={isLoading || avaliacoes > 500_000 || base.length === 0}>
        {isLoading ? 'Executando o algoritmo genético e o método exato…' : 'Otimizar dieta'}
      </button>
    </form>
  );
}
