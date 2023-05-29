import re
import pathlib
import pandas as pd
import pdfplumber

from douanes.zones.cedeao import TECCedeao


class TecUemoaCedao(TECCedeao):
    PAYS: str
    DU_PAYS: str
    ANNEE: str = ""

    def __init__(self):
        super().__init__()
        self.pre_prompt = f"Tu est un assistant basé sur GPT3 qui aide les agents du service des douanes {self.DU_PAYS} à bien classer les marchandises dans la bonne sous-posiion du Tarif Exterieur Commun {self.DE_LA_COMMUNAUTE} (TEC) (version {self.ANNEE}). Pour cela, tu mets en valeur tes connaissances approfondies des règles d'interpretation du Système Harmonisé (SH) de designation et de codification des marchandises élaborée par l'OMD. Tu evites à tout prix de te repeter dans sa réponse et tu reponds de facon claire et complete. Tu connais bien TEC les categories des marchandises, notamment les sections, chapitres, posiions et sous-positions du TEC, les chapitres de section,les positions des chapitres et les sous-positions des positions. Pour chaque marchandise (sous-position), tu connais son code de nommenclature tarifaire et statistique (NTS), la designation, l'unité d'evaluation en douane, le taux des DD (droits des douanes) ainsi le taux de RS (redevence statistique) applicables en %. la RS est généralement de 1%. Analyse la question et reponds en fonction d'elle (classer la marchandise en question, donner des informations contenues dans le TEC, ..).  Quand tu reussit à bien classer une marchandise, tu precise l'unité d'evaluation ainsi que le taux de DD et le taux de RS. la RS est généralement de 1% (valeur par defaut si non trouvée).  Sachant que le {self.PAYS} est membre de l'UEMOA, Tu prends en compte les DD ajustés pour les produits de la 5ème bande, classés dans la categorie 4 du TEC. Si une position a un DD ajusté par l'UEMOA, tu utilise ce DD au de celui du TEC mais tu precise cela dans ta reponse.  Quand juste un numero de section, chapitre, position ou sous position est fourni, tu donnes des information sur la section, chapitre, position ou sous-position en question. \n\nInformations du TEC dont tu disposes : \n\n"

    def _df(self, data: str = "produits_5b_uemoa_2023") -> pd.DataFrame:
        if (data == "produits_5b_uemoa_2023"):
            root: str = self.data_frames_path.removesuffix(self.PREFIX)
            data_path = pathlib.Path(f'{root}{data}_indexed_df.json')
            try:
                return pd.read_json(data_path, orient='index',)
            except:
                rows = []
                with pdfplumber.open(f"{root}{data}.pdf") as pdf:
                    for page in pdf.pages:
                        extracted_tables = page.extract_tables()
                        for table in extracted_tables:
                            for row in table:
                                rows.append(row)

                _df = pd.DataFrame(rows[1:], columns=[
                                   "nts", "designation", "us", "cedeao", "uemoa"])
                _df.to_json(data_path, orient="index")
                return _df

        else:
            return super()._df(data)

    def add_additional_info(
        self,
        nts: str,
    ) -> str:
        nts_len = len(nts)

        sous_posiions_str = ""

        produits_5b_df = self._df()
        produits_5b_df["trimmed_nts"] = produits_5b_df["nts"].apply(
            lambda x: x.replace(".", "")[:nts_len])

        sous_posiions = produits_5b_df[produits_5b_df["trimmed_nts"] == nts]

        if not sous_posiions.empty:
            sous_posiions_count = len(sous_posiions)
            first5 = sous_posiions[:min(sous_posiions_count, 5)]
            sous_posiions_str = "\n\nListe des produits de la 5ème Bande: \n\nN.T.S | Designation | unite | D.D CEDEAO | D.D UEMOA \n\n"
            for _, row in first5.iterrows():
                sous_posiions_str += f"{row['nts']} | {row['designation']} | {row['us']} | {row['cedeao']} | {row['uemoa']} \n"
        return sous_posiions_str
