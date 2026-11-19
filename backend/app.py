import logging
import os

from flask import Flask, g, jsonify, request
from flask_cors import CORS
from firebase_admin import firestore

from auth import requer_login
from estratos import VERSAO_LIMITES, grupos_do_extrato, lista_extratos
from exact_engine import executa_exato
from firebase_config import db
from ga_engine import ErroValidacao, aplica_ajustes, executa_ag, valida_parametros

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024  # 256 KB por requisição

# Só o frontend configurado pode chamar a API (por padrão, o Vite em localhost:5173)
origens = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
CORS(app, origins=origens)

log = logging.getLogger("dieta-ag")
logging.basicConfig(level=logging.INFO)


def _runs_ref(uid: str):
    return db.collection("users").document(uid).collection("runs")


@app.errorhandler(ErroValidacao)
def _erro_validacao(e):
    return jsonify({"error": str(e)}), 400


@app.errorhandler(Exception)
def _erro_interno(e):
    # Registra o erro completo no log, mas não expõe detalhes internos para o cliente
    log.exception("Erro não tratado")
    status = getattr(e, "code", 500)
    if isinstance(status, int) and 400 <= status < 500:
        return jsonify({"error": getattr(e, "description", "Requisição inválida")}), status
    return jsonify({"error": "Erro interno no servidor"}), 500


@app.get("/api/health")
def health():
    return jsonify({"ok": True})


@app.get("/api/strata")
def get_strata():
    """Lista os extratos disponíveis (UF x faixa de renda)."""
    return jsonify(lista_extratos())


@app.get("/api/strata/<int:uf>/<int:faixa>")
def get_stratum(uf: int, faixa: int):
    """Limites e preços dos 17 componentes para um extrato."""
    try:
        return jsonify(grupos_do_extrato(uf, faixa))
    except KeyError as e:
        return jsonify({"error": str(e)}), 404


@app.post("/api/optimize")
@requer_login
def optimize():
    """Executa o AG e o método exato para um extrato, salva no histórico do usuário e devolve tudo."""
    data = request.get_json(silent=True) or {}
    try:
        uf, faixa = int(data.get("uf")), int(data.get("faixa"))
    except (TypeError, ValueError):
        raise ErroValidacao("Informe UF e faixa de renda")
    try:
        grupos_base = grupos_do_extrato(uf, faixa)
    except KeyError as e:
        raise ErroValidacao(str(e))

    params = valida_parametros(data.get("params"))
    grupos = aplica_ajustes(grupos_base, data.get("adjustments"))
    nome = str(data.get("name") or "").strip()[:80]

    resultado = executa_ag(params, grupos)
    exato = executa_exato(uf, faixa)

    doc = {
        "name": nome,
        "uf": uf,
        "faixa": faixa,
        "params": params,
        "inputs": grupos,
        **resultado,
        "exact": exato,
        "limits_version": VERSAO_LIMITES,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    ref = _runs_ref(g.uid).document()
    ref.set(doc)

    resposta = {k: v for k, v in doc.items() if k != "created_at"}
    resposta["id"] = ref.id
    return jsonify(resposta), 201


def _serializa(snap, completo: bool):
    d = snap.to_dict()
    criado = d.get("created_at")
    base = {
        "id": snap.id,
        "name": d.get("name", ""),
        "uf": d.get("uf"),
        "faixa": d.get("faixa"),
        "params": d.get("params"),
        "summary": d.get("summary"),
        "created_at": criado.isoformat() if criado else None,
    }
    if completo:
        base.update({
            "inputs": d.get("inputs"),
            "items": d.get("items"),
            "history": d.get("history"),
            "warnings": d.get("warnings", []),
            "exact": d.get("exact"),
        })
    return base


@app.get("/api/runs")
@requer_login
def list_runs():
    """Histórico de execuções do usuário logado (mais recentes primeiro)."""
    campos = ["name", "uf", "faixa", "params", "summary", "created_at"]
    consulta = (
        _runs_ref(g.uid)
        .select(campos)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(100)
    )
    return jsonify([_serializa(s, completo=False) for s in consulta.stream()])


@app.get("/api/runs/<run_id>")
@requer_login
def get_run(run_id: str):
    snap = _runs_ref(g.uid).document(run_id).get()
    if not snap.exists:
        return jsonify({"error": "Execução não encontrada"}), 404
    return jsonify(_serializa(snap, completo=True))


@app.delete("/api/runs/<run_id>")
@requer_login
def delete_run(run_id: str):
    ref = _runs_ref(g.uid).document(run_id)
    if not ref.get().exists:
        return jsonify({"error": "Execução não encontrada"}), 404
    ref.delete()
    return "", 204


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug)
