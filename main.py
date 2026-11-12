"""Roda a triagem de pós-venda em lote.

Exemplos:
  python main.py --demo                  # sem IA, sem chave (regras)
  python main.py                         # com IA (precisa de ANTHROPIC_API_KEY)
  python main.py --limite 5              # só as 5 primeiras mensagens
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

from agente.dados import carregar_base, carregar_clientes, carregar_mensagens
from agente.modo_demo import triar_demo
from agente.relatorio import gerar_relatorio, salvar_csv


def main() -> int:
    p = argparse.ArgumentParser(description="Agente de triagem de pós-venda")
    p.add_argument("--demo", action="store_true", help="usa regras em vez da IA (não precisa de chave)")
    p.add_argument("--hoje", default=date.today().isoformat(), help="data de referência AAAA-MM-DD")
    p.add_argument("--limite", type=int, default=None, help="processa só N mensagens")
    p.add_argument("--saida", default="saida", help="pasta de saída")
    args = p.parse_args()

    hoje = date.fromisoformat(args.hoje)
    clientes = carregar_clientes()
    mensagens = carregar_mensagens()[: args.limite]

    if not args.demo and not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY não definida. Rodando em modo demo (--demo).", file=sys.stderr)
        args.demo = True

    if args.demo:
        modo = "demo (regras)"
        triar = lambda m: triar_demo(m["mensagem"], clientes[m["cliente_id"]], hoje)  # noqa: E731
    else:
        from agente.agente_claude import AgenteClaude

        modo = "agente com Claude"
        agente = AgenteClaude(clientes, carregar_base(), hoje)
        triar = agente.triar

    linhas = []
    for m in mensagens:
        t = triar(m)
        linhas.append({**m, "empresa": clientes[m["cliente_id"]]["empresa"], **t})
        print(f"{m['mensagem_id']}  {t['prioridade']:<5}  {t['categoria']:<22}  {clientes[m['cliente_id']]['empresa']}")

    pasta = Path(args.saida)
    salvar_csv(linhas, pasta / "triagem.csv")
    (pasta / "relatorio.md").write_text(gerar_relatorio(linhas, modo), encoding="utf-8")
    print(f"\nPronto: {pasta / 'triagem.csv'} e {pasta / 'relatorio.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
