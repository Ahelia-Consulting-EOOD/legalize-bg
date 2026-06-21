"""Tests for crawl_with_probe — crawls past the hardcoded page counts and
reports when CATEGORIES_CONFIG is stale (new acts hiding on new tree pages)."""

from refresh import crawl_with_probe


class FakeTreeTransport:
    """Returns canned cp1251 bytes per URL; empty bytes for unknown URLs."""

    def __init__(self, url_to_html: dict[str, str]):
        self._map = {u: h.encode("cp1251") for u, h in url_to_html.items()}
        self.requested: list[str] = []

    def get_tree_page(self, url: str) -> bytes:
        self.requested.append(url)
        return self._map.get(url, b"<html><body></body></html>")


def _tree_html(doc_ids: list[tuple[int, str]]) -> str:
    links = "".join(f'<a href="/laws/ldoc/{d}">{n}</a>' for d, n in doc_ids)
    return f"<html><body>{links}</body></html>"


def _url(cat: str, page: int) -> str:
    return f"https://lex.bg/laws/tree/{cat}/{page}"


def test_crawl_no_growth_stops_at_configured_plus_one_probe():
    cfg = {"laws": 1}
    urls = {_url("laws", 0): _tree_html([(1, "A"), (2, "B")])}  # page 1 -> empty
    result = crawl_with_probe(FakeTreeTransport(urls), config=cfg)
    assert {e["doc_id"] for e in result.catalog} == {1, 2}
    assert result.pages_used["laws"] == 1
    assert result.stale_categories == {}


def test_crawl_detects_growth_beyond_configured_pages():
    cfg = {"laws": 1}
    urls = {
        _url("laws", 0): _tree_html([(1, "A"), (2, "B")]),
        _url("laws", 1): _tree_html([(3, "NEW")]),  # a page that didn't exist in April
    }  # page 2 -> empty, stops probe
    result = crawl_with_probe(FakeTreeTransport(urls), config=cfg)
    assert {e["doc_id"] for e in result.catalog} == {1, 2, 3}
    assert result.pages_used["laws"] == 2
    assert result.stale_categories == {"laws": 1}  # 1 extra act found beyond config


def test_crawl_clamped_page_does_not_false_flag_stale():
    # lex.bg may clamp an out-of-range page index to the last page's content.
    # That repeat is all-seen -> 0 new acts -> must NOT be reported as stale.
    cfg = {"laws": 1}
    page0 = _tree_html([(1, "A"), (2, "B")])
    urls = {_url("laws", 0): page0, _url("laws", 1): page0}  # page 1 echoes page 0
    result = crawl_with_probe(FakeTreeTransport(urls), config=cfg)
    assert {e["doc_id"] for e in result.catalog} == {1, 2}
    assert result.stale_categories == {}


def test_crawl_cap_halts_runaway_probe():
    cfg = {"laws": 1}
    transport = _EndlessTransport()
    result = crawl_with_probe(transport, config=cfg, max_extra=3)
    # configured 1 page + at most 3 extra probe pages = stop at page index 4.
    assert result.pages_used["laws"] == 4


def test_crawl_dedupes_shared_act_first_wins():
    cfg = {"laws": 1, "regs": 1}
    urls = {
        _url("laws", 0): _tree_html([(42, "Konst"), (1, "Law")]),
        _url("regs", 0): _tree_html([(42, "Konst"), (2, "Reg")]),
    }
    result = crawl_with_probe(FakeTreeTransport(urls), config=cfg)
    konst = [e for e in result.catalog if e["doc_id"] == 42]
    assert len(konst) == 1
    assert konst[0]["category"] == "laws"  # first category wins


class _EndlessTransport:
    """Every page returns a brand-new unique act, forever — to exercise the cap."""

    def get_tree_page(self, url: str) -> bytes:
        page = int(url.rsplit("/", 1)[-1])
        html = _tree_html([(1000 + page, f"Act {page}")])
        return html.encode("cp1251")
