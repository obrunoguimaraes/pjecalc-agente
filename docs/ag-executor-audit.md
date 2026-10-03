# Auditoria inicial — AG PJe-Calc Executor

Branch de trabalho: `ag-executor-base`

## Objetivo do fork

Transformar o projeto em um executor determinístico do PJe-Calc Cidadão.

A interpretação jurídica pertence ao calculista/usuário. O sistema recebe uma **Ordem de Cálculo já definida**, valida a estrutura, aplica literalmente os parâmetros no PJe-Calc, liquida, confere e exporta os artefatos.

Princípio central:

> O executor não interpreta sentença, não cria premissas e não corrige silenciosamente parâmetros. Na falta ou inconsistência de dado necessário, deve bloquear e informar a pendência.

## Achado principal

O repositório já contém a base arquitetural adequada em:

- `core/aplicador.py`: "Aplicador puro 1:1", explicitamente sem inferência.
- `infrastructure/pjecalc_pages.py`: modelos Pydantic espelhando os campos do PJe-Calc e usando `extra="forbid"`.
- `docs/pjecalc-fields-catalog.json`: catálogo de campos do PJe-Calc.
- `knowledge/pjecalc_selectors.py`: seletores DOM já auditados.
- `knowledge/pjecalc_dom_map*.json`: mapas extensos do DOM.
- `core/browser_manager.py`: ciclo de vida do Playwright, retries e recuperação.
- `tests/test_e2e_*.py`: testes end-to-end existentes.
- `skills/pjecalc-operacional/`: conhecimento operacional sobre sequência e dependências do PJe-Calc.

Isso significa que o novo projeto deve evoluir o **aplicador puro**, não reescrever a automação a partir do zero.

## MANTER

### Núcleo operacional
- `core/aplicador.py`
- `infrastructure/pjecalc_pages.py`
- `knowledge/pjecalc_selectors.py`
- `knowledge/pjecalc_dom_map*.json`
- `docs/pjecalc-fields-catalog.json`
- `docs/dom-mapping/`
- `tools/dom_auditor.py`

### Infraestrutura útil
- `core/state_manager.py`, se permanecer útil para rastrear execução
- `infrastructure/calculation_store.py`
- `infrastructure/logging_config.py`
- configuração local do PJe-Calc e Playwright
- screenshots e logs de diagnóstico

### Testes e documentação operacional
- testes de automação e E2E relevantes
- `docs/diagnostico-*.md`
- `docs/registro-erros-automacao.md`
- `docs/erros-conhecidos-pje-calc.md`
- referências puramente operacionais das skills de PJe-Calc

## ADAPTAR

### `core/browser_manager.py`
Manter retries, screenshots, detecção de crash e ViewExpiredException.

Remover a dependência de LLM/Gemini para decidir recovery. Recuperação deve ser determinística e, quando não houver regra segura, a execução deve falhar de forma explícita.

### `modules/pjecalc_validators.py`
Hoje algumas validações **corrigem automaticamente** valores, por exemplo desabilitando prescrição ou substituindo datas.

Para o AG Executor, o comportamento deve ser:

1. detectar inconsistência;
2. retornar erro estruturado;
3. bloquear execução;
4. nunca alterar a Ordem de Cálculo silenciosamente.

### `modules/playwright_pjecalc.py`
É o executor legado e contém muito conhecimento prático valioso sobre DOM, AJAX, retry, reabertura de cálculo e sequências.

Usar como **fonte de conhecimento e compatibilidade**, não como arquitetura principal. Migrar o que for necessário para `core/aplicador.py`.

### `modules/export.py`
A lógica de validar/liquidar/exportar é útil, mas ainda depende da interface legada `PJECalcAutomation`.

Adaptar para operar diretamente com o aplicador/Playwright atual e downloads nativos do browser.

### `skills/pjecalc-operacional/`
Manter regras operacionais do software.

Remover ou isolar qualquer conteúdo que:
- interprete a decisão judicial;
- escolha índice, incidência ou reflexo pelo usuário;
- aplique default jurídico;
- transforme falta de dado em premissa.

### Prévia web
A prévia v3 existente pode ser reaproveitada posteriormente como editor visual da Ordem de Cálculo, mas não é requisito do primeiro MVP.

## ISOLAR / RETIRAR DO FLUXO PRINCIPAL

Não apagar inicialmente; mover para legado ou simplesmente retirar do runtime novo.

### Interpretação e extração jurídica
- `modules/extraction.py`
- `modules/extraction_v2.py`
- `modules/classification.py`
- `modules/document_collector.py`
- `modules/ingestion.py`
- prompts de leitura/interpretação de sentença

### Orquestração por LLM
- `core/llm_orchestrator.py`

O Claude pode existir acima do executor, mas não deve participar das decisões internas do preenchimento.

### Learning engine jurídico
- `learning/learning_engine.py`
- `learning/rule_injector.py`
- `learning/verba_strategies.py`
- `learning/estrategia_parametrizacao.py`

Ferramentas de diff de PJC podem continuar úteis para QA, mesmo que o learning engine saia do fluxo.

### Automação por mouse
- backend PyAutoGUI de `modules/automation.py`

Playwright deve ser o caminho principal.

### Gerador PJC nativo
- `modules/pjc_generator.py`

Não usar como motor principal. O próprio projeto registra que o caminho confiável é operar o PJe-Calc, liquidar e exportar pela interface. Pode permanecer apenas para pesquisa/QA enquanto o executor não precisar dele.

## Riscos identificados

1. **Aplicador puro ainda incompleto.** O cabeçalho de `core/aplicador.py` marca várias fases como pendentes; devemos verificar o estado real de cada método antes do primeiro teste.
2. **Auto-correções ainda existem.** `modules/pjecalc_validators.py` altera parâmetros em alguns cenários; isso viola o contrato do AG Executor.
3. **Recovery por LLM.** `core/browser_manager.py` ainda prevê decisão de recuperação com Gemini.
4. **Versão do PJe-Calc.** Há referências e schemas vinculados ao PJe-Calc 2.15.1. Antes de validar seletores, precisamos testar contra a versão local que será usada na AG.
5. **Código legado misturado ao novo.** Existem pelo menos duas arquiteturas de automação no mesmo repositório. O novo entrypoint deve depender somente da pilha determinística.
6. **Conhecimento jurídico misturado ao conhecimento operacional.** Skills/documentação precisam ser separadas para impedir defaults jurídicos não solicitados.

## Arquitetura alvo

```
Calculista
    ↓
Ordem de Cálculo
    ↓
Schema Pydantic estrito
    ↓
Validador (somente valida; não corrige)
    ↓
AplicadorPJECalc
    ↓
Playwright
    ↓
PJe-Calc Cidadão
    ↓
Validar / Liquidar
    ↓
PJC + PDF + log de execução
```

Claude/Skill pode atuar acima dessa cadeia para ajudar o usuário a montar e revisar a Ordem de Cálculo, mas o executor interno deve permanecer determinístico.

## Primeiro MVP recomendado

Não tentar cobrir todo o PJe-Calc.

### MVP-0 — smoke test
1. detectar PJe-Calc local;
2. abrir um cálculo novo;
3. preencher Dados do Processo/Parâmetros mínimos;
4. salvar;
5. confirmar que os valores persistiram;
6. encerrar sem inferência.

### MVP-1 — primeiro cálculo completo
Adicionar:
1. Histórico Salarial;
2. uma única verba simples e controlada;
3. reflexos expressamente informados na Ordem de Cálculo;
4. validar;
5. liquidar;
6. exportar PJC;
7. comparar com um cálculo-gabarito elaborado manualmente.

### Critério de aprovação

O MVP só é aprovado quando, para a mesma Ordem de Cálculo, o executor reproduzir de forma repetível o resultado do PJe-Calc manual sem adicionar, remover ou alterar premissas.

## Próxima tarefa técnica

Antes de alterar arquitetura:

1. mapear a implementação real de cada método `aplicar_*` em `core/aplicador.py`;
2. identificar o menor subconjunto já funcional;
3. criar teste de smoke específico do AG Executor;
4. substituir autocorreções por erros bloqueantes nesse subconjunto;
5. só então expandir página a página.
