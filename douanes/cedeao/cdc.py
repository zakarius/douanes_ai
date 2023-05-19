from douanes.utils.code_des_douanes import CodeDesDouanesCommunautaire


class CodeDesDouanesCEDEAO(CodeDesDouanesCommunautaire):
    COMMUAUTE = "cedeao"
    ANNEE: str
    CODE_ABBR = "CDC"
    DE_LA_COMMUNAUTE = "de la CEDEAO"


class CodeDesDouanesCEDEAO2017(CodeDesDouanesCEDEAO):
    ANNEE = "2017"
