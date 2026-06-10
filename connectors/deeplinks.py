"""
Conectores "deep-link" — estados onde (por enquanto) o app encaminha
para o portal oficial de verificação em vez de raspar.

Por que assim? Cada um desses portais tem peculiaridades (CAPTCHA,
sessão, JavaScript pesado). Começar com o link oficial deixa o app útil
pros 8 estados desde o dia 1; depois você promove um estado a scraper
completo quando valer a pena (use florida.py e california.py como modelo).

Observação importante sobre o TEXAS: o estado NÃO licencia "general
contractor" — só ofícios específicos (eletricista, HVAC, encanador via
TSBPE etc.). Pra GC no Texas a exigência costuma ser municipal.
"""
from __future__ import annotations

from .base import BaseConnector, LicenseRecord


class DeepLinkConnector(BaseConnector):
    """Conector que só fornece o link oficial (sem scraping)."""

    note: str = ""

    def _stub(self, query: str) -> list[LicenseRecord]:
        return [LicenseRecord(
            state=self.state,
            license_number=query,
            raw_status="(verificação manual — abra o link oficial)",
            source=self.manual_link(query),
            extra={"note": self.note} if self.note else {},
        )]

    def verify_by_number(self, license_number: str) -> list[LicenseRecord]:
        return self._stub(license_number)

    def search_by_name(self, name: str) -> list[LicenseRecord]:
        return self._stub(name)


class TexasConnector(DeepLinkConnector):
    state = "TX"
    state_name = "Texas"
    agency = "TDLR — Texas Department of Licensing and Regulation"
    verify_url = "https://www.tdlr.texas.gov/LicenseSearch/"
    note = ("Texas não licencia general contractor estadual — só ofícios "
            "(eletricista, HVAC etc.). GC é regulado por cidade/condado. "
            "O TDLR também publica arquivos de dados em "
            "https://www.tdlr.texas.gov/LicenseSearch/licfile.asp")


class GeorgiaConnector(DeepLinkConnector):
    state = "GA"
    state_name = "Georgia"
    agency = "Georgia Secretary of State — Professional Licensing Boards"
    verify_url = "https://verify.sos.ga.gov/verification/"


class NorthCarolinaConnector(DeepLinkConnector):
    state = "NC"
    state_name = "North Carolina"
    agency = "NC Licensing Board for General Contractors"
    verify_url = "https://portal.nclbgc.org/Public/Search"


class ArizonaConnector(DeepLinkConnector):
    state = "AZ"
    state_name = "Arizona"
    agency = "AZ ROC — Registrar of Contractors"
    verify_url = "https://azroc.my.site.com/AZRoc/s/contractor-search"


class TennesseeConnector(DeepLinkConnector):
    state = "TN"
    state_name = "Tennessee"
    agency = "TN Dept. of Commerce & Insurance — Board for Licensing Contractors"
    verify_url = "https://verify.tn.gov/"


class NevadaConnector(DeepLinkConnector):
    state = "NV"
    state_name = "Nevada"
    agency = "Nevada State Contractors Board"
    verify_url = "https://app.nvcontractorsboard.com/Clients/NVSCB/Public/Verification/Search.aspx"


class WashingtonConnector(DeepLinkConnector):
    state = "WA"
    state_name = "Washington"
    agency = "WA L&I — Department of Labor & Industries"
    verify_url = "https://secure.lni.wa.gov/verify/"
    note = ("Washington tem dados abertos de contractors no portal "
            "data.wa.gov (API Socrata) — ótimo candidato a virar conector "
            "automático no estilo da Flórida.")
