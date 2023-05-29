
from langchain.chat_models import ChatOpenAI
from langchain.tools import Tool
from langchain.agents import AgentType, initialize_agent, AgentExecutor
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


from douanes.utils import *


class BaseChainedAi():
    _api_key: str | None = None
    _codeDesDouanes: CodeDesDouanes
    _tec: TarifExterieurCommun
    _fiche_valeur: FicheValeurs
    _fiscalite: FiscaliteDouaniere
    _regime: RegimeEconomique

    _llm: ChatOpenAI
    streaming: bool

    def __init__(self,
                 code: CodeDesDouanes,
                 tec: TarifExterieurCommun,
                 fiche_valeur: FicheValeurs,
                 fiscalite: FiscaliteDouaniere,
                 regime: RegimeEconomique,
                 streaming: bool = False
                 ) -> None:
        self._codeDesDouanes = code
        self._tec = tec
        self._fiche_valeur = fiche_valeur
        self._fiscalite = fiscalite
        self._regime = regime
        self.streaming = streaming

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, api_key: str):
        self._api_key = api_key
        self._codeDesDouanes.api_key = api_key
        self._tec.api_key = api_key
        self._fiche_valeur.api_key = api_key
        self._fiscalite.api_key = api_key
        self._regime.api_key = api_key

        self._llm = ChatOpenAI(
            temperature=0,
            streaming=self.streaming,
            callbacks=[StreamingStdOutCallbackHandler()],
            openai_api_key=api_key,
        )

    @property
    def codeDesDouanes(self) -> CodeDesDouanes:
        return self._codeDesDouanes

    @property
    def tec(self) -> TarifExterieurCommun:
        return self._tec

    @property
    def fiche_valeur(self) -> FicheValeurs:
        return self._fiche_valeur

    @property
    def fiscalite(self) -> FiscaliteDouaniere:
        return self._fiscalite

    @property
    def regime(self) -> RegimeEconomique:
        return self._regime

    @property
    def llm(self) -> ChatOpenAI:
        return self._llm

    @property
    def tools(self) -> list[Tool]:
        code_des_douanes = self.codeDesDouanes
        tec = self.tec
        fiche_valeur = self.fiche_valeur
        fiscalite = self.fiscalite
        regime = self.regime

        return [
            Tool.from_function(
                func=code_des_douanes.get_info,
                name="Code des douanes",
                description="Recherche dans le code des douanes",
            ),
            Tool.from_function(
                func=tec.answer,
                name="Tarif extérieur commun",
                description="Recherche informations dans le tarif extérieur commun",
            ),
            # Tool.from_function(
            #     func=fiche_valeur.answer,
            #     name="Fiche valeur",
            #     description="Recherche dans la fiche valeur de référence",
            # ),
            Tool.from_function(
                func=fiscalite.chercher_taxes_appliquables,
                name="Taxes applicables",
                description="Chercher les taxes applicables",
            ),
            # Tool.from_function(
            #     func=fiscalite.get_info,
            #     name="Fiscalité douanière",
            #     description="Recherche dans la fiscalité douanière",
            # ),
            Tool.from_function(
                func=fiscalite.infos_sur_taxes_applicables,
                name="Taxes",
                description="Chercher les informations sur les taxes applicables",
            ),
            # Tool.from_function(
            #     func=regime.get_info,
            #     name="Régime économique",
            #     description="Recherche les informations sur les régimes économiques et les codes additionnels",
            # ),
        ]

    @property
    def agent(self) -> AgentExecutor:

        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
        )

    def answer(self, question: str) -> str:

        return self.agent.run(question)
