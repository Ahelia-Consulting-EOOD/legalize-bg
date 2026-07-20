/** Verbatim port of index/synonyms.py `LEGAL_ABBREVIATIONS` +
 * `expand_if_abbreviation`. Keys are bg_normalize-d; values are the
 * canonical titulo strings, lowercased to match indexed laws_fts.title. */

export const LEGAL_ABBREVIATIONS: Readonly<Record<string, string>> = {
  // Public-procurement / IT / e-government
  "зоп": "закон за обществените поръчки",
  "ппзоп": "правилник за прилагане на закона за обществените поръчки",
  "зеу": "закон за електронното управление",
  "завп": "закон за автомобилните превози",
  // Tax
  "здде": "закон за данък върху добавената стойност",
  "здднс": "закон за данъците върху доходите на физическите лица",
  "здфл": "закон за данъците върху доходите на физическите лица",
  "здффл": "закон за данъците върху доходите на физическите лица",
  "зкпо": "закон за корпоративното подоходно облагане",
  "змдт": "закон за местните данъци и такси",
  // Civil / commercial
  "зн": "закон за наследството",
  "зс": "закон за собствеността",
  "зтр": "закон за търговския регистър",
  "зт": "закон за туризма",
  "змоип": "закон за мерките против изпирането на пари",
  // Codes
  "нк": "наказателен кодекс",
  "нпк": "наказателно-процесуален кодекс",
  "гпк": "граждански процесуален кодекс",
  "апк": "административнопроцесуален кодекс",
  "кт": "кодекс на труда",
  "ск": "семеен кодекс",
  "тк": "търговски кодекс",
};

export function expandIfAbbreviation(normalizedQuery: string): string | null {
  if (!normalizedQuery || normalizedQuery.includes(" ")) return null;
  return LEGAL_ABBREVIATIONS[normalizedQuery] ?? null;
}
