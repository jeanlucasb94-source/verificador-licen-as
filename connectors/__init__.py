from .florida import FloridaConnector
from .california import CaliforniaConnector
from .deeplinks import (
    TexasConnector, GeorgiaConnector, NorthCarolinaConnector,
    ArizonaConnector, TennesseeConnector, NevadaConnector, WashingtonConnector,
)

CONNECTORS = {
    c.state: c() for c in (
        FloridaConnector, CaliforniaConnector, TexasConnector,
        GeorgiaConnector, NorthCarolinaConnector, ArizonaConnector,
        TennesseeConnector, NevadaConnector, WashingtonConnector,
    )
}


def get(state: str):
    conn = CONNECTORS.get(state.upper().strip())
    if not conn:
        raise KeyError(
            f"Estado '{state}' não suportado. Disponíveis: {', '.join(sorted(CONNECTORS))}"
        )
    return conn
