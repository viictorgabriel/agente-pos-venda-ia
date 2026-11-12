"""Agente de triagem com Claude (API da Anthropic + ferramentas).

Fluxo do agente para cada mensagem:
  1. lê a mensagem do cliente;
  2. decide consultar o CRM (buscar_cliente) e a base de conhecimento;
  3. registra a triagem final pela ferramenta registrar_triagem (formato validado).
"""
from __future__ import annotations

import json
from datetime import date

import anthropic

from .dados import buscar_na_base, contexto_cliente
from .schema import TRIAGEM_SCHEMA, validar

MODELO = "claude-opus-5-5"
MAX_PASSOS = 6

SYSTEM_PROMPT = """Você é um agente de pós-venda de uma revenda de Microsoft 365 e Copilot.
Sua tarefa é triar cada mensagem de cliente para o time humano agir rápido.

Como trabalhar:
- Sempre consulte o CRM com buscar_cliente antes de decidir: renovação próxima,
  adoção baixa do Copilot e NPS baixo mudam a prioridade.
- Consulte a base de conhecimento quando a mensagem tiver dúvida ou problema,
  e use só o que ela disser na resposta sugerida. Não invente prazos, preços ou recursos.
- Prioridade alta: risco de perder o cliente, cliente parado em algo urgente,
  ou renovação em até 45 dias com sinais de insatisfação.
- Se o cliente pedir mais licenças, preencha oportunidade_licencas com o número citado.
- A resposta sugerida é um rascunho em português, cordial e curto (até 4 frases),
  que um humano vai revisar antes de enviar.
- Termine chamando registrar_triagem uma única vez."""

FERRAMENTAS = [
    {
        "name": "buscar_cliente",
        "description": "Busca a ficha do cliente no CRM: plano, licenças, % de adoção do Copilot, "
                       "data de renovação, dias até a renovação, NPS e responsável.",
        "input_schema": {
            "type": "object",
            "properties": {"cliente_id": {"type": "string", "description": "Ex.: C001"}},
            "required": ["cliente_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "consultar_base_conhecimento",
        "description": "Busca artigos da base de conhecimento interna sobre Copilot e Microsoft 365 "
                       "(adoção, Teams, segurança, licenças, relatórios, suporte, financeiro, Copilot Studio).",
        "input_schema": {
            "type": "object",
            "properties": {"consulta": {"type": "string", "description": "Palavras-chave do assunto."}},
            "required": ["consulta"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "registrar_triagem",
        "description": "Registra a triagem final da mensagem. Chame uma única vez, no fim.",
        "input_schema": TRIAGEM_SCHEMA,
        "strict": True,
    },
]


class AgenteClaude:
    def __init__(self, clientes: dict, base: list[dict], hoje: date, client=None, modelo: str = MODELO):
        self.clientes = clientes
        self.base = base
        self.hoje = hoje
        self.modelo = modelo
        self.client = client or anthropic.Anthropic()  # lê ANTHROPIC_API_KEY do ambiente

    def _executar(self, nome: str, entrada: dict) -> tuple[str, bool]:
        """Executa uma ferramenta e devolve (resultado em texto, deu_erro)."""
        if nome == "buscar_cliente":
            cliente = self.clientes.get(entrada.get("cliente_id", ""))
            if not cliente:
                return "Cliente não encontrado no CRM.", True
            return json.dumps(contexto_cliente(cliente, self.hoje), ensure_ascii=False), False
        if nome == "consultar_base_conhecimento":
            artigos = buscar_na_base(entrada.get("consulta", ""), self.base, limite=3)
            return json.dumps(artigos or "Nada encontrado.", ensure_ascii=False), False
        return f"Ferramenta desconhecida: {nome}", True

    def triar(self, mensagem: dict) -> dict:
        pedido = (
            f"Mensagem {mensagem['mensagem_id']} de {mensagem['data']} pelo canal {mensagem['canal']}.\n"
            f"cliente_id: {mensagem['cliente_id']}\n"
            f"Data de hoje: {self.hoje.isoformat()}\n\n"
            f"<mensagem_do_cliente>\n{mensagem['mensagem']}\n</mensagem_do_cliente>"
        )
        historico = [{"role": "user", "content": pedido}]

        for _ in range(MAX_PASSOS):
            resposta = self.client.beta.messages.create(
                model=self.modelo,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                tools=FERRAMENTAS,
                messages=historico,
                output_config={"effort": "medium"},
                # Se o modelo recusar por política, a API tenta outro modelo automaticamente.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
            if resposta.stop_reason == "refusal":
                raise RuntimeError(f"Mensagem {mensagem['mensagem_id']}: o modelo recusou a tarefa.")

            historico.append({"role": "assistant", "content": resposta.content})
            chamadas = [b for b in resposta.content if b.type == "tool_use"]

            for chamada in chamadas:
                if chamada.name == "registrar_triagem":
                    return validar(dict(chamada.input))

            if not chamadas:
                historico.append({"role": "user", "content": "Finalize chamando registrar_triagem."})
                continue

            resultados = []
            for chamada in chamadas:
                texto, erro = self._executar(chamada.name, chamada.input)
                resultados.append({
                    "type": "tool_result",
                    "tool_use_id": chamada.id,
                    "content": texto,
                    "is_error": erro,
                })
            historico.append({"role": "user", "content": resultados})

        raise RuntimeError(f"Mensagem {mensagem['mensagem_id']}: o agente não concluiu em {MAX_PASSOS} passos.")
