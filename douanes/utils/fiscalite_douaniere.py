import pandas as pd
import re
from .base_douanes_ai import BaseDouaneAI

def taxe_douaniere_content(row: pd.Series):
    return "|".join([
        row.code,
        row.nom,
        row.base_legal,
        row.base_taxable,
        row.imposition
    ])

def regime_taxes_content(row: pd.Series):
    return "|".join([
        row.regime,
        row.taxes
    ])

class FiscaliteDouaniere(BaseDouaneAI):
    BASE_COLLECTION = "taxes"
    PAYS: str  | None = ''
    DU_PAYS: str | None = ''
    VERSION: str = "2023"

    def __init__(self):
        self.PREFIX = f"fiscalite_{self.PAYS}_{self.VERSION}_"
        self.pre_prompt = f"""Tu est un assistant basé sur GPT3. Tu repond de facon précise, concise et complete aux questions des agents des services des douanes {self.DU_PAYS} en te basant sur tes connaissance en matière de fiscalité douanière {self.DU_PAYS} en vigueur ({self.VERSION}), dans le style académique. Tu connais bien les pays du monde entier (cotiers, enclavé, iles ...), les taxes douanières (abbreviation|nom|fondement ou base legale|base de taxation|taux d'imposition) et les spécificités des régimes économiques des marchandises (regime|taxes appliquables). Tu evites à tout prix de se repeter dans sa réponse et ne fabrique pas de reponse si les infos dont tu disposes ne le permettent pas.
        \n\n"""

        super().__init__()

    def df(self, data: str = BASE_COLLECTION):
        file_path = self.data_frames_path
        df_path = file_path+data+"_df.json"
        try:
            _df = pd.read_json(df_path, orient="records")
        except:
            excel_data = pd.read_excel(
                open(file_path[:-1]+".xlsx", "rb"), header=0, dtype=str, sheet_name=[data])[data]
            _df = pd.DataFrame(data=excel_data, dtype=str)
        
            if (data == "taxes"):
                _df.columns = ["code", "nom", "base_legal",
                               "base_taxable", "imposition"]
                _df["content"] = _df.apply(taxe_douaniere_content, axis=1)
            else: # regimes
                _df.columns = ["regime", "taxes"]
                _df["content"] = _df.apply(regime_taxes_content, axis=1)
            _df.to_json(df_path, orient="records")
        _df.reset_index(inplace=True)
        return _df
    
    @property
    def taxes_df(self):
        return self.df("taxes")

    @property
    def taxes_codes(self):
        return self.df("taxes")["code"].tolist()
    
    def taxes_appliquables(self):
        self.BASE_COLLECTION = "regimes"
        self.pre_prompt+=""""Analyse la question et donne les noms (avec leurs abbreviation entre parentheses) taxes douanières appliquables en prenant bien en compte le regime economique conconcerné, les pays d'origne et de destination si renseingés et necessaires"""


    def infos_sur_taxes_applicables(self, taxes: str, stream : bool = False):
        codes  = re.findall(r"\(([A-Z]+)\)", taxes)
        self.BASE_COLLECTION = "taxes"
        content_items = {
            "taxes": [row.content for _, row in self.taxes_df[self.taxes_df.code.isin(codes)].iterrows()]
        }
        return self.answer(
            question = f"Informations sur les taxes applicqbles: {codes}",
            stream= stream, 
            content_items = content_items,
            )


    def get_info(self, 
                question: str, 
                show_prompt: bool = False,
                prompt_only: bool = False,
                n_result: int = 5, 
                stream: bool = False,
                completor: str = "open_ai",
                use_gpt4: bool = False
            ):
        question = question.strip()
        content_items: dict[str, list[str]] | None  = None
        if (question in self.taxes_codes):
            self.BASE_COLLECTION = "taxes"
            content_items = {
                "taxes": [row.content  for _, row in self.taxes_df[self.taxes_df.code == question].iterrows()]
            }

        return self.answer(
            question = question, 
            show_prompt = show_prompt, 
            prompt_only = prompt_only, 
            n_result = n_result, 
            stream= stream, 
            completor = completor, 
            use_gpt4= use_gpt4, 
            content_items = content_items,
            )
    