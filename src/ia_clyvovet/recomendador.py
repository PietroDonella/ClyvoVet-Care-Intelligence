"""Sistema de recomendação baseado em conteúdo (perfil + histórico).

Não é collaborative filtering: a clínica ainda não tem volume de
avaliações explícitas. A abordagem é content-based + regras de jornada,
o que funciona com o volume atual de prontuários, vacinas e IoT.
"""

from __future__ import annotations

from datetime import date

from .modelos import Pet, Recomendacao
from .motor_regras import faixa_etaria


def _vacinas_do_pet(vacinas: list[dict], id_pet: int) -> list[dict]:
    return [v for v in vacinas if v["id_pet"] == id_pet]


def _ultimo_prontuario(prontuarios: list[dict], id_pet: int) -> dict | None:
    itens = [p for p in prontuarios if p.get("id_pet") == id_pet]
    if not itens:
        return None
    return sorted(itens, key=lambda p: p["data_registro"], reverse=True)[0]


def recomendar(
    pet: Pet,
    vacinas: list[dict],
    prontuarios: list[dict],
    consultas: list[dict],
    medicamentos: list[dict],
    internado: bool,
    nivel_risco: str,
    clima_fora_faixa: bool,
    identidade_divergente: bool,
) -> list[Recomendacao]:
    recs: list[Recomendacao] = []
    hoje = date.fromisoformat("2026-09-11")
    etapa = faixa_etaria(pet)

    if identidade_divergente:
        recs.append(
            Recomendacao(
                servico="Conferência imediata de identidade na gaiola",
                motivo="RFID lido não corresponde ao pet alocado. Risco de procedimento no animal errado.",
                prioridade=1,
                publico="clinica",
            )
        )

    for vacina in _vacinas_do_pet(vacinas, pet.id_pet):
        status = vacina["status"]
        if status == "Vencida":
            recs.append(
                Recomendacao(
                    servico="Vacinação / atualização de protocolo",
                    motivo=f"{vacina['nome']} venceu em {vacina['validade']}.",
                    prioridade=1,
                    publico="clinica",
                )
            )
        elif status == "Reforco pendente":
            recs.append(
                Recomendacao(
                    servico="Retorno para reforço vacinal",
                    motivo=f"{vacina['nome']} exige próxima dose (validade {vacina['validade']}).",
                    prioridade=1,
                    publico="tutor",
                )
            )

    pront = _ultimo_prontuario(prontuarios, pet.id_pet)
    if pront:
        texto = pront["diagnostico"].lower()
        if "sobrepeso" in texto or "dieta" in texto:
            recs.append(
                Recomendacao(
                    servico="Consulta nutricional",
                    motivo="Prontuário registra sobrepeso/dieta controlada.",
                    prioridade=2,
                    publico="tutor",
                )
            )
        if "otite" in texto:
            recs.append(
                Recomendacao(
                    servico="Reavaliação otológica",
                    motivo="Histórico recente de otite; conferir resposta ao antibiótico.",
                    prioridade=2,
                    publico="clinica",
                )
            )
        if "alergia" in texto or "cutanea" in texto:
            recs.append(
                Recomendacao(
                    servico="Acompanhamento dermatológico",
                    motivo="Alergia cutânea em andamento; personalizar produto e retorno.",
                    prioridade=2,
                    publico="tutor",
                )
            )
        if "geriatrico" in texto or etapa == "senior":
            recs.append(
                Recomendacao(
                    servico="Check-up geriátrico periódico",
                    motivo="Pet sênior: priorizar exames de rotina e monitoramento renal.",
                    prioridade=2,
                    publico="clinica",
                )
            )

    meds = [m for m in medicamentos if m["id_pet"] == pet.id_pet and m.get("em_uso")]
    if meds:
        nomes = ", ".join(m["nome"] for m in meds)
        recs.append(
            Recomendacao(
                servico="Conferência de medicação em uso",
                motivo=f"Tratamento ativo: {nomes}.",
                prioridade=1 if internado else 2,
                publico="clinica",
            )
        )

    if internado and clima_fora_faixa:
        recs.append(
            Recomendacao(
                servico="Ajuste imediato do microclima da gaiola",
                motivo="Leitura IoT fora da faixa personalizada do pet internado.",
                prioridade=1,
                publico="clinica",
            )
        )

    if etapa == "filhote":
        recs.append(
            Recomendacao(
                servico="Protocolo de filhote (vacina + vermífugo + socialização)",
                motivo="Idade inferior a 2 anos: jornada de imunização ainda incompleta.",
                prioridade=2,
                publico="tutor",
            )
        )

    realizadas = [
        c for c in consultas
        if c["id_pet"] == pet.id_pet and c["status"] == "Realizada"
    ]
    if realizadas:
        ultima = max(date.fromisoformat(c["data_consulta"]) for c in realizadas)
        dias = (hoje - ultima).days
        if dias >= 180:
            recs.append(
                Recomendacao(
                    servico="Consulta de retorno / check-up",
                    motivo=f"Última consulta realizada há {dias} dias.",
                    prioridade=3,
                    publico="tutor",
                )
            )

    # Remove duplicatas preservando a maior prioridade (menor número).
    unicas: dict[str, Recomendacao] = {}
    for rec in recs:
        atual = unicas.get(rec.servico)
        if atual is None or rec.prioridade < atual.prioridade:
            unicas[rec.servico] = rec

    return sorted(unicas.values(), key=lambda r: (r.prioridade, r.servico))
