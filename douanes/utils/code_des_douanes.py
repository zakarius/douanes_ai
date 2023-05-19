import json
import pathlib
from chromadb.api import Collection, QueryResult, Where, WhereDocument
from chromadb.api.types import Embedding
import pandas as pd
from .base_douanes_ai import BaseDouaneAI
from gpt3 import SEPARATOR, count_tokens, separator_len

def articleTitle(titre: str) -> str:
    return "" if titre == "" else f" ({titre}) "


def titre_content(row, code):
    chapitres = row['chapitres']
    sections = len(str(row['sections']).split(','))
    sousSections = len(str(row['sousSections']).split(','))
    parties = len(str(row['parties']).split(','))
    articles = len(str(row['articles']).split(','))

    description = f"le titre {row['numero']} du {code} intitulé {row['titre']} contient : Chapitres : {chapitres} repgroupés en  {sections} sections, reparties en {sousSections} sous-sections. Ce chapitre a  {parties} parties et {articles} articles ( {row['articles']})"

    return description

def chapitre_content(row, code):
    titre = row['titreId']

    sections = len(str(row['sections']).split(','))
    sousSections = len(str(row['sousSections']).split(','))
    parties = len(str(row['parties']).split(','))
    articles = len(str(row['articles']).split(','))

    description = f"le chapitre {row['numero']} du titre {titre} du {code} intitulé {row['titre']} contient : {sections} sections, reparties en {sousSections} sous-sections. Ce chapitre a  {parties} parties et {articles} articles ( {row['articles']})"

    return description


def section_content(row, code):
    titre = row['titreId']
    if row['chapitreId']:
        chapitre = str(row['chapitreId']).split('_')[-1]
    else:
        chapitre = ""

    sousSections = len(str(row['sousSections']).split(','))
    parties = len(str(row['parties']).split(','))
    articles = len(str(row['articles']).split(','))

    description = f"la section {row['numero']} du chapitre {chapitre} du titre {titre} du {code} intitulé {row['titre']} contient : {sousSections} sous-sections. Cette section a  {parties} parties et {articles} articles ( {row['articles']})"
    return description


def sous_section_content(row, code):

    titre = row['titreId']
    if row['chapitreId'] != "":
        chapitre = str(row['chapitreId']).split('_')[-1]
    else:
        chapitre = ""

    if row['sectionId'] != "":
        section = str(row['sectionId']).split('_')[-1]
    else:
        section = ""
    parties = len(str(row['parties']).split(','))
    articles = len(str(row['articles']).split(','))

    description = f"la sous-section {row['numero']} de la section {section} du chapitre {chapitre} du titre {titre} du {code} intitulé {row['titre']} contient : {parties} parties et {articles} articles ( {row['articles']})"
    return description


def partie_content(row, code):

    titre = row['titreId']
    if row['chapitreId']:
        chapitre = str(row['chapitreId']).split('_')[-1]
    else:
        chapitre = ""

    if row['sectionId']:
        section = str(row['sectionId']).split('_')[-1]
    else:
        section = ""

    if row['sousSectionId']:
        sousSection = str(row['sousSectionId']).split('_')[-1]
    else:
        sousSection = ""

    articles = len(str(row['articles']).split(','))

    description = f"la partie {row['numero']} de la sous-section {sousSection} de la section {section} du chapitre {chapitre} du titre {titre} du {code} intitulé {row['titre']} contient : {articles} articles ( {row['articles']})"
    return description


class CodeDesDouanes(BaseDouaneAI):
    BASE_COLLECTION = "articles"
    TITRES_DF = "titres"
    CHAPITRES_DF = "chapitres"
    SECTIONS_DF = "sections"
    SOUS_SECTIONS_DF = "sous_sections"
    PARTIES_DF = "parties"
    ARTICLES_DF = "articles"
    METADATA_DF = "metadata"

    CODE_ABBR: str = "CODE"
    CODE_DATA_TEXT_FILE_NAME: str = "code_des_douanes"

    def __init__(self):
        self.PREFIX = f"{self.CODE_DATA_TEXT_FILE_NAME}{self.PREFIX}"
        self.pre_prompt = self.pre_prompt + \
            "Tu reponds dans untyle académique en precisant les sources, evites à tout prix de te repeter dans ta réponse et ne fabrique pas de reponse si les textes douaniers ne le permettent pas.\n\n"
        super().__init__()


    def df(self, data: str = "articles") -> pd.DataFrame:
        root: str = self.data_frames_path
        abbr = self.CODE_ABBR
        try:
            return pd.read_json(pathlib.Path(f'{root}{data}_df.json'), orient='index')
        except:
            titres_df = pd.DataFrame(
                columns=['numero', 'titre', 'content', 'tokens_count'])
            chapitres_df = pd.DataFrame(
                columns=['titreId', 'numero', 'titre', 'content', 'tokens_count'])
            sections_df = pd.DataFrame(
                columns=['titreId', 'chapitreId', 'numero', 'titre', 'content', 'tokens_count'])
            sous_sections_df = pd.DataFrame(columns=[
                                            'titreId', 'chapitreId', 'sectionId', 'numero', 'titre', 'content', 'tokens_count'])
            parties_df = pd.DataFrame(columns=['titreId', 'chapitreId', 'sectionId',
                                               'sousSectionId', 'numero', 'titre', 'content', 'tokens_count'])
            articles_df = pd.DataFrame(
                columns=['numero', 'content', 'tokens_count',])

            with open(f'{root[:-1]}.txt', 'r',  encoding='utf-8') as file:
                code_json = json.loads(file.read())
            _titres_df = pd.DataFrame(
                code_json['titres'], columns=['numero', 'titre'])
            _chapitres_df = pd.DataFrame(code_json['chapitres'], columns=[
                'titreId', 'numero', 'titre'])
            _sections_df = pd.DataFrame(code_json['sections'], columns=[
                                        'titreId', 'chapitreId', 'numero', 'titre'])
            _sous_sections_df = pd.DataFrame(code_json['sousSections'], columns=[
                'titreId', 'chapitreId', 'sectionId', 'numero', 'titre'])
            _parties_df = pd.DataFrame(code_json['parties'], columns=[
                'titreId', 'chapitreId', 'sectionId', 'sousSectionId', 'numero', 'titre'])
            _articles_df = pd.DataFrame(code_json['articles'], columns=[
                                        "titreId", "chapitreId", "sectionId", "sousSectionId", "partieId", "numero", "titre", "definition", ])

            _titres_df['chapitres'] = _titres_df.apply(
                lambda row: ",".join(_chapitres_df[_chapitres_df['titreId'] == row['numero']]['numero'].to_list()), axis=1)
            _titres_df['sections'] = _titres_df.apply(
                lambda row: ",".join(_sections_df[_sections_df['titreId'] == row['numero']]['numero'].to_list()), axis=1)
            _titres_df['sousSections'] = _titres_df.apply(
                lambda row: ",".join(_sous_sections_df[_sous_sections_df['titreId'] == row['numero']]['numero'].to_list()), axis=1)
            _titres_df['parties'] = _titres_df.apply(
                lambda row: ",".join(_parties_df[_parties_df['titreId'] == row['numero']]['numero'].to_list()), axis=1)
            _titres_df['articles'] = _titres_df.apply(
                lambda row: ",".join(_articles_df[_articles_df['titreId'] == row['numero']]['numero'].to_list()), axis=1)
            _titres_df["content"] = _titres_df.apply(
                lambda row: titre_content(row, f'({abbr})'), axis=1)
            _titres_df["tokens_count"] = _titres_df.apply(
                lambda row: count_tokens(row['content']), axis=1)
            titres_df = pd.concat(
                [titres_df, _titres_df], ignore_index=True)
            titres_df.to_json(
                f'{root}{self.TITRES_DF}_df.json', orient='index')

            _chapitres_df['sections'] = _chapitres_df.apply(lambda row: ",".join(_sections_df[(_sections_df['titreId'] == row['titreId']) & (
                _sections_df['chapitreId'] == f"titre_{row['titreId']}_chapitre_{row['numero']}")]['numero'].to_list()), axis=1)
            _chapitres_df['sousSections'] = _chapitres_df.apply(lambda row: ",".join(_sous_sections_df[(_sous_sections_df['titreId'] == row['titreId']) & (
                _sous_sections_df['chapitreId'] == f"titre_{row['titreId']}_chapitre_{row['numero']}")]['numero'].to_list()), axis=1)
            _chapitres_df['parties'] = _chapitres_df.apply(lambda row: ",".join(_parties_df[(_parties_df['titreId'] == row['titreId']) & (
                _parties_df['chapitreId'] == f"titre_{row['titreId']}_chapitre_{row['numero']}")]['numero'].to_list()), axis=1)
            _chapitres_df['articles'] = _chapitres_df.apply(lambda row: ",".join(_articles_df[(_articles_df['titreId'] == row['titreId']) & (
                _articles_df['chapitreId'] == f"titre_{row['titreId']}_chapitre_{row['numero']}")]['numero'].to_list()), axis=1)
            _chapitres_df["content"] = _chapitres_df.apply(
                lambda row: chapitre_content(row, f'({abbr})'), axis=1)
            _chapitres_df["tokens_count"] = _chapitres_df.apply(
                lambda row: count_tokens(row['content']), axis=1)
            chapitres_df = pd.concat(
                [chapitres_df, _chapitres_df],  ignore_index=True)
            chapitres_df.to_json(
                f'{root}{self.CHAPITRES_DF}_df.json', orient='index')

            _sections_df['sousSections'] = _sections_df.apply(lambda row: ",".join(_sous_sections_df[(
                _sous_sections_df['sectionId'] == f"{row['chapitreId']}_section_{row['numero']}")]['numero'].to_list()), axis=1)
            _sections_df['parties'] = _sections_df.apply(lambda row: ",".join(_parties_df[(
                _parties_df['sectionId'] == f"{row['chapitreId']}_section_{row['numero']}")]['numero'].to_list()), axis=1)
            _sections_df['articles'] = _sections_df.apply(lambda row: ",".join(_articles_df[(
                _articles_df['sectionId'] == f"{row['chapitreId']}_section_{row['numero']}")]['numero'].to_list()), axis=1)
            _sections_df["content"] = _sections_df.apply(
                lambda row: section_content(row, f'({abbr})'), axis=1)
            _sections_df["tokens_count"] = _sections_df.apply(
                lambda row: count_tokens(row['content']), axis=1)
            sections_df = pd.concat(
                [sections_df, _sections_df], ignore_index=True)
            sections_df.to_json(
                f'{root}{self.SECTIONS_DF}_df.json', orient='index')

            _sous_sections_df['parties'] = _sous_sections_df.apply(lambda row: ",".join(_parties_df[(
                _parties_df['sousSectionId'] == f"{row['sectionId']}_sous_section_{row['numero']}")]['numero'].to_list()), axis=1)
            _sous_sections_df['articles'] = _sous_sections_df.apply(lambda row: ",".join(
                _articles_df[_articles_df['sousSectionId'] == f"{row['sectionId']}_sous_section_{row['numero']}"]['numero'].to_list()), axis=1)
            _sous_sections_df["content"] = _sous_sections_df.apply(
                lambda row: sous_section_content(row, f'({abbr})'), axis=1)
            _sous_sections_df["tokens_count"] = _sous_sections_df.apply(
                lambda row: count_tokens(row['content']), axis=1)
            sous_sections_df = pd.concat(
                [sous_sections_df, _sous_sections_df], ignore_index=True)
            sous_sections_df.to_json(
                f'{root}{self.SOUS_SECTIONS_DF}_df.json', orient='index')

            _parties_df['articles'] = _parties_df.apply(lambda row: ",".join(_articles_df[(
                _articles_df['partieId'] == f"sous_section_{row['sousSectionId']}_partie_{row['numero']}")]['numero'].to_list()), axis=1)
            _parties_df["content"] = _parties_df.apply(
                lambda row: partie_content(row, f'({abbr})'), axis=1)
            _parties_df["tokens_count"] = _parties_df.apply(
                lambda row: count_tokens(row['content']), axis=1)
            parties_df = pd.concat(
                [parties_df, _parties_df], ignore_index=True)
            parties_df.to_json(
                f'{root}{self.PARTIES_DF}_df.json', orient='index')

            _articles_df = pd.DataFrame.from_dict(code_json['articles']).loc[:,  [
                'numero', 'definition', "titre"]]
            _articles_df["content"] = "Article " + _articles_df.numero + \
                _articles_df.titre.apply(
                    articleTitle) + "(" + abbr + ") -->" + _articles_df.definition
            _articles_df["tokens_count"] = _articles_df.content.apply(
                count_tokens)
            articles_df = pd.concat(
                [articles_df, _articles_df], ignore_index=True)
            articles_df.to_json(
                f'{root}{self.ARTICLES_DF}_df.json', orient='index')
            
            metadata_df = pd.DataFrame(columns=['type', 'titreId', 'chapitreId', 'sectionId',
                                                'sousSectionId', 'partieId', 'numero', 'titre', 'content', 'tokens_count'], dtype=str)

            data_frames = [titres_df, chapitres_df,
                           sections_df, sous_sections_df, parties_df]
            for name, df in zip(['titres', 'chapitres', 'sections', 'sousSections', 'parties'], data_frames):
                metadata_df = pd.concat(
                    [metadata_df, df.assign(type=name)], ignore_index=True)

            metadata_df[["content", "tokens_count"]].to_json(
                f"{root}{self.METADATA_DF}_df.json", orient="index")

            df: pd.DataFrame | None = None
            if data == "titres":
                df = titres_df
            elif data == "chapitres":
                df = chapitres_df
            elif data == "sections":
                df = sections_df
            elif data == "sous_sections":
                df = sous_sections_df
            elif data == "parties":
                df = parties_df
            elif data == "articles":
                df = articles_df
            return df

    def articles_embeddings(self, _df: pd.DataFrame | None = None):
        return self.load_embeddings("articles", _df=_df)

    def articles_df(self):
        return self.df(self.ARTICLES_DF)

    def metadata_embeddings(self):
        return self.load_embeddings("metadata")

    def metadata_df(self):
        return self.df(self.METADATA_DF)



class CodeDesDouanesNational(CodeDesDouanes):
    PAYS : str= ""
    ANNEE : str = ""
    CODE_DATA_TEXT_FILE_NAME = "cdn"
    CODE_ABBR = "CDN"
    DU_PAYS: str = ""

    def __init__(self):
        self.PREFIX = f"_{self.PAYS}_{self.ANNEE}_"
        self.pre_prompt = f"""Tu est un agent du service des douanes {self.DU_PAYS}. tu repponds de facon précise, concise  et complete aux questions douanières en se basant uniquement sur le Code Des Douanes Nationale {self.DU_PAYS} (CDN)."""

        super().__init__()


class CodeDesDouanesCommunautaire(CodeDesDouanes):
    COMMUAUTE : str = ""
    ANNEE : str = ""
    CODE_DATA_TEXT_FILE_NAME : str = "cdc"
    CODE_ABBR : str = "CDC"
    DE_LA_COMMUNAUTE = ""

    def __init__(self):
        self.PREFIX = f"_{self.COMMUAUTE}_{self.ANNEE}_"
        self.pre_prompt = f"""Tu est un agent du service des douanes {self.DE_LA_COMMUNAUTE}. tu repponds de facon précise, concise  et complete aux questions douanières en se basant uniquement sur le Code Des Douanes Communautaire {self.DE_LA_COMMUNAUTE} (CDC)."""

        super().__init__()
    

class CodesDesDouanesNationalEtCommunautaire(CodeDesDouanes):
    COMMUAUTE : str = ""
    PAYS: str = ""
    ANNEE : str = ""

    DE_LA_COMMUNAUTE = ""
    DU_PAYS = ""

    cdn : CodeDesDouanesNational
    cdc: CodeDesDouanesCommunautaire

    def __init__(self):
        self.PREFIX = f"cdn_{self.PAYS}_{self.COMMUAUTE}_{self.ANNEE}_"
        self.pre_prompt = f"""Tu est un agent du service des douanes {self.DU_PAYS}. tu repponds de facon précise, concise  et complete aux questions douanières en se basant uniquement sur le Code Des Douanes Communautaire {self.DE_LA_COMMUNAUTE} (CDC) et le Code des Douanes National {self.DU_PAYS} (CDN)."""
        self.cdn.DU_PAYS = self.DU_PAYS
        self.cdc.DE_LA_COMMUNAUTE = self.DE_LA_COMMUNAUTE

        super().__init__()

    

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, api_key: str):
        self._api_key = api_key
        self.cdn.api_key = api_key
        self.cdc.api_key = api_key
        self.embedding_functions = self.cdn.embedding_functions 

    def df(self, data: str = "articles"):
        return pd.concat([
            self.cdn.df(data),
            self.cdc.df(data)
        ])

    def load_embeddings(self, data: str, _df: pd.DataFrame | None = None):
        merged_dict = {}
        index = 0
        for key, value in self.cdn.load_embeddings(data).items():
            merged_dict[str(key) if index ==0 else str(index)] = value
            index += 1

        for key, value in self.cdc.load_embeddings(data).items():
            merged_dict[str(index)] = value
            index += 1
        return merged_dict
    


