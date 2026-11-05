"""Cidades/aeroportos conhecidos pelo robô.

Cada entrada: código IATA -> (nome para exibir, [apelidos para buscar no texto], "BR" ou região)
Os apelidos são comparados sem acento e em minúsculas.
Para nomes ambíguos (ex.: "Natal", "Vitória"), os apelidos exigem contexto ("para natal").
"""

LUGARES = {
    # ---------------- Brasil ----------------
    "FOR": ("Fortaleza", ["fortaleza"], "BR"),
    "JJD": ("Jericoacoara", ["jericoacoara", "jeri"], "BR"),
    "JDO": ("Juazeiro do Norte", ["juazeiro do norte"], "BR"),
    "REC": ("Recife", ["recife"], "BR"),
    "FEN": ("Fernando de Noronha", ["noronha"], "BR"),
    "NAT": ("Natal", ["para natal", "pra natal", "em natal", "saindo de natal", "natal (rn)", "natal/rn", "natal-rn", "natal e ", ", natal"], "BR"),
    "JPA": ("João Pessoa", ["joao pessoa"], "BR"),
    "MCZ": ("Maceió", ["maceio"], "BR"),
    "AJU": ("Aracaju", ["aracaju"], "BR"),
    "SSA": ("Salvador", ["salvador"], "BR"),
    "BPS": ("Porto Seguro", ["porto seguro"], "BR"),
    "IOS": ("Ilhéus", ["ilheus"], "BR"),
    "PNZ": ("Petrolina", ["petrolina"], "BR"),
    "SLZ": ("São Luís", ["sao luis"], "BR"),
    "THE": ("Teresina", ["teresina"], "BR"),
    "BEL": ("Belém", ["belem"], "BR"),
    "STM": ("Santarém", ["santarem"], "BR"),
    "MAO": ("Manaus", ["manaus"], "BR"),
    "MCP": ("Macapá", ["macapa"], "BR"),
    "BVB": ("Boa Vista", ["boa vista"], "BR"),
    "PVH": ("Porto Velho", ["porto velho"], "BR"),
    "RBR": ("Rio Branco", ["rio branco"], "BR"),
    "PMW": ("Palmas", ["para palmas", "pra palmas", "palmas (to)", "palmas/to", "saindo de palmas"], "BR"),
    "BSB": ("Brasília", ["brasilia"], "BR"),
    "GYN": ("Goiânia", ["goiania"], "BR"),
    "CGB": ("Cuiabá", ["cuiaba"], "BR"),
    "CGR": ("Campo Grande", ["campo grande"], "BR"),
    "BYO": ("Bonito", ["bonito (ms)", "para bonito", "pra bonito"], "BR"),
    "SAO": ("São Paulo", ["sao paulo", "guarulhos", "congonhas"], "BR"),
    "VCP": ("Campinas", ["campinas", "viracopos"], "BR"),
    "RIO": ("Rio de Janeiro", ["rio de janeiro", "galeao", "santos dumont"], "BR"),
    "CNF": ("Belo Horizonte", ["belo horizonte", "confins"], "BR"),
    "VIX": ("Vitória", ["para vitoria", "pra vitoria", "vitoria (es)", "vitoria/es", "saindo de vitoria"], "BR"),
    "UDI": ("Uberlândia", ["uberlandia"], "BR"),
    "CWB": ("Curitiba", ["curitiba"], "BR"),
    "IGU": ("Foz do Iguaçu", ["foz do iguacu"], "BR"),
    "FLN": ("Florianópolis", ["florianopolis", "floripa"], "BR"),
    "NVT": ("Navegantes", ["navegantes", "balneario camboriu"], "BR"),
    "POA": ("Porto Alegre", ["porto alegre"], "BR"),
    "LDB": ("Londrina", ["londrina"], "BR"),
    "MGF": ("Maringá", ["maringa"], "BR"),
    "JOI": ("Joinville", ["joinville"], "BR"),
    "CXJ": ("Caxias do Sul", ["caxias do sul", "gramado"], "BR"),
    "IMP": ("Imperatriz", ["imperatriz"], "BR"),
    # ---------------- Internacional ----------------
    "LIS": ("Lisboa", ["lisboa"], "Europa"),
    "OPO": ("Porto (Portugal)", ["porto (portugal)", "cidade do porto", "para o porto"], "Europa"),
    "MAD": ("Madri", ["madri", "madrid"], "Europa"),
    "BCN": ("Barcelona", ["barcelona"], "Europa"),
    "PAR": ("Paris", ["paris"], "Europa"),
    "LON": ("Londres", ["londres"], "Europa"),
    "ROM": ("Roma", ["roma"], "Europa"),
    "MIL": ("Milão", ["milao"], "Europa"),
    "FRA": ("Frankfurt", ["frankfurt"], "Europa"),
    "MUC": ("Munique", ["munique"], "Europa"),
    "AMS": ("Amsterdã", ["amsterda", "amsterdam"], "Europa"),
    "BRU": ("Bruxelas", ["bruxelas"], "Europa"),
    "ZRH": ("Zurique", ["zurique"], "Europa"),
    "VIE": ("Viena", ["viena"], "Europa"),
    "PRG": ("Praga", ["praga"], "Europa"),
    "ATH": ("Atenas", ["atenas"], "Europa"),
    "DUB": ("Dublin", ["dublin"], "Europa"),
    "IST": ("Istambul", ["istambul"], "Europa"),
    "MIA": ("Miami", ["miami"], "América do Norte"),
    "FLL": ("Fort Lauderdale", ["fort lauderdale"], "América do Norte"),
    "MCO": ("Orlando", ["orlando"], "América do Norte"),
    "NYC": ("Nova York", ["nova york", "nova iorque", "new york"], "América do Norte"),
    "BOS": ("Boston", ["boston"], "América do Norte"),
    "ATL": ("Atlanta", ["atlanta"], "América do Norte"),
    "LAX": ("Los Angeles", ["los angeles"], "América do Norte"),
    "LAS": ("Las Vegas", ["las vegas"], "América do Norte"),
    "YTO": ("Toronto", ["toronto"], "América do Norte"),
    "MEX": ("Cidade do México", ["cidade do mexico"], "América do Norte"),
    "CUN": ("Cancún", ["cancun"], "Caribe"),
    "PUJ": ("Punta Cana", ["punta cana"], "Caribe"),
    "PTY": ("Cidade do Panamá", ["panama"], "Caribe"),
    "AUA": ("Aruba", ["aruba"], "Caribe"),
    "CUR": ("Curaçao", ["curacao"], "Caribe"),
    "BUE": ("Buenos Aires", ["buenos aires"], "América do Sul"),
    "BRC": ("Bariloche", ["bariloche"], "América do Sul"),
    "SCL": ("Santiago", ["santiago do chile", "santiago (chile)", "para santiago", "pra santiago"], "América do Sul"),
    "MVD": ("Montevidéu", ["montevideu"], "América do Sul"),
    "PDP": ("Punta del Este", ["punta del este"], "América do Sul"),
    "LIM": ("Lima", ["para lima", "pra lima", "lima (peru)", "lima, peru"], "América do Sul"),
    "CUZ": ("Cusco", ["cusco", "machu picchu"], "América do Sul"),
    "BOG": ("Bogotá", ["bogota"], "América do Sul"),
    "CTG": ("Cartagena", ["cartagena"], "América do Sul"),
    "ASU": ("Assunção", ["assuncao"], "América do Sul"),
    "DXB": ("Dubai", ["dubai"], "Oriente Médio"),
    "DOH": ("Doha", ["doha", "catar"], "Oriente Médio"),
    "TYO": ("Tóquio", ["toquio", "japao"], "Ásia"),
    "BKK": ("Bangkok", ["bangkok", "tailandia"], "Ásia"),
    "CPT": ("Cidade do Cabo", ["cidade do cabo"], "África"),
    "JNB": ("Joanesburgo", ["joanesburgo"], "África"),
    "CAI": ("Cairo", ["cairo", "egito"], "África"),
    "SYD": ("Sydney", ["sydney"], "Oceania"),
}

# Palavras que indicam viagem internacional mesmo sem cidade conhecida
PALAVRAS_INTERNACIONAIS = [
    "internacional", "internacionais", "exterior", "europa", "estados unidos", "eua",
    "portugal", "espanha", "italia", "franca", "alemanha", "inglaterra", "reino unido",
    "holanda", "suica", "grecia", "irlanda", "turquia", "canada", "mexico", "caribe",
    "argentina", "chile", "uruguai", "peru", "colombia", "paraguai", "bolivia",
    "asia", "africa", "oceania", "australia", "oriente medio", "emirados",
]

# Expressões que indicam várias cidades de origem (a promoção pode valer para você)
ORIGEM_GENERICA = [
    "varias cidades", "diversas cidades", "varias origens", "diversas origens",
    "todo o brasil", "varias capitais", "diversas capitais", "todas as regioes",
    "partindo de varias", "saindo de varias", "saindo de diversas", "de todo o pais",
]

# Regiões que o usuário pode usar como destino (ex.: /destinos Europa)
REGIOES = {
    "europa": "Europa",
    "america do norte": "América do Norte",
    "eua": "América do Norte",
    "estados unidos": "América do Norte",
    "caribe": "Caribe",
    "america do sul": "América do Sul",
    "asia": "Ásia",
    "africa": "África",
    "oriente medio": "Oriente Médio",
    "oceania": "Oceania",
    "nordeste": "BR-NE",
}

NORDESTE = {"FOR", "JJD", "JDO", "REC", "FEN", "NAT", "JPA", "MCZ", "AJU", "SSA",
            "BPS", "IOS", "PNZ", "SLZ", "THE", "IMP"}

# Códigos de aeroporto que pertencem a uma cidade com código "metropolitano"
AEROPORTO_PARA_CIDADE = {
    "GRU": "SAO", "CGH": "SAO", "GIG": "RIO", "SDU": "RIO", "CDG": "PAR", "ORY": "PAR",
    "LHR": "LON", "LGW": "LON", "FCO": "ROM", "MXP": "MIL", "JFK": "NYC", "EWR": "NYC",
    "EZE": "BUE", "AEP": "BUE", "NRT": "TYO", "HND": "TYO", "YYZ": "YTO", "PLU": "CNF",
}
