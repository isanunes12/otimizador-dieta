export interface Stratum {
  uf: number;
  uf_nome: string;
  faixa: number;
  faixa_nome: string;
  /** kcal atuais da população no PHDI (meta calórica padrão, a mesma do método exato) */
  target_calories?: number;
  /** custo atual da dieta da população, R$/dia (custo alvo padrão) */
  target_cost?: number;
}

/** Limites e preço de um componente do PHDI para o extrato escolhido */
export interface ComponentInput {
  phdi_index: number;
  name: string;
  name_pt: string;
  fixed: boolean;
  min_kcal: number;
  max_kcal: number;
  cultural_min: number;
  cultural_max: number;
  price_per_kcal: number;
  adjusted?: boolean;
}

export type EditableField = 'min_kcal' | 'max_kcal' | 'cultural_min' | 'cultural_max' | 'price_per_kcal';

export interface Adjustment extends Partial<Record<EditableField, number>> {
  phdi_index: number;
}

export interface GAParameters {
  generations: number;
  population_size: number;
  crossover_rate: number;
  mutation_rate: number;
  target_calories: number;
  target_cost: number;
  elite_ratio: number;
  tournament_ratio: number;
  tournament_upset: number;
  blx_alpha: number;
  blx_beta: number;
  /** vazio = semente aleatória escolhida pelo servidor */
  seed?: number | null;
}

export interface DietItem {
  phdi_index: number;
  group: string;
  group_pt: string;
  calories: number;
  other_vegetables_calories: number | null;
  percentage: number;
  phdi_score: number | null;
  cost: number;
  cultural_min: number;
  cultural_max: number;
  is_penalized: boolean;
  penalty: number;
}

export interface GenerationPoint {
  generation: number;
  fo: number;
  phdi: number;
  penalty_total: number;
  penalty_calories: number;
  penalty_cost: number;
  penalty_cultural: number;
  calories: number;
  cost: number;
}

export interface RunSummary {
  fitness: number;
  phdi_total: number;
  total_calories: number;
  total_cost: number;
  is_penalized: boolean;
  penalty_total: number;
  penalty_calories: number;
  penalty_cost: number;
  penalty_cultural: number;
  duration_s: number;
}

export interface RunListItem {
  id: string;
  name: string;
  uf: number;
  faixa: number;
  params: GAParameters & { seed: number };
  summary: RunSummary;
  created_at: string | null;
}

export interface ExactItem {
  key: string;
  group_pt: string;
  calories: number;
  percentage: number;
  /** null para cereais refinados, que não pontuam no PHDI */
  phdi_score: number | null;
  acceptability_score: number;
  acceptability_min: number;
  acceptability_max: number;
  gap_lower: number;
  gap_upper: number;
  cost: number;
}

export interface ExactSolution {
  phdi: number;
  acceptability: number;
  total_calories: number;
  total_cost: number;
  items: ExactItem[];
}

export type ExactResult =
  | { status: 'error'; message: string }
  | {
      status: 'ok';
      method: string;
      epsilon_points: number;
      rho: number;
      target_calories: number;
      target_cost: number;
      duration_s: number;
      skipped_points: number;
      /** ordenadas do maior para o menor PHDI */
      solutions: ExactSolution[];
    };

export interface RunDetail extends RunListItem {
  inputs: ComponentInput[];
  items: DietItem[];
  history: GenerationPoint[];
  warnings: string[];
  /** ausente em execuções antigas do histórico */
  exact?: ExactResult | null;
}
