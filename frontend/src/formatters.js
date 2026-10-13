const PRODUCT_FORMS = {
  one: "средство",
  few: "средства",
  many: "средств",
  other: "средства",
};

const PRODUCT_PLURAL_RULES = new Intl.PluralRules("ru-RU");

export function formatProductCount(value) {
  const count = Number.isFinite(Number(value)) ? Number(value) : 0;
  const form = PRODUCT_FORMS[PRODUCT_PLURAL_RULES.select(Math.abs(count))];
  return `${count.toLocaleString("ru-RU")} ${form}`;
}
