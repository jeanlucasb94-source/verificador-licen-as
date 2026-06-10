"""
Modelo padronizado de licença + classe base dos conectores.

Cada estado tem seu próprio portal, então cada conector traduz o formato
do estado para o LicenseRecord abaixo. Assim o app trata tudo igual.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


# Status que consideramos "válidos" depois de normalizar (minúsculas)
VALID_STATUSES = {
    "active", "current", "current,active", "current, active",
    "valid", "license is current and active",
}


@dataclass
class LicenseRecord:
    state: str                       # "FL", "CA", ...
    license_number: str
    holder_name: str = ""            # nome do profissional/empresa
    license_type: str = ""           # ex.: "Certified General Contractor"
    raw_status: str = ""             # status exatamente como o estado retorna
    expires: str = ""                # data de expiração (texto como veio)
    address: str = ""
    source: str = ""                 # URL oficial onde o dado foi obtido
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    extra: dict = field(default_factory=dict)  # campos específicos do estado

    @property
    def is_valid(self) -> Optional[bool]:
        """True/False se conseguimos interpretar o status; None se incerto."""
        s = self.raw_status.strip().lower()
        if not s:
            return None
        if s in VALID_STATUSES or s.startswith("current") or s.startswith("active"):
            return True
        bad = ("delinquent", "expired", "suspend", "revoked", "null", "inactive",
               "void", "cancel", "denied")
        if any(b in s for b in bad):
            return False
        return None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["is_valid"] = self.is_valid
        return d


class BaseConnector:
    """Interface que todo conector de estado implementa."""

    state: str = ""          # sigla, ex.: "FL"
    state_name: str = ""     # nome por extenso
    agency: str = ""         # órgão licenciador
    verify_url: str = ""     # página oficial de verificação (fallback manual)

    def verify_by_number(self, license_number: str) -> list[LicenseRecord]:
        raise NotImplementedError

    def search_by_name(self, name: str) -> list[LicenseRecord]:
        raise NotImplementedError

    def manual_link(self, query: str = "") -> str:
        """URL oficial para conferência manual (sempre disponível)."""
        return self.verify_url
