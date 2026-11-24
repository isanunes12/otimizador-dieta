"""
Algoritmo Genético (mesmas classes do código original da orientadora).

As classes se importam pelo nome do arquivo (ex.: `from ClasseDieta import Dieta`).
Para manter esses arquivos idênticos ao original, esta pasta é adicionada ao
caminho de importação em vez de reescrever os imports.
"""
import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from ClasseAlgoritmoGenetico import AlgoritmoGenetico  # noqa: E402
from ClasseFerramentas import Ferramentas  # noqa: E402

__all__ = ["AlgoritmoGenetico", "Ferramentas"]
