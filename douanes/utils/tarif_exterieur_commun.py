import pathlib
import openai
import pandas as pd
from .base_douanes_ai import BaseDouaneAI
from gpt3 import COMPLETIONS_MODEL, count_tokens


def section_content(row: pd.Series):
    content = f"Section {row.number} - ({row.title}). :\n{row.note}\n"
    return content


def split_text_by_char_limit(text: str | None = None, max_char_token_chunk: int = 500):
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
    content: str
    def __init__(self, number: str | None = None, title: str | None = None, note: str | None = None):
        self.number = number
        self.title = title
        self.note = note

    

class TecChapitre(TecSection):
    def __init__(self, number: str | None = None, title: str | None = None, note: str | None = None, section: str | None = None):
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

    def content(self):
        return f"{self.nts}|{self.designation}|{self.unite}|{self.dd}|{self.rs}"


class TarifExterieurCommun(BaseDouaneAI):
    SECTIONS_DF = "sections"
    CHAPISTES_DF = "chapitres"
    ITEMS_DF = "items"
    NOTES_DF = "notes"
    COMMUNAUTE= "communaute"
    DE_LA_COMMUNAUTE = "de la commuanuté"
    ANNEE = ""
    PREFIX = "tec"
    
    BASE_COLLECTION = "all"


    def __init__(self, ):
        self.pre_prompt = f"Tu est un assistant basé sur GPT3 qui aide les douaniers à bien classer les marchandises dans le Tarif Exterieur Commun {self.DE_LA_COMMUNAUTE} (TEC). Tu evite à tout prix de se repeter dans sa réponse. Tu as des informations sur les sections, chapitres, posiions et sous-positions du TEC, les chapitres de section,les positions des chapitres et les sous-positions des positions. Pour chaque posion, tu connais sa Nomenclature Tarifaire et Statisqtique (NTS), la designation, l'unité d'avaluation de la valeur en douane, le taux des DD (droits des douanes) et le taux de RS (redevence statistique) applicaples en %.  Quand tu reussit à bien classer une marchandise, tu preise l'unité d'evaluation ainsi que les taux de DD et RS appliquables. \n\nInformations des TEC dont tu dispose : \n\n"
        self.PREFIX = f"tec_{self.COMMUNAUTE}_{self.ANNEE}_"
        super().__init__()


    def load_data(self, name: str = "items"):
        root: str = self.data_frames_path
        return pd.read_json(
            pathlib.Path(f'{root}{name}_df.json'), orient='records',
        )
    
    def _df(self, data: str = "positions") -> pd.DataFrame:
        root: str = self.data_frames_path
        data_path = pathlib.Path(f'{root}{data}_indexed_df.json')
        try:
            return pd.read_json(data_path, orient='index',)
        except:
            if data == "notes":
                _df = self.notes_data
            elif data == "sections":
                _df = self.sections_data
                _df["content"] = _df.apply(lambda row: self._get_section_info(row.number, True), axis=1)
            elif data == "chapitres":
                _df = self.chapitres_data
                _df["content"] = _df.apply(lambda row: self._get_chapitre_info(row.number, content=True), axis=1)
            elif data == "positions":
                _df = self.items_data[self.items_data.position != ""]
                _df["content"] = _df.apply(
                    lambda row: self._get_position_info(row.position, content=True), axis=1)
            else:
                _df = self.items_data[self.items_data.nts != ""]
                _df["content"] = _df.apply(lambda row : self._get_nts_infp(row.nts), axis=1)
            _df = _df[["content"]]
            _df.to_json(data_path, orient="index")
            return _df

    def df(self, data: str = "all"):
        if data == "all":
            return pd.concat([
                self._df("notes"),
                self._df("sections"),
                self._df("chapitres"),
                self._df("positions"),
            ])
        return self._df(data)

    def load_embeddings(self, data: str = "all", _df: pd.DataFrame | None = None):
        if data != 'all':
            return super().load_embeddings(data, _df)
        
        merged_dict = {}
        index = 0
        for key, value in self.load_embeddings("notes").items():
            merged_dict[str(key) if index == 0 else str(index)] = value
            index += 1
        for key, value in self.load_embeddings("sections").items():
            merged_dict[str(index)] = value
            index += 1

        for key, value in self.load_embeddings("chapitres").items():
            merged_dict[str(index)] = value
            index += 1
        
        for key, value in self.load_embeddings("positions").items():
            merged_dict[str(index)] = value
            index += 1
        return merged_dict

    @property
    def regles_generales(self):
        with open(self.data_frames_path+"regles_generales.txt") as f:
           return  "\n".join(f.readlines())

    @property
    def chapitres_data(self) -> pd.DataFrame:
        _df = self.load_data("chapitres")
        _df["number"] = _df.number.apply(
            lambda x: len(str(x)) == 1 and "0"+str(x) or str(x))
        return _df

    @property
    def sections_data(self) -> pd.DataFrame:
        return self.load_data("sections")

    @property
    def items_data(self) -> pd.DataFrame:
        _df = self.load_data("items")
        _df["position"] = _df.position.apply(
            lambda x: x.replace(".", "").strip())
        _df["nts"] = _df.nts.apply(lambda x: x.replace(".", "").strip())
        return _df

    @property
    def notes_data(self) -> pd.DataFrame:
        rg_chunks = split_text_by_char_limit(self.regles_generales, 50)
        notes_sections = self.sections_data.apply(lambda row : "\n".join([f"Note Section {row.number} {chunk}"  for chunk in   split_text_by_char_limit(row.note, 50)]), axis=1)
        notes_chapitres = self.chapitres_data.apply(lambda row : "\n".join([f"Note Chapitre {row.number} {chunk}"  for chunk in   split_text_by_char_limit(row.note, 50)]), axis=1)
        notes: list[str] = [*rg_chunks, *notes_sections.to_list(), *notes_chapitres.to_list()]
        return pd.DataFrame(
            data=[note for note in  notes if note.strip() != ""],
            columns=["content"]
        )
        

        

    def get_position_items(self, position: str):
        position_items: list[pd.Series] = []
        in_position = False
        position_prefix = position.replace(".", "")
        for _, row in self.items_data[::-1].iterrows():
            if row.nts.startswith(position_prefix):
                in_position = True
                position_items.append(row)
            elif in_position and row.nts != "":
                break
            elif in_position and row.nts == "":
                position_items.append(row)
        return position_items[::-1]

    def _get_section_info(self, number: str, use_gpt4=False, content: bool = False):
        try:
            item_section = self.sections_data[self.sections_data.number ==
                                              number].iloc[0]
        except:
            return None
        item_chapitres = self.chapitres_data[(
            self.chapitres_data.section == number)]
        chapitres = [
            f"{row.number} -> {row.title} " for (_, row) in item_chapitres.iterrows()]
        info = f"Section {item_section.number} - ({item_section.title}).\nChapitres:\n"
        info += "\n".join(chapitres)

        if content:
            return info

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

    def _get_chapitre_info(self, nts: str, use_gpt4=False, content : bool = False):
        nts = nts.replace(".", "")
        try:
            item_chapitre = self.chapitres_data[self.chapitres_data.number ==
                                                nts[:2]].iloc[0]
            item_section = self.sections_data[self.sections_data.number ==
                                              item_chapitre.section].iloc[0]
        except:
            return None
        item_positions = self.items_data[(
            self.items_data.position.apply(lambda x: x[:2]) == nts[:2])]
        positions = [
            f"{row.position} -> {row.designation} " for (_, row) in item_positions.iterrows()]
        if content:
            info = ""
        else:
            info = f"Section {item_section.number} - ({item_section.title})."
        info+=f"\nChapitre {item_chapitre.number} - ({item_chapitre.title}).\n\nPositions:\n"
        info += "\n".join(positions)

        if content:
            return info

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

    def _get_position_info(self, nts: str, use_gpt4=False, content: bool =  False):
        nts = nts.replace(".", "")
        try:
            item_position = TecItem(
                **self.items_data[self.items_data.position == nts[:4]].iloc[0].to_dict())
        except:
            return None
        item_chapitre = self.chapitres_data[self.chapitres_data.number ==
                                            nts[:2]].iloc[0]
        item_section = self.sections_data[self.sections_data.number ==
                                          item_chapitre.section].iloc[0]
        if content:
            info = f"Position {item_position.position}: {item_position.designation}"
        else:
            info = f"Section {item_section.number} - ({item_section.title}).\n"
            info += f"Chapitre {item_chapitre.number} - ({item_chapitre.title}).\n\nSOUS-POSITIONS:\n"
            info += "Sous-position  \t| Désignation \t| Unite \t| DD (Drroits de douanes %) \t| RS (Rédevence Statistique %) \n"
        item_sous_positions = [TecItem(
            **item.to_dict()) for item in self.get_position_items(item_position.position)]
        for item in item_sous_positions:
            item_info = f"{info}{item.nts} \t| {item.designation} \t| {item.unite} \t| {item.dd} \t| {item.rs} \n"
            if use_gpt4 or content:
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

        parents: list[TecItem] = []
        nts_detected = False
        number_of_dash = 0
        for _, row in self.items_data[::-1].iterrows():
            tec_item = TecItem(**row.to_dict())
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
                    if ((tec_item.position != "") and (not tec_item.position.startswith(nts[:2]))):
                        break
                    parents.append(tec_item)
                elif _number_of_daash < number_of_dash:
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

    def get_info(
            self, 
            question: str, 
            completor: str = "open_ai",
            stream: bool = False, 
            show_prompt: bool = False,
            prompt_only: bool = False, 
            use_gpt4: bool = False,
            n_result: int = 10,
        ):
        def error_message():
            return self.answer(
                question=question,
                completor=completor,
                show_prompt=show_prompt,
                prompt_only=prompt_only,
                stream=stream,
                n_result=n_result,
            )

        nts = question.replace(".", "").strip()
        nts_len = len(nts)
        info: str | None = None
        numeros_sections = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
                            "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI"]
        if (nts in numeros_sections):
            data_label = "Section"
            info = self._get_section_info(nts, use_gpt4=use_gpt4)
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
                            info = self._get_chapitre_info(
                                nts, use_gpt4=use_gpt4)
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

        prompt_parts = prompt.split("AGENT0: ")

        response = openai.ChatCompletion.create(
            model="gpt-4" if (len(nts) == 2 and use_gpt4 ==
                              True and count_tokens(prompt) > 1500) else COMPLETIONS_MODEL,
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
