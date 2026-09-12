# Dados que alimentam a IA

Origem, estrutura e uso. Parte dos campos já existe na API/Oracle; parte é extensão necessária para a camada de IA (marcada como **proposta**).

## 1. Origem dos dados

```
Tutor e equipe  →  App / API .NET  →  Oracle
Pet internado   →  Tag RFID (MFRC522) + DHT22  →  ESP32  →  MQTT/HiveMQ  →  Node-RED
                                                ↘ serviço de IA (este repositório)
```

| Fonte | Sistema já existente | O que a IA consome |
|---|---|---|
| Cadastro | `TUTOR`, `PET` | perfil, tutor, espécie, idade, peso |
| Jornada clínica | `CONSULTA`, `PRONTUARIO` | último diagnóstico, status, datas |
| IoT (Sprints 1–2) | tópicos HiveMQ | temperatura, umidade, UID da coleira, gaiola |
| Extensão proposta | vacina, medicação, comportamento, RFID, internação | calendário imunológico, tratamento ativo, alocação na gaiola |

## 2. Dados já presentes na API (Oracle)

Estrutura alinhada a `script_bd.sql` / entidades .NET.

### PET

| Campo | Tipo | Uso na IA |
|---|---|---|
| id_pet | número | chave |
| id_tutor | número | personalização da mensagem |
| nome | texto | comunicação |
| especie | texto | faixa térmica e serviços |
| idade | número | filhote / adulto / sênior |
| peso | número | vulnerabilidade (ex.: 1,2 kg) |

### TUTOR

| Campo | Uso na IA |
|---|---|
| nome, telefone | destinatário da mensagem generativa |

### PRONTUARIO

| Campo | Uso na IA |
|---|---|
| diagnostico | sinais para recomendação (otite, sobrepeso, alergia, geriátrico) |
| data_registro | recência do evento clínico |

### CONSULTA

| Campo | Uso na IA |
|---|---|
| data_consulta, status | retorno atrasado; ignora canceladas |

## 3. Dados IoT (já medidos no Wokwi)

Payload real das sprints 1 e 2:

```json
{ "temperatura": 32.4, "umidade": 78 }
```

```json
{ "pet_id": "C3D4E5F6" }
```

Tópicos: `clyvovet/internacao/temp` e `clyvovet/triagem/rfid`.

No protótipo, cada leitura ganha `gaiola` e `pet_esperado_id` para cruzar **quem deveria estar** versus **quem a tag diz que está**.

| Campo | Origem | Uso |
|---|---|---|
| temperatura, umidade | DHT22 | estresse térmico personalizado |
| rfid_lido | MFRC522 | identidade; alerta de troca |
| gaiola | alocação da internação | contexto do alerta |
| timestamp | ESP32 / broker | auditoria |

## 4. Dados necessários que a base atual ainda não tem (proposta)

Sem estes campos a IA até ranqueia clima, mas não fecha a jornada (vacina, medicação, internado vs. ambulatorial).

### RFID e internação (extensão de PET)

```json
{
  "rfid_uid": "C3D4E5F6",
  "status_internacao": "Internado",
  "gaiola": "G-04"
}
```

- **Origem:** cadastro na admissão + gravação da tag.
- **Uso:** chave de segurança (RFID) e recorte da fila (só internados têm leitura contínua).

### VACINA (nova tabela sugerida)

| Campo | Uso |
|---|---|
| id_pet, nome, data_aplicacao, validade, status | recomendar vacinação / reforço |

Status usados no protótipo: `Em dia`, `Vencida`, `Reforco pendente`.

### MEDICAMENTO (nova tabela sugerida)

| Campo | Uso |
|---|---|
| id_pet, nome, indicacao, em_uso | resumo clínico e conferência na ronda |

### COMPORTAMENTO

Texto livre observado na internação ou no consultório (`comportamento` no JSON). Entra no resumo do veterinário (IoB: o comportamento do animal no ambiente da clínica).

## 5. Como a IA utiliza o conjunto

Ordem de consumo no orquestrador:

1. Carrega perfil do pet + tutor.
2. Se existe leitura IoT da gaiola alocada → regras térmicas + RFID.
3. Cruza vacinas, prontuário, consultas e medicação → recomendações.
4. Empacota alertas + recomendações + perfil → textos generativos.

Nada é treinado nesta sprint: o valor está no **cruzamento estruturado**. Um modelo preditivo (ex.: probabilidade de reinternação) só faz sentido depois de acumular séries de internação rotuladas.

## 6. Privacidade

CPF do tutor existe na base operacional e **não entra** no prompt. O contexto da geração usa nome, telefone, dados do pet e eventos clínicos necessários à mensagem. Em produção, o serviço de IA deve receber um DTO mínimo, não o dump da tabela `TUTOR`.
