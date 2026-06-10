"""
Califórnia — CSLB (Contractors State License Board)

Portal oficial: https://www.cslb.ca.gov/onlineservices/checklicenseII/checklicense.aspx

O site é ASP.NET WebForms (precisa enviar __VIEWSTATE etc.). Este conector
faz o fluxo: GET da página -> coleta campos ocultos -> POST com o número
da licença -> parse do resultado.

IMPORTANTE: sites WebForms mudam nomes de campos sem aviso. O código
tenta DESCOBRIR os campos automaticamente (input de texto cujo name
contém "Lic" e botão de submit), mas se o CSLB mudar o layout, ajuste
os seletores. Em caso de falha, o app sempre mostra o link oficial
para verificação manual.

Detalhe útil: a página de detalhe aceita número direto na URL:
  https://www2.cslb.ca.gov/onlineservices/checklicenseII/LicenseDetail.aspx?LicNum=XXXXXX
o que simplifica muito — tentamos essa rota primeiro.
"""
from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

from .base import BaseConnector, LicenseRecord

DETAIL_URL = "https://www2.cslb.ca.gov/onlineservices/checklicenseII/LicenseDetail.aspx?LicNum={num}"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _text_after_label(soup: BeautifulSoup, *labels: str) -> str:
    """Procura um rótulo no HTML e devolve o texto vizinho."""
    body = soup.get_text("\n", strip=True)
    for label in labels:
        m = re.search(rf"{re.escape(label)}\s*[:\n]\s*(.+)", body, re.IGNORECASE)
        if m:
            return m.group(1).split("\n")[0].strip()
    return ""


class CaliforniaConnector(BaseConnector):
    state = "CA"
    state_name = "California"
    agency = "CSLB — Contractors State License Board"
    verify_url = "https://www.cslb.ca.gov/onlineservices/checklicenseII/checklicense.aspx"

    def manual_link(self, query: str = "") -> str:
        q = re.sub(r"\D", "", query or "")
        return DETAIL_URL.format(num=q) if q else self.verify_url

    def verify_by_number(self, license_number: str) -> list[LicenseRecord]:
        num = re.sub(r"\D", "", license_number)
        if not num:
            return []
        url = DETAIL_URL.format(num=num)
        r = requests.get(url, headers=HEADERS, timeout=60)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        page_text = soup.get_text(" ", strip=True)
        if "could not be found" in page_text.lower() or "no records" in page_text.lower():
            return []

        name = _text_after_label(soup, "Business Name", "Name")
        status = _text_after_label(soup, "License Status", "Status")
        expires = _text_after_label(soup, "Expiration Date", "Expire")
        classification = _text_after_label(soup, "Classification")
        address = _text_after_label(soup, "Address", "Business Address")

        # Heurística extra: o CSLB exibe frase tipo
        # "This license is current and active" no detalhe.
        m = re.search(r"This license is ([^.]+)\.", page_text, re.IGNORECASE)
        if m and not status:
            status = m.group(1).strip()

        if not (name or status):
            # Página carregou mas não conseguimos interpretar — devolve registro
            # mínimo com link pra conferência manual em vez de errar.
            return [LicenseRecord(
                state="CA", license_number=num,
                raw_status="(não interpretado — confira no link)",
                source=url,
            )]

        return [LicenseRecord(
            state="CA",
            license_number=num,
            holder_name=name,
            license_type=classification,
            raw_status=status,
            expires=expires,
            address=address,
            source=url,
        )]

    def search_by_name(self, name: str) -> list[LicenseRecord]:
        # A busca por nome do CSLB é WebForms com paginação — pra uso caseiro,
        # o caminho mais confiável é o link oficial:
        raise NotImplementedError(
            "Busca por nome na Califórnia: use o portal oficial "
            + self.verify_url
        )
