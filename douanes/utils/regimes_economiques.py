import pandas as pd

from .base_douanes_ai import BaseDouaneAI

def regime_content(row: pd.Series):
    regime = row["regime"]
    code = row['code']
    def_code = row["def_code"]
    def_regime = row["def_regime"]

    return "|".join([
        str(regime) if regime else "",
        str(code) if code is not None else "",
        str(def_regime) if def_regime is not None else "",
        str(def_code) if def_code is not None else "",
    ])


class RegimeEconomique(BaseDouaneAI):

    BASE_COLLECTION = "codes"
    TEMPERATURE = 0
    SOURCE = "sydonia"
    SOURCE_NAME = "Sydonia"
    VERSION = "plus"
    DONNEES_FICIVES = None    
    EXEMPLES_FICTIFS = None
    PAYS : str  | None= None
    DU_PAYS:  str  | None = ""

    def __init__(self):
        self.pre_prompt = f"""Tu est un assistant basé sur GPT3 qui reppond de facon précise, concise et complete aux questions des agents du service des douanes {self.DU_PAYS} relatives aux regimes économiques en vigueur {('au/en '+self.PAYS) if self.PAYS is not None else ''}. Tu te bases sur la liste des régimes et codes additionnels contenus dans {self.SOURCE_NAME}. Tu evites à tout prix de se repeter dans sa réponse et ne fabrique pas de reponse si la liste à ta disposition ne le permet pas. Tu precises les codes additionnels (si necessaire).\n\n
        Régime etendu | Code additionnel | libéllés régime etendu | Libellés Code additionnel 
        """
        self.PREFIX = f"regimes_{self.SOURCE}{('_'+ self.VERSION + '_') if self.VERSION is not None else '_'}"
        super().__init__()

    def df(self, data: str = BASE_COLLECTION):
        file_path = self.data_frames_path+data
        try:
            _df = pd.read_json(file_path+"_df.json", orient="records")
        except:
            excel_data = pd.read_excel(
                open(file_path+".xlsx", "rb"), header=0, dtype=str).values
            _df = pd.DataFrame(columns=["regime", "code", "def_regime",
                               "def_code"], data=excel_data, dtype=str)
            
            _df["content"] = _df.apply(regime_content, axis=1)
            _df = _df[['content']]
            _df.to_json(file_path+"_df.json", orient="records")
        _df.reset_index(inplace=True)
        return _df

    def get_info(self,
               question: str,
               show_prompt: bool = False,
               prompt_only: bool = False,
               n_result: int = 10,
               stream: bool = False,
               completor: str = "open_ai",
                use_gpt4: bool = False
               ):
        question = question.strip()
        if(len(question.split(" ")) == 1):
            if(len(question) > 4):
                question = "Régime" +  question[:4] + " "+ question[4:]

        return self.answer(question, show_prompt, prompt_only, n_result, stream, completor, use_gpt4)
    

class RegimesSyndoniaWorld(RegimeEconomique):
    SOURCE_NAME = "SYDONIA World"
    VERSION = "world"


__all__ = ["RegimeEconomique", "RegimesSyndoniaWorld"]