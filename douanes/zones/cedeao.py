from douanes.utils.tarif_exterieur_commun import TarifExterieurCommun
from douanes.utils.code_des_douanes import CodeDesDouanesCommunautaire


class CodeDesDouanesCEDEAO(CodeDesDouanesCommunautaire):
    COMMUAUTE = "cedeao"
    ANNEE: str
    CODE_ABBR = "CDC"
    DE_LA_COMMUNAUTE = "de la CEDEAO"


class CodeDesDouanesCEDEAO2017(CodeDesDouanesCEDEAO):
    ANNEE = "2017"


class TECCedeao(TarifExterieurCommun):
    COMMUNAUTE = "cedeao"
    DE_LA_COMMUNAUTE = "de la CEDEAO"


class TECCedeao2022(TECCedeao):
    def __init__(self):
        self.ANNEE = "2022"
        super().__init__()
