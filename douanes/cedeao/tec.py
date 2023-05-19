
from douanes.utils.tarif_exterieur_commun import TarifExterieurCommun

class TECCedeao(TarifExterieurCommun):
    def __init__(self):
        self.COMMUNAUTE ="cedeao"
        self.DE_lA_COMMUNAUTE= "de la CEDEAO"
        super().__init__()


class TECCedeao2022(TECCedeao):
    def __init__(self):
        self.ANNEE = "2022"
        super().__init__()