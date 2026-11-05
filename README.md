# Robô de Passagens ✈️

Robô pessoal que manda alertas de passagens aéreas no Telegram.

- **Promoções**: lê Melhores Destinos, Passageiro de Primeira, Pontos pra Voar e Passagens Imperdíveis e filtra por origem, destino, nacional/internacional, preço e milhas.
- **Rotas em R$** (opcional, `SERPAPI_KEY`): acompanha o Google Flights e avisa quando o preço cai.
- **Rotas em milhas** (opcional, `SEATS_AERO_KEY`): Smiles e Azul Fidelidade via Seats.aero.

Roda no GitHub Actions a cada 30 minutos (`.github/workflows/robo.yml`) e guarda o estado em `data/estado.json`.
Mande `/ajuda` ao bot para ver os comandos.

| Arquivo | Conteúdo |
| --- | --- |
| `robo.py` | O robô |
| `lugares.py` | Cidades, aeroportos e regiões reconhecidos (dá para acrescentar) |
| `data/estado.json` | Configurações e histórico (o robô atualiza sozinho) |
