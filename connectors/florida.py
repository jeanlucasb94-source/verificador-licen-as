"""
Flórida — DBPR (Department of Business and Professional Regulation)

Estratégia: em vez de raspar o site, baixamos os EXTRATOS OFICIAIS em CSV
que o próprio DBPR publica (atualizados periodicamente) e consultamos
localmente. É mais rápido, não quebra com mudança de layout do site e
não corre risco de bloqueio.

Extratos de construção (Construction Industry Licensing Board):
  http://www.myfloridalicense.com/dbpr/sto/file_download/extracts/CONSTRUCTIONLICENSE_1.csv
  (pode haver _2, _3... — o código tenta em sequência até dar 404)

Verificação manual oficial (tempo real):
  https://www.myfloridalicense.com/portalsearches/VerifyLicensee

OBS: os CSVs do DBPR vêm SEM cabeçalho (ASCII, quote/comma delimited).
O layout oficial está documentado em "Download File Layout Information"
na página de Public Records do DBPR. O mapeamento FIELD_LAYOUT abaixo
segue o layout padrão de licenciados — se notar campos trocados,
ajuste a lista conforme o documento oficial.
"""
from __future__ import annotations

import csv
import io
import os
import time
import unicodedata

import requests

from .base import BaseConnector, LicenseRecord

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
CACHE_MAX_AGE_HOURS = 24

EXTRACT_URL = "http://www.myfloridalicense.com/dbpr/sto/file_download/extracts/CONSTRUCTIONLICENSE_{n}.csv"
MAX_PARTS = 12  # tenta CONSTRUCTIONLICENSE_1.csv ... _12.csv até dar 404

# Layout típico dos extratos de licenciados do DBPR (confira com o
# "Download File Layout Information" oficial e ajuste se necessário):
FIELD_LAYOUT = [
    "board",            # 0  - conselho/board
    "board_name",       # 1
    "licensee_name",    # 2  - nome do licenciado
    "dba_name",         # 3  - nome fantasia
    "rank",             # 4  - rank/classe da licença (ex.: CGC)
    "address1",         # 5
    "address2",         # 6
    "address3",         # 7
    "city",             # 8
    "state",            # 9
    "zip",              # 10
    "county",           # 11
    "license_number",   # 12 - número da licença
    "primary_status",   # 13 - Current / Delinquent / ...
    "secondary_status", # 14 - Active / Inactive / ...
    "original_date",    # 15
    "status_date",      # 16
    "expiration_date",  # 17
]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).upper().strip()


class FloridaConnector(BaseConnector):
    state = "FL"
    state_name = "Florida"
    agency = "DBPR — Construction Industry Licensing Board"
    verify_url = "https://www.myfloridalicense.com/portalsearches/VerifyLicensee"

    # ------------------------------------------------------------------ cache

    def _cache_path(self, n: int) -> str:
        return os.path.join(CACHE_DIR, f"FL_construction_{n}.csv")

    def _download_extracts(self, force: bool = False) -> list[str]:
        """Baixa (ou reaproveita do cache) os arquivos de extrato. Retorna paths."""
        os.makedirs(CACHE_DIR, exist_ok=True)
        paths = []
        for n in range(1, MAX_PARTS + 1):
            path = self._cache_path(n)
            fresh = (
                os.path.exists(path)
                and (time.time() - os.path.getmtime(path)) < CACHE_MAX_AGE_HOURS * 3600
            )
            if fresh and not force:
                paths.append(path)
                continue
            url = EXTRACT_URL.format(n=n)
            try:
                r = requests.get(url, timeout=120, headers={"User-Agent": "Mozilla/5.0"})
            except requests.RequestException as e:
                if os.path.exists(path):          # sem rede? usa cache velho
                    paths.append(path)
                    continue
                if n == 1:
                    raise RuntimeError(f"Falha ao baixar extrato da Flórida: {e}")
                break
            if r.status_code == 404 or len(r.content) < 100:
                break                              # acabou a sequência de partes
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
            paths.append(path)
        if not paths:
            raise RuntimeError(
                "Nenhum extrato da Flórida disponível. Verifique a URL em "
                "https://www2.myfloridalicense.com/construction-industry/public-records/"
            )
        return paths

    # ------------------------------------------------------------------ parse

    def _rows(self):
        for path in self._download_extracts():
            with open(path, "r", encoding="latin-1", errors="replace", newline="") as f:
                for row in csv.reader(f):
                    if not row or len(row) < 5:
                        continue
                    yield row

    def _row_to_record(self, row: list[str]) -> LicenseRecord:
        d = {FIELD_LAYOUT[i]: row[i].strip() for i in range(min(len(row), len(FIELD_LAYOUT)))}
        # fallback: se o layout estiver deslocado, tenta achar o nº de licença
        lic = d.get("license_number", "")
        status = ", ".join(x for x in (d.get("primary_status"), d.get("secondary_status")) if x)
        addr = ", ".join(x for x in (d.get("address1"), d.get("city"),
                                     d.get("state"), d.get("zip")) if x)
        return LicenseRecord(
            state="FL",
            license_number=lic,
            holder_name=d.get("licensee_name", "") or d.get("dba_name", ""),
            license_type=d.get("rank", ""),
            raw_status=status,
            expires=d.get("expiration_date", ""),
            address=addr,
            source="Extrato oficial DBPR (CSV) — confirme em " + self.verify_url,
            extra={"dba": d.get("dba_name", ""), "county": d.get("county", ""),
                   "raw_row": row},
        )

    # ------------------------------------------------------------------ API

    def verify_by_number(self, license_number: str) -> list[LicenseRecord]:
        q = _norm(license_number).replace(" ", "")
        out = []
        for row in self._rows():
            # procura o número em qualquer coluna (robusto a mudança de layout)
            if any(_norm(c).replace(" ", "") == q for c in row):
                out.append(self._row_to_record(row))
                if len(out) >= 5:
                    break
        return out

    def search_by_name(self, name: str) -> list[LicenseRecord]:
        q = _norm(name)
        out = []
        for row in self._rows():
            joined = _norm(" ".join(row[:6]))
            if q in joined:
                out.append(self._row_to_record(row))
                if len(out) >= 25:
                    break
        return out
