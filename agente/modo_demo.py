"""Modo demo: triagem por regras, sem IA e sem chave de API.

Serve para qualquer pessoa rodar o projeto na hora e para os testes automáticos.
O modo com IA (agente_claude.py) devolve o mesmo formato, com mais nuance.
"""
from __future__ import annotations

import re
from datetime import date

from .dados import buscar_na_base, carregar_base, dias_para_renovacao

_BASE = carregar_base()

SINAIS_CHURN = [
    "decepcionad", "não vamos renovar", "reduzir as licenças", "escalar",
    "ninguém respondeu", "se vale renovar", "cobrando resultado", "retorno é quase zero",
]
SINAIS_TECNICOS = ["sumiu", "erro", "travando", "não consigo", "não aparece"]
SINAIS_FINANCEIRO = ["fatura", "boleto", "segunda via", "cobrança"]
SINAIS_EXPANSAO = [
    "proposta", "ampliar", "liberar para mais", "levar o copilot", "condição especial",
    "quanto custaria", "workshop", "antes de comprar", "mais ",
]
SINAIS_POSITIVOS = ["ótimo", "adorou", "parabéns", "ajudando muito", "resolveram"]
SINAIS_URGENCIA = ["urgente", "prazo", "antes do fechamento"]

RE_LICENCAS = re.compile(
    r"(\d+)\s*(?:pessoas|usuários|analistas|vendedores|funcionários|licenças)"
)


def _contem(texto: str, termos: list[str]) -> list[str]:
    return [t for t in termos if t in texto]


def _licencas_pedidas(texto: str) -> int:
    numeros = [int(n) for n in RE_LICENCAS.findall(texto)]
    return max(numeros) if numeros else 0


def triar_demo(mensagem: str, cliente: dict, hoje: date) -> dict:
    texto = mensagem.lower()
    dias = dias_para_renovacao(cliente, hoje)
    sinais_risco = [f"mensagem: '{s}'" for s in _contem(texto, SINAIS_CHURN)]
    if cliente["licencas_copilot"] and cliente["adocao_copilot_pct"] < 30:
        sinais_risco.append(f"adoção do Copilot baixa ({cliente['adocao_copilot_pct']}%)")
    if 0 <= dias <= 45:
        sinais_risco.append(f"renovação em {dias} dias")
    if cliente["nps"] <= 6:
        sinais_risco.append(f"NPS {cliente['nps']}")

    licencas = 0
    if _contem(texto, SINAIS_CHURN):
        categoria, area, prioridade = "risco_churn", "customer_success", "alta"
    elif _contem(texto, SINAIS_TECNICOS):
        categoria, area, prioridade = "problema_tecnico", "suporte", "media"
    elif _contem(texto, SINAIS_FINANCEIRO):
        categoria, area, prioridade = "financeiro", "financeiro", "baixa"
    elif _contem(texto, SINAIS_EXPANSAO):
        categoria, area, prioridade = "oportunidade_expansao", "comercial", "media"
        licencas = _licencas_pedidas(texto)
    elif "renovação" in texto or "renovar" in texto:
        categoria, area, prioridade = "renovacao", "customer_success", "media"
    else:
        categoria, area, prioridade = "duvida_uso", "customer_success", "baixa"

    if _contem(texto, SINAIS_URGENCIA):
        prioridade = "alta" if prioridade != "baixa" else "media"
    # Contexto do CRM pesa: renovação próxima com vários sinais de risco sobe a prioridade.
    if len(sinais_risco) >= 2 and prioridade != "alta" and categoria != "financeiro":
        prioridade = "alta" if 0 <= dias <= 45 else "media"

    if _contem(texto, SINAIS_POSITIVOS):
        sentimento = "positivo"
    elif categoria in ("risco_churn", "problema_tecnico") or _contem(texto, SINAIS_URGENCIA):
        sentimento = "negativo"
    else:
        sentimento = "neutro"

    artigos = buscar_na_base(texto, base=_BASE)
    # Só usa a base de conhecimento quando o cliente pediu ajuda (dúvida ou problema).
    usa_dica = categoria in ("duvida_uso", "problema_tecnico", "risco_churn")
    dica = artigos[0]["conteudo"] if artigos and usa_dica else ""
    abertura = {
        "oportunidade_expansao": "Que ótimo saber do interesse! Vou preparar uma proposta e já agendo uma conversa.",
        "financeiro": "Já encaminhei ao nosso financeiro; se puder, nos envie o número do contrato e o mês de referência.",
        "renovacao": "Já estou preparando a proposta de renovação para vocês.",
        "risco_churn": "Entendo a frustração e quero resolver isso com vocês. Proposta:",
    }.get(categoria, "")
    nome = cliente["empresa"]

    acoes = {
        "risco_churn": f"{cliente['responsavel']} liga hoje para {nome} e agenda plano de adoção antes da renovação.",
        "problema_tecnico": "Abrir chamado no suporte com o checklist inicial e retornar ao cliente em até 4h.",
        "financeiro": "Encaminhar ao financeiro com número do contrato e mês de referência.",
        "oportunidade_expansao": f"Comercial envia proposta para {licencas or 'novas'} licenças e agenda reunião.",
        "renovacao": "Confirmar condições de renovação e enviar proposta antes do vencimento.",
        "duvida_uso": "Responder com o passo a passo da base e oferecer treinamento rápido.",
    }
    follow_up = {"alta": 1, "media": 3, "baixa": 7}[prioridade]

    resposta = (
        f"Olá, equipe {nome}! Obrigado pela mensagem. "
        + (abertura + " " if abertura else "")
        + (dica + " " if dica else "")
        + "Vou acompanhar pessoalmente e retorno em até "
        + ("1 dia útil." if follow_up == 1 else f"{follow_up} dias.")
    )

    return {
        "categoria": categoria,
        "prioridade": prioridade,
        "sentimento": sentimento,
        "encaminhar_para": area,
        "resumo": mensagem[:140].rstrip() + ("..." if len(mensagem) > 140 else ""),
        "sinais_de_risco": sinais_risco,
        "oportunidade_licencas": licencas,
        "proxima_acao": acoes[categoria],
        "resposta_sugerida": resposta,
        "follow_up_dias": follow_up,
    }

