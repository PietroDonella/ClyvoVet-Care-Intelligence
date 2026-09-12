# Diagrama de arquitetura — CLYVO VET Care Intelligence

Comunicação entre usuários, aplicação, banco, APIs, IoT e componentes de IA.

## Visão de contexto

```mermaid
flowchart LR
    tutor[Tutor]
    equipe[Equipe da clínica]
    app[App / API Clyvo Vet<br/>.NET 10]
    oracle[(Oracle<br/>PET TUTOR CONSULTA<br/>PRONTUARIO VACINA)]
    esp[ESP32<br/>RFID + DHT22]
    mqtt[HiveMQ MQTT]
    nodered[Dashboard Node-RED]
    ia[Care Intelligence]
    regras[Motor de regras]
    rec[Recomendador]
    llm[Camada generativa / LLM]

    equipe --> app
    equipe --> nodered
    tutor --> app
    app --> oracle
    esp --> mqtt
    mqtt --> nodered
    mqtt --> ia
    app --> ia
    oracle --> ia
    ia --> regras
    ia --> rec
    ia --> llm
    rec --> ia
    regras --> ia
    llm --> ia
    ia --> app
    ia --> nodered
    app --> tutor
    app --> equipe
```

## Fluxo de dados (sequência)

```mermaid
sequenceDiagram
    participant Pet as Pet / gaiola
    participant ESP as ESP32
    participant MQ as HiveMQ
    participant API as API .NET
    participant BD as Oracle
    participant IA as Care Intelligence
    participant UI as App e dashboard

    Pet->>ESP: tag RFID + temperatura/umidade
    ESP->>MQ: JSON nos tópicos clyvovet/*
    API->>BD: lê perfil, prontuário, vacinas
    MQ->>IA: leitura IoT
    API->>IA: contexto clínico do pet
    IA->>IA: regras (risco + RFID)
    IA->>IA: recomendação de serviços
    IA->>IA: geração tutor + resumo clínico
    IA->>UI: insight (score, fila, textos)
    UI->>Pet: equipe age na gaiola
    UI->>Pet: tutor recebe próximo passo
```

## Onde cada componente de IA atua

```mermaid
flowchart TB
    subgraph entrada [Entradas]
        iot[Leitura MQTT]
        cli[Perfil e prontuário Oracle]
    end

    subgraph hibrido [Serviço de IA híbrido]
        r[Regras inteligentes<br/>térmico + troca de paciente]
        s[Recomendação content-based<br/>vacina dieta retorno]
        g[IA generativa<br/>prompts versionados]
    end

    subgraph saida [Saídas]
        fila[Fila de prioridade]
        serv[Lista de serviços]
        txt[Mensagem e resumo]
    end

    iot --> r
    cli --> r
    cli --> s
    r --> s
    r --> g
    s --> g
    r --> fila
    s --> serv
    g --> txt
```

## Integração com o que o grupo já entregou

| Bloco | Repositório / artefato | Papel agora |
|---|---|---|
| Hardware simulado | IoT-Challenge (Wokwi) | Origem dos eventos |
| Mensageria | HiveMQ `broker.hivemq.com` | Barramento IoT |
| Dashboard | Node-RED `flow_nodered.json` | Visualização humana da internação |
| Backend | ClyvoVet .NET + Oracle | Sistema de registro clínico |
| IA | este repositório | Decisão, personalização e linguagem |

O serviço de IA é **desacoplado**: consome JSON da API e JSON do MQTT. Não substitui a API e não substitui o dashboard; adiciona uma porta de insights.

## Protótipo desta pasta

Para a banca, o mesmo fluxo roda localmente:

`data/leituras_iot.json` + `data/base_clinica.json` → `python app.py` → fila, alertas, serviços e textos.

Em produção, troca-se o JSON estático pelas APIs reais e a função `ia_generativa` por uma chamada ao LLM com `prompts/sistema_tutor.txt` e `prompts/sistema_veterinario.txt`.
