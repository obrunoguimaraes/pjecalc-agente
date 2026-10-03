#!/usr/bin/env python3
"""Diagnóstico mínimo do AG Executor contra o PJe-Calc local.

Não altera nenhum cálculo. Apenas abre a home, detecta versão e confirma
que o botão de criação existe.
"""

from __future__ import annotations

import argparse
import re
import sys

from playwright.sync_api import sync_playwright


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe do PJe-Calc local")
    parser.add_argument(
        "--base-url",
        default="http://localhost:9257/pjecalc",
        help="URL do PJe-Calc Cidadão",
    )
    args = parser.parse_args()

    url = f"{args.base_url.rstrip('/')}/pages/principal.jsf"

    with sync_playwright() as pw:
        browser = pw.firefox.launch(headless=False)
        page = browser.new_page()
        try:
            print(f"Abrindo: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)

            body = page.locator("body").inner_text(timeout=5000)
            m = re.search(r"Vers[aã]o\s*:?\s*(\d+\.\d+\.\d+)", body, re.I)
            version = m.group(1) if m else "desconhecida"

            normalized = " ".join(body.upper().split())
            has_new = (
                "CRIAR NOVO CÁLCULO" in normalized
                or "CRIAR NOVO CALCULO" in normalized
                or page.locator("li#li_calculo_novo").count() > 0
            )

            print(f"Versão detectada: {version}")
            print(f"Botão 'Criar Novo Cálculo': {'OK' if has_new else 'NÃO ENCONTRADO'}")

            if version == "2.16.0" and has_new:
                print("PROBE_OK: ambiente pronto para o MVP-01.")
                return 0

            print("PROBE_ATENCAO: PJe-Calc respondeu, mas o DOM precisa ser revisado.")
            return 2
        finally:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
