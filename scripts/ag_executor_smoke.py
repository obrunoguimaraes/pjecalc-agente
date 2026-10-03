#!/usr/bin/env python3
"""Smoke runner determinístico do AG PJe-Calc Executor.

Objetivo: provar o menor fluxo útil:
JSON explícito -> validação -> Playwright -> PJe-Calc -> liquidação -> .PJC.

Este runner NÃO usa LLM, NÃO interpreta sentença e NÃO preenche módulos
omitidos silenciosamente. Todos os módulos raiz da Ordem de Cálculo devem
estar presentes no JSON, ainda que explicitamente desativados.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

from pydantic import ValidationError

from core.aplicador import AplicadorPJECalc
from core.browser_manager import BrowserManager
from infrastructure.pjecalc_pages import PreviaCalculo


REQUIRED_ROOT_KEYS = {
    "processo",
    "historico_salarial",
    "faltas",
    "ferias",
    "verbas",
    "cartao_de_ponto",
    "fgts",
    "contribuicao_social",
    "imposto_renda",
    "honorarios",
    "custas",
    "correcao_juros",
}

REQUIRED_PROCESS_KEYS = {
    "numero",
    "digito",
    "ano",
    "regiao",
    "vara",
    "estado",
    "municipio",
    "data_admissao",
    "data_ajuizamento",
    "data_inicio_calculo",
    "data_termino_calculo",
}


class OrdemIncompletaError(ValueError):
    pass


def _check_explicit_contract(raw: dict) -> None:
    missing_root = sorted(REQUIRED_ROOT_KEYS - set(raw))
    if missing_root:
        raise OrdemIncompletaError(
            "Ordem incompleta: módulos raiz ausentes: " + ", ".join(missing_root)
        )

    processo = raw.get("processo")
    if not isinstance(processo, dict):
        raise OrdemIncompletaError("'processo' deve ser um objeto JSON.")

    missing_process = sorted(
        k for k in REQUIRED_PROCESS_KEYS
        if processo.get(k) in (None, "")
    )
    if missing_process:
        raise OrdemIncompletaError(
            "Dados mínimos do processo ausentes: " + ", ".join(missing_process)
        )

    verbas = raw.get("verbas")
    if not isinstance(verbas, list) or len(verbas) != 1:
        raise OrdemIncompletaError(
            "MVP-01 exige exatamente 1 verba. "
            "Lotes/reflexos/múltiplas verbas ficam para etapas posteriores."
        )

    verba = verbas[0]
    if not isinstance(verba, dict) or not isinstance(verba.get("parametros"), dict):
        raise OrdemIncompletaError("A verba deve conter o objeto 'parametros'.")

    params = verba["parametros"]
    must = {
        "descricao",
        "tipo_de_verba",
        "caracteristica_verba",
        "ocorrencia_pagto",
        "periodo_inicial",
        "periodo_final",
        "valor",
        "fgts",
        "inss",
        "irpf",
    }
    missing = sorted(k for k in must if k not in params or params[k] in (None, ""))
    if missing:
        raise OrdemIncompletaError(
            "Parâmetros explícitos ausentes na verba: " + ", ".join(missing)
        )

    if verba.get("reflexos"):
        raise OrdemIncompletaError("MVP-01 não admite reflexos.")


def _pjecalc_online(base_url: str) -> bool:
    try:
        req = urllib.request.Request(base_url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return 200 <= resp.status < 500
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="AG Executor — smoke test PJe-Calc")
    parser.add_argument("ordem", type=Path, help="JSON da Ordem de Cálculo")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/smoke-calculo.pjc"),
        help="Destino do .PJC exportado",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("PJECALC_LOCAL_URL", "http://localhost:9257/pjecalc"),
        help="URL local do PJe-Calc",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Executar Firefox sem interface gráfica",
    )
    args = parser.parse_args()

    try:
        raw = json.loads(args.ordem.read_text(encoding="utf-8"))
        _check_explicit_contract(raw)
        ordem = PreviaCalculo.model_validate(raw)
    except FileNotFoundError:
        print(f"ERRO: arquivo não encontrado: {args.ordem}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERRO: JSON inválido: {exc}", file=sys.stderr)
        return 2
    except (OrdemIncompletaError, ValidationError) as exc:
        print(f"BLOQUEADO: {exc}", file=sys.stderr)
        return 3

    if not _pjecalc_online(args.base_url):
        print(
            f"BLOQUEADO: PJe-Calc não responde em {args.base_url}. "
            "Inicie o PJe-Calc Cidadão antes de executar.",
            file=sys.stderr,
        )
        return 4

    args.output.parent.mkdir(parents=True, exist_ok=True)

    print("Ordem validada.")
    print(f"PJe-Calc: {args.base_url}")
    print("Iniciando execução determinística...")

    try:
        with BrowserManager(headless=args.headless, orchestrator=None) as browser:
            page = browser.page
            page.goto(
                f"{args.base_url.rstrip('/')}/pages/principal.jsf",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            aplicador = AplicadorPJECalc(
                page=page,
                base_url=args.base_url,
                log_cb=lambda msg: print(msg, flush=True),
            )
            result = aplicador.aplicar(ordem)
    except Exception as exc:
        print(f"ERRO_EXECUCAO: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 5

    if not result.get("sucesso"):
        print(
            f"ERRO_EXECUCAO: fase={result.get('fase_falhou')} "
            f"mensagens={result.get('mensagens')}",
            file=sys.stderr,
        )
        return 6

    pjc = result.get("pjc_bytes")
    if not pjc:
        print(
            "ERRO_EXPORTACAO: pipeline terminou sem bytes de .PJC. "
            "A execução NÃO será considerada concluída.",
            file=sys.stderr,
        )
        return 7

    args.output.write_bytes(pjc)
    print(f"CONCLUIDO: {args.output} ({len(pjc)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
