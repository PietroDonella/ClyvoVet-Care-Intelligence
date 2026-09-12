from __future__ import annotations

import json
from pathlib import Path

from . import ia_generativa, motor_regras, recomendador
from .modelos import InsightPet, LeituraIoT, Pet


class CareIntelligence:
    """Orquestra regras + recomendação + geração de linguagem para um pet."""

    def __init__(self, pasta_dados: Path):
        clinica = json.loads((pasta_dados / "base_clinica.json").read_text(encoding="utf-8"))
        iot = json.loads((pasta_dados / "leituras_iot.json").read_text(encoding="utf-8"))
        self.tutores = {t["id_tutor"]: t for t in clinica["tutores"]}
        self.pets = [self._montar_pet(p) for p in clinica["pets"]]
        self.pets_por_id = {p.id_pet: p for p in self.pets}
        self.pets_por_rfid = {p.rfid_uid.upper(): p for p in self.pets}
        self.prontuarios = clinica["prontuarios"]
        self.consultas = clinica["consultas"]
        self.vacinas = clinica["vacinas"]
        self.medicamentos = clinica["medicamentos"]
        self.leituras = [LeituraIoT(**item) for item in iot["leituras"]]

    def _montar_pet(self, bruto: dict) -> Pet:
        tutor = self.tutores[bruto["id_tutor"]]
        return Pet(
            id_pet=bruto["id_pet"],
            id_tutor=bruto["id_tutor"],
            nome=bruto["nome"],
            especie=bruto["especie"],
            cor=bruto["cor"],
            idade=bruto["idade"],
            peso=bruto["peso"],
            rfid_uid=bruto["rfid_uid"],
            status_internacao=bruto["status_internacao"],
            gaiola=bruto["gaiola"],
            comportamento=bruto["comportamento"],
            tutor_nome=tutor["nome"],
            tutor_telefone=tutor["telefone"],
        )

    def analisar_pet(self, id_pet: int) -> InsightPet:
        pet = self.pets_por_id[id_pet]
        leitura = next((l for l in self.leituras if l.pet_esperado_id == pet.id_pet), None)

        alertas = []
        score = 0
        internado = pet.status_internacao == "Internado"

        if leitura is not None:
            score_iot, alertas_iot = motor_regras.avaliar_ambiente(pet, leitura)
            score += score_iot
            alertas.extend(alertas_iot)
            alertas.extend(motor_regras.avaliar_identificacao(pet, self.pets_por_rfid, leitura))

        tem_critico = any(a.nivel == "critico" for a in alertas)
        if tem_critico:
            score = max(score, 90)

        nivel = motor_regras.nivel_de_score(score, tem_critico)
        _, _, _, _, faixa = motor_regras.faixa_conforto(pet)

        clima_fora_faixa = any(a.codigo in {"IOT_TERMICO", "IOT_UMIDADE"} for a in alertas)
        identidade_divergente = any(
            a.codigo in {"RFID_TROCA_PACIENTE", "RFID_DESCONHECIDO"} for a in alertas
        )
        recs = recomendador.recomendar(
            pet=pet,
            vacinas=self.vacinas,
            prontuarios=self.prontuarios,
            consultas=self.consultas,
            medicamentos=self.medicamentos,
            internado=internado,
            nivel_risco=nivel,
            clima_fora_faixa=clima_fora_faixa,
            identidade_divergente=identidade_divergente,
        )

        if tem_critico:
            acao = "Conferir identidade RFID e interromper procedimento até validar o paciente."
        elif nivel == "alto":
            acao = "Priorizar este animal na ronda de internação e ajustar temperatura/umidade da gaiola."
        elif recs:
            acao = f"Oferecer ao tutor: {recs[0].servico}."
        else:
            acao = "Manter acompanhamento de rotina."

        insight = InsightPet(
            pet=pet,
            score_risco=min(score, 100),
            nivel_risco=nivel,
            faixa_conforto=faixa,
            internado=internado,
            alertas=alertas,
            recomendacoes=recs,
            acao_priorizada=acao,
        )

        pront = next((p for p in self.prontuarios if p.get("id_pet") == pet.id_pet), None)
        meds = [m for m in self.medicamentos if m["id_pet"] == pet.id_pet and m.get("em_uso")]
        insight.mensagem_tutor = ia_generativa.mensagem_tutor(pet, insight)
        insight.resumo_clinico = ia_generativa.resumo_clinico(pet, insight, pront, meds)
        return insight

    def fila_prioridade(self) -> list[InsightPet]:
        insights = [self.analisar_pet(p.id_pet) for p in self.pets]
        ordem = {"critico": 0, "alto": 1, "medio": 2, "baixo": 3}
        return sorted(insights, key=lambda i: (ordem[i.nivel_risco], -i.score_risco, i.pet.nome))
