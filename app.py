from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from ia_clyvovet import CareIntelligence  # noqa: E402


def _barra(score: int) -> str:
    cheio = round(score / 10)
    return "#" * cheio + "-" * (10 - cheio)


def imprimir_insight(insight) -> None:
    pet = insight.pet
    print("=" * 78)
    print(f"  {pet.nome}  |  {pet.especie}  |  {pet.idade}a  |  {pet.peso} kg  |  RFID {pet.rfid_uid}")
    print(f"  Tutor: {pet.tutor_nome}  ({pet.tutor_telefone})")
    internacao = pet.status_internacao or "Ambulatorial"
    gaiola = f"  gaiola {pet.gaiola}" if pet.gaiola else ""
    print(f"  Situação: {internacao}{gaiola}")
    print(f"  Conforto esperado: {insight.faixa_conforto}")
    print(f"  Risco: {insight.nivel_risco.upper()}  {_barra(insight.score_risco)}  {insight.score_risco}/100")
    print(f"  Ação priorizada: {insight.acao_priorizada}")
    print("-" * 78)
    if insight.alertas:
        print("  Alertas")
        for alerta in insight.alertas:
            print(f"    [{alerta.nivel.upper():8}] {alerta.titulo}")
            print(f"               {alerta.detalhe}")
    else:
        print("  Alertas: nenhum")
    print("-" * 78)
    print("  Recomendações de serviço")
    if insight.recomendacoes:
        for rec in insight.recomendacoes:
            print(f"    P{rec.prioridade}  ({rec.publico})  {rec.servico}")
            print(f"         {rec.motivo}")
    else:
        print("    Nenhuma no momento")
    print("-" * 78)
    print("  Mensagem ao tutor (camada generativa)")
    print(f"    {insight.mensagem_tutor}")
    print("-" * 78)
    print("  Resumo clínico (apoio à decisão)")
    print(f"    {insight.resumo_clinico}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLYVO VET Care Intelligence — demo da camada de IA (Sprint 3)."
    )
    parser.add_argument("--pet", type=int, default=None, help="Analisa apenas o id_pet informado.")
    parser.add_argument("--json", action="store_true", help="Imprime a fila em JSON.")
    args = parser.parse_args()

    ia = CareIntelligence(ROOT / "data")

    if args.pet is not None:
        if args.pet not in ia.pets_por_id:
            raise SystemExit(f"Pet {args.pet} não encontrado. IDs: {sorted(ia.pets_por_id)}")
        insights = [ia.analisar_pet(args.pet)]
    else:
        insights = ia.fila_prioridade()

    if args.json:
        print(json.dumps([i.to_dict() for i in insights], ensure_ascii=False, indent=2))
        return

    print("\nCLYVO VET  -  Care Intelligence")
    print("Fila de priorização (motor de regras + recomendação + IA generativa)\n")
    for insight in insights:
        imprimir_insight(insight)
    print("Legenda de risco: critico > alto > medio > baixo")
    print("A IA prioriza e recomenda; a conduta clínica é do veterinário.\n")


if __name__ == "__main__":
    main()
