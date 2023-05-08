import re
import pathlib
import openai
import pandas as pd
from gpt3 import COMPLETIONS_MODEL, SEPARATOR, _compute_or_load_doc_embeddings, count_tokens, separator_len
from chromadb.api import Where, WhereDocument, QueryResult, Collection
from chromadb.api.types import Embedding
from vectorstore import chromadb, BaseDouaneData
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction


def section_content(row: pd.Series):
    content = f"Section {row.number} - ({row.title}). :\n{row.note}\n"
    return content


def split_text_by_char_limit(text : str | None = None, max_char_token_chunk: int = 500):
    chunks = []
    if not text:
        return chunks
    current_chunk = ""
    for line in text.split("\n"):
        if count_tokens(current_chunk) + count_tokens(line) + 1 > max_char_token_chunk:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += "\n"
            current_chunk += line
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

class TecSection():
    def __init__(self, number: str | None = None, title: str | None = None, note: str | None = None):
        self.number = number
        self.title = title
        self.note = note

class TecChapitre(TecSection):
    def __init__(self, number: str | None = None, title: str | None = None, note: str | None = None, section : str | None = None):
        super().__init__(number, title, note)
        self.section: section

class TecItem():
    def __init__(self, position: str | None = None, nts: str | None = None, designation: str | None = None, unite: str | None = None, dd: str | None = None, rs: str | None = None):
        self.position = position
        self.nts = nts
        self.designation = designation
        self.unite = unite
        self.dd = dd
        self.rs = rs



class Tec2022(BaseDouaneData):
    SECTIONS_DF= "sections"
    CHAPISTES_DF= "chapitres"
    ITEMS_DF= "items"

    data_frames_path: str = "data/"
    embeddings_path: str = "embeddings/"
    embedding_functions: OpenAIEmbeddingFunction

    pre_prompt = "AGENT0 est un douanier Togolais. SuperDouanier est un assistant basé sur GPT3 qui donnes des informations de facon précise en se basant uniquement sur le Tarif Exterieur Commun de la CEDEAO (TEC) dans le style académique. SuperDouanier evite à tout prix de se repeter dans sa réponse. Si la demande de AGENT0 ne demande pas de generer des question, SuperDouanier ne le fais pas. SuperDouanier ne mentionne pas AGENT0 dans ses reponse.\n\nInformations connues du SuperDouanier à partir du TEC : \n\n"

    def __init__(self):
        super().__init__()
        self.data_frames_path = __file__.replace("tec2022.py", "")+"data/"
        self.embeddings_path = __file__.replace("tec2022.py", "")+"embeddings/"
    
    def load_data(self, name: str = "items"):
        root: str = self.data_frames_path
        return pd.read_json(
            pathlib.Path(f'{root}{name}_df.json'), orient='records',
        )

    
    def df(self, data: str = "items") -> pd.DataFrame:
        root: str = self.data_frames_path
        try:
            tec_df = pd.read_json(
                pathlib.Path(f'{root}{data}_df_parsed.json'), orient='records',
            );
        except:
            sections_df =  self.load_data("sections")
            chapitres_df =  self.load_data("chapitres")
            items_df =  self.load_data("items")

    
    @property
    def chapitres_data(self) -> pd.DataFrame: 
        _df = self.load_data("chapitres")
        _df["number"] = _df.number.apply(lambda x: len(str(x)) == 1 and "0"+str(x) or str(x))
        return _df

    @property
    def sections_data(self) -> pd.DataFrame:
        return self.load_data("sections")
    
    @property
    def items_data(self) -> pd.DataFrame:
        _df =  self.load_data("items")
        _df["position"] = _df.position.apply(lambda x: x.replace(".", "").strip())
        _df["nts"] = _df.nts.apply(lambda x: x.replace(".", "").strip())
        return _df

    def get_position_items(self, position: str):
        position_items: list[pd.Series] = []
        in_position = False
        position_prefix = position.replace(".", "")
        for _, row in self.items_data[::-1].iterrows():
            if row.nts.startswith(position_prefix):
                in_position = True
                position_items.append(row)
            elif in_position  and row.nts != "":
                break
            elif in_position and row.nts == "":
                position_items.append(row)
        return position_items[::-1]
    
    def _get_section_info(self, number: str, use_gpt4 = False):
        try:
            item_section = self.sections_data[self.sections_data.number == number].iloc[0]
        except:
            return None
        item_chapitres = self.chapitres_data[(self.chapitres_data.section == number) ]
        chapitres = [
            f"{row.number} -> {row.title} " for (_, row) in item_chapitres.iterrows()]
        info = f"Section {item_section.number} - ({item_section.title}).\nChapitres:\n"
        info += "\n".join(chapitres)
        
        notes_chunks = split_text_by_char_limit(item_section.note, 10)
        notes = ""
        if len(notes_chunks) > 0:
            for _, note in enumerate(notes_chunks):
                _info = f"{notes}\n{note}"
                if use_gpt4:
                    notes = _info
                elif count_tokens(f"{info}\n\nNotes:\n{_info}") > 1900:
                    break
                else:
                    notes = _info
        if len(notes) > 0:
            info += f"\n\nNotes:\n{notes}"
        return info

    def _get_chapitre_info(self, nts: str, use_gpt4=False):
        nts = nts.replace(".", "")
        try:
            item_chapitre = self.chapitres_data[self.chapitres_data.number == nts[:2]].iloc[0]
            item_section = self.sections_data[self.sections_data.number == item_chapitre.section].iloc[0]
        except:
            return None
        item_positions = self.items_data[(
            self.items_data.position.apply(lambda x: x[:2]) == nts[:2])]
        positions = [
            f"{row.position} -> {row.designation} " for (_, row) in item_positions.iterrows()]
        info = f"Section {item_section.number} - ({item_section.title}).\nChapitre {item_chapitre.number} - ({item_chapitre.title}).\n\nPositions:\n"
        info += "\n".join(positions)

        notes_chunks = split_text_by_char_limit(item_chapitre.note, 10)
        notes = ""
        if len(notes_chunks) > 0:
            for _, note in enumerate(notes_chunks):
                _info = f"{notes}\n{note}"
                if use_gpt4:
                    notes = _info
                elif count_tokens(f"{info}\nNotes:\n{_info}") > 1900:
                    break
                else:
                    notes = _info
        if len(notes) > 0:
            info += f"\n\nNotes:\n{notes}"
        return info
    
    def _get_position_info(self, nts: str, use_gpt4 = False):
        nts = nts.replace(".", "")
        try:
            item_position = TecItem(
            **self.items_data[self.items_data.position == nts[:4]].iloc[0].to_dict())
        except:
            return None
        item_chapitre = self.chapitres_data[self.chapitres_data.number == nts[:2]].iloc[0]
        item_section = self.sections_data[self.sections_data.number ==
                                          item_chapitre.section].iloc[0]
        info = f"Section {item_section.number} - ({item_section.title}).\n"
        info += f"Chapitre {item_chapitre.number} - ({item_chapitre.title}).\n\nSOUS-POSITIONS:\n"
        
        info+= "Sous-position  \t| Désignation \t| Unite \t| DD (Drroits de douanes %) \t| RS (Rédevence Statistique %) \n"
        item_sous_positions = [TecItem(**item.to_dict()) for item in  self.get_position_items(item_position.position)]
        for item in item_sous_positions:
            item_info = f"{info}{item.nts} \t| {item.designation} \t| {item.unite} \t| {item.dd} \t| {item.rs} \n"
            if use_gpt4:
                info = item_info
            elif count_tokens(item_info) > 1900:
                break
            else:
                info = item_info
        return info

    def _get_nts_infp(self, nts: str):
        nts = nts.replace(".", "")
        item_chapitres = self.chapitres_data[self.chapitres_data.number == nts[:2]]
        try:
            item_chapitre = item_chapitres.iloc[0]

            item_section = self.sections_data[self.sections_data.number ==
                                          item_chapitre.section].iloc[0]
        except:
            return None
        
        parents : list[TecItem] = []
        nts_detected = False
        number_of_dash = 0
        for  _ , row in self.items_data[::-1].iterrows():
            tec_item= TecItem(**row.to_dict())
            _number_of_daash = tec_item.designation.split("\t")[0].count("-")
            if tec_item.position == nts[:4]:
                parents.append(tec_item)
                number_of_dash = 0
            elif tec_item.nts == nts or tec_item.nts.startswith(nts):
                nts_detected = True
                parents.append(tec_item)
                number_of_dash = _number_of_daash
            elif nts_detected:
                if (_number_of_daash == number_of_dash):
                    if ((tec_item.position != "") and  (not tec_item.position.startswith(nts[:2]))):
                        break
                    parents.append(tec_item)
                elif _number_of_daash < number_of_dash :
                    parents.append(tec_item)
                    number_of_dash = _number_of_daash
                
        parents = parents[::-1]
        info = f"Section {item_section.number} - ({item_section.title}).\n"
        info += f"Chapitre {item_chapitre.number} - ({item_chapitre.title}).\n"
        for index, parent in enumerate(parents):
            if index == len(parents) - 1:
                info += f"{parent.nts if parent.position == '' else parent.position} \t{parent.designation}.\n"
                info += f"\nAutures informations sur {parent.nts}:\nUnité = {parent.unite}.\n"
                info += f"DD: {parent.dd}% de la valeur en douane.\n"
                info += f"RS (Redevence statistique): {parent.rs}%"
            else:
                info += f"{parent.nts if parent.position == '' else parent.position}\t{parent.designation}.\n"
        
        return info if len(parents) > 0 else None
    
    def get_info(self, nts: str, stream : bool = False, show_prompt: bool = False, prompt_only: bool = False, use_gpt4: bool = False):
        def error_message():
            error = "Je n'ai pas pu trouver les informations que vous cherchez. Veuillez vérifier le numéro de nomenclature et réessayer."
            if stream:
               return  (w for w in error.split(" "))
            else:
                return error
        
        nts = nts.replace(".", "").strip()
        nts_len = len(nts)
        info: str | None = None
        numeros_sections = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI"]
        if (nts in numeros_sections ):
            data_label = "Section"
            info = self._get_section_info(nts, use_gpt4 = use_gpt4)
        else:
            try:
                if int(nts) != 0:
                    if (nts_len >= 6):
                        nts = nts[:min(nts_len, 8)]
                        data_label = "Sous position"
                        info = self._get_nts_infp(nts)
                    elif nts_len >= 4:
                        nts = nts[:4]
                        data_label = "Position"
                        info = self._get_position_info(nts, use_gpt4=use_gpt4)
                    elif nts_len >= 2:
                        nts = nts[:2]
                        data_label = "Chapitre"
                        info = self._get_chapitre_info(nts, use_gpt4=use_gpt4)
                    elif nts_len == 1:
                        try:
                            nts = f"0{nts}"
                            data_label = "Chapitre"
                            info = self._get_chapitre_info(nts, use_gpt4=use_gpt4)
                        except:
                            pass

            except:
                return error_message()

        
       
        if info is None:
            return error_message()

        prompt = self.pre_prompt
        prompt += info
        prompt += ".\n\n"


        if not prompt_only:
            info += f"\n\nNB: RS= Rédevence statistique.\nUne position avec un nombre de '-' au début de la désignation est une position enfant de la position immediate avec un nombre de '-' au début de la désignation moins 1.\n\n"
            prompt += f"AGENT0: Informations sur '{data_label} {nts}'.\n SuperDouanier: "

        if show_prompt:
            print(prompt)

        if prompt_only:
            return prompt
        openai.api_key = self.api_key

        prompt_parts =prompt.split("AGENT0: ")

        response = openai.ChatCompletion.create(
            model="gpt-4" if (len(nts) == 2 and use_gpt4 == True and count_tokens(prompt) > 1500) else COMPLETIONS_MODEL,
            temperature=0,
            messages=[
                {'role': "system", 'content': prompt_parts[0]},
                {"role": "user", "content": "AGENT0: "+prompt_parts[1]},
            ],
            stream=stream,
            max_tokens=3000 - count_tokens(prompt),
        )
        if(stream):
            return response
        else:
            return response["choices"][0]["message"]["content"]

        





