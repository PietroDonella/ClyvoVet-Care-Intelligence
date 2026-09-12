# Roteiro falado (~5 min) — professor exigente

Fale como se estivesse explicando um caso clínico, não um trabalho de faculdade.
Não diga “inteligência artificial avançada”, “inovação disruptiva” nem “ChatGPT”.
O professor compra: problema real → dado → regra → decisão → limite da IA.

YouTube **não listado**. Tela: README/diagrama no começo; `python app.py` na demo.

---

## 0:00–0:45 — Abre com uma cena (não com o nome da matéria)

**Fala:**

Nas sprints anteriores a CLYVO VET já identificava o pet por RFID e já media temperatura e umidade da gaiola. O dado chegou. A decisão, não.

Imagina a internação às dez da manhã. Tem um cão sênior numa gaiola a 32 graus, um gato filhote de um quilo a 17 graus, e uma coleira RFID que não é do animal que deveria estar naquela gaiola. Se a equipe olhar só o dashboard, os três avisos parecem iguais. Não são.

O problema desta sprint é este: **na jornada contínua de cuidado, quem a clínica atende primeiro, o que ela oferece ao tutor, e como ela explica isso — sem substituir o veterinário.**

É para isso que entra o componente de IA. A gente chama de Care Intelligence.

---

## 0:45–1:40 — O que a IA é (e o que ela não é)

**Fala:**

A gente não treinou uma rede neural e não colocou um chatbot para “inventar” conduta. Em medicina veterinária isso seria irresponsável.

A abordagem é **híbrida**, de propósito, com três peças no lugar certo:

Primeira: **motor de regras inteligentes**. Estresse térmico e troca de paciente. Aqui o erro pode medicar o animal errado. Então a saída é determinística, auditável, explicável. Se o RFID da gaiola 2 é do Rex e o internado é o Bidu, o sistema trava a prioridade no máximo. Isso não pode depender de um modelo que às vezes parafraseia.

Segunda: **sistema de recomendação**. Vacina vencida, reforço de filhote, sobrepeso, retorno. A base ainda é a da API: poucos prontuários, sem milhares de avaliações. Por isso a recomendação é por conteúdo — perfil mais histórico — e não collaborative filtering.

Terceira: **IA generativa**. O mesmo insight vira mensagem para o tutor e resumo para o plantão. Em produção isso vai para um LLM, com prompt travado: não inventa diagnóstico, não inventa dose. Neste protótipo a geração está simulada para a demo ser reproduzível e segura.

Frase para cravar: **a IA prioriza, recomenda e explica. Quem decide o tratamento é o veterinário.**

---

## 1:40–2:20 — Benefício (tutor vs clínica vs pet)

**Fala:**

Para o **pet**: a faixa de conforto não é a da sala. É a da espécie, da idade e do peso dele. 24 graus pode ser normal para um cão adulto e frio demais para um gato filhote.

Para a **clínica**: a ronda ganha ordem. Serviço sai do prontuário — vacina, nutrição, reavaliação — não da memória da recepção. E o alerta de RFID ataca o risco original do projeto: medicação no animal errado.

Para o **tutor**: ele não vê o Node-RED. Ele recebe o próximo passo daquele pet, em linguagem de gente, sem jargão.

---

## 2:20–3:10 — Arquitetura (um fluxo, sem tour de pasta)

**[Tela: diagrama do README ou `docs/diagrama-arquitetura.md`]**

**Fala:**

O fluxo é este, ponta a ponta.

O tutor e a equipe usam o app. O app grava no Oracle pela API .NET: pet, tutor, consulta, prontuário.

Na gaiola, o ESP32 lê RFID e DHT22 e publica no MQTT, no HiveMQ, nos tópicos que já existiam: temperatura da internação e triagem RFID. O Node-RED continua sendo o dashboard.

A IA não substitui nada disso. Ela **consome** os dois lados — clínico e IoT — e devolve um insight: score de risco, fila, lista de serviços, texto do tutor, resumo do vet.

Por isso o serviço é desacoplado. JSON entra, JSON sai. Nesta sprint a demonstração é simulada, com a mesma carga da API. O enunciado pede demo real ou simulada; a integração nativa com Oracle e LLM é o passo seguinte, com o contrato já definido.

---

## 3:10–4:40 — Demo (aqui o professor acredita ou não)

**[Tela: terminal na pasta do repo]**

```text
python app.py
```

Não leia o dump. Aponte três casos, de cima para baixo.

### Caso 1 — Bidu (o professor cabeça dura “compra” neste)

Este é o Bidu, internado na G-02. Temperatura da gaiola está ok. O score mesmo assim é crítico, 90.

Por quê? A tag lida é a do Rex. A gaiola é do Bidu.

Isso é o problema de negócio das sprints de IoT, agora virando decisão: **conferir identidade e interromper procedimento**. A recomendação para a clínica é conferência imediata. A mensagem do tutor não vaza o detalhe técnico da tag — fala que a equipe está conferindo a identificação. O resumo clínico, para o vet, traz o fato completo.

Se fosse só um LLM, esse alerta podia sair fofo. Aqui ele sai **crítico**, sempre.

### Caso 2 — Pipoca (personalização)

Pipoca, gato, um ano, 1,2 kg, G-07, 17 graus. Risco alto.

A faixa segura dela não é a do cão adulto. É 22 a 28 graus, filhote felino, baixo peso. Por isso o frio pesa mais.

Ao mesmo tempo a IA recomenda o reforço da V4. Clima é da internação; vacina é da jornada. Os dois entram no mesmo insight, sem misturar responsabilidade: ajustar a gaiola é da equipe; o reforço é conversa com a tutora Fernanda.

### Caso 3 — Thor (a “mesma sala”, outro animal)

Thor, cão, oito anos, 25 kg, 32 graus. Também risco alto — mas por **calor**, não por frio.

Mesmo corredor, outra faixa: sênior canino, 20 a 25 graus. Histórico de otite, antibiótico em uso, V10 vencida. A fila não diz só “quente”. Diz: ajustar microclima, conferir medicação, atualizar vacina, reavaliar ouvido.

Se sobrar quinze segundos: `python app.py --pet 3` e leia só a primeira frase da mensagem da Ana, a tutora. Mostre que o texto muda com o pet.

---

## 4:40–5:00 — Fecha sem slogan

**Fala:**

Recapitulando. Problema: dado IoT e dado clínico sem priorização. Solução: IA híbrida — regras onde o erro é perigoso, recomendação onde tem histórico, geração onde precisa de linguagem. A demo mostra três decisões diferentes a partir dos mesmos tipos de sensor.

O repositório tem o código, o README, o catálogo de dados e o diagrama. O veterinário continua no comando. A IA só organiza a jornada para ele não ter que montar isso de cabeça no meio da ronda.

Obrigado.

---

## Se o tempo apertar (versão 2 min)

1. Dado IoT já existia; faltava decisão.  
2. Três camadas: regra (segurança), recomendação (serviço), geração (texto).  
3. Demo: Bidu RFID errado; Pipoca frio de filhote; Thor calor de sênior.  
4. IA não prescreve.

## O que não falar

- “A gente usou ChatGPT.”  
- “É um modelo preditivo de deep learning.” (não é; se perguntarem, diga que preditivo fica para quando houver série rotulada de internação.)  
- “A API já chama a IA em produção.” (não chama; a demo é simulada e isso está no enunciado.)  
- Ler arquivo por arquivo da pasta.
