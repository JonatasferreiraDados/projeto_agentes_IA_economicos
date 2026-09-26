# scripts/noticias.py

import os
import sys
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime

# ============================================================
# Configurações de diretório e arquivo de saída
# ============================================================

# Diretório raiz do projeto (assumindo que este script está em scripts/)
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

ARQUIVO_SAIDA = DATA_DIR / "noticias_investimentos.csv"

# ============================================================
# Parâmetros de scraping
# ============================================================

PALAVRAS_CHAVE = [
    "ipca", "inflação", "selic", "juros", "bovespa", "ações", "investimentos",
    "bolsa", "ibovespa", "economia", "mercado", "taxa básica", "taxa de juros"
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
        "Edg/153.0.0.0"
    )
}

SITES = {
    "CNN Brasil": "https://www.cnnbrasil.com.br/economia/",
    "G1 Economia": "https://g1.globo.com/economia/",
    "InfoMoney Mercados": "https://www.infomoney.com.br/mercados/",
    "Exame Economia": "https://exame.com/economia/",
}

# ============================================================
# Funções auxiliares
# ============================================================

def filtrar_noticias(html: str, base_url: str, fonte: str) -> list[dict]:
    """
    Recebe o HTML de uma página, a base_url do site e o nome da fonte.
    Retorna uma lista de dicionários com título, link, fonte e data_coleta.
    """
    soup = BeautifulSoup(html, "html.parser")
    encontrados: list[dict] = []

    for a in soup.find_all("a", href=True):
        titulo = a.get_text().strip()
        titulo_lower = titulo.lower()
        link = a["href"].strip()

        # Ignorar títulos vazios ou muito curtos
        if not titulo or len(titulo_lower) < 10:
            continue

        # Verificar se contém algum termo de interesse
        if not any(palavra in titulo_lower for palavra in PALAVRAS_CHAVE):
            continue

        # Normalizar link
        if link.startswith("/"):
            # Construir link absoluto
            link = base_url.rstrip("/") + link

        # Filtrar links estranhos
        if not (link.startswith("http://") or link.startswith("https://")):
            continue

        encontrados.append(
            {
                "titulo": titulo.strip(),
                "link": link,
                "fonte": fonte,
                "data_coleta": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return encontrados


# ============================================================
# Execução principal
# ============================================================

def main():
    noticias: list[dict] = []

    for nome_site, url in SITES.items():
        print(f"🔎 Coletando notícias de: {nome_site} ({url})")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
        except Exception as e:
            print(f"❌ Erro de conexão ao acessar {nome_site}: {e}")
            continue

        if resp.status_code != 200:
            print(f"❌ Erro HTTP ao acessar {nome_site}: Status {resp.status_code}")
            continue

        # base_url = "https://g1.globo.com" etc.
        base_url = "/".join(url.split("/")[:3])

        try:
            encontrados = filtrar_noticias(resp.text, base_url, nome_site)
            print(f"✅ Encontradas {len(encontrados)} notícias relevantes em {nome_site}.")
            noticias.extend(encontrados)
        except Exception as e:
            print(f"❌ Erro ao processar HTML de {nome_site}: {e}")
            continue

    if not noticias:
        print("ℹ️ Nenhuma notícia encontrada com os filtros atuais.")
        # Não consideramos erro fatal para CI/CD
        return

    # Remover duplicadas por combinação de (titulo, link)
    df = pd.DataFrame(noticias)
    antes = len(df)
    df = df.drop_duplicates(subset=["titulo", "link"])
    depois = len(df)

    print(f"🧹 Removidas {antes - depois} duplicatas. Total final: {depois} notícias.")

    try:
        df.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8-sig")
        print(f"📁 CSV de notícias salvo em: {ARQUIVO_SAIDA}")
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo '{ARQUIVO_SAIDA}': {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
