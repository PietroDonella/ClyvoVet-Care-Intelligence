# CLYVO VET — Care Intelligence (Sprint 3)

**Disruptive Architectures: IoT, IoB & Generative IA**

Grupo: Enzo Vaz (RM561702) · Lucas Ryuji Fukuda (RM562152) · Pietro Donella Salomão (RM561722)

Camada de Inteligência Artificial da CLYVO VET: transforma dados clínicos e leituras IoT (RFID + clima da gaiola) em **priorização da internação**, **recomendação de serviços** e **comunicação personalizada** com o tutor.

- Vídeo (YouTube, não listado): https://youtu.be/NgxeQheO3Po
- IoT (Sprints 1 e 2): [PietroDonella/IoT-Challenge](https://github.com/PietroDonella/IoT-Challenge)
- API .NET: [EnzoVazz/ClyvoVet](https://github.com/EnzoVazz/ClyvoVet)

---

## O problema que a IA resolve

A clínica já identifica o pet por RFID e já mede temperatura/umidade da gaiola. Ainda assim, a equipe precisa decidir **quem atender primeiro**, **o que oferecer ao tutor** e **como explicar o cuidado** sem varrer prontuário, vacina e dashboard ao mesmo tempo.

A IA entra exatamente nesse ponto da jornada contínua:

| Sem IA | Com IA |
|---|---|
| Alerta climático genérico para todas as gaiolas | Faixa de conforto **personalizada** por espécie, idade e peso |
| Risco de medicação no animal errado depende só do olho humano | Motor de regras dispara **troca de paciente** quando o RFID não bate com a gaiola |
| Tutor recebe recado padronizado | Mensagem generativa com o próximo passo daquele pet |
| Serviços oferecidos por memória da recepção | Recomendação a partir de vacina, prontuário e internação |

A IA **não substitui** o veterinário. Ela prioriza, recomenda e redige; a conduta clínica continua humana.

---

## Abordagem de IA (híbrida, justificada)

Três técnicas, cada uma no lugar em que o erro tem um custo diferente:

1. **Motor de regras inteligentes** — segurança (estresse térmico e RFID). Saída determinística, auditável, sem alucinação.
2. **Sistema de recomendação content-based** — vacinas vencidas, filhote, sênior, sobrepeso, retorno. Funciona com o volume atual da base Oracle (não depende de milhares de avaliações).
3. **IA generativa (LLM)** — mensagem ao tutor e resumo clínico. Em produção, os prompts de `prompts/` vão para um LLM; neste repositório a geração está **simulada** para a demo rodar sem chave de API e com texto reproduzível.

Detalhamento técnico: [`docs/componente-ia.md`](docs/componente-ia.md)  
Catálogo de dados: [`docs/dados.md`](docs/dados.md)  
Arquitetura: [`docs/diagrama-arquitetura.md`](docs/diagrama-arquitetura.md)

---

## Arquitetura (visão geral)

```
Tutor / Clínica
        │
        ▼
 App CLYVO VET ──────────► API .NET (Clean Architecture)
                                │
                                ▼
                         Oracle (PET, TUTOR, CONSULTA,
                         PRONTUARIO + vacina / medicação)
                                │
 ESP32 (RFID + DHT22)           │
   MQTT / HiveMQ                │
        │                       │
        ▼                       ▼
 Dashboard Node-RED ──► Serviço Care Intelligence
                        ├── motor de regras
                        ├── recomendador
                        └── camada generativa
                                │
                                ▼
                  Insights: fila de risco, serviços, textos
```

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Protótipo da IA (esta sprint) | Python 3.10+ (biblioteca padrão) |
| Dados de demonstração | JSON (`data/`) alinhado ao schema Oracle da API |
| IoT já entregue | ESP32, MFRC522, DHT22, MQTT, HiveMQ, Node-RED, Wokwi |
| Aplicação | .NET 10, Clean Architecture, Oracle |
| IA em produção (prevista) | Regras + recomendação na API/serviço; LLM via prompt versionado |

Não há `pip install`. Só Python.

---

## Instruções de uso

Pré-requisito: [Python 3.10 ou superior](https://www.python.org/downloads/).

```bash
git clone https://github.com/PietroDonella/ClyvoVet-Care-Intelligence.git
cd ClyvoVet-Care-Intelligence
python app.py
```

A demo imprime a **fila de priorização** de todos os pets da base (internados primeiro quando o risco sobe).

Outros modos:

```bash
python app.py --pet 3          # só o Thor (internado, calor, vacina vencida)
python app.py --pet 8          # só a Pipoca (filhote, frio, reforço vacinal)
python app.py --pet 7          # Bidu: RFID de outro pet na gaiola G-02
python app.py --json           # mesma fila em JSON
```

O que observar na tela:

1. **Score de risco** e ação priorizada  
2. **Alertas IoT** (temperatura, umidade, RFID)  
3. **Serviços recomendados** (vacina, nutrição, retorno, ajuste de gaiola)  
4. **Mensagem ao tutor** e **resumo clínico**

---

## Estrutura do repositório

```
├── README.md
├── LINKS-ENTREGA.txt          ← YouTube + GitHub da entrega
├── app.py                     ← demo executável
├── data/
│   ├── base_clinica.json      ← tutores, pets, prontuários, vacinas, medicação
│   └── leituras_iot.json      ← payload MQTT simulado (temp + RFID)
├── src/ia_clyvovet/
│   ├── motor_regras.py
│   ├── recomendador.py
│   ├── ia_generativa.py
│   └── orquestrador.py
├── prompts/                   ← prompts de produção para o LLM
└── docs/
```

---

## Resultados parciais

A simulação, com a mesma carga da API (Rex, Mia, Thor, Luna, Frajola, Nina, Bidu, Pipoca) e três leituras IoT, produz:

| Pet | Situação | Resultado da IA |
|---|---|---|
| **Bidu** (G-02) | RFID lido = Rex | Risco **crítico** — troca de paciente; bloquear procedimento |
| **Thor** (G-04) | 32,4 °C, sênior, otite, vacina vencida | Risco **alto** — ajuste climático + vacinação + reavaliação otológica |
| **Pipoca** (G-07) | 17,1 °C, filhote 1,2 kg | Risco **alto** — frio fora da faixa felina de filhote + reforço V4 |
| Demais pets | Ambulatoriais | Risco **baixo/médio** — recomendações de vacina, dieta ou retorno |

Isso demonstra, de ponta a ponta, os quatro papéis pedidos no enunciado: **personalização**, **priorização**, **recomendação de serviços** e **apoio à decisão**.
