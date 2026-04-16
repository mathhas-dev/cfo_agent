# Claude Code — Estrutura de projeto

Referência para configurar as instruções de IA em um novo projeto com Claude Code.

---

## Estrutura de pastas

```
your-project/
├── CLAUDE.md                        # instruções do time — carrega toda sessão
├── CLAUDE.local.md                  # overrides pessoais — gitignore este
│
└── .claude/
    ├── settings.json                # permissões allow/deny — commitado
    ├── settings.local.json          # permissões pessoais — gitignore este
    │
    ├── commands/                    # slash commands: /project:<nome>
    │   ├── review.md                # → /project:review
    │   ├── fix-issue.md             # → /project:fix-issue
    │   └── deploy.md                # → /project:deploy
    │
    ├── rules/                       # quebra o CLAUDE.md quando fica grande
    │   ├── code-style.md
    │   ├── testing.md
    │   └── api-conventions.md
    │
    ├── skills/                      # workflows auto-invocados pelo Claude
    │   ├── security-review/
    │   │   ├── SKILL.md             # frontmatter YAML + instruções
    │   │   └── checklist.md         # arquivos de suporte opcionais
    │   └── deploy/
    │       ├── SKILL.md
    │       └── templates/
    │           └── release-notes.md
    │
    └── agents/                      # subagents com persona dedicada
        ├── code-reviewer.md
        └── security-auditor.md


~/.claude/                           # nível global — todos os projetos
├── CLAUDE.md                        # preferências pessoais globais
├── settings.json                    # config global
├── commands/                        # slash commands pessoais
├── skills/                          # skills pessoais (todos os projetos)
│   └── git-commit-writer/
│       ├── SKILL.md
│       └── scripts/
│           └── parse-diff.sh
└── projects/                        # auto-gerenciado pelo Claude
    └── <hash-do-projeto>/
        └── memory/
            └── MEMORY.md            # auto-memory acumulada por sessão
```

---

## O que vai em cada arquivo

### `CLAUDE.md` (raiz do projeto)

O arquivo mais importante. Carregado no início de toda sessão. Mantenha abaixo de 200 linhas.

Conteúdo típico:
- visão geral do projeto e stack
- convenções de código (naming, padrões, libs preferidas)
- workflow de git e PR
- o que evitar / decisões arquiteturais já tomadas
- referências a arquivos com `@path/para/arquivo.md`

```markdown
## Projeto
API de aquisição de dados IIoT em Python + FastAPI + PostgreSQL.

## Stack
- Python 3.11, FastAPI, SQLAlchemy (raw SQL via DatabaseFacade)
- Docker Compose, Ansible, GitHub Actions
- PostgreSQL (dart_db)

## Convenções
- Snake_case para variáveis e funções
- Sempre usar async/await em endpoints FastAPI
- Nunca usar console.log — usar o logger customizado do módulo `core.logging`

## Regras de código
@.claude/rules/code-style.md
@.claude/rules/testing.md
```

### `CLAUDE.local.md`

Suas preferências pessoais que não devem ir para o repositório.

```
CLAUDE.local.md
```

Adicione ao `.gitignore`:

```gitignore
CLAUDE.local.md
.claude/settings.local.json
```

### `.claude/settings.json`

Controla o que o Claude pode executar sem pedir confirmação.

```json
{
  "permissions": {
    "allow": [
      "Bash(pytest:*)",
      "Bash(docker compose:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Read(.env)"
    ]
  }
}
```

### `.claude/rules/`

Use quando o `CLAUDE.md` ultrapassar ~200 linhas. Cada arquivo cobre um domínio.

```markdown
<!-- .claude/rules/testing.md -->
## Testes
- Sempre escrever testes antes da implementação (TDD)
- Usar pytest com fixtures para setup de banco
- Cobertura mínima de 80% em módulos de domínio
```

Importe no `CLAUDE.md` com:

```
@.claude/rules/testing.md
```

### `.claude/commands/`

Arquivo único `.md` por comando. Você invoca com `/project:<nome>`.

```markdown
<!-- .claude/commands/review.md -->
Revise o código alterado no PR atual:
1. Verifique cobertura de testes
2. Aponte violações de convenção do CLAUDE.md
3. Liste riscos de segurança ou performance
```

Uso: `/project:review`

### `.claude/skills/`

Pasta por skill, com `SKILL.md` obrigatório e arquivos de suporte opcionais.
O Claude invoca automaticamente quando o contexto bate com o `description`.

```
.claude/skills/
└── security-review/
    ├── SKILL.md
    └── checklist.md
```

Estrutura do `SKILL.md`:

```yaml
---
name: security-review
description: Auditoria de segurança. Usar ao revisar código antes de deploy ou quando o usuário mencionar vulnerabilidades.
allowed-tools: Read, Grep, Glob
disable-model-invocation: false   # true = só você pode invocar (ex: deploy)
user-invocable: true              # false = só o Claude invoca (ex: contexto de fundo)
---

## Instruções

Analise o código em busca de:
1. SQL injection e XSS
2. Credenciais expostas ou secrets hardcoded
3. Dependências com CVEs conhecidos

Consulte @checklist.md para a lista completa.
```

### `.claude/agents/`

Subagents com persona dedicada. Útil para tarefas complexas que se beneficiam
de um especialista isolado (não polui o contexto principal).

```markdown
<!-- .claude/agents/code-reviewer.md -->
---
name: code-reviewer
description: Revisor de código especializado. Usar proativamente ao revisar PRs.
model: sonnet
tools: Read, Grep, Glob
---

Você é um senior engineer focado em corretude e manutenibilidade.
Revise sem condescendência. Seja direto e objetivo.
```

---

## Diferença entre commands e skills

| | `commands/` | `skills/` |
|---|---|---|
| Estrutura | arquivo único `.md` | pasta com `SKILL.md` + suporte |
| Invocação | você chama `/project:nome` | Claude chama automaticamente |
| Suporte a arquivos extras | não | sim |
| Caso de uso | workflows manuais (deploy, commit) | conhecimento especializado sob demanda |

---

## `.gitignore` recomendado

```gitignore
# Claude Code — arquivos pessoais
CLAUDE.local.md
.claude/settings.local.json
```

---

## Como começar

1. Rode `/init` dentro de uma sessão do Claude Code — ele lê o projeto e gera um `CLAUDE.md` inicial.
2. Edite o `CLAUDE.md` gerado, mantendo abaixo de 200 linhas.
3. Adicione `.claude/settings.json` com as permissões do seu stack.
4. Crie `commands/` para os workflows que você repete mais (code review, fix de issue).
5. Quando o `CLAUDE.md` crescer, mova seções para `.claude/rules/`.
6. Skills e agents são opcionais — adicione quando tiver workflows recorrentes complexos.
