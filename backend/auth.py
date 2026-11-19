"""
Autenticação: o frontend faz login no Firebase Authentication (e-mail e senha)
e envia o ID token no cabeçalho `Authorization: Bearer <token>`.
Aqui o token é verificado com o Firebase Admin SDK.
"""
import logging
from functools import wraps

from flask import g, jsonify, request
from firebase_admin import auth as fb_auth

log = logging.getLogger("dieta-ag.auth")

# O relógio do container Docker (principalmente no Windows/WSL) costuma ficar alguns
# segundos atrasado em relação aos servidores do Google. Sem essa tolerância, o token
# recém-emitido é recusado com "Token used too early" e o usuário é deslogado.
TOLERANCIA_RELOGIO_S = 60


def _motivo(e: Exception) -> str:
    texto = str(e)
    if "too early" in texto or "used before" in texto:
        return "O relógio do servidor está fora de sincronia com o Firebase. Reinicie o Docker Desktop e tente de novo."
    if isinstance(e, fb_auth.ExpiredIdTokenError):
        return "Sua sessão expirou. Entre novamente."
    if "audience" in texto:
        return "O token é de outro projeto Firebase: a chave da Web (.env) e a chave do servidor (secrets/) precisam ser do mesmo projeto."
    if isinstance(e, fb_auth.CertificateFetchError):
        return "O servidor não conseguiu baixar os certificados do Firebase (sem internet no container?)."
    return f"Token recusado pelo servidor: {type(e).__name__}"


def requer_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        cabecalho = request.headers.get("Authorization", "")
        if not cabecalho.startswith("Bearer "):
            return jsonify({"error": "Faça login para continuar"}), 401
        token = cabecalho.removeprefix("Bearer ").strip()
        try:
            decodificado = fb_auth.verify_id_token(token, clock_skew_seconds=TOLERANCIA_RELOGIO_S)
        except Exception as e:
            # Aparece no terminal do docker compose, para facilitar o diagnóstico
            log.warning("Falha ao validar token: %s: %s", type(e).__name__, e)
            return jsonify({"error": _motivo(e)}), 401
        g.uid = decodificado["uid"]
        g.email = decodificado.get("email")
        return func(*args, **kwargs)

    return wrapper
