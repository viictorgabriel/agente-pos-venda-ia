"""Formato único da triagem, usado pelo agente com IA e pelo modo demo."""

CATEGORIAS = [
    "duvida_uso",
    "problema_tecnico",
    "financeiro",
    "renovacao",
    "oportunidade_expansao",
    "risco_churn",
]
PRIORIDADES = ["alta", "media", "baixa"]
SENTIMENTOS = ["positivo", "neutro", "negativo"]
AREAS = ["suporte", "customer_success", "comercial", "financeiro"]

TRIAGEM_SCHEMA = {
    "type": "object",
    "properties": {
        "categoria": {"type": "string", "enum": CATEGORIAS},
        "prioridade": {"type": "string", "enum": PRIORIDADES},
        "sentimento": {"type": "string", "enum": SENTIMENTOS},
        "encaminhar_para": {"type": "string", "enum": AREAS},
        "resumo": {"type": "string", "description": "Resumo da mensagem em 1 frase."},
        "sinais_de_risco": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Sinais de risco de churn (pode ser lista vazia).",
        },
        "oportunidade_licencas": {
            "type": "integer",
            "description": "Licenças novas que o cliente sinalizou querer (0 se nenhuma).",
        },
        "proxima_acao": {"type": "string", "description": "Ação interna recomendada."},
        "resposta_sugerida": {"type": "string", "description": "Rascunho de resposta ao cliente."},
        "follow_up_dias": {"type": "integer", "description": "Em quantos dias fazer follow-up."},
    },
    "required": [
        "categoria", "prioridade", "sentimento", "encaminhar_para", "resumo",
        "sinais_de_risco", "oportunidade_licencas", "proxima_acao",
        "resposta_sugerida", "follow_up_dias",
    ],
    "additionalProperties": False,
}


def validar(triagem: dict) -> dict:
    """Confere se a triagem segue o formato; levanta ValueError se não seguir."""
    faltando = [c for c in TRIAGEM_SCHEMA["required"] if c not in triagem]
    if faltando:
        raise ValueError(f"Campos faltando: {faltando}")
    for campo, opcoes in (
        ("categoria", CATEGORIAS),
        ("prioridade", PRIORIDADES),
        ("sentimento", SENTIMENTOS),
        ("encaminhar_para", AREAS),
    ):
        if triagem[campo] not in opcoes:
            raise ValueError(f"{campo} inválido: {triagem[campo]!r}")
    if not isinstance(triagem["sinais_de_risco"], list):
        raise ValueError("sinais_de_risco deve ser uma lista")
    for campo in ("oportunidade_licencas", "follow_up_dias"):
        if not isinstance(triagem[campo], int) or triagem[campo] < 0:
            raise ValueError(f"{campo} deve ser inteiro >= 0")
    return triagem
