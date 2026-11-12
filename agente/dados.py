"""Carrega os dados fictícios (CRM, mensagens e base de conhecimento)."""
from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"


def carregar_clientes(caminho: Path = PASTA_DADOS / "clientes.csv") -> dict[str, dict]:
    with open(caminho, encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    for linha in linhas:
        for campo in ("licencas_m365", "licencas_copilot", "adocao_copilot_pct", "nps"):
            linha[campo] = int(linha[campo])
    return {linha["cliente_id"]: linha for linha in linhas}


def carregar_mensagens(caminho: Path = PASTA_DADOS / "mensagens.csv") -> list[dict]:
    with open(caminho, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def carregar_base(caminho: Path = PASTA_DADOS / "base_conhecimento.json") -> list[dict]:
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def dias_para_renovacao(cliente: dict, hoje: date) -> int:
    return (date.fromisoformat(cliente["renovacao"]) - hoje).days


def contexto_cliente(cliente: dict, hoje: date) -> dict:
    """Ficha do cliente que o agente recebe ao consultar o CRM."""
    return {**cliente, "dias_para_renovacao": dias_para_renovacao(cliente, hoje)}


def buscar_na_base(texto: str, base: list[dict], limite: int = 2) -> list[dict]:
    """Busca simples por palavras-chave: devolve os artigos mais parecidos."""
    texto = texto.lower()
    pontuados = []
    for artigo in base:
        pontos = sum(1 for p in artigo["palavras"] if p in texto)
        if pontos:
            pontuados.append((pontos, artigo))
    pontuados.sort(key=lambda par: par[0], reverse=True)
    return [{"tema": a["tema"], "conteudo": a["conteudo"]} for _, a in pontuados[:limite]]
