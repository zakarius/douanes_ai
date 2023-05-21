import pandas as pd
from .base_douanes_ai import BaseDouaneAI

def valeur_content(row: pd.Series):
    marchandise = row["marchandise"]
    position = row['position']
    unite = row["unite"]
    ancienne_valeur = row["ancienne_valeur"]
    nouvelle_valeur = row["nouvelle_valeur"]
    return "|".join([
        str(marchandise) if marchandise else "",
        str(position) if position is not None else "",
        str(unite) if unite is not None else "",
        str(ancienne_valeur) if ancienne_valeur is not None else "",
        str(nouvelle_valeur) if nouvelle_valeur is not None else ""
    ])


class FicheValeurs(BaseDouaneAI):
    BASE_COLLECTION = "valeurs"
    PREFIX = "fiche"
    PAYS : str  | None= ""
    DU_PAYS:  str  | None = ""
    TEMPERATURE = 0.1
    VERSION: str | None = None


    def __init__(self):
        self.pre_prompt = f"""Tu est un assistant douanier basé sur GPT3. Tu aides agents du service des douanes {self.DU_PAYS} à determiner la valeur connue des marchandies en utilisant la fiche des valeur à ta disposition.Tu repponds de facon précise, concise et complete, en evitant à tout prix de te repeter. Tu ne fabrique pas de reponse si la fiche des valeur ne le permet pas.\n\n"""

        self.PREFIX = f"valeur_{self.PAYS}_{self.PREFIX}{('_'+ self.VERSION + '_') if self.VERSION is not None else '_'}"

        self.DONNEES_FICIVES = """
        Marchandises | Position Tarifaire dans le Tarif Exterieur Commun de la CEDEAO| unité ou reference | ancienne valeur | nouvelle valeur
        * Pièce détachée vélo | 87141100900 8714920090 | Kg/TC X 20 / TC X40 | 700/2 500 000 / 3 500 000 DD | 700/2 500 000 / 3500 000 DD
        * Ustensiles de cuisine en série | |Carton|8000-12000|
        * TV /Sonny/Samsung/Ecran LCD 32/42/47/50 |85287200901|Unité|70 000/90 000/ 110 000/170 000 |
        * Sucre en poudre|17019910000|CST|CST|CST
        * Carreaux ordinaire|69079000000|M carré/TC X 20' |3 500 000|4 500 000
        * Chewing gum|17041000000|Kg/ TC X 20' TC X 40' |250/ DD≥1 500 000 DD≥3 000 000 |250/ DD≥2 500 000 DD≥4 000 000"""

        self.EXEMPLES_FICTIFS = """
        Exemple2: Ustensiles de cuisine en série \nReponse: Les ustensiles de cuisine en série sont evalués en carton. La valeur par carton va de 8.000 à 12.000F"
        Exemple3: Télévision Samsung écran LCD \nReponse:Les télévisions de marque Samsung à ecran LCD classées sour la 85287200901 du TEC sont evaluées comme suit:\n\t- Ecran de 32 pouces : 70.000F/unité\n\t- Ecran de 42 pouces : 90.000F/unité\n\t- Ecran de 47 pouces : 110.000F/unité\n\t- Ecran de 50 pouces : 170.000F/unité"
        Exemple4: Sucre en poudre\nReponse: la valeur du sucre en poudre depend du Code CST (Code Spécial de Tarification) associé à sa marque et son origine"
        Exemple5: les carreaux ordinaire classés sous la position 69079000000 sont evalués à 4.500.000F/TCx20'. l'ancienne valeur était de 3.500.000F/TCx20'  \nReponse: La valeur des carreaux depend de leur qualité"
        Exemple6: Chewing gum\nReponse: les Chewing-gums classés sous la position 17041000000 du TEC peuvent être evalués par kilogramme ou par conteneur.La valeur par kilo est de 250F. le total des droits déclarés (DD) doit être au minimum de 2.500.000F pour un TCx20' et 4.000.000F pour un TCx40'. les anciennes valeurs sont respectivement de 250F, 1.500.000F et 3.000.000F
        """
        super().__init__()

    def df(self, data: str = BASE_COLLECTION):
        file_path = self.data_frames_path + data
        try:
            _df = pd.read_json(file_path+"_df.json", orient="records")
        except:
            excel_data = pd.read_excel(
                open(file_path+".xlsx", "rb"), header=0,).values
            _df = pd.DataFrame(columns=["marchandise", "position", "unite",
                               "ancienne_valeur", "nouvelle_valeur"], data=excel_data)
            _df = _df[~(_df[['position', 'unite', 'ancienne_valeur',
                        'nouvelle_valeur']].isna().all(axis=1))]
            _df["position"] = _df.position.apply(lambda x: None if (
                str(x) == "nan")else str(x).replace(".", "").replace(" ", ""))
            _df.fillna(" ", inplace=True)
            _df["content"] = _df.apply(valeur_content, axis=1)
            _df = _df[['content']]
            _df.to_json(file_path+"_df.json", orient="records")
        _df.reset_index(inplace=True)
        return _df


class CodesCST(FicheValeurs):
    BASE_COLLECTION = "codes"
    PREFIX = "cst"
    DONNEES_FICIVES = None
    EXEMPLES_FICTIFS = None

    def __init__(self):
        self.pre_prompt = f"""Tu est un assistant douanier basé sur GPT3. Tu aides agents du service des douanes {self.DU_PAYS} à determiner la valeur connue des marchandies en utilisant la liste des CST (Codes Spécifique de Tarification) à ta disposition.Tu repponds de facon précise, concise et complete, en evitant à tout prix de te repeter. Tu ne fabrique pas de reponse si la fiche des valeur ne le permet pas.\n\n"""

        self.PREFIX = f"valeur_{self.PAYS}_{self.PREFIX}{('_'+ self.VERSION + '_') if self.VERSION is not None else '_'}"
        super().__init__()

__all__ = ["FicheValeurs", "CodesCST"]