#!/usr/bin/env python3
"""Re-scrape the FULL current ЗУО with a FIXED body parser, RIGHT NOW.

Faithful to the real pipeline (LexBgClient.fetch_soup -> MetadataParser -> assemble_file),
swapping ONLY the body converter for a fixed one that captures the three dropped
subdivision classes and de-glues headings. Does NOT edit the protected parser module.

Fetch: live lex.bg (ldoc 2135802037) with the project's rate-limited client; on any
network/Cloudflare failure, fall back to the 2026-06-21 capture (ЗУО is unchanged since
dv 81/2024, so the fallback is the same current text).
"""
import re, sys, shutil
from pathlib import Path
from bs4 import BeautifulSoup, Tag

ROOT = Path("/Users/ekimir/swprj/legalize-bg"); sys.path.insert(0, str(ROOT))
from fetcher.bg.text_parser import HtmlToMarkdown, CLASS_MAP
from fetcher.bg.metadata import MetadataParser
from fetcher.bg.assembler import assemble_file
from fetcher.bg.client import LexBgClient, HttpTransport

DOC_ID = 2135802037
CATEGORY = "laws"
TARGET = ROOT / "laws/zakon-za-upravlenie-na-otpadatsite.md"
RESEARCH = ROOT / "docs/research/2026-06-29-parser-data-loss-forensics"
SAVED = Path("/Users/ekimir/swprj/drs-business-work/source-extracts/national-law/zuo-lexbg-2026-06-21.html")

# extended map: the 3 dropped classes added (FEA gets structured handling, not crude get_text)
EXT = {**CLASS_MAP,
       "AdditionalEdicts": ("## ", True),
       "FinalEdicts": ("## ", True),
       "FinalEdictsArticle": ("", True)}


class FixedHtmlToMarkdown(HtmlToMarkdown):
    def _mapped(self, el):
        for c in el.get("class", []):
            if c in EXT:
                return c
        return None

    def _block_text(self, el):
        """Flatten, treating <br> and block tags as line breaks (so §1 точки as <div>s,
        and alineas separated by <br>, each become their own paragraph)."""
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
        lines = [re.sub(r"[ \t ]+", " ", l).strip() for l in "".join(out).split("\n")]
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
            else:  # heading classes — de-glue with a separator, collapse whitespace
                t = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
                if t:
                    lines.append(f"{prefix}{t}")
            lines.append("")
        return "\n".join(lines).strip() + "\n"


def get_soup():
    try:
        with LexBgClient(HttpTransport()) as client:
            soup = client.fetch_soup(DOC_ID)
        print(f"[fetch] LIVE lex.bg ldoc/{DOC_ID} OK")
        return soup, "live lex.bg"
    except Exception as e:
        print(f"[fetch] live fetch failed ({type(e).__name__}: {e}); falling back to saved capture")
        raw = SAVED.read_bytes().decode("cp1251", errors="replace")
        return BeautifulSoup(raw, "lxml"), f"saved capture {SAVED.name}"


def main():
    soup, src = get_soup()
    meta = MetadataParser().parse(soup, DOC_ID, CATEGORY)
    body = FixedHtmlToMarkdown().convert(soup)
    out = assemble_file(meta, body)

    # backup the old broken file for diffing
    if TARGET.exists():
        shutil.copy(TARGET, RESEARCH / "zuo-OLD-broken.md")
    TARGET.write_text(out, encoding="utf-8")
    shutil.copy(TARGET, RESEARCH / "zuo-NEW-fixed.md")

    # ---- verification ----
    old = (RESEARCH / "zuo-OLD-broken.md").read_text(encoding="utf-8") if (RESEARCH / "zuo-OLD-broken.md").exists() else ""
    tochki = len(re.findall(r"(?m)^\d+\.\s", out))
    max_para = max([int(x) for x in re.findall(r"§\s*(\d+)\.", out)] or [0])
    print("\n==================== ЗУО RE-SCRAPE VERIFICATION ====================")
    print(f"  source ................................. {src}")
    print(f"  written ................................ {TARGET}")
    print(f"  title (frontmatter) .................... {meta['titulo']}")
    print(f"  ultima_actualizacion ................... {meta['ultima_actualizacion']}")
    print(f"  amendment_history entries .............. {len(meta['amendment_history'])}")
    print(f"  size: OLD={len(old):,} chars  ->  NEW={len(out):,} chars   (+{len(out)-len(old):,})")
    print(f"  'Допълнителни разпоредби' present ...... {'Допълнителни разпоредби' in out}")
    print(f"  '§ 1. По смисъла' present .............. {'§ 1. По смисъла' in out or '§ 1.' in out and 'По смисъла' in out}")
    print(f"  numbered точки (^N. lines) ............. {tochki}")
    print(f"  max § provision number captured ....... §{max_para}")
    print(f"  base-ДР glued-heading artifacts ........ {len(re.findall(r'разпоредби(?:КЪМ|Преходни|Допълнителни)', out))}")
    print(f"  Чл. articles preserved ................. {len(re.findall(r'\\*\\*Чл\\.', out))}")

if __name__ == "__main__":
    main()
