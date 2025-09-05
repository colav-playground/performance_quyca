from itertools import product
import random

BASE_URL = "http://localhost:8010"

# Lista de endpoints /api con placeholders
RAW_ENDPOINTS = [
    "/api/affiliation/<affiliation_type>/<affiliation_id>/research/products",
    "/api/apc/affiliation/<affiliation_id>",
    "/api/apc/person/<person_id>",
    "/api/apc/search",
    "/api/person/<person_id>",
    "/api/person/<person_id>/research/products",
    "/api/person/<person_id>/research/news",
    "/api/search/affiliations/<affiliation_type>",
    "/api/search/person",
    "/api/search/works"
]

# Valores de prueba que nos diste
AFFILIATION_IDS = [
    "01p9nak43", "04j43p132", "027nnzv91", "059d6yn51", "0374c0d66",
    "006703856", "057jm7w82", "05sq6ae13", "05w5shm69", "03ag0xf08"
]
PERSON_IDS = [
    "A5105622035", "A5112693177", "0000000347185957", "A5113454003",
    "A5092999615", "0000000294031566", "A5106325669", "0001513368",
    "A5041111652", "Gwak4WYAAAAJ'"
]
AFFILIATION_TYPES = ["institution"]

# Armamos un diccionario de listas para los placeholders
PARAM_VALUES = {
    "<affiliation_type>": AFFILIATION_TYPES,
    "<affiliation_id>": AFFILIATION_IDS,
    "<person_id>": PERSON_IDS
}

# Endpoints que necesitan query params extra
KEYWORDS = {
    "/api/search/affiliations": ["university", "andes", "antioquia", "open"],
    "/api/search/person": ["esteban", "alejandra", "jaime", "garcia"],
    "/api/search/works": ["ciencia", "data", "ai", "salud"],
    "/api/apc/search": ["500", "1000", "1500", "2000"]
}

def expand_endpoints():
    """
    Genera todas las URLs reemplazando los placeholders
    con valores de prueba (tomamos solo unos pocos para no hacer explosión combinatoria).
    También agrega query params a los endpoints que lo requieran.
    """
    urls = []
    for endpoint in RAW_ENDPOINTS:
        # Con placeholders affiliation_type + affiliation_id
        if "<affiliation_type>" in endpoint and "<affiliation_id>" in endpoint:
            for affiliation_type, affiliation_id in product(AFFILIATION_TYPES, AFFILIATION_IDS[:3]):
                url = endpoint.replace("<affiliation_type>", affiliation_type).replace("<affiliation_id>", affiliation_id)
                urls.append(BASE_URL + url)

        # Con placeholder affiliation_id
        elif "<affiliation_id>" in endpoint:
            for affiliation_id in AFFILIATION_IDS[:3]:
                url = endpoint.replace("<affiliation_id>", affiliation_id)
                urls.append(BASE_URL + url)

        # Con placeholder person_id
        elif "<person_id>" in endpoint:
            for person_id in PERSON_IDS[:3]:
                url = endpoint.replace("<person_id>", person_id)
                urls.append(BASE_URL + url)

        elif "<affiliation_type>" in endpoint:
            for affiliation_type in AFFILIATION_TYPES:
                url = endpoint.replace("<affiliation_type>", affiliation_type)
                urls.append(BASE_URL + url)

        # Endpoints sin placeholders pero con query params
        elif endpoint in KEYWORDS:
            keyword = random.choice(KEYWORDS[endpoint])
            urls.append(f"{BASE_URL}{endpoint}?keywords={keyword}")

        # Endpoints planos
        else:
            urls.append(BASE_URL + endpoint)

    return urls