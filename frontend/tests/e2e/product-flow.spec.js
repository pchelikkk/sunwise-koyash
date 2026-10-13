import { expect, test } from "@playwright/test";

const questionnaire = {
  version: "e2e-v1",
  questions: [
    {
      id: "skin_type",
      step: 1,
      total_steps: 4,
      title: "Как обычно ведёт себя твоя кожа?",
      description: "Выбери самое похожее описание.",
      answer_type: "single",
      why_we_ask: "Так мы подберём комфортные текстуры.",
      required: true,
      options: [
        {
          id: "oily",
          label: "Склонная к жирности",
          value: "oily",
          description: "Блеск заметен на большей части лица",
        },
        {
          id: "unknown",
          label: "Помогите определить",
          value: "unknown",
          description: "Отвечу на короткие уточнения",
        },
      ],
      popular_suggestions: [],
      visible_when_values: [],
    },
    {
      id: "concerns",
      step: 2,
      total_steps: 4,
      title: "Что сейчас хочется улучшить?",
      description: "Можно выбрать несколько пунктов.",
      answer_type: "multi",
      why_we_ask: "Так мы поймём главные задачи.",
      required: true,
      min_selections: 1,
      max_selections: 5,
      options: [
        { id: "acne", label: "Высыпания", value: "acne" },
        { id: "unknown", label: "Пока не знаю", value: "unknown" },
      ],
      popular_suggestions: [],
      visible_when_values: [],
    },
    {
      id: "primary_concern",
      step: 3,
      total_steps: 4,
      title: "На чём сосредоточимся?",
      description: "Выбери главное.",
      answer_type: "single",
      why_we_ask: "Это делает подбор точнее.",
      required: true,
      depends_on_question_id: "concerns",
      options: [{ id: "acne", label: "Высыпания", value: "acne" }],
      popular_suggestions: [],
      visible_when_values: [],
    },
    {
      id: "age",
      step: 4,
      total_steps: 4,
      title: "И последний необязательный вопрос",
      description: "Возраст можно не указывать.",
      answer_type: "number",
      why_we_ask: "Он нужен только для общей статистики.",
      required: false,
      min_value: 12,
      max_value: 100,
      unit: "лет",
      options: [],
      popular_suggestions: [],
      visible_when_values: [],
    },
  ],
};

const restrictionQuestionnaire = {
  version: "e2e-restrictions",
  questions: [
    {
      id: "skin_type",
      step: 1,
      total_steps: 2,
      title: "Choose a skin type",
      description: "Choose one option.",
      answer_type: "single",
      why_we_ask: "This makes the routine more precise.",
      required: true,
      options: [{ id: "normal", label: "Normal skin", value: "normal" }],
      popular_suggestions: [],
      visible_when_values: [],
    },
    {
      id: "restrictions",
      step: 2,
      total_steps: 2,
      title: "Ingredient restrictions",
      description: "Choose any restrictions that apply.",
      answer_type: "multi_with_custom",
      why_we_ask: "We exclude products before ranking them.",
      required: false,
      max_selections: 10,
      allows_custom: true,
      custom_input_max_length: 100,
      options: [],
      popular_suggestions: [
        { canonical_key: "fragrance", display_name: "Fragrance" },
        { canonical_key: "alcohol", display_name: "Alcohol" },
        { canonical_key: "essential_oils", display_name: "Essential oils" },
        { canonical_key: "none", display_name: "No restrictions" },
        { canonical_key: "unknown", display_name: "Not sure" },
      ],
      visible_when_values: [],
    },
  ],
};

const diagnosticQuestionnaire = {
  version: "e2e-diagnostic",
  questions: [
    {
      id: "skin_type",
      title: "Как обычно ведёт себя твоя кожа?",
      description: "Если не уверена, поможем определить.",
      answer_type: "single",
      why_we_ask: "Это основа персонального подбора.",
      required: true,
      options: [{ id: "unknown", label: "Помогите определить", value: "unknown" }],
    },
    ...[
      ["diagnostic_after_cleansing", "После умывания", "Комфортно", "comfortable"],
      ["diagnostic_midday_shine", "Блеск к середине дня", "В Т-зоне", "t_zone"],
      ["diagnostic_pore_visibility", "Насколько заметны поры?", "Заметнее в Т-зоне", "t_zone_visible"],
      ["diagnostic_flaking", "Как часто появляется шелушение?", "Иногда", "sometimes"],
    ].map(([id, title, label, value]) => ({
      id,
      title,
      description: "Короткое уточнение.",
      answer_type: "single",
      why_we_ask: "Ответ уточняет профиль кожи.",
      required: true,
      visible_when_question_id: "skin_type",
      visible_when_values: ["unknown"],
      options: [{ id: value, label, value }],
    })),
    {
      id: "concerns",
      title: "Что сейчас хочется улучшить?",
      description: "Можно выбрать несколько пунктов.",
      answer_type: "multi",
      why_we_ask: "Определяем задачи ухода.",
      required: true,
      min_selections: 1,
      max_selections: 5,
      options: [{ id: "acne", label: "Высыпания", value: "acne" }],
    },
  ],
};

const product = {
  external_id: "product_001",
  name: "Мягкая пенка",
  brand: "Pleyana",
  category: "Очищение",
  routine_step: "cleanser",
  price_rub: 743,
  budget_segment: "minimum",
  skin_types: ["all"],
  concerns: ["dehydration"],
  ingredients: ["Aqua", "Glycerin"],
  key_ingredients: ["Glycerin"],
  risk_flags: [],
  values: ["soft_formula"],
  texture: "Пенка",
  description: "Мягко очищает кожу без лишней сложности.",
  how_to_use: "Нанеси на влажную кожу и смой водой.",
  image_url: null,
  product_url: null,
  vegan: true,
  cruelty_free: true,
  volume_ml: 75,
  is_active: true,
};

const replacementProduct = {
  ...product,
  external_id: "product_002",
  name: "Деликатный гель",
  brand: "Bioderma",
  price_rub: 865,
};

const routineItem = (selectedProduct) => ({
  product: selectedProduct,
  routine_step: "cleanser",
  score: 82,
  why_here: "Мягко очищает и поддерживает комфорт кожи.",
  how_to_use: selectedProduct.how_to_use,
  budget_reason: "Соответствует выбранному бюджету.",
  safety_note: "Перед первым применением сделайте патч-тест.",
});

async function mockApi(page, questionnaireFixture = questionnaire) {
  let cosmeticBagItems = [];
  await page.addInitScript(() => {
    if (window.name !== "koyash-e2e-initialized") {
      localStorage.clear();
      sessionStorage.clear();
      window.name = "koyash-e2e-initialized";
    }
  });
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    if (url.includes("/users/me/cosmetic-bag")) {
      const method = route.request().method();
      const productId = decodeURIComponent(url.split("/cosmetic-bag/")[1] || "");
      if (method === "PUT") {
        const selectedProduct = productId === product.external_id ? product : replacementProduct;
        cosmeticBagItems = [
          ...cosmeticBagItems.filter((item) => item.product.external_id !== productId),
          { product: selectedProduct, created_at: "2026-07-17T00:00:00Z" },
        ];
        await route.fulfill({ json: cosmeticBagItems.at(-1) });
        return;
      }
      if (method === "DELETE") {
        cosmeticBagItems = productId
          ? cosmeticBagItems.filter((item) => item.product.external_id !== productId)
          : [];
        await route.fulfill({ status: 204 });
        return;
      }
      await route.fulfill({
        json: { items: cosmeticBagItems, total: cosmeticBagItems.length },
      });
      return;
    }
    if (url.includes("/users/me/favorites")) {
      await route.fulfill({ json: { items: [], total: 0 } });
      return;
    }
    if (url.includes("/users/me/profile")) {
      await route.fulfill({ json: { questionnaire_history: [] } });
      return;
    }
    if (url.includes("/users/me")) {
      await route.fulfill({
        json: {
          user_id: "admin-e2e",
          email: "admin@koyash.test",
          display_name: "Администратор",
          role: "admin",
          anonymous_id: "admin-anon-e2e",
        },
      });
      return;
    }
    if (url.includes("/admin/analytics/dashboard")) {
      await route.fulfill({
        json: {
          period: { calendar_days: 30 },
          overview: {
            recommendations_generated: 128,
            questionnaires_completed: 172,
            registrations: 43,
            feedback_submitted: 19,
            replacement_sessions: 12,
            replacement_selections: 8,
            recommendation_shares: 31,
            llm_success: 102,
            llm_fallback: 4,
          },
          users: {
            registered_total: 482,
            registered_in_period: 43,
            active_accounts: 214,
            returning_accounts: 97,
            unique_visitors: 685,
            anonymous_visitors: 241,
          },
          llm: {
            enabled: true,
            configured: true,
            provider: "openai",
            model: "gpt-test",
            attempts: 106,
            success: 102,
            fallback: 4,
            success_rate: { rate_percent: 96.23 },
          },
          activity: [
            { recommendations_generated: 3 },
            { recommendations_generated: 7 },
            { recommendations_generated: 11 },
          ],
          conversion: {
            questionnaire_to_recommendation: { rate_percent: 74 },
            feedback_to_replacement: { rate_percent: 63 },
            replacement_to_selection: { rate_percent: 42 },
          },
          products: {
            top_recommended: [
              { product_external_id: "product_001", name: product.name, count: 21 },
            ],
            top_viewed: [
              { product_external_id: "product_001", name: product.name, count: 48 },
            ],
            top_favorited: [
              { product_external_id: "product_001", name: product.name, count: 17 },
            ],
            top_bagged: [
              { product_external_id: "product_001", name: product.name, count: 14 },
            ],
            top_store_opened: [
              { product_external_id: "product_001", name: product.name, count: 11 },
            ],
            replacement_frequency: [
              { product_external_id: "product_001", name: product.name, count: 9 },
            ],
            replacement_selection_frequency: [
              { product_external_id: "product_001", name: product.name, count: 6 },
            ],
          },
          feedback: {
            reasons: { too_expensive: 9, dislikes_brand: 4 },
            reasons_by_product: [{
              product_external_id: "product_001",
              name: product.name,
              brand: product.brand,
              count: 13,
              reasons: { too_expensive: 9, dislikes_brand: 4 },
            }],
          },
          audience: {
            skin_types: { combination: 41, dry: 27 },
            concerns: { acne: 32, dryness: 24 },
            budgets: { balanced: 39, minimum: 18 },
            experience: { beginner: 35, guided: 21 },
            restrictions: { fragrance: 16, alcohol: 8 },
          },
        },
      });
      return;
    }
    if (url.includes("/admin/catalog/import")) {
      await route.fulfill({
        json: {
          file_name: "new-products.csv",
          fingerprint: "a".repeat(64),
          rows_valid: 2,
          inserted: 1,
          updated: 1,
          deactivated: 0,
          dataset_products_after: 70,
          active_products_after: 70,
          synchronize_missing: false,
          imported_at: "2026-07-17T00:00:00Z",
        },
      });
      return;
    }
    if (url.includes("/admin/catalog/quality")) {
      await route.fulfill({
        json: {
          completeness_percent: 100,
          active_products: 69,
          dataset_products: 69,
          step_counts: { cleanser: 16, moisturizer: 9, spf: 9 },
          usage_coverage_percent: 100,
          product_link_coverage_percent: 100,
          image_coverage_percent: 100,
          strict_dataset_ok: true,
        },
      });
      return;
    }
    if (url.includes("/admin/catalog/issues")) {
      await route.fulfill({
        json: {
          total: 1,
          items: [
            {
              ...product,
              issues: ["missing_image"],
              image_url: "",
              product_url: "https://example.test/product_001",
            },
          ],
        },
      });
      return;
    }
    if (url.includes("/questionnaire")) {
      await route.fulfill({ json: questionnaireFixture });
      return;
    }
    if (url.includes("/skin-diagnosis")) {
      await route.fulfill({
        json: {
          method: "guided_diagnostic",
          submitted_skin_type: "unknown",
          resolved_skin_type: "combination",
          confidence: "high",
          confidence_percent: 86,
          scores: { combination: 7, oily: 4, normal: 2, dry: 1 },
          signals: ["Блеск заметнее в Т-зоне.", "Поры заметнее в Т-зоне."],
          disclaimer: "Косметический ориентир, не медицинская диагностика.",
        },
      });
      return;
    }
    if (url.includes("/feedback")) {
      await route.fulfill({
        json: {
          feedback_id: "feedback-e2e",
          replacement_session_id: "replacement-e2e",
          replacement_status: "available",
          replacement_message: "Нашли безопасную замену.",
          replacement_candidates: [
            {
              rank: 1,
              product: replacementProduct,
              reason: "too_expensive",
              replacement_score: 87,
              why_better: "Подходит для того же шага ухода.",
              replacement_reason: "Тот же шаг ухода",
            },
          ],
        },
      });
      return;
    }
    if (url.includes("/replacements/") && url.endsWith("/select")) {
      await route.fulfill({
        json: {
          replacement_session_id: "replacement-e2e",
          original_product_external_id: product.external_id,
          selected_product_external_id: replacementProduct.external_id,
          replacement_item: routineItem(replacementProduct),
          routine: {
            morning: [routineItem(replacementProduct)],
            evening: [routineItem(replacementProduct)],
          },
          total_price_rub: replacementProduct.price_rub,
          status: "selected",
        },
      });
      return;
    }
    if (url.includes("/products/catalog")) {
      await route.fulfill({
        json: {
          items: [product],
          total: 1,
          page: 1,
          page_size: 12,
          total_pages: 1,
          facets: {
            routine_steps: [{ value: "cleanser", count: 1 }],
            budget_segments: [{ value: "minimum", count: 1 }],
            skin_types: [{ value: "all", count: 1 }],
            concerns: [{ value: "dehydration", count: 1 }],
            values: [{ value: "soft_formula", count: 1 }],
            textures: [{ value: "Пенка", count: 1 }],
            min_price_rub: 743,
            max_price_rub: 743,
          },
        },
      });
      return;
    }
    if (url.includes("/products/product_001")) {
      await route.fulfill({ json: product });
      return;
    }
    await route.fulfill({ json: { status: "ok" } });
  });
}

test("landing preserves the approved visual promise without horizontal overflow", async ({
  page,
}) => {
  await mockApi(page);
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });

  await page.goto("/#home");
  await expect(
    page.getByRole("heading", { name: /Разберёмся с уходом вместе/ }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "собрать косметичку" }).first()).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Уход без догадок и лишних покупок" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Не список банок, а понятную систему" }),
  ).toBeVisible();
  await expect(page.getByText("наведи, чтобы открыть")).toHaveCount(0);
  await expect(page.locator(".revealWin")).toHaveCount(0);
  const overflows = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
  );
  const decorativeOverlaps = await page.evaluate(() => {
    const decorations = [...document.querySelectorAll(".dec")].filter(
      (node) => getComputedStyle(node).display !== "none",
    );
    const content = [...document.querySelectorAll(
      ".lsec h1, .lsec h2, .lsec h3, .lsec p, .lsec img, .lsec li",
    )];
    const intersects = (a, b) =>
      Math.max(a.left, b.left) < Math.min(a.right, b.right) &&
      Math.max(a.top, b.top) < Math.min(a.bottom, b.bottom);
    return decorations.flatMap((decoration) => {
      const decorationRect = decoration.getBoundingClientRect();
      return content
        .filter((node) => intersects(decorationRect, node.getBoundingClientRect()))
        .map((node) => `${decoration.className} -> ${node.tagName}.${node.className}`);
    });
  });

  expect(overflows).toBe(false);
  expect(decorativeOverlaps).toEqual([]);
  expect(errors).toEqual([]);
});

test("every public surface uses the exact exported Figma logo", async ({ page }) => {
  await mockApi(page);
  const logoSources = [];

  for (const route of ["home", "quiz", "login"]) {
    await page.goto(`/#${route}`);
    const logo = page.getByTestId("brand-logo").first();
    await expect(logo).toBeVisible();
    const image = logo.locator("img");
    await expect(image).toHaveAttribute("src", /koyash-logo\.png/);
    await expect
      .poll(() =>
        image.evaluate((node) => ({
          complete: node.complete,
          naturalWidth: node.naturalWidth,
          naturalHeight: node.naturalHeight,
        })),
      )
      .toEqual({ complete: true, naturalWidth: 299, naturalHeight: 103 });
    logoSources.push(
      await image.evaluate((node) => ({
        path: new URL(node.currentSrc || node.src).pathname,
        naturalWidth: node.naturalWidth,
        naturalHeight: node.naturalHeight,
      })),
    );
    await expect(page.locator(".brandWord")).toHaveCount(0);
  }

  expect(new Set(logoSources.map(({ path }) => path)).size).toBe(1);
  for (const source of logoSources) {
    expect(source.naturalWidth).toBe(299);
    expect(source.naturalHeight).toBe(103);
  }
});

test("landing navigation reports scroll state without layout jumps", async ({ page }) => {
  await mockApi(page);
  await page.goto("/#home");

  const header = page.locator(".landingHeader");
  const firstSectionButton = page.locator(".landingHeader .topnav .navpill").first();
  const viewportWidth = await page.evaluate(() => window.innerWidth);
  if (viewportWidth <= 760) {
    await expect(page.locator(".landingHeader .mobileNavLink")).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: "собрать косметичку" }).first(),
    ).toBeVisible();
  }
  await firstSectionButton.click();
  await expect(header).toHaveClass(/scrolled/);
  await expect(firstSectionButton).toHaveClass(/active/);
  await expect(firstSectionButton).toHaveAttribute("aria-current", "location");
  expect(
    await header.evaluate((node) => Math.round(node.getBoundingClientRect().top)),
  ).toBe(0);

  const progress = await page.locator(".landingScrollProgress").evaluate((node) =>
    Number(node.style.transform.match(/[\d.]+/)?.[0] || 0),
  );
  expect(progress).toBeGreaterThan(0);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    ),
  ).toBe(false);
});

test("neutral concern is exclusive and skips the irrelevant priority step", async ({
  page,
}) => {
  await mockApi(page);
  await page.goto("/#quiz");

  await page.getByRole("button", { name: /Помогите определить/ }).click();
  await page.getByRole("button", { name: "Далее" }).click();
  await expect(page.getByRole("heading", { name: "Что сейчас хочется улучшить?" })).toBeVisible();
  await page.getByRole("button", { name: /Пока не знаю/ }).click();
  await page.getByRole("button", { name: "Далее" }).click();
  await expect(
    page.getByRole("heading", { name: "И последний необязательный вопрос" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "К результатам" }).click();
  await expect(page.getByRole("heading", { name: "Проверим всё ещё раз" })).toBeVisible();
  await expect(page.getByText("Пока не знаю", { exact: true })).toBeVisible();
});

test("a single concern becomes the priority without a redundant question", async ({
  page,
}) => {
  await mockApi(page);
  await page.goto("/#quiz");

  await page.getByRole("button", { name: /Склонная к жирности/ }).click();
  await page.getByRole("button", { name: "Далее" }).click();
  await page.getByRole("button", { name: "Высыпания" }).click();
  await page.getByRole("button", { name: "Далее" }).click();

  await expect(
    page.getByRole("heading", { name: "И последний необязательный вопрос" }),
  ).toBeVisible();
});

test("guided skin diagnostic reveals the resolved type before concerns", async ({ page }) => {
  await mockApi(page, diagnosticQuestionnaire);
  await page.goto("/#quiz");

  for (const option of [
    "Помогите определить",
    "Комфортно",
    "В Т-зоне",
    "Заметнее в Т-зоне",
    "Иногда",
  ]) {
    await page.getByRole("button", { name: option }).click();
    await page.getByRole("button", { name: "Далее" }).click();
  }

  await expect(page.getByRole("heading", { name: "Что сейчас хочется улучшить?" })).toBeVisible();
  await expect(page.getByRole("status")).toContainText("Профиль кожи определён");
  await expect(page.getByRole("status")).toContainText("комбинированная кожа");
  await expect(page.getByRole("status")).toContainText("86%");
});

test("neutral restriction choices cannot conflict with selected ingredients", async ({ page }) => {
  await mockApi(page, restrictionQuestionnaire);
  await page.goto("/#quiz");

  await page.getByRole("button", { name: /Normal skin/ }).click();
  await page.locator(".navRow .solid").click();

  const fragrance = page.getByRole("button", { name: "Fragrance" });
  const alcohol = page.getByRole("button", { name: "Alcohol" });
  const none = page.getByRole("button", { name: "No restrictions" });
  const unknown = page.getByRole("button", { name: "Not sure" });

  await fragrance.click();
  await alcohol.click();
  await expect(fragrance).toHaveAttribute("aria-pressed", "true");
  await expect(alcohol).toHaveAttribute("aria-pressed", "true");

  await none.click();
  await expect(none).toHaveAttribute("aria-pressed", "true");
  await expect(fragrance).toHaveAttribute("aria-pressed", "false");
  await expect(alcohol).toHaveAttribute("aria-pressed", "false");

  await unknown.click();
  await expect(unknown).toHaveAttribute("aria-pressed", "true");
  await expect(none).toHaveAttribute("aria-pressed", "false");

  await page.locator(".field input").fill("lanolin");
  await page.locator(".field .btn").click();
  await expect(unknown).toHaveAttribute("aria-pressed", "false");
  await expect(page.locator(".customRestrictionChip", { hasText: "lanolin" })).toBeVisible();
});

test("starting a new questionnaire clears answers from an earlier session", async ({
  page,
}) => {
  await mockApi(page);
  await page.addInitScript(() => {
    sessionStorage.setItem(
      "koyash_quiz_answers",
      JSON.stringify({ skin_type: "oily", concerns: ["acne"] }),
    );
  });
  await page.goto("/#home");

  await page.getByRole("button", { name: "собрать косметичку" }).first().click();
  await expect(page.getByRole("heading", { name: "Как обычно ведёт себя твоя кожа?" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Склонная к жирности/ })).not.toHaveClass(/sel/);
  await expect
    .poll(() => page.evaluate(() => sessionStorage.getItem("koyash_quiz_answers")))
    .toBe("{}");
});

test("guest result offers account sign-in instead of a public catalog", async ({ page }) => {
  await mockApi(page);
  await page.addInitScript(({ recommendation }) => {
    sessionStorage.setItem("koyash_latest_recommendation", JSON.stringify(recommendation));
  }, {
    recommendation: {
      recommendation_id: "guest-save-e2e",
      algorithm_version: "e2e-v1",
      skin_profile: { resolved_skin_type: "oily", method: "self_reported" },
      filter_summary: { restriction_coverage: { unmatched_restrictions: [] } },
      routine: {
        morning: [routineItem(product)],
        evening: [routineItem(product)],
      },
      total_price_rub: product.price_rub,
    },
  });

  await page.goto("/#results");
  await expect(page.getByText("Сохрани подбор после входа")).toBeVisible();
  await page.getByRole("button", { name: "Войти и сохранить" }).click();
  await expect(page).toHaveURL(/#login/);
  await expect(page.getByRole("heading", { name: "Вход" })).toBeVisible();

  await page.goto("/#catalog");
  await expect(page.getByRole("heading", { name: "Разберёмся с уходом вместе" })).toBeVisible();
  await expect(page.getByText("Каталог, в котором легко разобраться")).toHaveCount(0);
});

test("selected replacement immediately removes the old product from both routines", async ({ page }) => {
  await mockApi(page);
  await page.addInitScript(({ recommendation }) => {
    if (!sessionStorage.getItem("koyash_latest_recommendation")) {
      sessionStorage.setItem("koyash_latest_recommendation", JSON.stringify(recommendation));
    }
  }, {
    recommendation: {
      recommendation_id: "recommendation-e2e",
      algorithm_version: "e2e-v1",
      skin_profile: { resolved_skin_type: "oily", method: "self_reported" },
      filter_summary: { restriction_coverage: { unmatched_restrictions: [] } },
      routine: {
        morning: [routineItem(product)],
        evening: [routineItem(product)],
      },
      total_price_rub: product.price_rub,
    },
  });

  await page.goto("/#results");
  await expect(page.locator(".resultHeroCard")).toBeVisible();
  await expect(page.locator(".resultHeroCard")).toContainText("1");
  await expect(page.locator(".resultSummaryPanel")).toContainText("743");
  await page.getByRole("button", { name: "О средстве" }).first().click();
  await page.getByLabel("Причина").selectOption("too_expensive");
  await page.getByRole("button", { name: "Подобрать замену" }).click();
  await page.getByRole("button", { name: "Выбрать замену" }).click();

  await expect(page).toHaveURL(/#results/);
  await expect(page.locator(".resultSummaryPanel")).toContainText("865");
  await expect(page.locator(".routineName").filter({ hasText: "Деликатный гель" })).toHaveCount(2);
  await expect(page.locator(".routineName").filter({ hasText: "Мягкая пенка" })).toHaveCount(0);
  await expect(page.getByText(/теперь стоит в подборе/)).toBeVisible();

  await page.reload();
  await expect(page.locator(".routineName").filter({ hasText: "Деликатный гель" })).toHaveCount(2);
  await expect(page.locator(".routineName").filter({ hasText: "Мягкая пенка" })).toHaveCount(0);
});

test("recommendation can be shared from the result screen", async ({ page }) => {
  await mockApi(page);
  await page.addInitScript(({ recommendation }) => {
    sessionStorage.setItem("koyash_latest_recommendation", JSON.stringify(recommendation));
    Object.defineProperty(navigator, "share", {
      configurable: true,
      value: async ({ text }) => {
        window.__sharedRoutine = text;
      },
    });
  }, {
    recommendation: {
      recommendation_id: "share-e2e",
      algorithm_version: "e2e-v1",
      skin_profile: { resolved_skin_type: "oily", method: "self_reported" },
      filter_summary: { restriction_coverage: { unmatched_restrictions: [] } },
      routine: {
        morning: [routineItem(product)],
        evening: [routineItem(product)],
      },
      total_price_rub: product.price_rub,
    },
  });

  await page.goto("/#results");
  await page.getByRole("button", { name: "Поделиться подбором" }).click();
  await expect(page.getByRole("status")).toContainText("Подбор отправлен");
  await expect.poll(() => page.evaluate(() => window.__sharedRoutine)).toContain("Мягкая пенка");
});

test("authentication screen keeps the Figma card state", async ({ page }) => {
  await mockApi(page);
  await page.goto("/#login");

  await expect(page.getByRole("heading", { name: "Вход" })).toBeVisible();
  await expect(page.getByLabel("Почта")).toBeVisible();
  await expect(page.getByLabel("Пароль")).toBeVisible();
  await expect(page.getByRole("button", { name: "Войти" })).toBeVisible();
});

test("admin sees product analytics and the audited catalog editor", async ({ page }) => {
  await mockApi(page);
  await page.addInitScript(() => localStorage.setItem("koyash_token", "e2e-admin-token"));
  await page.goto("/#admin");

  await expect(page.getByRole("heading", { name: "Пульс продукта" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Пользователи" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "LLM-объяснения" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Переходят в магазин" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Что именно не подошло" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Качество каталога" })).toBeVisible();
  await expect(page.getByText("Инструкции 100%", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Редактор каталога" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Импорт нового датасета" })).toBeVisible();

  await page.locator('.datasetFilePicker input[type="file"]').setInputFiles({
    name: "new-products.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("external_id,name\nnew_001,New product\n"),
  });
  await page.getByRole("checkbox").uncheck();
  await page.getByRole("button", { name: "Проверить и импортировать" }).click();
  await expect(page.getByRole("status")).toContainText("Датасет применён без ошибок");
  await expect(page.getByRole("status")).toContainText("70 активных");

  const issueRow = page.getByRole("button", { name: /Мягкая пенка/ });
  await expect(issueRow).toHaveCount(1);
  await issueRow.click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByLabel("Как использовать")).toBeVisible();
});
