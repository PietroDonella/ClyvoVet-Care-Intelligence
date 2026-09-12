# Componente de IA — CLYVO VET Care Intelligence

Documento técnico da Sprint 3 (Disruptive Architectures: IoT, IoB & Generative IA).

## 1. Problema de negócio

A jornada da CLYVO VET já cobre cadastro (tutor/pet), atendimento (consulta/prontuário) e internamento com IoT (coleira RFID + DHT22 na gaiola). O buraco está na **decisão operacional contínua**:

- Na internação, temperatura 32 °C não significa o mesmo para um cão sênior de 25 kg e para um gato filhote de 1,2 kg.
- A troca de pacientes (coleira na gaiola errada) é o risco que o RFID deveria eliminar — mas só elimina se alguém cruzar a leitura com o prontuário na hora.
- O tutor não vê o dashboard Node-RED; ele precisa de uma mensagem clara do próximo passo (reforço, retorno, dieta).
- A clínica precisa priorizar a ronda e sugerir serviços com base no histórico, não só na memória da recepção.

**Problema que a IA trata:** dado o pet identificado, seu histórico clínico e o estado IoT da gaiola, **priorizar quem precisa de ação agora**, **recomendar o serviço certo** e **explicar isso em linguagem de tutor**, sem substituir o veterinário.

Valor por público:

- **Pet** — menos tempo em estresse térmico e menor chance de procedimento no animal errado.
- **Tutor** — cuidado percebido como contínuo e personalizado, com próximo passo explícito.
- **Clínica** — fila de ronda objetiva, oferta de serviços (vacina, check-up, nutrição) alinhada ao prontuário.

## 2. Estratégia de personalização

A personalização não é um texto com o nome do pet. O perfil muda a regra:

| Atributo | Como personaliza |
|---|---|
| Espécie | Faixa térmica de cão ≠ gato |
| Idade | Filhote e sênior têm faixa mais estreita e peso extra no score |
| Peso | Filhote de baixo peso agrava alerta de frio |
| RFID + gaiola | A identidade do internado é a chave da triagem |
| Prontuário | Otite, sobrepeso, alergia disparam serviços diferentes |
| Vacina | Vencida vs. reforço pendente vs. em dia |
| Comportamento | Entra no resumo clínico (ansiedade em gaiola, busca de calor) |

Dois pets na mesma sala, mesma temperatura, saem com **risco e recomendação diferentes**. Esse é o critério de personalização da sprint.

## 3. Priorização de ações

O orquestrador monta uma fila:

1. Alerta **crítico** (RFID de outro pet na gaiola) vai para o topo, score mínimo 90.
2. Score climático 0–100 (desvio de temperatura, umidade, vulnerabilidade).
3. Empate: maior score, depois nome.

A **ação priorizada** é uma única frase operacional:

- crítico → conferir identidade e interromper procedimento
- alto → ronda imediata e ajuste do microclima
- demais → primeiro serviço recomendado ao tutor

A clínica deixa de ter “vários avisos iguais” e passa a ter uma ordem de atendimento.

## 4. Recomendação de serviços

O recomendador é **content-based** (perfil + histórico), não collaborative filtering. Motivo: a base atual (Oracle da API) tem volume pequeno e não há rating explícito de serviços.

Sinais → serviço:

- vacina vencida / reforço pendente → vacinação
- diagnóstico de sobrepeso → consulta nutricional
- otite recente + antibiótico em uso → reavaliação otológica
- sênior / check-up geriátrico → check-up periódico
- internado com risco alto → ajuste de gaiola
- filhote → protocolo de imunização
- última consulta antiga → retorno

Cada item tem `prioridade` (1 = imediato) e `publico` (`clinica` ou `tutor`), para a recepção e o plantão não receberem a mesma lista.

## 5. Apoio à tomada de decisão

Dois artefatos, dois leitores:

- **Resumo clínico** (veterinário): identificação, IoT, prontuário, medicação, score, ação. Fato separado de inferência. Fecha com a reserva de conduta humana.
- **Mensagem ao tutor**: empática, sem dose e sem diagnóstico inventado, com próximo passo.

A IA apoia. Quem decide tratamento é o CRMV da unidade.

## 6. Abordagem escolhida e justificativa técnica

**Híbrido: motor de regras + recomendação content-based + IA generativa.**

Por que não “só um LLM”?

- Troca de paciente e estresse térmico são **segurança do paciente**. LLM pode omitir, suavizar ou alucinar. Regra determinística é testável e auditável (código em `motor_regras.py`).
- Recomendação de serviço com poucos registros não precisa de treino supervisionado nesta sprint; regras de conteúdo já extraem valor do prontuário e das vacinas.
- Linguagem natural **sim** se beneficia de LLM: o mesmo insight vira texto de tutor e texto de plantão. Por isso a terceira camada existe — e os prompts de produção estão em `prompts/`.

Por que não só regras?

- Texto rígido não escala para o app do tutor (IoB: o comportamento do tutor muda se a mensagem for genérica).
- O enunciado pede personalização da experiência; geração condicionada ao JSON de contexto é o mecanismo certo.

Mapeamento para o enunciado:

| Opção do enunciado | Uso neste projeto |
|---|---|
| Motor de regras inteligentes | Triagem IoT + RFID |
| Sistema de recomendação | Serviços da jornada |
| IA generativa / LLM | Mensagem e resumo |
| NLP | Camada generativa (produção) |
| Modelo preditivo | Fora de escopo agora (poucos eventos temporais rotulados); evolução natural com histórico de internação |

## 7. Como a IA se integra à aplicação

Fluxo previsto em produção:

1. ESP32 publica `clyvovet/internacao/temp` e `clyvovet/triagem/rfid` no HiveMQ (já existe).
2. Node-RED (ou a API) persiste a leitura e dispara o serviço de IA.
3. O serviço lê PET/TUTOR/CONSULTA/PRONTUARIO no Oracle (API .NET já expõe esses recursos).
4. Motor de regras + recomendador + LLM devolvem um JSON de insight.
5. App/dashboard exibem a fila; o tutor recebe a mensagem no canal do produto.

Nesta sprint o serviço está **simulado em Python**, com a mesma carga da API e payloads MQTT equivalentes. Isso atende à “demonstração funcional (real ou simulada)” sem depender de chave de LLM nem do Oracle ligado.

Contrato de saída (simplificado):

```json
{
  "id_pet": 3,
  "nivel_risco": "alto",
  "score_risco": 85,
  "acao_priorizada": "...",
  "alertas": [],
  "recomendacoes": [],
  "mensagem_tutor": "...",
  "resumo_clinico": "..."
}
```

## 8. Limites éticos e técnicos (para a banca)

- Sem prescrição automática.
- Sem treino em dados reais de tutores nesta sprint (base de demonstração).
- Geração atual é template determinístico; os prompts já estão prontos para trocar a função `ia_generativa` por uma chamada de LLM sem mudar o orquestrador.
- RFID desconhecido e RFID trocado são falhas de processo, não “sugestões” — o nível é crítico.
