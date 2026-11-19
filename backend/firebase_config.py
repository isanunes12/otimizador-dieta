import os

import firebase_admin
from firebase_admin import credentials, firestore

# A chave da conta de serviço NÃO deve ficar dentro de backend/ (ela iria parar na imagem Docker).
# Ordem de busca: variável GOOGLE_APPLICATION_CREDENTIALS -> ../secrets/serviceAccountKey.json
_dir = os.path.dirname(os.path.abspath(__file__))
_padrao = os.path.join(_dir, "..", "secrets", "serviceAccountKey.json")
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", _padrao)

if not os.path.exists(cred_path):
    raise RuntimeError(
        f"Chave do Firebase não encontrada em '{cred_path}'. "
        "Coloque o serviceAccountKey.json em secrets/ ou defina GOOGLE_APPLICATION_CREDENTIALS."
    )

if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(cred_path))

db = firestore.client()
