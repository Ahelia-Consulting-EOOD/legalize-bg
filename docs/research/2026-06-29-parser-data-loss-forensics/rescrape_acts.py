#!/usr/bin/env python3
"""Re-scrape the 12 DRS-consumer acts from lex.bg (Cloudflare cleared via cf_clearance),
with the FIXED body parser. Writes laws/<slug>.md. Rate-limited 1 req/s. Saves raw HTML.
"""
import re, sys, time, shutil
from pathlib import Path
import requests
from bs4 import BeautifulSoup, Tag

ROOT = Path("/Users/ekimir/swprj/legalize-bg"); sys.path.insert(0, str(ROOT))
from fetcher.bg.text_parser import HtmlToMarkdown, CLASS_MAP
from fetcher.bg.metadata import MetadataParser
from fetcher.bg.assembler import assemble_file

RAW = Path("/private/tmp/claude-501/-Users-ekimir-swprj-legalize-bg/acbebd20-17b3-48f9-b315-56c69fae83a7/scratchpad/raw12")
RAW.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
CF = "<cf_clearance token — refresh via Playwright browser: navigate lex.bg, clear CF, read context.cookies>"

ACTS = [
    ("targovski-zakon", -14917630),
    ("zakon-za-publichnite-predpriyatiya", 2137196641),
    ("zakon-za-opazvane-na-okolnata-sreda", 2135458102),
    ("zakon-za-normativnite-aktove", 2127837184),
    ("zakon-za-zashtita-na-potrebitelite", 2135513678),
    ("zakon-za-hranite", 2137203080),
    ("zakon-za-vinoto-i-spirtnite-napitki", 2135798102),
    ("zakon-za-danak-varhu-dobavenata-stoynost", 2135533201),
    ("zakon-za-korporativnoto-podohodno-oblagane", 2135540562),
    ("zakon-za-schetovodstvoto", 2136697598),
    ("zakon-za-mestnite-danatsi-i-taksi", 2134174720),
    ("zakon-za-aktsizite-i-danachnite-skladove", 2135512728),
]

EXT = {**CLASS_MAP, "AdditionalEdicts": ("## ", True), "FinalEdicts": ("## ", True),
       "FinalEdictsArticle": ("", True)}


class FixedHtmlToMarkdown(HtmlToMarkdown):
    def _mapped(self, el):
        for c in el.get("class", []):
            if c in EXT:
                return c
        return None

    def _block_text(self, el):
        out = []
        def walk(node):
            for ch in node.children:
                if isinstance(ch, Tag):
                    if ch.name == "br":
                        out.append("\n")
                    elif ch.name in ("div", "p", "li", "tr"):
                        out.append("\n"); walk(ch); out.append("\n")
                    else:
                        walk(ch)
                else:
                    out.append(str(ch))
        walk(el)
        lines = [re.sub(r"[ \t ]+", " ", l).strip() for l in "".join(out).split("\n")]
        return "\n\n".join(l for l in lines if l)

    def _format_edict_article(self, el):
        text = self._block_text(el)
        m = re.match(r"^(§\s*\d+[а-я]?\.)", text) or re.match(r"^(Чл\.\s*\d+[а-я]?\.)", text)
        return f"**{m.group(1)}**{text[m.end():]}" if m else text

    def convert(self, soup):
        lines = []
        for el in soup.find_all(class_=list(EXT.keys())):
            if not isinstance(el, Tag):
                continue
            css = self._mapped(el)
            if css is None:
                continue
            prefix, include = EXT[css]
            if not include:
                continue
            if css == "Article":
                lines.append(self._format_article(el))
            elif css == "FinalEdictsArticle":
                lines.append(self._format_edict_article(el))
            elif css == "PreHistory":
                t = el.get_text(strip=True)
                if t:
                    lines.append(f"*{t}*")
            else:
                t = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
                if t:
                    lines.append(f"{prefix}{t}")
            lines.append("")
        return "\n".join(lines).strip() + "\n"


def main():
    sess = requests.Session()
    sess.headers.update({"User-Agent": UA,
                         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                         "Accept-Language": "bg,en;q=0.9"})
    sess.cookies.set("cf_clearance", CF, domain=".lex.bg")
    results = []
    for i, (slug, doc_id) in enumerate(ACTS):
        if i > 0:
            time.sleep(1.0)  # rate limit 1 req/s
        url = f"https://lex.bg/laws/ldoc/{doc_id}"
        r = sess.get(url, timeout=40)
        blocked = r.headers.get("cf-mitigated") == "challenge" or b"Just a moment" in r.content[:3000]
        if r.status_code != 200 or blocked:
            results.append((slug, doc_id, f"FETCH-FAIL status={r.status_code} cf={blocked}", 0))
            print(f"[{i+1:2}/12] {slug:46} FETCH-FAIL status={r.status_code} cf-blocked={blocked}")
            continue
        (RAW / f"{slug}.html").write_bytes(r.content)
        soup = BeautifulSoup(r.content.decode("cp1251", errors="replace"), "lxml")
        meta = MetadataParser().parse(soup, doc_id, "laws")
        body = FixedHtmlToMarkdown().convert(soup)
        out = assemble_file(meta, body)
        target = ROOT / f"laws/{slug}.md"
        target.write_text(out, encoding="utf-8")
        base_dr = len([m for m in re.finditer(r"Допълнителни разпоредби", out)
                       if "КЪМ" not in out[m.end():m.end()+30]])
        results.append((slug, doc_id, "OK", len(out)))
        print(f"[{i+1:2}/12] {slug:46} OK  {len(out):>8,} chars  base-ДР={base_dr}  title={meta['titulo'][:30]!r}")
    print("\nfetch summary:", sum(1 for _,_,s,_ in results if s == "OK"), "/ 12 OK")
    fails = [r for r in results if r[2] != "OK"]
    if fails:
        print("FAILURES:", fails)

if __name__ == "__main__":
    main()
