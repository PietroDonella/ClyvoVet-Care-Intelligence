"""Camada generativa (LLM) — neste protótipo, simulada de forma determinística.

Em produção, os mesmos payloads seriam enviados a um LLM (ex.: GPT-4.1 mini
ou equivalente) com os prompts de `prompts/`. A simulação existe para a
demo funcionar sem chave de API, sem alucinar conduta clínica e com
saída reproduzível para avaliação da sprint.
"""

from __future__ import annotations

from .modelos import InsightPet, Pet
from .motor_regras import faixa_etaria


def mensagem_tutor(pet: Pet, insight: InsightPet) -> str:
    etapa = faixa_etaria(pet)
    tutor = pet.tutor_nome.split()[0] if pet.tutor_nome else "tutor"

    if insight.nivel_risco == "critico":
        abertura = (
            f"Olá, {tutor}. Identificamos um alerta de segurança envolvendo {pet.nome} "
            "na internação da CLYVO VET e a equipe já foi acionada."
        )
    elif insight.nivel_risco == "alto":
        abertura = (
            f"Olá, {tutor}. O acompanhamento de {pet.nome} na CLYVO VET gerou um alerta "
            "de prioridade alta, pensado no conforto e na segurança dele."
        )
    else:
        abertura = (
            f"Olá, {tutor}. Segue um resumo personalizado do cuidado de {pet.nome} "
            f"({pet.especie.lower()} {etapa}, {pet.idade} ano(s))."
        )

    alertas_tutor = [
        a for a in insight.alertas if a.codigo != "RFID_TROCA_PACIENTE"
    ]
    if any(a.codigo == "RFID_TROCA_PACIENTE" for a in insight.alertas):
        texto_alertas = (
            f"A equipe está conferindo a identificação de {pet.nome} na internação "
            "antes de qualquer procedimento."
        )
    elif alertas_tutor:
        texto_alertas = " ".join(a.detalhe for a in alertas_tutor[:2])
    else:
        texto_alertas = "Nenhum alerta ambiental crítico no momento."
    recs_tutor = [r for r in insight.recomendacoes if r.publico == "tutor"][:3]
    if not recs_tutor:
        recs_tutor = insight.recomendacoes[:2]
    proximos = " ".join(f"{i + 1}) {r.servico} — {r.motivo}" for i, r in enumerate(recs_tutor))
    if not proximos:
        proximos = "Manter o calendário de consultas em dia já é suficiente nesta etapa."

    fechamento = (
        "Esta mensagem é um apoio à jornada de cuidado: a conduta clínica continua "
        "com o veterinário responsável. Responda pelo app se quiser agendar o próximo passo."
    )
    return f"{abertura} {texto_alertas} Próximas ações sugeridas: {proximos} {fechamento}"


def resumo_clinico(pet: Pet, insight: InsightPet, prontuario: dict | None, meds: list[dict]) -> str:
    diagnostico = prontuario["diagnostico"] if prontuario else "Sem prontuário recente."
    med_txt = ", ".join(f"{m['nome']} ({m['indicacao']})" for m in meds) or "nenhum em uso"
    alertas = "; ".join(f"[{a.nivel}] {a.titulo}" for a in insight.alertas) or "sem alertas IoT"
    recs = "; ".join(r.servico for r in insight.recomendacoes[:4]) or "nenhuma"
    return (
        f"Paciente {pet.nome} (id {pet.id_pet}, {pet.especie}, {pet.idade}a, {pet.peso} kg). "
        f"RFID {pet.rfid_uid}. Internação: {pet.status_internacao or 'ambulatorial'}"
        f"{f' / gaiola {pet.gaiola}' if pet.gaiola else ''}. "
        f"Comportamento: {pet.comportamento} "
        f"Último diagnóstico: {diagnostico} "
        f"Medicação: {med_txt}. "
        f"Risco {insight.nivel_risco} (score {insight.score_risco}). "
        f"Alertas: {alertas}. "
        f"Ação priorizada: {insight.acao_priorizada}. "
        f"Serviços sugeridos: {recs}. "
        "A IA prioriza e contextualiza; a decisão terapêutica é do veterinário."
    )
