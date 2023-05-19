from douanes.utils.code_des_douanes import CodeDesDouanesNational, CodesDesDouanesNationalEtCommunautaire
from douanes.cedeao import CodeDesDouanesCEDEAO2017

class CodeDesDouanesTogo(CodeDesDouanesNational):
    PAYS = "togo"
    ANNEE : str = ""
    CODE_ABBR = "CDN"
    DU_PAYS = "du Togo"

class CodeDesDouanesTogo2017(CodeDesDouanesTogo):
    ANNEE = "2017"

class CdnTogoEtCedeao2017(CodesDesDouanesNationalEtCommunautaire):
    COMMUAUTE = "cedeao"
    PAYS = "togo"
    ANNEE= "2017"
    DU_PAYS = "du Togo"
    DE_LA_COMMUNAUTE = "de la CEDEAO"

    cdn = CodeDesDouanesTogo2017()
    cdc = CodeDesDouanesCEDEAO2017()



