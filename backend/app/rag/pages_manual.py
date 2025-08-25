import sys, time, argparse
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs, urlencode
import requests
from bs4 import BeautifulSoup

BASE = "https://ajuda.infinitepay.io/pt-BR/"
DOMAIN = "ajuda.infinitepay.io"
HEADERS = {"User-Agent":"Mozilla/5.0 (compatible; InfinitePagesCrawler/1.0)",
           "Accept-Language":"pt-BR,pt;q=0.9,en;q=0.8"}

def http_get(url: str, retries: int = 3, sleep: float = 0.8) -> str:
    for _ in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
        time.sleep(sleep)
    return ""

def normalize(u: str) -> str:
    p = list(urlparse(u))
    p[0] = "https"; p[1] = DOMAIN; p[5] = ""
    q = parse_qs(p[4] or "")
    if "page" in q and q["page"] == ["1"]:
        q.pop("page", None)
    p[4] = urlencode({k:v[0] for k,v in q.items()})
    return urlunparse(p)

def extract_links(html: str, base: str):
    soup = BeautifulSoup(html, "lxml")
    out = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base, a["href"])
        if urlparse(href).netloc == DOMAIN:
            out.add(normalize(href))
    return out

def collect_all_articles() -> list[str]:
    home = http_get(BASE)
    if not home:
        print("ERRO: não consegui baixar a home.", file=sys.stderr); sys.exit(2)
    to_visit = {u for u in extract_links(home, BASE) if "/collections/" in u}
    visited, articles = set(), set()
    while to_visit:
        u = to_visit.pop()
        if u in visited: continue
        visited.add(u)
        html = http_get(u)
        if not html: continue
        links = extract_links(html, u)
        for lk in links:
            if "/articles/" in lk: articles.add(lk)
            if "/collections/" in lk: to_visit.add(lk)
    return sorted(articles)

def write_pages_py(urls: list[str], out_path: str):
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("PAGES = [\n")
        for u in urls:
            f.write(f'    "{u}",\n')
        f.write("]\n")
    print(f"[OK] Gerado {out_path} ({len(urls)} URLs)")

def write_json(urls: list[str], json_path: str):
    import json
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(urls, f, ensure_ascii=False, indent=2)
    print(f"[OK] JSON em {json_path} ({len(urls)} URLs)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="app/rag/pages_auto.py")
    ap.add_argument("--json", default="")
    args = ap.parse_args()
    urls = collect_all_articles()
    if not urls:
        print("ATENÇÃO: 0 URLs encontradas.", file=sys.stderr); sys.exit(1)
    write_pages_py(urls, args.out)
    if args.json:
        write_json(urls, args.json)

if __name__ == "__main__":
    main()
