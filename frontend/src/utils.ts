import type { RunDetail, Stratum } from './types/diet';

const nf = (casas: number) =>
  new Intl.NumberFormat('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas });

export const fmt = (v: number | null | undefined, casas = 2) =>
  v === null || v === undefined || Number.isNaN(v) ? '—' : nf(casas).format(v);

export const brl = (v: number | null | undefined) =>
  v === null || v === undefined ? '—' : new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v);

export const dataHora = (iso: string | null) =>
  iso ? new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }) : '—';

export function rotuloExtrato(uf: number, faixa: number, strata: Stratum[]): string {
  const s = strata.find((e) => e.uf === uf && e.faixa === faixa);
  return s ? `${s.uf_nome} · ${s.faixa_nome}` : `UF ${uf} · faixa ${faixa}`;
}

function csv(linhas: (string | number | boolean | null)[][]): string {
  const esc = (v: string | number | boolean | null) => {
    const s = v === null ? '' : String(v);
    return /[";\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  // ";" como separador abre direto no Excel em português
  return '﻿' + linhas.map((l) => l.map(esc).join(';')).join('\n');
}

function baixar(nome: string, conteudo: string) {
  const url = URL.createObjectURL(new Blob([conteudo], { type: 'text/csv;charset=utf-8' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = nome;
  a.click();
  URL.revokeObjectURL(url);
}

export function baixarCsvHistorico(run: RunDetail) {
  const cab = ['geracao', 'fo', 'phdi', 'penalizacao_total', 'penalizacao_calorias', 'penalizacao_custo', 'penalizacao_cultural', 'calorias', 'custo'];
  const linhas = run.history.map((h) => [h.generation, h.fo, h.phdi, h.penalty_total, h.penalty_calories, h.penalty_cost, h.penalty_cultural, h.calories, h.cost]);
  baixar(`execucao-${run.id}-convergencia.csv`, csv([cab, ...linhas]));
}

export function baixarCsvDieta(run: RunDetail) {
  const cab = ['indice', 'componente', 'kcal', 'perc_vct', 'pontuacao_phdi', 'custo', 'cultural_min', 'cultural_max', 'penalizado', 'penalizacao'];
  const linhas = run.items.map((i) => [i.phdi_index, i.group_pt, i.calories, i.percentage, i.phdi_score, i.cost, i.cultural_min, i.cultural_max, i.is_penalized, i.penalty]);
  baixar(`execucao-${run.id}-dieta.csv`, csv([cab, ...linhas]));
}

/** Tipo de cada componente no PHDI (Cacau et al., 2021). */
export type TipoComponente = 'adequacao' | 'otimo' | 'razao' | 'moderacao' | 'fora';

export const ROTULO_TIPO: Record<TipoComponente, string> = {
  adequacao: 'Adequação',
  otimo: 'Ótimo',
  razao: 'Razão',
  moderacao: 'Moderação',
  fora: 'Fora do PHDI',
};

/** Pelo índice do componente no AG (0–16). */
export function tipoPorIndice(i: number): TipoComponente {
  if (i <= 4) return 'adequacao';
  if (i <= 9) return 'otimo';
  if (i <= 11) return 'razao';
  if (i <= 15) return 'moderacao';
  return 'fora';
}

/** Pela chave do componente no método exato. */
const TIPO_POR_CHAVE: Record<string, TipoComponente> = {
  nozes_amendoim: 'adequacao', leguminosas: 'adequacao', frutas: 'adequacao', veg_totais: 'adequacao', cereais_integrais: 'adequacao',
  ovos: 'otimo', peixes: 'otimo', batatas_tuber: 'otimo', laticinios: 'otimo', oleos_insat: 'otimo',
  veg_verde: 'razao', veg_vermelho: 'razao',
  carne_vermelha: 'moderacao', aves_frango: 'moderacao', gord_animal: 'moderacao', acucares: 'moderacao',
};

export function tipoPorChave(chave: string): TipoComponente {
  return TIPO_POR_CHAVE[chave] ?? 'fora';
}
