import { localeOptions, messages, resolveLocale } from "../src/locales.js";
import { termsByLocale } from "../src/terms.js";

const referenceKeys = new Set(Object.keys(messages.en));
let failed = false;

function placeholders(value) {
  return [...String(value).matchAll(/\{([a-zA-Z0-9_]+)\}/g)]
    .map((match) => match[1])
    .sort();
}

for (const option of localeOptions) {
  const dictionary = messages[option.value];
  if (!dictionary) {
    console.error(`Missing dictionary: ${option.value}`);
    failed = true;
    continue;
  }
  const missing = [...referenceKeys].filter((key) => !(key in dictionary));
  const extra = Object.keys(dictionary).filter((key) => !referenceKeys.has(key));
  if (missing.length || extra.length) {
    failed = true;
    console.error(`${option.value}: missing=${missing.join(",")} extra=${extra.join(",")}`);
  }
  for (const key of referenceKeys) {
    const translated = dictionary[key];
    if (typeof translated !== "string" || !translated.trim()) {
      failed = true;
      console.error(`${option.value}: empty translation for ${key}`);
      continue;
    }
    if (JSON.stringify(placeholders(translated)) !== JSON.stringify(placeholders(messages.en[key]))) {
      failed = true;
      console.error(`${option.value}: placeholder mismatch for ${key}`);
    }
    if (option.value !== "en" && translated === messages.en[key]) {
      failed = true;
      console.error(`${option.value}: untranslated English value for ${key}`);
    }
  }
  const sections = termsByLocale[option.value];
  if (!sections || sections.length !== termsByLocale.en.length) {
    failed = true;
    console.error(`Terms section coverage missing for ${option.value}`);
  } else if (
    sections.some(
      (section, index) =>
        !section.title ||
        !Array.isArray(section.paragraphs) ||
        section.paragraphs.length === 0 ||
        section.paragraphs.length !== termsByLocale.en[index].paragraphs.length ||
        section.paragraphs.some((paragraph) => !paragraph)
    )
  ) {
    failed = true;
    console.error(`Terms content incomplete for ${option.value}`);
  }
}

if (failed) process.exit(1);
console.log(`Locale key coverage verified for: ${localeOptions.map((item) => item.value).join(", ")}`);
console.log("Localized Terms of Service section coverage verified.");

const detections = [
  [["zh-CN", "en-US"], "zh-CN"],
  [["ru-RU"], "ru"],
  [["es-MX"], "es"],
  [["fr-CA"], "fr"],
  [["de-AT"], "de"],
  [["ko-KR"], "ko"],
  [["ja-JP"], "ja"],
  [["uz-UZ"], "uz"],
  [["it-IT"], "en"]
];
for (const [languages, expected] of detections) {
  const actual = resolveLocale(languages);
  if (actual !== expected) {
    console.error(`Locale detection failed: ${languages.join(",")} -> ${actual}, expected ${expected}`);
    process.exit(1);
  }
}
console.log("Browser language detection verified.");
