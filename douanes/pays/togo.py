from douanes.zones import CodeDesDouanesCEDEAO2017, TecUemoaCedao
from douanes.utils import FicheValeurs, FiscaliteDouaniere, RegimeEconomique
from douanes.utils.code_des_douanes import CodeDesDouanesNational, CodesDesDouanesNationalEtCommunautaire
from douanes.utils.valeur_en_douanes import FicheValeurs, CodesCST
from douanes.utils.regimes_economiques import RegimeEconomique
from douanes.utils.fiscalite_douaniere import FiscaliteDouaniere

from douanes.utils.chained_ai import BaseChainedAi

# ---------------#
#   BASE AI #
# ----------------#

_PAYS = "togo"
_DU_PAYS = "du Togo"


class CodeDesDouanesTogo(CodeDesDouanesNational):
    PAYS = _PAYS
    ANNEE: str = ""
    DU_PAYS = _DU_PAYS


class TecTogo(TecUemoaCedao):
    PAYS = _PAYS
    DU_PAYS = _DU_PAYS
    ANNEE: str = ""


class FicheValeurTogo(FicheValeurs):
    PAYS = _PAYS
    DU_PAYS = _DU_PAYS
    VERSION = None


class CodesCSTTogo(CodesCST):
    PAYS = _PAYS
    DU_PAYS = _DU_PAYS
    DONNEES_FICIVES = None
    EXEMPLES_FICTIFS = None


class RegimesTogo(RegimeEconomique):
    PAYS = _PAYS
    DU_PAYS = _DU_PAYS
    SOURCE_NAME = "SYDONIA World"
    VERSION = "world"


class FiscaliteDouanesTogo(FiscaliteDouaniere):
    PAYS = _PAYS
    DU_PAYS = _DU_PAYS
    VERSION = ""


# ---------------#
#   VERSIONED AI #
# ----------------#

# Codes des douanes
class CodeDesDouanesTogo2017(CodeDesDouanesTogo):
    ANNEE = "2017"


class CdnTogoEtCedeao2017(CodesDesDouanesNationalEtCommunautaire):
    COMMUAUTE = "cedeao"
    PAYS = _PAYS
    ANNEE = "2017"
    DU_PAYS = _DU_PAYS
    DE_LA_COMMUNAUTE = "de la CEDEAO"

    cdn = CodeDesDouanesTogo2017()
    cdc = CodeDesDouanesCEDEAO2017()


# TEC
class TecTogo2022(TecTogo):
    ANNEE = "2022"


# Valeurs
class FicheValeurTogo2022(FicheValeurTogo):
    VERSION = "31_2022"


class CodesCSTTogo2023(CodesCSTTogo):
    VERSION = "2023"


# Regimes
class RegimesTogo2021(RegimesTogo):
    VERSION = "plus"
    SOURCE_NAME = "SYDONIA++"


class RegimesTogo2023(RegimesTogo):
    VERSION = "world"
    SOURCE_NAME = "SYDONIA World - Togo"


# Fiscalite
class FiscaliteDouanesTogo2019(FiscaliteDouanesTogo):
    VERSION = 2019


class DouanesTogolaises(BaseChainedAi):
    def __init__(self) -> None:
        super().__init__(
            code=CdnTogoEtCedeao2017(),
            tec=TecTogo2022(),
            fiche_valeur=FicheValeurTogo2022(),
            fiscalite=FiscaliteDouanesTogo2019(),
            regime=RegimesTogo2021(),
            streaming=True,
        )


__all__ = [
    # Codes des douanes
    "CodeDesDouanesTogo2017",
    "CdnTogoEtCedeao2017",
    # Valeur
    "FicheValeurTogo2022",
    "CodesCSTTogo2023",
    # Regimes
    "RegimesTogo2021",
    "RegimesTogo2023",
    "FiscaliteDouanesTogo2019",

    # Base AI
    "DouanesTogolaises",
]
