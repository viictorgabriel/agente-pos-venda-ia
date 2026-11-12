"""Testes que rodam sem chave de API (modo demo + agente com cliente falso)."""
from datetime import date
from types import SimpleNamespace

import pytest

from agente.agente_claude import AgenteClaude
from agente.dados import carregar_base, carregar_clientes, carregar_mensagens
from agente.modo_demo import triar_demo
from agente.relatorio import gerar_relatorio, resumo_numeros
from agente.schema import validar

HOJE = date(2026, 11, 12)
CLIENTES = carregar_clientes()
MENSAGENS = {m["mensagem_id"]: m for m in carregar_mensagens()}


def triar(mid):
    m = MENSAGENS[mid]
    return triar_demo(m["mensagem"], CLIENTES[m["cliente_id"]], HOJE)


def test_todas_as_triagens_seguem_o_formato():
    for mid in MENSAGENS:
        validar(triar(mid))


def test_cliente_insatisfeito_vira_risco_de_churn_alto():
    t = triar("M007")
    assert t["categoria"] == "risco_churn"
    assert t["prioridade"] == "alta"
    assert t["encaminhar_para"] == "customer_success"


def test_pedido_de_licencas_vira_oportunidade_com_quantidade():
    t = triar("M003")
    assert t["categoria"] == "oportunidade_expansao"
    assert t["oportunidade_licencas"] == 100


def test_contexto_do_crm_aparece_nos_sinais_de_risco():
    sinais = " ".join(triar("M001")["sinais_de_risco"])
    assert "adoção do Copilot baixa" in sinais
    assert "renovação em" in sinais


def test_problema_urgente_tem_prioridade_alta():
    t = triar("M004")
    assert t["categoria"] == "problema_tecnico"
    assert t["prioridade"] == "alta"


def test_validar_recusa_categoria_inventada():
    t = triar("M005") | {"categoria": "qualquer_coisa"}
    with pytest.raises(ValueError):
        validar(t)


def test_relatorio_tem_numeros_principais():
    linhas = [{**m, "empresa": CLIENTES[m["cliente_id"]]["empresa"], **triar(mid)} for mid, m in MENSAGENS.items()]
    r = resumo_numeros(linhas)
    assert r["mensagens"] == len(MENSAGENS)
    assert r["licencas_oportunidade"] > 0
    texto = gerar_relatorio(linhas, "demo")
    assert "Fila de atendimento" in texto


# ---------- Agente com Claude, usando um cliente falso (sem chamar a API) ----------

def _bloco_ferramenta(nome, entrada, id_):
    return SimpleNamespace(type="tool_use", name=nome, input=entrada, id=id_)


class ClienteFalso:
    """Imita client.beta.messages.create: 1º pede o CRM, 2º registra a triagem."""

    def __init__(self, triagem_final):
        self.chamadas = []
        self.triagem_final = triagem_final
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.chamadas.append({**kwargs, "messages": list(kwargs["messages"])})  # cópia do histórico
        if len(self.chamadas) == 1:
            bloco = _bloco_ferramenta("buscar_cliente", {"cliente_id": "C007"}, "t1")
        else:
            bloco = _bloco_ferramenta("registrar_triagem", self.triagem_final, "t2")
        return SimpleNamespace(stop_reason="tool_use", content=[bloco])


def test_loop_do_agente_consulta_crm_e_registra_triagem():
    esperado = triar("M007")
    falso = ClienteFalso(esperado)
    agente = AgenteClaude(CLIENTES, carregar_base(), HOJE, client=falso)

    resultado = agente.triar(MENSAGENS["M007"])

    assert resultado == esperado
    assert len(falso.chamadas) == 2
    # O resultado do CRM voltou para o modelo na 2ª chamada.
    resultado_ferramenta = falso.chamadas[1]["messages"][-1]["content"][0]
    assert resultado_ferramenta["type"] == "tool_result"
    assert "Metalúrgica Forte Aço" in resultado_ferramenta["content"]
    assert '"dias_para_renovacao": 38' in resultado_ferramenta["content"]
