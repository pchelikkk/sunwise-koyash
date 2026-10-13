import React from "react";
import {
  ArrowLeft,
  Check,
  ChevronLeft,
  ChevronRight,
  Heart,
  Search,
  ShieldCheck,
  ShoppingBag,
  SlidersHorizontal,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import * as api from "./api.js";
import BrandLogo from "./BrandLogo.jsx";
import { formatProductCount } from "./formatters.js";
import ProductVisual from "./ProductVisual.jsx";
import {
  useCosmeticBag,
  useFavorites,
} from "./productCollection.js";

const STEP_LABELS = {
  cleanser: "Очищение",
  toner: "Тонизация",
  serum: "Сыворотки",
  treatment: "Активный уход",
  moisturizer: "Увлажнение",
  spf: "SPF-защита",
  exfoliation: "Эксфолиация",
  mask: "Маски",
};

const BUDGET_LABELS = {
  minimum: "До 1 200 ₽",
  balanced: "Средний сегмент",
  premium: "Премиум",
};

const SKIN_LABELS = {
  all: "Для всех типов",
  normal: "Нормальная",
  oily: "Жирная",
  dry: "Сухая",
  combination: "Комбинированная",
  sensitive: "Чувствительная",
};

function trackStoreOpen(product, surface) {
  api.trackEvent("store_opened", {
    product_external_id: product.external_id,
    metadata: { surface },
  });
}

function FavoriteButton({ productId, active, toggle }) {
  return (
    <button
      className={"heartButton" + (active ? " active" : "")}
      onClick={(event) => {
        event.stopPropagation();
        toggle(productId);
      }}
      aria-label={active ? "Убрать из избранного" : "Добавить в избранное"}
      title={active ? "Убрать из избранного" : "Добавить в избранное"}
    >
      <Heart size={19} fill={active ? "currentColor" : "none"} />
    </button>
  );
}

function ProductDetails({
  product,
  close,
  favorite,
  toggleFavorite,
  bag,
}) {
  React.useEffect(() => {
    if (!product) return undefined;
    const previousOverflow = document.body.style.overflow;
    const onKeyDown = (event) => {
      if (event.key === "Escape") close();
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [product, close]);

  if (!product) return null;
  const ingredients = product.key_ingredients?.length
    ? product.key_ingredients
    : product.ingredients?.slice(0, 12) || [];

  return (
    <div
      className="detailOverlay"
      role="dialog"
      aria-modal="true"
      aria-label={product.name}
    >
      <button className="detailBackdrop" onClick={close} aria-label="Закрыть" />
      <article className="detailPanel">
        <div className="detailPanelTop">
          <button
            className="iconButton"
            onClick={close}
            aria-label="Закрыть карточку"
          >
            <X size={22} />
          </button>
        </div>
        <div className="detailHero">
          <ProductVisual product={product} />
          <div>
            <div className="eyebrow">
              {STEP_LABELS[product.routine_step] || product.category}
            </div>
            <h2>{product.name}</h2>
            <p className="detailBrand">{product.brand}</p>
            <div className="detailPrice">
              {product.price_rub.toLocaleString("ru-RU")} ₽
            </div>
          </div>
        </div>
        <p className="detailDescription">
          {product.description || "Описание средства уточняется."}
        </p>
        <div className="detailFacts">
          {product.volume_ml ? <span>{product.volume_ml} мл</span> : null}
          {product.texture ? <span>{product.texture}</span> : null}
          {product.vegan ? <span>Vegan</span> : null}
          {product.cruelty_free ? <span>Cruelty-free</span> : null}
        </div>
        {ingredients.length ? (
          <section className="detailSection">
            <h3>Ключевое в составе</h3>
            <div className="tagCloud">
              {ingredients.map((ingredient) => (
                <span key={ingredient}>{ingredient}</span>
              ))}
            </div>
          </section>
        ) : null}
        <section className="detailSection softSection">
          <ShieldCheck size={20} />
          <div>
            <h3>Как использовать</h3>
            <p>{product.how_to_use || "Следуйте инструкции производителя."}</p>
          </div>
        </section>
        <div className="detailActions">
          <button
            className="button secondary"
            onClick={() => toggleFavorite(product.external_id)}
          >
            <Heart size={18} fill={favorite ? "currentColor" : "none"} />
            {favorite ? "В избранном" : "Сохранить"}
          </button>
          <button
            className="button primary"
            onClick={() => bag.toggle(product)}
          >
            <ShoppingBag size={18} />
            {bag.has(product.external_id) ? "В косметичке ✓" : "В косметичку"}
          </button>
          {product.product_url ? (
            <a
              className="button secondary"
              href={product.product_url}
              target="_blank"
              rel="noreferrer"
              onClick={() => trackStoreOpen(product, "product_details")}
            >
              Открыть магазин
            </a>
          ) : null}
        </div>
      </article>
    </div>
  );
}

function CosmeticBagDrawer({ bag, open, close }) {
  React.useEffect(() => {
    if (!open) return undefined;
    const previousOverflow = document.body.style.overflow;
    const onKeyDown = (event) => {
      if (event.key === "Escape") close();
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open, close]);

  if (!open) return null;

  return (
    <div
      className="bagOverlay"
      role="dialog"
      aria-modal="true"
      aria-label="Моя косметичка"
    >
      <button className="detailBackdrop" onClick={close} aria-label="Закрыть" />
      <aside className="bagDrawer">
        <header className="bagDrawerHeader">
          <div>
            <span className="eyebrow">Список покупок</span>
            <h2>Моя косметичка</h2>
          </div>
          <button className="iconButton" onClick={close} aria-label="Закрыть косметичку">
            <X size={22} />
          </button>
        </header>

        {bag.products.length ? (
          <div className="bagItems">
            {bag.products.map((product) => (
              <article className="bagItem" key={product.external_id}>
                <ProductVisual product={product} compact />
                <div className="bagItemCopy">
                  <b>{product.name}</b>
                  <span>{product.brand}</span>
                  <strong>{product.price_rub.toLocaleString("ru-RU")} ₽</strong>
                  {product.product_url ? (
                    <a
                      href={product.product_url}
                      target="_blank"
                      rel="noreferrer"
                      onClick={() => trackStoreOpen(product, "cosmetic_bag")}
                    >
                      Открыть магазин
                    </a>
                  ) : null}
                </div>
                <button
                  className="bagRemove"
                  onClick={() => bag.remove(product.external_id)}
                  aria-label={`Убрать ${product.name}`}
                >
                  <Trash2 size={18} />
                </button>
              </article>
            ))}
          </div>
        ) : (
          <div className="bagEmpty">
            <ShoppingBag size={34} />
            <h3>Здесь пока пусто</h3>
            <p>Добавь средства из каталога или готового подбора.</p>
          </div>
        )}

        <footer className="bagDrawerFooter">
          <div>
            <span>Ориентировочная сумма</span>
            <b>{bag.total.toLocaleString("ru-RU")} ₽</b>
          </div>
          <p>Цена и наличие окончательно подтверждаются на сайте магазина.</p>
          {bag.products.length ? (
            <button className="textButton" onClick={bag.clear}>
              Очистить косметичку
            </button>
          ) : null}
        </footer>
      </aside>
    </div>
  );
}

export default function CatalogPage({ go, auth }) {
  const bag = useCosmeticBag(auth);
  const favorites = useFavorites(auth);
  const [catalog, setCatalog] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");
  const [searchDraft, setSearchDraft] = React.useState("");
  const [filters, setFilters] = React.useState({
    search: "",
    routine_step: [],
    budget_segment: [],
    skin_type: [],
    no_known_irritants: false,
    sort: "relevance",
    page: 1,
    page_size: 12,
  });
  const [selected, setSelected] = React.useState(null);
  const [filtersOpen, setFiltersOpen] = React.useState(false);
  const [bagOpen, setBagOpen] = React.useState(false);
  const [notice, setNotice] = React.useState("");

  React.useEffect(() => {
    let alive = true;
    setLoading(true);
    setError("");
    api
      .getProductCatalog(filters)
      .then((data) => alive && setCatalog(data))
      .catch((requestError) => alive && setError(requestError.message))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [filters]);

  React.useEffect(() => {
    if (catalog?.items?.length) bag.refresh(catalog.items);
  }, [catalog, bag.refresh]);

  React.useEffect(() => {
    if (!notice) return undefined;
    const timeout = setTimeout(() => setNotice(""), 2800);
    return () => clearTimeout(timeout);
  }, [notice]);

  const update = (patch) =>
    setFilters((current) => ({ ...current, ...patch, page: patch.page || 1 }));
  const toggleList = (key, value) => {
    const current = filters[key] || [];
    update({
      [key]: current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value],
    });
  };
  const toggleFavorite = async (productId) => {
    try {
      const product =
        catalog?.items?.find((item) => item.external_id === productId) ||
        (selected?.external_id === productId ? selected : productId);
      const result = await favorites.toggle(product);
      setNotice(result.added ? "Сохранено в избранном" : "Убрано из избранного");
    } catch (requestError) {
      setNotice(requestError.message || "Не удалось обновить избранное.");
    }
  };
  const submitSearch = (event) => {
    event.preventDefault();
    update({ search: searchDraft.trim() });
  };
  const openProduct = (product) => {
    setSelected(product);
    api.trackEvent("product_details_opened", {
      product_external_id: product.external_id,
    });
  };

  const steps = catalog?.facets?.routine_steps || [];
  const budgets = catalog?.facets?.budget_segments || [];

  return (
    <main className="catalogPage appSurface">
      <header className="innerHeader">
        <BrandLogo onClick={() => go("home")} />
        <nav>
          <button onClick={() => go("quiz")}>Подбор ухода</button>
          <button className="active">Каталог</button>
          <button className="favoriteHeaderButton" onClick={() => go("favorites")}>
            <Heart size={17} />
            <span className="headerButtonLabel">Избранное</span>
            {favorites.count ? <span className="navCount">{favorites.count}</span> : null}
          </button>
          <button onClick={() => go(auth ? "account" : "login")}>
            {auth ? "Кабинет" : "Войти"}
          </button>
          <button className="bagHeaderButton" onClick={() => setBagOpen(true)}>
            <ShoppingBag size={17} />
            <span className="headerButtonLabel">Косметичка</span>
            {bag.count ? <span>{bag.count}</span> : null}
          </button>
        </nav>
      </header>

      <section className="catalogIntro">
        <button className="quietLink" onClick={() => go("home")}>
          <ArrowLeft size={17} /> На главную
        </button>
        <span className="eyebrow">Осознанный выбор ухода</span>
        <h1>Каталог, в котором легко разобраться</h1>
        <p>
          Фильтруй по шагу, типу кожи и бюджету. Мы показываем известные
          признаки состава без медицинских обещаний.
        </p>
        <form className="catalogSearch" onSubmit={submitSearch}>
          <Search size={21} />
          <input
            value={searchDraft}
            onChange={(event) => setSearchDraft(event.target.value)}
            placeholder="Название, бренд или ингредиент"
          />
          <button className="button primary" type="submit">
            Найти
          </button>
        </form>
      </section>

      <div className="catalogLayout">
        <button
          className="mobileFilterToggle"
          onClick={() => setFiltersOpen((value) => !value)}
          aria-expanded={filtersOpen}
        >
          <SlidersHorizontal size={18} />
          {filtersOpen ? "Скрыть фильтры" : "Показать фильтры"}
        </button>
        <aside className={"filterPanel" + (filtersOpen ? " open" : "")}>
          <div className="filterHeading">
            <SlidersHorizontal size={19} />
            <b>Фильтры</b>
          </div>
          <div className="filterGroup">
            <span>Шаг ухода</span>
            {steps.map((facet) => (
              <label key={facet.value} className="checkRow">
                <input
                  type="checkbox"
                  checked={filters.routine_step.includes(facet.value)}
                  onChange={() => toggleList("routine_step", facet.value)}
                />
                <span className="fakeCheck">
                  <Check size={13} />
                </span>
                <span>{STEP_LABELS[facet.value] || facet.value}</span>
                <small>{facet.count}</small>
              </label>
            ))}
          </div>
          <div className="filterGroup">
            <span>Бюджет</span>
            {budgets.map((facet) => (
              <label key={facet.value} className="checkRow">
                <input
                  type="checkbox"
                  checked={filters.budget_segment.includes(facet.value)}
                  onChange={() => toggleList("budget_segment", facet.value)}
                />
                <span className="fakeCheck">
                  <Check size={13} />
                </span>
                <span>{BUDGET_LABELS[facet.value] || facet.value}</span>
                <small>{facet.count}</small>
              </label>
            ))}
          </div>
          <div className="filterGroup">
            <span>Тип кожи</span>
            <select
              value={filters.skin_type[0] || ""}
              onChange={(event) =>
                update({
                  skin_type: event.target.value ? [event.target.value] : [],
                })
              }
            >
              <option value="">Любой</option>
              {Object.entries(SKIN_LABELS)
                .filter(([key]) => key !== "all")
                .map(([key, label]) => (
                  <option value={key} key={key}>
                    {label}
                  </option>
                ))}
            </select>
          </div>
          <label className="safeSwitch">
            <input
              type="checkbox"
              checked={filters.no_known_irritants}
              onChange={(event) =>
                update({ no_known_irritants: event.target.checked })
              }
            />
            <span />
            <div>
              <b>Без известных раздражителей</b>
              <small>По флагам каталога</small>
            </div>
          </label>
          <button
            className="textButton"
            onClick={() => {
              setSearchDraft("");
              setFilters({
                search: "",
                routine_step: [],
                budget_segment: [],
                skin_type: [],
                no_known_irritants: false,
                sort: "relevance",
                page: 1,
                page_size: 12,
              });
            }}
          >
            Сбросить всё
          </button>
        </aside>

        <section className="catalogResults" aria-live="polite">
          <div className="resultControls">
            <div>
              {catalog ? (
                <>
                  <b>{formatProductCount(catalog.total)}</b> найдено
                </>
              ) : (
                <b>Загружаем каталог…</b>
              )}
            </div>
            <select
              value={filters.sort}
              onChange={(event) => update({ sort: event.target.value })}
            >
              <option value="relevance">Подборка KOYASH</option>
              <option value="price_asc">Сначала дешевле</option>
              <option value="price_desc">Сначала дороже</option>
              <option value="name">По названию</option>
            </select>
          </div>
          {error ? <div className="notice errorNotice">{error}</div> : null}
          {loading ? (
            <div className="catalogSkeleton">
              {Array.from({ length: 6 }).map((_, index) => (
                <span key={index} />
              ))}
            </div>
          ) : null}
          {!loading && catalog?.items.length ? (
            <div className="productGrid">
              {catalog.items.map((product) => (
                <article
                  className="catalogCard"
                  key={product.external_id}
                  onClick={() => openProduct(product)}
                >
                  <FavoriteButton
                    productId={product.external_id}
                    active={favorites.has(product.external_id)}
                    toggle={toggleFavorite}
                  />
                  <div className="catalogVisual">
                    <ProductVisual product={product} />
                  </div>
                  <span className="stepPill">
                    {STEP_LABELS[product.routine_step] || product.category}
                  </span>
                  <h2>{product.name}</h2>
                  <p className="cardBrand">{product.brand}</p>
                  <p className="catalogUsage" title={product.how_to_use}>
                    <b>Как использовать:</b> {product.how_to_use}
                  </p>
                  <div className="cardTags">
                    {(product.skin_types || []).slice(0, 2).map((type) => (
                      <span key={type}>{SKIN_LABELS[type] || type}</span>
                    ))}
                  </div>
                  <div className="catalogCardBottom">
                    <b>{product.price_rub.toLocaleString("ru-RU")} ₽</b>
                    <div className="catalogCardActions">
                      <button
                        className={bag.has(product.external_id) ? "inBag" : ""}
                        onClick={(event) => {
                          event.stopPropagation();
                          bag.toggle(product);
                          setNotice(
                            bag.has(product.external_id)
                              ? "Убрано из косметички"
                              : "Добавлено в косметичку",
                          );
                        }}
                      >
                        <ShoppingBag size={15} />
                        {bag.has(product.external_id) ? "Добавлено" : "Добавить"}
                      </button>
                      <button
                        aria-label={`Подробнее о ${product.name}`}
                        onClick={(event) => {
                          event.stopPropagation();
                          openProduct(product);
                        }}
                      >
                        <ChevronRight size={17} />
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          ) : null}
          {!loading && catalog && !catalog.items.length ? (
            <div className="emptyPanel">
              <Sparkles size={28} />
              <h2>Ничего не нашли</h2>
              <p>Попробуй убрать один из фильтров или изменить запрос.</p>
            </div>
          ) : null}
          {catalog?.total_pages > 1 ? (
            <div className="pagination">
              <button
                disabled={filters.page <= 1}
                onClick={() => update({ page: filters.page - 1 })}
              >
                <ChevronLeft size={18} />
              </button>
              <span>
                {filters.page} / {catalog.total_pages}
              </span>
              <button
                disabled={filters.page >= catalog.total_pages}
                onClick={() => update({ page: filters.page + 1 })}
              >
                <ChevronRight size={18} />
              </button>
            </div>
          ) : null}
        </section>
      </div>
      <ProductDetails
        product={selected}
        close={() => setSelected(null)}
        favorite={selected ? favorites.has(selected.external_id) : false}
        toggleFavorite={toggleFavorite}
        bag={bag}
      />
      <CosmeticBagDrawer
        bag={bag}
        open={bagOpen}
        close={() => setBagOpen(false)}
      />
      {notice ? <div className="catalogToast" role="status">{notice}</div> : null}
    </main>
  );
}
