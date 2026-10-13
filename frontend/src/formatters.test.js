import { describe, expect, it } from "vitest";

import { formatProductCount } from "./formatters.js";

describe("formatProductCount", () => {
  it("uses natural Russian product forms", () => {
    expect(formatProductCount(0)).toBe("0 средств");
    expect(formatProductCount(1)).toBe("1 средство");
    expect(formatProductCount(3)).toBe("3 средства");
    expect(formatProductCount(12)).toBe("12 средств");
    expect(formatProductCount(21)).toBe("21 средство");
  });
});
