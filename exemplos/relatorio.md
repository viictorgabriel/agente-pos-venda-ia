# Relatório de triagem de pós-venda

_Modo: demo (regras). Dados 100% fictícios._

## Resumo

- **20 mensagens** triadas; **8 com prioridade alta**.
- **Clientes em risco de churn:** Construtora Horizonte, Escritório Lima & Prado, Metalúrgica Forte Aço.
- **Oportunidades:** 230 licenças pedidas, cerca de R$ 414.000/ano (preço fictício de R$ 150/usuário/mês).
- **Tempo poupado estimado:** 2,0 h neste lote, cerca de 40 h/mês com 400 mensagens (premissa: 8 min manuais vs 2 min de revisão por mensagem).

## Mensagens por categoria

| Categoria | Qtde |
|---|---|
| oportunidade_expansao | 6 |
| risco_churn | 5 |
| problema_tecnico | 3 |
| duvida_uso | 3 |
| financeiro | 2 |
| renovacao | 1 |

## Fila de atendimento (mais urgente primeiro)

| Prioridade | Cliente | Categoria | Área | Próxima ação |
|---|---|---|---|---|
| alta | Construtora Horizonte | risco_churn | customer_success | Ana liga hoje para Construtora Horizonte e agenda plano de adoção antes da renovação. |
| alta | Escritório Lima & Prado | problema_tecnico | suporte | Abrir chamado no suporte com o checklist inicial e retornar ao cliente em até 4h. |
| alta | Metalúrgica Forte Aço | risco_churn | customer_success | Ana liga hoje para Metalúrgica Forte Aço e agenda plano de adoção antes da renovação. |
| alta | Hotel Mar Azul | problema_tecnico | suporte | Abrir chamado no suporte com o checklist inicial e retornar ao cliente em até 4h. |
| alta | Construtora Horizonte | risco_churn | customer_success | Ana liga hoje para Construtora Horizonte e agenda plano de adoção antes da renovação. |
| alta | Escritório Lima & Prado | risco_churn | customer_success | Carla liga hoje para Escritório Lima & Prado e agenda plano de adoção antes da renovação. |
| alta | Metalúrgica Forte Aço | risco_churn | customer_success | Ana liga hoje para Metalúrgica Forte Aço e agenda plano de adoção antes da renovação. |
| alta | Hotel Mar Azul | renovacao | customer_success | Confirmar condições de renovação e enviar proposta antes do vencimento. |
| media | Clínica Vida Plena | oportunidade_expansao | comercial | Comercial envia proposta para 30 licenças e agenda reunião. |
| media | Logística Rota Sul | oportunidade_expansao | comercial | Comercial envia proposta para 100 licenças e agenda reunião. |
| media | Instituto Aprender+ | financeiro | financeiro | Encaminhar ao financeiro com número do contrato e mês de referência. |
| media | Fintech Nuvem Pay | oportunidade_expansao | comercial | Comercial envia proposta para novas licenças e agenda reunião. |
| media | Agro Campo Verde | oportunidade_expansao | comercial | Comercial envia proposta para novas licenças e agenda reunião. |
| media | Laboratório BioTeste | oportunidade_expansao | comercial | Comercial envia proposta para 60 licenças e agenda reunião. |
| media | Transportes Via Rápida | oportunidade_expansao | comercial | Comercial envia proposta para 40 licenças e agenda reunião. |
| media | Logística Rota Sul | problema_tecnico | suporte | Abrir chamado no suporte com o checklist inicial e retornar ao cliente em até 4h. |
| baixa | Varejo Ponto Certo | duvida_uso | customer_success | Responder com o passo a passo da base e oferecer treinamento rápido. |
| baixa | Transportes Via Rápida | duvida_uso | customer_success | Responder com o passo a passo da base e oferecer treinamento rápido. |
| baixa | Instituto Aprender+ | duvida_uso | customer_success | Responder com o passo a passo da base e oferecer treinamento rápido. |
| baixa | Varejo Ponto Certo | financeiro | financeiro | Encaminhar ao financeiro com número do contrato e mês de referência. |
