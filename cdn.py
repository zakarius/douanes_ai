import json
import pathlib
import pandas as pd
from gpt3 import  SEPARATOR, count_tokens, separator_len
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from vectorstore import BaseDouaneData

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


class CodesDesDouanes(BaseDouaneData):
    CODES_DF = "codes_des_douanes"
    TITRES_DF = "titres"
    CHAPITRES_DF = "chapitres"
    SECTIONS_DF = "sections"
    SOUS_SECTIONS_DF = "sous_sections"
    PARTIES_DF = "parties"
    ARTICLES_DF = "articles"
    METADATA_DF = "metadata"

    SUFFIX: str = 'codes_des_douanes'


    data_frames_path: str = "data/"
    embeddings_path: str = "embeddings/"

    embedding_functions: OpenAIEmbeddingFunction

    def __init__(self):
        super().__init__()
        self.data_frames_path = __file__.replace("cdn.py", "")+"data/"
        self.embeddings_path = __file__.replace("cdn.py", "")+"embeddings/"

    def df(self, data: str = "articles") -> pd.DataFrame:
        root: str = self.data_frames_path
        try:
            codes_des_douanes_df = pd.read_json(
                pathlib.Path(f'{root}{data}_df.json'), orient='index',
            )
            return codes_des_douanes_df
        except:
            codesDesDouanes = [("CDN", 'codeDesDouanesNational2017'),
                               ('CDC', 'codeDesDouanesCedeao2017')]

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

            for abbr, code in codesDesDouanes:
                with open(f'{root}{code}.txt', 'r',  encoding='utf-8') as file:
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

    def construct_prompt(self, question: str, n_result: int = 5
                         ) -> str:
        header_prefix = """AGENT0 est un douanier Togolais. SuperDouanier est un assistant basé sur GPT3. qui repponds de facon précise, concise  et complete aux questions douanières en se basant uniquement sur le Codes Des Douanes Nationale du Togo (CDN) et le Codes Des Douanes Communautaire de la CEDEAO (CDC), dans le style académique. SuperDouanier est instruit par l'inspecteur des douanes Bilali ZAKARI disponible à l'adresse bilal@zakarius.com et sur le +22892108274 pour toute information complementaire. SuperDouanier precise les sources dans sa réponse, priorise les sources du CDN sur celles du CDC, evite à tout prix de se repeter dans sa réponse et ne fabrique pas de reponse si les textes douanier ne le permettent pas. Si la demande de AGENT0 ne demande pas de generer des question, SuperDouanier ne le fais pas.\n\n"""

        query_embedding = self.embedding_functions([question])[0]

        header = ""

        sources = [self.ARTICLES_DF]

        MAX_PROMPT_LEN = 2024 - \
            count_tokens(header_prefix) - \
            count_tokens("\n\n AGENT0: ""\n SuperDouanier:")

        for source in sources:
            chosen_items = []
            chosen_item_len = 0

            query_result = self.search(
                collection=source,
                query_embeddings=query_embedding,
                n_result=n_result
            )
            best_items: list[str] = query_result["documents"][0]
            for item in best_items:
                item = item.replace("\n", " ").replace("##LINE## ", "\n")
                chosen_item_len += count_tokens(item) + separator_len()

                if chosen_item_len < MAX_PROMPT_LEN:
                    try:
                        chosen_items.append(SEPARATOR + item)
                    except:
                        pass

            if len(chosen_items) > 0:
                header += f"\n\n{source}".upper()
                header += "\n" + "".join(chosen_items)

        return header_prefix + header + "\n\n AGENT0: " + question + "\n SuperDouanier:"