"""Robô de alertas de passagens aéreas (Telegram).

Roda a cada ~30 minutos no GitHub Actions. Em cada execução:
  1. Lê os comandos que você mandou no Telegram e atualiza as configurações.
  2. Lê os feeds dos sites de promoção e avisa o que bate com seus filtros.
  3. Consulta o preço das rotas monitoradas (Google Flights via SerpApi) e avisa quedas.
  4. (Opcional) Consulta passagens em milhas Smiles/Azul (Seats.aero).
  5. Salva tudo em data/estado.json.

Variáveis de ambiente (Secrets do GitHub):
  TELEGRAM_TOKEN   (obrigatório) token do bot criado no @BotFather
  TELEGRAM_CHAT_ID (opcional)    seu chat; se vazio, o primeiro /start vira o dono
  SERPAPI_KEY      (opcional)    para monitorar preços de rotas em reais
  SEATS_AERO_KEY   (opcional)    para monitorar rotas em milhas (Smiles/Azul)
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import feedparser
import requests

from lugares import (AEROPORTO_PARA_CIDADE, LUGARES, NORDESTE, ORIGEM_GENERICA,
                     PALAVRAS_INTERNACIONAIS, REGIOES)

# --------------------------------------------------------------------------- #
# Configuração geral
# --------------------------------------------------------------------------- #

PASTA = Path(__file__).resolve().parent
ARQUIVO_ESTADO = PASTA / "data" / "estado.json"
FUSO = timezone(timedelta(hours=-3))  # America/Fortaleza (sem horário de verão)
UA = "Mozilla/5.0 (compatible; RoboPassagens/1.0; uso pessoal)"
TIMEOUT = 25

FEEDS = {
    "Melhores Destinos": "https://www.melhoresdestinos.com.br/feed",
    "Passageiro de Primeira": "https://passageirodeprimeira.com/feed",
    "Pontos pra Voar": "https://pontospravoar.com/feed",
    "Passagens Imperdíveis": "https://passagensimperdiveis.com.br/feed",
}

MAX_ALERTAS_POR_EXECUCAO = 8
LIMITE_SERPAPI_PADRAO = 240   # plano grátis: 250 buscas/mês
LIMITE_SEATS_DIA = 900        # Seats.aero Pro: até 1.000 chamadas/dia

CONFIG_PADRAO = {
    "origens": ["FOR"],        # códigos IATA; [] = qualquer origem
    "destinos": [],            # IATA, regiões ou palavras; [] = qualquer destino
    "tipo": "ambos",           # nacional | internacional | ambos
    "milhas": True,            # incluir promoções de passagens em milhas/pontos
    "bonus": False,            # incluir bônus de transferência de pontos (Livelo, Esfera...)
    "preco_max": None,         # R$ máximo para promoções (None = sem limite)
    "milhas_max": None,        # milhas máximas por trecho (None = sem limite)
    "intervalo_horas": 12,     # de quanto em quanto tempo checar cada rota
    "limite_serpapi": LIMITE_SERPAPI_PADRAO,
    "pausado": False,
}

TEXTO_AJUDA = """<b>✈️ Robô de Passagens — comandos</b>

<b>Promoções (sites de ofertas)</b>
/origens FOR REC — de onde você sai (ou <code>/origens todas</code>)
/destinos Lisboa, Europa, SSA — o que te interessa (ou <code>/destinos todos</code>)
/adddestino Orlando — acrescenta um destino
/remdestino Orlando — tira um destino
/tipo nacional | internacional | ambos
/precomax 1500 — só avisa promoções até R$ 1.500 (<code>/precomax off</code>)
/milhas sim | nao — incluir promoções de milhas/pontos
/milhasmax 40000 — só avisa milhas até 40 mil por trecho (<code>/milhasmax off</code>)
/bonus sim | nao — avisar bônus de transferência de pontos (Livelo, Esfera…)
/ultimas — mostra as últimas promoções que batem com os filtros

<b>Rotas monitoradas (preço em R$, Google Flights)</b>
/rota FOR LIS 10/03/2027 25/03/2027 3500
   ida, volta (opcional) e preço-alvo (opcional)
/rotas — lista suas rotas e o último preço
/removerrota 2 — remove a rota nº 2
/intervalo 12 — checa cada rota a cada 12 horas
/checar — checa todas as rotas agora

<b>Rotas em milhas (Smiles/Azul, precisa Seats.aero)</b>
/rotamilhas FOR LIS 01/03/2027 31/03/2027 60000
   origem, destino, janela de datas e milhas máximas

<b>Geral</b>
/status — mostra suas configurações
/pausar e /retomar — desliga/liga os alertas
/ajuda — esta mensagem

Os comandos são lidos a cada ~30 min (quando o robô roda)."""


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #

def agora() -> datetime:
    return datetime.now(FUSO)


def normalizar(texto: str) -> str:
    """minúsculas, sem acento, espaços simples."""
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto.lower()).strip()


def limpar_html(texto: str) -> str:
    texto = re.sub(r"<[^>]+>", " ", texto or "")
    return re.sub(r"\s+", " ", html.unescape(texto)).strip()


def reais(valor: float | int | None) -> str:
    if valor is None:
        return "—"
    return "R$ " + f"{valor:,.0f}".replace(",", ".")


def milhar(valor: float | int | None) -> str:
    if valor is None:
        return "—"
    return f"{valor:,.0f}".replace(",", ".")


def esc(texto: str) -> str:
    return html.escape(str(texto), quote=False)


def ler_data(texto: str, hoje: date | None = None) -> date | None:
    """Aceita 10/03/2027, 10/03/27, 10/03 (próxima ocorrência) ou 2027-03-10."""
    hoje = hoje or agora().date()
    texto = texto.strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", texto):
            return date.fromisoformat(texto)
        m = re.fullmatch(r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", texto)
        if not m:
            return None
        dia, mes, ano = int(m.group(1)), int(m.group(2)), m.group(3)
        if ano:
            ano = int(ano)
            if ano < 100:
                ano += 2000
            return date(ano, mes, dia)
        d = date(hoje.year, mes, dia)
        return d if d >= hoje else date(hoje.year + 1, mes, dia)
    except ValueError:
        return None


def br(d: date | str) -> str:
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return d.strftime("%d/%m/%Y")


def codigo_cidade(codigo: str) -> str:
    codigo = codigo.upper()
    return AEROPORTO_PARA_CIDADE.get(codigo, codigo)


def nome_lugar(codigo: str) -> str:
    c = codigo_cidade(codigo)
    return LUGARES[c][0] if c in LUGARES else codigo.upper()


def contem(texto_norm: str, termo_norm: str) -> bool:
    """Procura termo como palavra inteira (sem pegar 'roma' em 'aroma')."""
    if not termo_norm:
        return False
    padrao = r"(?<![a-z0-9])" + re.escape(termo_norm) + r"(?![a-z0-9])"
    return re.search(padrao, texto_norm) is not None


# --------------------------------------------------------------------------- #
# Estado (persistido em data/estado.json)
# --------------------------------------------------------------------------- #

def estado_inicial() -> dict:
    return {
        "versao": 1,
        "chat_id": None,
        "telegram_offset": 0,
        "config": dict(CONFIG_PADRAO),
        "vistos": [],              # ids de posts já processados
        "feeds_iniciados": False,
        "recentes": [],            # últimos posts lidos (para /ultimas com filtros atuais)
        "rotas": [],
        "rotas_milhas": [],
        "uso_serpapi": {"mes": "", "usadas": 0, "avisado": False},
        "uso_seats": {"dia": "", "usadas": 0},
        "erros_feed": {},
    }


def carregar_estado() -> dict:
    estado = estado_inicial()
    if ARQUIVO_ESTADO.exists():
        try:
            salvo = json.loads(ARQUIVO_ESTADO.read_text(encoding="utf-8"))
            estado.update(salvo)
            config = dict(CONFIG_PADRAO)
            config.update(salvo.get("config", {}))
            estado["config"] = config
        except (json.JSONDecodeError, OSError) as e:
            print(f"[aviso] estado.json ilegível, recomeçando: {e}")
    return estado


def salvar_estado(estado: dict) -> None:
    ARQUIVO_ESTADO.parent.mkdir(parents=True, exist_ok=True)
    estado["vistos"] = estado["vistos"][-3000:]
    estado["recentes"] = estado["recentes"][-60:]
    estado.pop("ultimas_promocoes", None)
    ARQUIVO_ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Telegram
# --------------------------------------------------------------------------- #

class Telegram:
    def __init__(self, token: str):
        self.base = f"https://api.telegram.org/bot{token}"
        self.enviadas = 0

    def atualizacoes(self, offset: int) -> list[dict]:
        r = requests.get(f"{self.base}/getUpdates",
                         params={"offset": offset, "timeout": 0,
                                 "allowed_updates": json.dumps(["message"])},
                         timeout=TIMEOUT)
        r.raise_for_status()
        return r.json().get("result", [])

    def enviar(self, chat_id, texto: str) -> None:
        if not chat_id:
            print("[telegram] sem chat_id, mensagem não enviada:\n" + texto)
            return
        # Telegram limita mensagens a 4096 caracteres
        for i in range(0, len(texto), 4000):
            r = requests.post(f"{self.base}/sendMessage", timeout=TIMEOUT, data={
                "chat_id": chat_id, "text": texto[i:i + 4000], "parse_mode": "HTML",
                "disable_web_page_preview": "true",
            })
            if not r.ok:
                print(f"[telegram] erro {r.status_code}: {r.text[:300]}")
            self.enviadas += 1


# --------------------------------------------------------------------------- #
# Comandos
# --------------------------------------------------------------------------- #

def dividir_args(texto: str) -> list[str]:
    if "," in texto:
        return [p.strip() for p in texto.split(",") if p.strip()]
    return texto.split()


def interpretar_lugar(token: str) -> str:
    """Converte 'lisboa', 'LIS', 'GRU' -> 'LIS'/'SAO'; regiões e palavras ficam como texto."""
    t = token.strip()
    if re.fullmatch(r"[A-Za-z]{3}", t) and codigo_cidade(t.upper()) in LUGARES:
        return codigo_cidade(t.upper())
    n = normalizar(t)
    for cod, (nome, apelidos, _) in LUGARES.items():
        if n == normalizar(nome) or n in apelidos:
            return cod
    return t


def descrever_lugar(item: str) -> str:
    if item in LUGARES:
        return f"{LUGARES[item][0]} ({item})"
    return item


def texto_status(estado: dict) -> str:
    c = estado["config"]
    origens = ", ".join(descrever_lugar(o) for o in c["origens"]) or "qualquer origem"
    destinos = ", ".join(descrever_lugar(d) for d in c["destinos"]) or "qualquer destino"
    uso = estado["uso_serpapi"]
    linhas = [
        "<b>⚙️ Suas configurações</b>",
        f"Alertas: {'⏸️ pausados' if c['pausado'] else '▶️ ligados'}",
        f"Origens: {esc(origens)}",
        f"Destinos: {esc(destinos)}",
        f"Tipo: {c['tipo']}",
        f"Promoções de milhas: {'sim' if c['milhas'] else 'não'}",
        f"Preço máximo: {reais(c['preco_max']) if c['preco_max'] else 'sem limite'}",
        f"Milhas máximas: {milhar(c['milhas_max']) if c['milhas_max'] else 'sem limite'}",
        f"Bônus de transferência de pontos: {'sim' if c['bonus'] else 'não'}",
        f"Rotas monitoradas: {len(estado['rotas'])} (a cada {c['intervalo_horas']}h)",
        f"Rotas em milhas: {len(estado['rotas_milhas'])}",
        f"Buscas SerpApi no mês: {uso.get('usadas', 0)}/{c['limite_serpapi']}"
        + ("" if os.getenv("SERPAPI_KEY") else " (chave não configurada)"),
    ]
    return "\n".join(linhas)


def texto_rotas(estado: dict) -> str:
    if not estado["rotas"] and not estado["rotas_milhas"]:
        return "Nenhuma rota monitorada. Exemplo:\n<code>/rota FOR LIS 10/03/2027 25/03/2027 3500</code>"
    linhas = []
    if estado["rotas"]:
        linhas.append("<b>📍 Rotas (R$)</b>")
        for i, r in enumerate(estado["rotas"], 1):
            datas = br(r["ida"]) + (f" ↔ {br(r['volta'])}" if r.get("volta") else " (só ida)")
            alvo = f" · alvo {reais(r['teto'])}" if r.get("teto") else ""
            ult = f"\n   último: {reais(r['ultimo_preco'])}" if r.get("ultimo_preco") else "\n   ainda não checada"
            menor = f" · menor visto {reais(r['menor_preco'])}" if r.get("menor_preco") else ""
            linhas.append(f"{i}. {r['origem']}→{r['destino']} {datas}{alvo}{ult}{menor}")
    if estado["rotas_milhas"]:
        linhas.append("\n<b>🎟️ Rotas em milhas</b>")
        n0 = len(estado["rotas"])
        for i, r in enumerate(estado["rotas_milhas"], n0 + 1):
            ult = f" · menor visto {milhar(r['menor'])} milhas" if r.get("menor") else ""
            linhas.append(f"{i}. {r['origem']}→{r['destino']} {br(r['inicio'])}–{br(r['fim'])}"
                          f" · até {milhar(r['milhas_max'])}{ult}")
    return "\n".join(linhas).strip()


def processar_comando(texto: str, estado: dict, tg: Telegram, chat_id) -> None:
    c = estado["config"]
    partes = texto.strip().split(maxsplit=1)
    cmd = partes[0].lower().split("@")[0]
    args = partes[1].strip() if len(partes) > 1 else ""
    responder = lambda msg: tg.enviar(chat_id, msg)  # noqa: E731

    if cmd in ("/start", "/ajuda", "/help"):
        responder(TEXTO_AJUDA)
        if cmd == "/start":
            responder(texto_status(estado))
            mostrar_ultimas(estado, tg, chat_id, primeira_vez=True)

    elif cmd == "/status":
        responder(texto_status(estado))

    elif cmd in ("/origens", "/origem"):
        if not args:
            responder("Use: <code>/origens FOR REC</code> ou <code>/origens todas</code>")
        elif normalizar(args) in ("todas", "todos", "qualquer"):
            c["origens"] = []
            responder("✅ Vou considerar promoções saindo de qualquer cidade.")
        else:
            c["origens"] = [interpretar_lugar(a) for a in dividir_args(args)]
            responder("✅ Origens: " + esc(", ".join(descrever_lugar(o) for o in c["origens"])))

    elif cmd == "/destinos":
        if not args:
            responder("Use: <code>/destinos Lisboa, Europa, SSA</code> ou <code>/destinos todos</code>")
        elif normalizar(args) in ("todos", "todas", "qualquer"):
            c["destinos"] = []
            responder("✅ Vou considerar qualquer destino.")
        else:
            c["destinos"] = [interpretar_lugar(a) for a in dividir_args(args)]
            responder("✅ Destinos: " + esc(", ".join(descrever_lugar(d) for d in c["destinos"])))

    elif cmd == "/adddestino" and args:
        for a in dividir_args(args):
            lugar = interpretar_lugar(a)
            if lugar not in c["destinos"]:
                c["destinos"].append(lugar)
        responder("✅ Destinos: " + esc(", ".join(descrever_lugar(d) for d in c["destinos"])))

    elif cmd == "/remdestino" and args:
        remover = {normalizar(interpretar_lugar(a)) for a in dividir_args(args)}
        c["destinos"] = [d for d in c["destinos"] if normalizar(d) not in remover]
        responder("✅ Destinos: " + (esc(", ".join(descrever_lugar(d) for d in c["destinos"])) or "qualquer destino"))

    elif cmd == "/tipo":
        t = normalizar(args)
        if t in ("nacional", "nacionais"):
            c["tipo"] = "nacional"
        elif t in ("internacional", "internacionais"):
            c["tipo"] = "internacional"
        elif t in ("ambos", "todos", "todas"):
            c["tipo"] = "ambos"
        else:
            responder("Use: <code>/tipo nacional</code>, <code>/tipo internacional</code> ou <code>/tipo ambos</code>")
            return
        responder(f"✅ Tipo de promoção: {c['tipo']}")

    elif cmd == "/precomax":
        if normalizar(args) in ("off", "nao", "sem", "0", ""):
            c["preco_max"] = None
            responder("✅ Sem limite de preço.")
        else:
            valor = numero(args)
            if valor:
                c["preco_max"] = valor
                responder(f"✅ Só aviso promoções até {reais(valor)} (as que não mostram preço continuam vindo).")
            else:
                responder("Use: <code>/precomax 1500</code>")

    elif cmd == "/milhas":
        c["milhas"] = normalizar(args) in ("sim", "s", "on", "ligar", "")
        responder(f"✅ Promoções de milhas/pontos: {'sim' if c['milhas'] else 'não'}")

    elif cmd == "/bonus":
        c["bonus"] = normalizar(args) in ("sim", "s", "on", "ligar", "")
        responder(f"✅ Bônus de transferência de pontos: {'sim' if c['bonus'] else 'não'}")

    elif cmd == "/milhasmax":
        if normalizar(args) in ("off", "nao", "sem", "0", ""):
            c["milhas_max"] = None
            responder("✅ Sem limite de milhas.")
        else:
            valor = numero(args)
            if valor and valor < 1000:   # "/milhasmax 40" = 40 mil
                valor *= 1000
            if valor:
                c["milhas_max"] = valor
                responder(f"✅ Só aviso passagens até {milhar(valor)} milhas/pontos por trecho.")
            else:
                responder("Use: <code>/milhasmax 40000</code>")

    elif cmd == "/pausar":
        c["pausado"] = True
        responder("⏸️ Alertas pausados. Use /retomar para voltar.")

    elif cmd == "/retomar":
        c["pausado"] = False
        responder("▶️ Alertas ligados!")

    elif cmd == "/ultimas":
        mostrar_ultimas(estado, tg, chat_id)

    elif cmd == "/rota":
        adicionar_rota(args, estado, tg, chat_id)

    elif cmd == "/rotamilhas":
        adicionar_rota_milhas(args, estado, tg, chat_id)

    elif cmd == "/rotas":
        responder(texto_rotas(estado))

    elif cmd in ("/removerrota", "/remrota"):
        try:
            n = int(args) - 1
            todas = estado["rotas"] + estado["rotas_milhas"]
            alvo = todas[n]
            if n < len(estado["rotas"]):
                estado["rotas"].remove(alvo)
            else:
                estado["rotas_milhas"].remove(alvo)
            responder(f"🗑️ Rota {alvo['origem']}→{alvo['destino']} removida.")
        except (ValueError, IndexError):
            responder("Use: <code>/removerrota 2</code> (veja os números em /rotas)")

    elif cmd == "/intervalo":
        valor = numero(args)
        if valor and 2 <= valor <= 168:
            c["intervalo_horas"] = int(valor)
            responder(f"✅ Cada rota será checada a cada {int(valor)}h."
                      f"\nℹ️ O plano grátis da SerpApi tem 250 buscas/mês: com {int(valor)}h, "
                      f"cabem ~{int(LIMITE_SERPAPI_PADRAO / (30 * 24 / valor))} rotas.")
        else:
            responder("Use: <code>/intervalo 12</code> (entre 2 e 168 horas)")

    elif cmd == "/checar":
        for r in estado["rotas"]:
            r["proxima"] = None
        for r in estado["rotas_milhas"]:
            r["proxima"] = None
        responder("🔎 Checando suas rotas agora…")
        estado["_forcar_rotas"] = True

    else:
        responder("Não entendi 🤔. Mande /ajuda para ver os comandos.")


def numero(texto: str) -> float | None:
    t = re.sub(r"[^\d,\.]", "", texto or "")
    if not t:
        return None
    t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def ler_comandos(estado: dict, tg: Telegram, dono_fixo: str | None) -> None:
    try:
        updates = tg.atualizacoes(estado["telegram_offset"])
    except requests.RequestException as e:
        print(f"[telegram] falha ao ler mensagens: {e}")
        return
    for up in updates:
        estado["telegram_offset"] = up["update_id"] + 1
        msg = up.get("message") or {}
        texto = (msg.get("text") or "").strip()
        chat_id = str((msg.get("chat") or {}).get("id", ""))
        if not texto or not chat_id:
            continue
        dono = dono_fixo or estado.get("chat_id")
        if not dono and texto.lower().startswith("/start"):
            estado["chat_id"] = dono = chat_id
            tg.enviar(chat_id, "🎉 Pronto! Este robô agora é seu. Só você recebe os alertas.")
        if chat_id != str(dono):
            tg.enviar(chat_id, "🔒 Este robô é particular.")
            continue
        if not texto.startswith("/"):
            tg.enviar(chat_id, "Mande /ajuda para ver os comandos.")
            continue
        try:
            processar_comando(texto, estado, tg, chat_id)
        except Exception as e:  # nunca derrubar o robô por um comando
            print(f"[comando] erro em {texto!r}: {e}")
            tg.enviar(chat_id, "⚠️ Deu um erro com esse comando. Confira o formato em /ajuda.")


# --------------------------------------------------------------------------- #
# Promoções (feeds RSS)
# --------------------------------------------------------------------------- #

RE_VOO = re.compile(r"passage|\bvoo|\bvoos\b|\bvoa\b|\bvoar\b|trecho|ida e volta|aere[oa]|"
                    r"\blatam\b|\bgol\b|\bazul\b|\btap\b|iberia|air france|american airlines|"
                    r"\bklm\b|emirates|qatar|copa airlines|aerolineas")
RE_MILHAS = re.compile(r"milhas|\bpontos\b|smiles|latam pass|tudoazul|azul fidelidade|livelo|"
                       r"esfera|transferencia bonificada|bonus de transferencia|resgate")
RE_NAO_VOO = re.compile(r"\bhote(l|is)\b|resort|ingresso|cruzeiro|aluguel de carro|seguro viagem|"
                        r"cartao de credito|chip|parque")
RE_PRECO = re.compile(r"r\$\s?(\d{1,3}(?:\.\d{3})+|\d+)(?:,\d{2})?")
RE_MILHAS_VALOR = re.compile(
    r"(\d{1,3}(?:[\.,]\d{1,3})?)\s?(mil|k)\s?(?:milhas|pontos)|(\d{1,3}(?:\.\d{3})+|\d{4,6})\s?(?:milhas|pontos)")


def extrair_precos(texto_norm: str) -> list[float]:
    valores = []
    for m in RE_PRECO.finditer(texto_norm):
        antes = texto_norm[max(0, m.start() - 12):m.start()]
        depois = texto_norm[m.end():m.end() + 16]
        if re.search(r"\b(ate|ganhe|economize|desconto de)\s*$", antes) or \
                re.match(r"\s*(off|de desconto|de cashback|de credito|em credito)", depois):
            continue
        v = float(m.group(1).replace(".", ""))
        if 50 <= v <= 50000:   # ignora "R$ 10 de desconto" e números estranhos
            valores.append(v)
    return valores


def extrair_milhas(texto_norm: str) -> list[float]:
    valores = []
    for m in RE_MILHAS_VALOR.finditer(texto_norm):
        if m.group(1):
            v = float(m.group(1).replace(",", ".")) * 1000
        else:
            v = float(m.group(3).replace(".", ""))
        if 1000 <= v <= 1_000_000:
            valores.append(v)
    return valores


def lugares_no_texto(texto_norm: str) -> set[str]:
    achados = set()
    for cod, (nome, apelidos, _) in LUGARES.items():
        if any(contem(texto_norm, normalizar(a)) for a in apelidos):
            achados.add(cod)
    return achados


def classificar(texto_norm: str, lugares: set[str]) -> str:
    internacional = any(LUGARES[c][2] != "BR" for c in lugares) or \
        any(contem(texto_norm, p) for p in PALAVRAS_INTERNACIONAIS)
    if internacional:
        return "internacional"
    if lugares:
        return "nacional"
    return "indefinido"


def bate_destino(destino: str, texto_norm: str, lugares: set[str]) -> bool:
    if destino in LUGARES:
        return destino in lugares
    n = normalizar(destino)
    regiao = REGIOES.get(n)
    if regiao == "BR-NE":
        return bool(lugares & NORDESTE)
    if regiao:
        if any(LUGARES[c][2] == regiao for c in lugares):
            return True
    return contem(texto_norm, n)


def bate_origem(origem: str, texto_norm: str) -> bool:
    if origem in LUGARES:
        return any(contem(texto_norm, normalizar(a)) for a in LUGARES[origem][1])
    return contem(texto_norm, normalizar(origem))


def avaliar_post(post: dict, config: dict) -> dict | None:
    """Devolve um dicionário com os dados do alerta, ou None se não bate com os filtros."""
    titulo_n = normalizar(post["titulo"])
    texto_n = normalizar(post["titulo"] + " " + post["texto"])

    eh_voo = bool(RE_VOO.search(titulo_n)) or (
        bool(RE_VOO.search(texto_n)) and not RE_NAO_VOO.search(titulo_n))
    eh_milhas = bool(RE_MILHAS.search(titulo_n))
    if not eh_voo and not eh_milhas:
        return None
    if eh_milhas and not eh_voo:
        # post só sobre pontos (bônus de transferência, compra de pontos etc.)
        if not config["bonus"]:
            return None
        return {"id": post["id"], "titulo": post["titulo"], "link": post["link"],
                "fonte": post["fonte"], "tipo": "bonus", "preco": None, "milhas": None,
                "eh_milhas": True, "data": post.get("data", "")}
    if eh_milhas and eh_voo and not config["milhas"] and "milhas" in titulo_n and "r$" not in titulo_n:
        return None

    lugares = lugares_no_texto(texto_n)
    tipo = classificar(texto_n, lugares)
    if config["tipo"] == "nacional" and tipo == "internacional":
        return None
    if config["tipo"] == "internacional" and tipo == "nacional":
        return None

    if config["origens"]:
        generica = any(g in texto_n for g in ORIGEM_GENERICA)
        if not generica and not any(bate_origem(o, texto_n) for o in config["origens"]):
            return None

    if config["destinos"]:
        if not any(bate_destino(d, texto_n, lugares) for d in config["destinos"]):
            return None

    precos = extrair_precos(titulo_n) or extrair_precos(texto_n)
    milhas = extrair_milhas(titulo_n) or extrair_milhas(texto_n)
    preco = min(precos) if precos else None
    qtd_milhas = min(milhas) if milhas else None

    if config["preco_max"] and preco and preco > config["preco_max"] and not (qtd_milhas and not precos):
        return None
    if config["milhas_max"] and qtd_milhas and qtd_milhas > config["milhas_max"] and not preco:
        return None

    return {
        "id": post["id"], "titulo": post["titulo"], "link": post["link"], "fonte": post["fonte"],
        "tipo": tipo, "preco": preco, "milhas": qtd_milhas, "eh_milhas": eh_milhas and not precos,
        "data": post.get("data", ""),
    }


def ler_feeds(estado: dict) -> list[dict]:
    posts = []
    for fonte, url in FEEDS.items():
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
            r.raise_for_status()
            feed = feedparser.parse(r.content)
            if not feed.entries:
                raise ValueError("feed vazio")
            estado["erros_feed"].pop(fonte, None)
        except Exception as e:
            estado["erros_feed"][fonte] = estado["erros_feed"].get(fonte, 0) + 1
            print(f"[feed] {fonte}: {e}")
            continue
        for e in feed.entries:
            conteudo = ""
            if e.get("content"):
                conteudo = " ".join(c.get("value", "") for c in e["content"])
            texto = limpar_html(e.get("summary", "") + " " + conteudo)[:6000]
            posts.append({
                "id": e.get("id") or e.get("link"),
                "titulo": limpar_html(e.get("title", "")),
                "link": e.get("link", ""),
                "texto": texto,
                "fonte": fonte,
                "data": e.get("published", ""),
            })
    return posts


def formatar_promo(p: dict) -> str:
    icone = "💳" if p["tipo"] == "bonus" else "🎟️" if p["eh_milhas"] else ("🌍" if p["tipo"] == "internacional" else "🇧🇷" if p["tipo"] == "nacional" else "✈️")
    extra = []
    if p["preco"]:
        extra.append(f"a partir de <b>{reais(p['preco'])}</b>")
    if p["milhas"]:
        extra.append(f"<b>{milhar(p['milhas'])}</b> milhas/pontos")
    linha_extra = (" · ".join(extra) + "\n") if extra else ""
    return (f"{icone} <b>{esc(p['titulo'])}</b>\n{linha_extra}"
            f"<i>{esc(p['fonte'])}</i> · <a href=\"{esc(p['link'])}\">ver promoção</a>")


def checar_promocoes(estado: dict, tg: Telegram) -> None:
    posts = ler_feeds(estado)
    vistos = set(estado["vistos"])
    novos = [p for p in reversed(posts) if p["id"] and p["id"] not in vistos]
    config = estado["config"]

    # Na primeira execução, só memoriza o que já existe (evita uma enxurrada de mensagens)
    primeira = not estado["feeds_iniciados"]
    alertas = []
    for p in novos:
        estado["vistos"].append(p["id"])
        estado["recentes"].append({**p, "texto": p["texto"][:1000]})
        a = avaliar_post(p, config)
        if a:
            alertas.append(a)
    if posts:
        estado["feeds_iniciados"] = True
    print(f"[feed] {len(posts)} posts, {len(novos)} novos, {len(alertas)} batem com filtros")

    if primeira or config["pausado"] or not estado.get("chat_id"):
        return
    for a in alertas[:MAX_ALERTAS_POR_EXECUCAO]:
        tg.enviar(estado["chat_id"], formatar_promo(a))
    if len(alertas) > MAX_ALERTAS_POR_EXECUCAO:
        tg.enviar(estado["chat_id"], f"…e mais {len(alertas) - MAX_ALERTAS_POR_EXECUCAO} promoções. Mande /ultimas para ver.")

    # Avisa uma vez se um site ficar fora do ar por muito tempo (~1 dia)
    for fonte, n in estado["erros_feed"].items():
        if n == 48:
            tg.enviar(estado["chat_id"], f"⚠️ Não consigo ler o site <b>{esc(fonte)}</b> há cerca de 1 dia. Os outros seguem funcionando.")


def mostrar_ultimas(estado: dict, tg: Telegram, chat_id, primeira_vez: bool = False) -> None:
    # reavalia com os filtros atuais (podem ter mudado)
    ultimas = [a for a in (avaliar_post(p, estado["config"]) for p in estado["recentes"]) if a]
    if not ultimas:
        if primeira_vez:
            tg.enviar(chat_id, "🔔 Assim que aparecer uma promoção que combine com seus filtros, eu te aviso aqui.")
        else:
            tg.enviar(chat_id, "Nenhuma das promoções recentes combina com seus filtros atuais.")
        return
    tg.enviar(chat_id, "<b>🗞️ Últimas promoções com seus filtros:</b>\n\n" +
              "\n\n".join(formatar_promo(p) for p in ultimas[-5:]))


# --------------------------------------------------------------------------- #
# Rotas em R$ (SerpApi / Google Flights)
# --------------------------------------------------------------------------- #

def adicionar_rota(args: str, estado: dict, tg: Telegram, chat_id) -> None:
    exemplo = ("Use: <code>/rota FOR LIS 10/03/2027 25/03/2027 3500</code>\n"
               "(a volta e o preço-alvo são opcionais)")
    t = args.split()
    if len(t) < 3:
        tg.enviar(chat_id, exemplo)
        return
    origem, destino = t[0].upper(), t[1].upper()
    if not (re.fullmatch(r"[A-Z]{3}", origem) and re.fullmatch(r"[A-Z]{3}", destino)):
        tg.enviar(chat_id, "Use os códigos de aeroporto com 3 letras (ex.: FOR, LIS, GRU).\n" + exemplo)
        return
    ida = ler_data(t[2])
    volta, teto = None, None
    for extra in t[3:]:
        if "/" in extra or "-" in extra:
            volta = ler_data(extra)
        else:
            teto = numero(extra)
    hoje = agora().date()
    if not ida or ida < hoje or (volta and volta < ida):
        tg.enviar(chat_id, "Datas inválidas (use dia/mês/ano e datas futuras).\n" + exemplo)
        return
    rota = {"origem": origem, "destino": destino, "ida": ida.isoformat(),
            "volta": volta.isoformat() if volta else None, "teto": teto,
            "ultimo_preco": None, "menor_preco": None, "ultimo_alerta": None,
            "historico": [], "proxima": None}
    estado["rotas"].append(rota)
    tg.enviar(chat_id, f"✅ Rota {nome_lugar(origem)} → {nome_lugar(destino)} adicionada. "
                       "Vou checar o preço na próxima rodada.")
    if not os.getenv("SERPAPI_KEY"):
        tg.enviar(chat_id, "⚠️ A chave da SerpApi ainda não foi configurada, então a rota fica "
                           "guardada mas não é checada. Veja o passo a passo.")


def link_google_flights(r: dict) -> str:
    q = f"Flights from {r['origem']} to {r['destino']} on {r['ida']}"
    if r.get("volta"):
        q += f" through {r['volta']}"
    else:
        q += " one way"
    return f"https://www.google.com/travel/flights?hl=pt-BR&curr=BRL&q={quote(q)}"


def consultar_serpapi(r: dict, chave: str) -> dict:
    params = {
        "engine": "google_flights", "departure_id": r["origem"], "arrival_id": r["destino"],
        "outbound_date": r["ida"], "type": "1" if r.get("volta") else "2",
        "currency": "BRL", "hl": "pt", "gl": "br", "api_key": chave,
    }
    if r.get("volta"):
        params["return_date"] = r["volta"]
    resp = requests.get("https://serpapi.com/search", params=params, timeout=60)
    dados = resp.json()
    if dados.get("error"):
        raise RuntimeError(dados["error"])
    voos = (dados.get("best_flights") or []) + (dados.get("other_flights") or [])
    voos = [v for v in voos if isinstance(v.get("price"), (int, float))]
    melhor = min(voos, key=lambda v: v["price"]) if voos else None
    insights = dados.get("price_insights") or {}
    preco = melhor["price"] if melhor else insights.get("lowest_price")
    cia = ""
    if melhor:
        cias = []
        for trecho in melhor.get("flights", []):
            if trecho.get("airline") and trecho["airline"] not in cias:
                cias.append(trecho["airline"])
        cia = " + ".join(cias)
        paradas = len(melhor.get("flights", [])) - 1
        cia += " · direto" if paradas == 0 else f" · {paradas} parada(s)"
    return {"preco": preco, "cia": cia, "nivel": insights.get("price_level"),
            "faixa": insights.get("typical_price_range")}


def checar_rotas(estado: dict, tg: Telegram) -> None:
    chave = os.getenv("SERPAPI_KEY")
    if not chave or not estado["rotas"]:
        return
    c = estado["config"]
    uso = estado["uso_serpapi"]
    mes = agora().strftime("%Y-%m")
    if uso.get("mes") != mes:
        uso.update({"mes": mes, "usadas": 0, "avisado": False})
    hoje = agora().date()
    chat = estado.get("chat_id")
    forcar = estado.get("_forcar_rotas", False)

    for r in list(estado["rotas"]):
        if date.fromisoformat(r["ida"]) < hoje:
            estado["rotas"].remove(r)
            tg.enviar(chat, f"📅 A rota {r['origem']}→{r['destino']} ({br(r['ida'])}) já passou e foi removida.")
            continue
        if r.get("proxima") and datetime.fromisoformat(r["proxima"]) > agora():
            continue
        if uso["usadas"] >= c["limite_serpapi"]:
            if not uso["avisado"]:
                tg.enviar(chat, "⚠️ Acabaram as buscas grátis da SerpApi deste mês. "
                                "As rotas voltam a ser checadas no dia 1º.")
                uso["avisado"] = True
            break
        try:
            res = consultar_serpapi(r, chave)
            uso["usadas"] += 1
        except Exception as e:
            print(f"[serpapi] {r['origem']}-{r['destino']}: {e}")
            r["proxima"] = (agora() + timedelta(hours=2)).isoformat()
            continue
        r["proxima"] = (agora() + timedelta(hours=c["intervalo_horas"])).isoformat()
        preco = res["preco"]
        if not preco:
            if forcar:
                tg.enviar(chat, f"🔎 {r['origem']}→{r['destino']}: nenhum voo encontrado para essas datas.")
            continue
        anterior = r.get("ultimo_preco")
        r["ultimo_preco"] = preco
        r["menor_preco"] = min(preco, r["menor_preco"] or preco)
        r["historico"] = (r.get("historico") or [])[-59:] + [[agora().strftime("%Y-%m-%d %H:%M"), preco]]

        motivo = motivo_alerta_rota(r, preco, anterior, res.get("nivel"))
        primeira_checagem = anterior is None
        if motivo or forcar or primeira_checagem:
            if motivo:
                r["ultimo_alerta"] = preco
            if not c["pausado"] or forcar:
                tg.enviar(chat, formatar_rota(r, res, motivo, anterior))


def motivo_alerta_rota(r: dict, preco: float, anterior: float | None, nivel: str | None) -> str | None:
    ja_avisado = r.get("ultimo_alerta")
    novo_minimo = ja_avisado is None or preco < ja_avisado * 0.97
    if r.get("teto") and preco <= r["teto"] and novo_minimo:
        return f"🎯 Abaixo do seu alvo de {reais(r['teto'])}!"
    if nivel == "low" and novo_minimo:
        return "📉 O Google classifica este preço como BAIXO para a rota."
    if anterior and preco <= anterior * 0.85:
        return f"📉 Caiu {round((1 - preco / anterior) * 100)}% desde a última checagem."
    return None


def formatar_rota(r: dict, res: dict, motivo: str | None, anterior: float | None) -> str:
    datas = br(r["ida"]) + (f" ↔ {br(r['volta'])}" if r.get("volta") else " (só ida)")
    nivel = {"low": "baixo 🟢", "typical": "normal 🟡", "high": "alto 🔴"}.get(res.get("nivel") or "", "")
    linhas = [motivo or "🔎 Preço atual da rota",
              f"<b>{esc(nome_lugar(r['origem']))} → {esc(nome_lugar(r['destino']))}</b> · {datas}",
              f"💰 <b>{reais(res['preco'])}</b>" + (f" · {esc(res['cia'])}" if res.get("cia") else "")]
    if anterior:
        linhas.append(f"Antes: {reais(anterior)} · menor já visto: {reais(r['menor_preco'])}")
    if nivel:
        faixa = res.get("faixa")
        linhas.append(f"Nível do preço: {nivel}" + (f" (normal: {reais(faixa[0])}–{reais(faixa[1])})" if faixa else ""))
    linhas.append(f"<a href=\"{link_google_flights(r)}\">abrir no Google Flights</a>")
    return "\n".join(linhas)


# --------------------------------------------------------------------------- #
# Rotas em milhas (Seats.aero — Smiles e Azul)
# --------------------------------------------------------------------------- #

def adicionar_rota_milhas(args: str, estado: dict, tg: Telegram, chat_id) -> None:
    exemplo = "Use: <code>/rotamilhas FOR LIS 01/03/2027 31/03/2027 60000</code>"
    t = args.split()
    if len(t) < 4:
        tg.enviar(chat_id, exemplo)
        return
    inicio, fim = ler_data(t[2]), ler_data(t[3])
    maximo = numero(t[4]) if len(t) > 4 else None
    if maximo and maximo < 1000:
        maximo *= 1000
    if not inicio or not fim or fim < inicio:
        tg.enviar(chat_id, "Datas inválidas.\n" + exemplo)
        return
    estado["rotas_milhas"].append({
        "origem": t[0].upper(), "destino": t[1].upper(), "inicio": inicio.isoformat(),
        "fim": fim.isoformat(), "milhas_max": maximo or 999999, "menor": None,
        "avisados": [], "proxima": None})
    tg.enviar(chat_id, f"✅ Rota em milhas {t[0].upper()}→{t[1].upper()} adicionada (Smiles e Azul).")
    if not os.getenv("SEATS_AERO_KEY"):
        tg.enviar(chat_id, "⚠️ Essa função precisa da chave do Seats.aero (assinatura Pro). "
                           "Sem ela, a rota fica guardada mas não é checada.")


def checar_rotas_milhas(estado: dict, tg: Telegram) -> None:
    chave = os.getenv("SEATS_AERO_KEY")
    if not chave or not estado["rotas_milhas"]:
        return
    uso = estado["uso_seats"]
    dia = agora().strftime("%Y-%m-%d")
    if uso.get("dia") != dia:
        uso.update({"dia": dia, "usadas": 0})
    chat = estado.get("chat_id")
    hoje = agora().date()
    forcar = estado.get("_forcar_rotas", False)

    for r in list(estado["rotas_milhas"]):
        if date.fromisoformat(r["fim"]) < hoje:
            estado["rotas_milhas"].remove(r)
            continue
        if r.get("proxima") and datetime.fromisoformat(r["proxima"]) > agora():
            continue
        if uso["usadas"] >= LIMITE_SEATS_DIA:
            break
        try:
            resp = requests.get("https://seats.aero/partnerapi/search", timeout=60,
                                headers={"Partner-Authorization": chave, "accept": "application/json"},
                                params={"origin_airport": r["origem"], "destination_airport": r["destino"],
                                        "start_date": max(r["inicio"], hoje.isoformat()), "end_date": r["fim"],
                                        "sources": "smiles,azul", "order_by": "lowest_mileage", "take": 100})
            uso["usadas"] += 1
            resp.raise_for_status()
            dados = resp.json().get("data", [])
        except Exception as e:
            print(f"[seats] {r['origem']}-{r['destino']}: {e}")
            continue
        r["proxima"] = (agora() + timedelta(hours=6)).isoformat()

        ofertas = []
        for d in dados:
            for cabine, nome in (("Y", "econômica"), ("W", "premium"), ("J", "executiva")):
                if d.get(f"{cabine}Available"):
                    custo = numero(str(d.get(f"{cabine}MileageCost") or ""))
                    if custo and custo <= r["milhas_max"]:
                        ofertas.append({"data": d.get("Date"), "programa": d.get("Source"),
                                        "cabine": nome, "milhas": custo,
                                        "cias": d.get(f"{cabine}Airlines") or "",
                                        "direto": d.get(f"{cabine}Direct")})
        ofertas.sort(key=lambda o: o["milhas"])
        novas = []
        for o in ofertas:
            chave_oferta = f"{o['data']}|{o['programa']}|{o['cabine']}|{int(o['milhas'])}"
            if chave_oferta not in r["avisados"]:
                r["avisados"].append(chave_oferta)
                novas.append(o)
        r["avisados"] = r["avisados"][-300:]
        if ofertas:
            r["menor"] = min(r["menor"] or ofertas[0]["milhas"], ofertas[0]["milhas"])
        if (novas or forcar) and (not estado["config"]["pausado"] or forcar):
            mostrar = novas[:6] if novas else ofertas[:3]
            if not mostrar:
                tg.enviar(chat, f"🎟️ {r['origem']}→{r['destino']}: nada abaixo de {milhar(r['milhas_max'])} milhas por enquanto.")
                continue
            prog = {"smiles": "Smiles", "azul": "Azul Fidelidade"}
            linhas = [f"🎟️ <b>Milhas: {esc(nome_lugar(r['origem']))} → {esc(nome_lugar(r['destino']))}</b>"]
            for o in mostrar:
                linhas.append(f"• {br(o['data'])} · <b>{milhar(o['milhas'])}</b> {prog.get(o['programa'], o['programa'])}"
                              f" · {o['cabine']}{' · direto' if o['direto'] else ''}"
                              + (f" · {esc(o['cias'])}" if o['cias'] else ""))
            linhas.append("Confirme no site do programa antes de transferir pontos (as taxas não estão incluídas).")
            tg.enviar(chat, "\n".join(linhas))


# --------------------------------------------------------------------------- #
# Principal
# --------------------------------------------------------------------------- #

def main() -> int:
    token = os.getenv("TELEGRAM_TOKEN", "").strip()
    if not token:
        print("ERRO: configure o secret TELEGRAM_TOKEN.")
        return 1
    dono_fixo = os.getenv("TELEGRAM_CHAT_ID", "").strip() or None

    estado = carregar_estado()
    if dono_fixo:
        estado["chat_id"] = dono_fixo
    tg = Telegram(token)

    etapas = [("comandos", lambda: ler_comandos(estado, tg, dono_fixo)),
              ("promoções", lambda: checar_promocoes(estado, tg)),
              ("rotas", lambda: checar_rotas(estado, tg)),
              ("milhas", lambda: checar_rotas_milhas(estado, tg))]
    for nome, etapa in etapas:
        try:
            etapa()
        except Exception as e:  # uma etapa com problema não impede as outras
            print(f"[{nome}] erro inesperado: {e}")
        salvar_estado(estado)
    estado.pop("_forcar_rotas", None)
    salvar_estado(estado)
    print(f"[fim] mensagens enviadas: {tg.enviadas}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
