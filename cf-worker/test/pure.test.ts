// Unit tests for the pure ports of index/fts.py (bg_normalize),
// index/synonyms.py (LEGAL_ABBREVIATIONS), mcp_server/queries.py
// (parse_article_spec, _legal_article_sort_key, date validation).
// Expected values derived by running the Python originals.
import { describe, expect, it } from "vitest";

import { bgNormalize } from "../src/normalize";
import { trimTitle } from "../src/fts";
import { LEGAL_ABBREVIATIONS, expandIfAbbreviation } from "../src/synonyms";
import { InvalidArticleSpecError, parseArticleSpec } from "../src/articles";
import { legalArticleSortKey, compareSortKeys } from "../src/sortkey";
import { validateDate } from "../src/validation";
import { ToolError } from "../src/errors";

describe("bgNormalize (port of index.fts.bg_normalize)", () => {
  it("lowercases and collapses whitespace", () => {
    // Verified against Python: bg_normalize('  ЗАКОН   ЗА \n ТРУДА ') == 'закон за труда'
    expect(bgNormalize("  ЗАКОН   ЗА \n ТРУДА ")).toBe("закон за труда");
  });
  it("strips definite-article suffixes with min-stem rules", () => {
    expect(bgNormalize("новият")).toBe("нов"); // ият, stem 3
    expect(bgNormalize("градът")).toBe("град"); // ът, stem 4
    expect(bgNormalize("жената")).toBe("жена"); // та
    expect(bgNormalize("детето")).toBe("дете"); // то
    expect(bgNormalize("новите")).toBe("нови"); // те
    expect(bgNormalize("обществените")).toBe("обществени");
  });
  it("respects min stem length (does not over-strip short words)", () => {
    expect(bgNormalize("това")).toBe("това");
    expect(bgNormalize("път")).toBe("път");
  });
  it("handles empty/null-ish", () => {
    expect(bgNormalize("")).toBe("");
    expect(bgNormalize("   ")).toBe("");
  });
  it("keeps digits and punctuation", () => {
    expect(bgNormalize("Чл. 5, ал. 2")).toBe("чл. 5, ал. 2");
  });
});

describe("trimTitle (port of index.fts._trim_title, FR-032)", () => {
  it("passes short titles through untouched", () => {
    expect(trimTitle("ЗАКОН ЗА МРЕЖИТЕ")).toBe("ЗАКОН ЗА МРЕЖИТЕ");
  });
  it("truncates to the leading 12 whitespace tokens with '...'", () => {
    const t = "а б в г д е ж з и к л м н о";
    expect(trimTitle(t)).toBe("а б в г д е ж з и к л м...");
    // exactly 12 tokens: no truncation, original string preserved
    expect(trimTitle("а б в г д е ж з и к л м")).toBe("а б в г д е ж з и к л м");
  });
  it("collapses runs of whitespace like Python str.split()", () => {
    expect(trimTitle("а  б\tв г д е ж з и к л м н")).toBe("а б в г д е ж з и к л м...");
  });
  it("maps null/empty to ''", () => {
    expect(trimTitle(null)).toBe("");
    expect(trimTitle("")).toBe("");
  });
});

describe("synonyms (verbatim port of index.synonyms)", () => {
  it("has the full 22-entry table", () => {
    expect(Object.keys(LEGAL_ABBREVIATIONS).length).toBe(22);
    expect(LEGAL_ABBREVIATIONS["зоп"]).toBe("закон за обществените поръчки");
    expect(LEGAL_ABBREVIATIONS["апк"]).toBe("административнопроцесуален кодекс");
  });
  it("expands only single-token normalized queries", () => {
    expect(expandIfAbbreviation("зоп")).toBe("закон за обществените поръчки");
    expect(expandIfAbbreviation("зоп и още")).toBeNull();
    expect(expandIfAbbreviation("")).toBeNull();
    expect(expandIfAbbreviation("нещо")).toBeNull();
  });
});

describe("parseArticleSpec (port of queries.parse_article_spec)", () => {
  it("parses plain numbers and чл. forms", () => {
    expect(parseArticleSpec("5")).toEqual({ article: "5", paragraph: null, rangeEnd: null });
    expect(parseArticleSpec("чл. 5")).toEqual({ article: "5", paragraph: null, rangeEnd: null });
    expect(parseArticleSpec("чл.5")).toEqual({ article: "5", paragraph: null, rangeEnd: null });
    expect(parseArticleSpec("ЧЛ. 14а")).toEqual({ article: "14а", paragraph: null, rangeEnd: null });
  });
  it("parses alinea forms", () => {
    expect(parseArticleSpec("чл. 5, ал. 2")).toEqual({ article: "5", paragraph: "2", rangeEnd: null });
    expect(parseArticleSpec("чл. 5 ал. 2")).toEqual({ article: "5", paragraph: "2", rangeEnd: null });
    expect(parseArticleSpec("5.2")).toEqual({ article: "5", paragraph: "2", rangeEnd: null });
    expect(parseArticleSpec("чл. 5. ал. 2")).toEqual({ article: "5", paragraph: "2", rangeEnd: null });
  });
  it("parses ranges", () => {
    expect(parseArticleSpec("5-7")).toEqual({ article: "5", paragraph: null, rangeEnd: "7" });
    expect(parseArticleSpec("чл. 14 - 16")).toEqual({ article: "14", paragraph: null, rangeEnd: "16" });
  });
  it("rejects garbage", () => {
    expect(() => parseArticleSpec("")).toThrow(InvalidArticleSpecError);
    expect(() => parseArticleSpec("   ")).toThrow(InvalidArticleSpecError);
    expect(() => parseArticleSpec("abc")).toThrow(InvalidArticleSpecError);
    expect(() => parseArticleSpec("чл. ")).toThrow(InvalidArticleSpecError);
  });
});

describe("legalArticleSortKey (port of queries._legal_article_sort_key)", () => {
  it("sorts 14а between 14 and 15, numerically not textually", () => {
    const arts = ["100", "14б", "9", "1", "15", "14", "10", "14а"];
    arts.sort((a, b) => compareSortKeys(legalArticleSortKey(a), legalArticleSortKey(b)));
    expect(arts).toEqual(["1", "9", "10", "14", "14а", "14б", "15", "100"]);
  });
  it("unparseable trails", () => {
    const arts = ["§1", "2"];
    arts.sort((a, b) => compareSortKeys(legalArticleSortKey(a), legalArticleSortKey(b)));
    expect(arts).toEqual(["2", "§1"]);
  });
});

describe("validateDate (port of queries._validate_date)", () => {
  it("passes null through and accepts valid ISO dates", () => {
    expect(validateDate(null, "date")).toBeNull();
    expect(validateDate("2026-06-05", "date")).toBe("2026-06-05");
    expect(validateDate("  2026-06-05  ", "date")).toBe("2026-06-05");
  });
  it("rejects malformed, empty, and calendar-invalid dates", () => {
    for (const bad of ["junk", "", "2026-1-1", "2026-02-30", "2026-13-01", "20260101"]) {
      let err: unknown;
      try {
        validateDate(bad, "date");
      } catch (e) {
        err = e;
      }
      expect(err).toBeInstanceOf(ToolError);
      expect((err as ToolError).code).toBe("INVALID_DATE");
    }
  });
  it("truncates the echoed value to 50 chars", () => {
    try {
      validateDate("x".repeat(100), "date");
      expect.unreachable();
    } catch (e) {
      expect((e as ToolError).payload.value).toBe("x".repeat(50));
    }
  });
});
