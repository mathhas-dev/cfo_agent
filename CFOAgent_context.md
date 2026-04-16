# CFOAgent — Contexto do Projeto

> Documento de sessão para continuidade no Claude Code (VS Code).
> Gerado em: 16/04/2026

---

## O que é o CFOAgent

Agente conversacional de BI financeiro para diretores interagirem com dados de **P&L (Profit & Loss)** via linguagem natural. O padrão de arquitetura é **NL2SQL (Text-to-SQL)** — o usuário faz uma pergunta em português, o agente gera uma query SQL, executa no banco, e retorna o resultado em formato tabular.

**Não é RAG clássico** (não busca chunks de texto). O "retrieval" aqui é do schema do banco, não de documentos.

---

## Decisões tomadas

| Decisão                       | Escolha                                   | Motivo                                                               |
| ----------------------------- | ----------------------------------------- | -------------------------------------------------------------------- |
| Arquitetura                   | NL2SQL pipeline                           | Dados estruturados em SQL Server                                     |
| Resposta ao usuário           | Tabela (sem narrativa LLM)                | Diretores querem dado, não interpretação                             |
| Interface                     | Microsoft Teams                           | Acesso corporativo já existente                                      |
| Orquestração                  | **LangChain + LangGraph**                 | Maior adoção de mercado, ecossistema mais amplo                      |
| LLM local (ambas as máquinas) | **Qwen2.5-Coder 14B** via Ollama          | Melhor benchmark Text-to-SQL open source; cabe em ambos os hardwares |
| LLM produção                  | A definir (Azure OpenAI ou Anthropic API) | Pay-as-you-go, ~$3-10/mês em uso leve                                |
| Runtime                       | Azure Container Apps                      | GitHub Actions CI/CD                                                 |
| Interface Teams               | Azure Bot Framework SDK                   | SDK oficial para bots no Teams, usado diretamente fora do LangChain  |

---

## Por que LangChain + LangGraph

- Framework com maior adoção no mercado open source de LLM
- LangGraph é o padrão emergente para agentes com estado — exatamente o que o CFOAgent precisa para memória de sessão e perguntas encadeadas
- A integração com Teams fica ligeiramente mais manual, mas o Bot Framework SDK do Python resolve por fora do LangChain sem problema

---

## Hardware de desenvolvimento

| Máquina                        | CPU                 | RAM             | GPU                      | Modelo LLM        |
| ------------------------------ | ------------------- | --------------- | ------------------------ | ----------------- |
| Dell Precision 3591 (trabalho) | Intel Core Ultra 9H | 64 GB DDR5      | NVIDIA RTX 2000 Ada 8 GB | Qwen2.5-Coder 14B |
| MacBook Air M4 (pessoal)       | Apple M4 10-core    | 16 GB unificada | GPU 10-core (Metal)      | Qwen2.5-Coder 14B |

Com 16 GB de RAM unificada, o M4 comporta o 14B com ~7 GB de folga para sistema e contexto. Ambas as máquinas rodam o mesmo modelo, eliminando diferença de qualidade de SQL entre elas.

**Quando usar cada máquina:**

- **Precision** — builds pesados, múltiplos containers simultâneos, testes com modelos maiores (26B+)
- **MacBook Air** — desenvolvimento diário: inferência ligeiramente mais rápida via Metal, fanless, sem depender de tomada; single-core superior torna editor e tooling mais responsivos

---

## Setup Ollama

```bash
# Instalar Ollama (Linux/Mac)
curl -fsSL https://ollama.com/install.sh | sh

# Mesmo modelo em ambas as máquinas
ollama pull qwen2.5-coder:14b

# Testar
ollama run qwen2.5-coder:14b "Write a SQL query to get total revenue by month"
```

Ollama expõe API em `localhost:11434` compatível com OpenAI — o LangChain conecta via `ChatOllama` sem mudança de interface.

**Alternativa monitorar:** Gemma 4 26B MoE (lançado 02/04/2026, Apache 2.0). Apenas 3.8B parâmetros ativos por inferência. Aguardar dados de comunidade específicos para Text-to-SQL antes de adotar.

---

## Arquitetura do sistema

```
Microsoft Teams
      |
Azure Bot Framework SDK  (roteamento de mensagens + auth)
      |
 ┌────┴──────────────────────────────────────┐
 │           LangGraph Agent                 │
 │  NL→SQL  →  Executor+Guard  →  Response Builder  │
 └──┬──────────────────┬──────────────┬──────┘
    |                  |              |
Schema Registry    SQL Server    LangGraph State
(tabelas P&L)    (dados reais)  (histórico conversa)
```

**Deploy:** Azure Container Apps via GitHub Actions

---

## Componentes principais

### Schema Registry

Arquivo (ou tabela) que descreve ao LLM quais tabelas existem, colunas e seus significados em contexto financeiro. **É o componente mais crítico do projeto** — sem schema bem descrito, o LLM gera SQL incorreto.

Exemplo de entrada no registry:

```
fact_pnl.ebitda_brl      = "EBITDA consolidado em BRL, calculado mensalmente por centro de custo"
fact_pnl.receita_bruta   = "Receita bruta antes de deduções fiscais"
dim_tempo.mes_ref        = "Mês de referência no formato YYYY-MM"
```

### NL → SQL

Recebe a pergunta + schema injetado no prompt → gera SQL para SQL Server via `ChatOllama` (dev) ou `AzureChatOpenAI` (produção).

### Executor + Guard

Valida o SQL gerado **antes** de executar: bloqueia `DELETE`, `UPDATE`, `DROP`, `EXEC`, `xp_*`. Nunca executar SQL de LLM sem guardrail.

### Response Builder

Converte o resultado da query em mensagem formatada para o Teams (tabela Markdown ou Adaptive Card).

### LangGraph State (memória de sessão)

Mantém o estado da conversa entre turnos para perguntas encadeadas:

> "qual foi o EBITDA do Q3?" → "e comparando com Q2?" → "por região?"

LangGraph gerencia esse estado nativamente com grafos de fluxo — mais flexível que `ChatHistory` simples para fluxos condicionais futuros.

---

## Roadmap de fases

| Fase                  | Escopo                                                 | Estimativa  |
| --------------------- | ------------------------------------------------------ | ----------- |
| 1 — Fundação          | Schema Registry + setup Ollama + estrutura do projeto  | 1-2 semanas |
| 2 — NL2SQL core       | Loop: pergunta → SQL → guardrail → execução → resposta | 2-3 semanas |
| 3 — Memória de sessão | LangGraph state para perguntas encadeadas              | 1 semana    |
| 4 — Integração Teams  | Bot Framework SDK + Bot Channels Registration          | 1-2 semanas |
| 5 — Deploy Azure      | Container Apps + GitHub Actions pipeline               | 1 semana    |

---

## Stack técnica

```
Python 3.11+
langchain                # orquestração core
langchain-community      # integrações (Ollama, SQL, etc.)
langgraph                # agente com estado e memória de sessão
sqlalchemy + pyodbc      # conexão SQL Server
ollama (local)           # servidor LLM em dev
pytest                   # testes
botbuilder-core          # Bot Framework SDK para Teams
Docker + GitHub Actions  # CI/CD
Azure Container Apps     # runtime em produção
```

---

## Próximo passo acordado

Gerar o **scaffold inicial do projeto**:

- Estrutura de pastas
- `pyproject.toml`
- Loop NL2SQL básico em Python com LangChain + LangGraph + Ollama

---
