import { ROTULO_TIPO, type TipoComponente } from '../utils';

export function SeloTipo({ tipo }: { tipo: TipoComponente }) {
  return <span className={`tipo-selo ${tipo}`}>{ROTULO_TIPO[tipo]}</span>;
}
