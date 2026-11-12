"""Gera a planilha de triagem e o relatório executivo."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

# Premissas (ajuste para a sua realidade). Valores ilustrativos, não são dados reais.
MINUTOS_MANUAIS_POR_MENSAGEM = 8   # ler, olhar o CRM, decidir, escrever resposta
MINUTOS_REVISAO_COM_AGENTE = 2     # humano revisa o rascunho e envia
PRECO_FICTICIO_LICENCA_MES = 150   # R$ por usuário/mês, só para estimar oportunidade
MENSAGENS_POR_MES = 400            # volume mensal suposto de uma carteira média

COLUNAS = [
    "mensagem_id", "data", "cliente_id", "empresa", "canal", "mensagem", "categoria", "prioridade",
    "sentimento", "encaminhar_para", "resumo", "sinais_de_risco", "oportunidade_licencas",
    "proxima_acao", "resposta_sugerida", "follow_up_dias",
]

ORDEM_PRIORIDADE = {"alta": 0, "media": 1, "baixa": 2}


def salvar_csv(linhas: list[dict], caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS)
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow({**linha, "sinais_de_risco": "; ".join(linha["sinais_de_risco"])})


def resumo_numeros(linhas: list[dict]) -> dict:
    n = len(linhas)
    licencas = sum(l["oportunidade_licencas"] for l in linhas)
    minutos_poupados = n * (MINUTOS_MANUAIS_POR_MENSAGEM - MINUTOS_REVISAO_COM_AGENTE)
    return {
        "mensagens": n,
        "por_categoria": Counter(l["categoria"] for l in linhas),
        "por_prioridade": Counter(l["prioridade"] for l in linhas),
        "licencas_oportunidade": licencas,
        "receita_anual_potencial": licencas * PRECO_FICTICIO_LICENCA_MES * 12,
        "horas_poupadas": round(minutos_poupados / 60, 1),
        "horas_poupadas_mes": round(
            MENSAGENS_POR_MES * (MINUTOS_MANUAIS_POR_MENSAGEM - MINUTOS_REVISAO_COM_AGENTE) / 60
        ),
        "clientes_em_risco": sorted({l["empresa"] for l in linhas if l["categoria"] == "risco_churn"}),
    }


def _reais(valor: int) -> str:
    return f"R$ {valor:,.0f}".replace(",", ".")


def gerar_relatorio(linhas: list[dict], modo: str) -> str:
    r = resumo_numeros(linhas)
    fila = sorted(linhas, key=lambda l: (ORDEM_PRIORIDADE[l["prioridade"]], l["data"]))
    partes = [
        "# Relatório de triagem de pós-venda",
        "",
        f"_Modo: {modo}. Dados 100% fictícios._",
        "",
        "## Resumo",
        "",
        f"- **{r['mensagens']} mensagens** triadas; **{r['por_prioridade'].get('alta', 0)} com prioridade alta**.",
        f"- **Clientes em risco de churn:** {', '.join(r['clientes_em_risco']) or 'nenhum'}.",
        f"- **Oportunidades:** {r['licencas_oportunidade']} licenças pedidas, cerca de "
        f"{_reais(r['receita_anual_potencial'])}/ano (preço fictício de {_reais(PRECO_FICTICIO_LICENCA_MES)}/usuário/mês).",
        f"- **Tempo poupado estimado:** {str(r['horas_poupadas']).replace('.', ',')} h neste lote, "
        f"cerca de {r['horas_poupadas_mes']} h/mês com {MENSAGENS_POR_MES} mensagens "
        f"(premissa: {MINUTOS_MANUAIS_POR_MENSAGEM} min manuais vs {MINUTOS_REVISAO_COM_AGENTE} min de revisão por mensagem).",
        "",
        "## Mensagens por categoria",
        "",
        "| Categoria | Qtde |",
        "|---|---|",
        *[f"| {c} | {q} |" for c, q in r["por_categoria"].most_common()],
        "",
        "## Fila de atendimento (mais urgente primeiro)",
        "",
        "| Prioridade | Cliente | Categoria | Área | Próxima ação |",
        "|---|---|---|---|---|",
        *[
            f"| {l['prioridade']} | {l['empresa']} | {l['categoria']} | {l['encaminhar_para']} | {l['proxima_acao']} |"
            for l in fila
        ],
        "",
    ]
    return "\n".join(partes)
