# MVP-01 — Cálculo simples

## Objetivo

Provar o menor fluxo autônomo possível do AG/Cursus Calc Executor:

```
Ordem JSON explícita
→ validação local
→ Playwright
→ PJe-Calc Cidadão local
→ 1 verba
→ liquidar
→ exportar .PJC
```

Sem Claude, sem LLM, sem Supabase, sem Vercel, sem lote e sem interface web.

## Escopo do primeiro cálculo

O cálculo de teste possui:

- 1 processo;
- 1 verba manual de valor informado;
- 1 competência;
- sem reflexos;
- sem histórico salarial;
- sem cartão de ponto;
- FGTS desligado;
- contribuição social desligada;
- IR desligado;
- honorários vazios;
- custas desligadas;
- correção e juros desligados.

É um caso sintético para testar a automação, não um padrão jurídico.

## Arquivos

- `scripts/ag_executor_smoke.py`: runner CLI determinístico.
- `examples/ordem-calculo-simples.json`: contrato de entrada de exemplo.

## Regra de segurança

O runner exige todos os módulos raiz no JSON. Não aceita omissão silenciosa.

Isso é necessário porque o schema legado possui alguns defaults ativos (FGTS, INSS, IR, custas etc.). O novo executor não deve transformar ausência de informação em premissa de cálculo.

## Execução local

O arquivo `examples/ordem-calculo-simples.json` é um **template técnico**. Antes do primeiro teste, substitua os campos de processo/reclamante/reclamado por um processo real acessível na instalação local do PJe-Calc. O aplicador bloqueia a execução se a busca do processo não retornar resultado.

Com o PJe-Calc Cidadão já iniciado e respondendo na porta configurada:

```bash
python scripts/ag_executor_smoke.py examples/ordem-calculo-simples.json
```

URL padrão:

```
http://localhost:9257/pjecalc
```

Para outro endereço:

```bash
python scripts/ag_executor_smoke.py examples/ordem-calculo-simples.json \
  --base-url http://localhost:9257/pjecalc
```

## Critério de aprovação

O MVP-01 só passa se:

1. o JSON for validado antes de abrir o browser;
2. o PJe-Calc estiver online;
3. o cálculo for criado/aberto;
4. os parâmetros informados persistirem;
5. a verba manual existir com exatamente os parâmetros fornecidos;
6. o cálculo for liquidado;
7. o PJe-Calc exportar um .PJC não vazio;
8. o runner retornar código 0;
9. nenhuma chamada de LLM ocorrer durante o fluxo.

## Critério de falha

Qualquer uma das situações abaixo deve terminar como erro/bloqueio, nunca como sucesso parcial:

- campo obrigatório ausente;
- PJe-Calc offline;
- falha em qualquer fase;
- falha de liquidação;
- exportação sem bytes de PJC;
- exceção do browser.

## O que NÃO entra neste MVP

- PDF;
- reflexos;
- histórico salarial;
- horas extras;
- cartão de ponto;
- lotes;
- retomada de execução;
- Supabase;
- Web App;
- Cursus;
- Claude/Skill.

Esses itens serão adicionados somente depois que o fluxo mínimo for repetível.

## Próximo marco

Depois de o MVP-01 passar várias vezes com o mesmo resultado:

**MVP-02:** histórico salarial + uma verba simples baseada no histórico.

A partir daí o projeto começa a provar cálculo trabalhista real, não apenas automação de interface.
