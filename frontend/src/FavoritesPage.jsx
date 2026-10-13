import React from "react";
import {
  ArrowLeft,
  Heart,
  ShoppingBag,
  Sparkles,
  Trash2,
} from "lucide-react";
import * as api from "./api.js";
import BrandLogo from "./BrandLogo.jsx";
import ProductVisual from "./ProductVisual.jsx";
import { useCosmeticBag, useFavorites } from "./productCollection.js";

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

function ProductPrice({ product }) {
  return <strong>{Number(product.price_rub || 0).toLocaleString("ru-RU")} ₽</strong>;
}

function trackStoreOpen(product, surface) {
  api.trackEvent("store_opened", {
    product_external_id: product.external_id,
    metadata: { surface },
  });
}

export default function FavoritesPage({ go, auth }) {
  const favorites = useFavorites(auth);
  const bag = useCosmeticBag(auth);
  const [notice, setNotice] = React.useState("");

  React.useEffect(() => {
    if (!notice) return undefined;
    const timeout = setTimeout(() => setNotice(""), 2800);
    return () => clearTimeout(timeout);
  }, [notice]);

  const removeFavorite = async (product) => {
    try {
      await favorites.toggle(product);
      setNotice("Убрано из избранного");
    } catch (error) {
      setNotice(error.message || "Не удалось обновить избранное.");
    }
  };

  return (
    <main className="libraryPage appSurface">
      <header className="innerHeader libraryHeader">
        <BrandLogo onClick={() => go("home")} />
        <nav>
          <button onClick={() => go("quiz")}>Подбор ухода</button>
          <button onClick={() => go("catalog")}>Каталог</button>
          <button className="active">Моя полка</button>
          <button onClick={() => go(auth ? "account" : "login")}>
            {auth ? "Кабинет" : "Войти"}
          </button>
        </nav>
      </header>

      <section className="libraryIntro">
        <button className="quietLink" onClick={() => go("catalog")}>
          <ArrowLeft size={17} /> В каталог
        </button>
        <span className="eyebrow">Всё, что хочется сохранить</span>
        <h1>Моя полка</h1>
        <p>
          Избранное помогает вернуться к сравнению, а косметичка собирает
          готовый список покупок. После входа оба списка доступны на всех устройствах; у гостя они сохраняются в этом браузере.
        </p>
        <div className="libraryStats">
          <div><Heart size={20} /><span>Избранное</span><b>{favorites.count}</b></div>
          <div><ShoppingBag size={20} /><span>В косметичке</span><b>{bag.count}</b></div>
          <div><Sparkles size={20} /><span>Ориентир по сумме</span><b>{bag.total.toLocaleString("ru-RU")} ₽</b></div>
        </div>
      </section>

      <section className="librarySection" aria-labelledby="favorites-heading">
        <div className="librarySectionHeading">
          <div>
            <span className="eyebrow">Сначала сравнить</span>
            <h2 id="favorites-heading">Избранное</h2>
          </div>
          {favorites.count ? <span>{favorites.count} сохранено</span> : null}
        </div>
        {favorites.error ? <div className="notice errorNotice">{favorites.error}</div> : null}
        {favorites.loading ? (
          <div className="libraryLoading" role="status">Загружаем сохранённые средства…</div>
        ) : favorites.products.length ? (
          <div className="libraryGrid">
            {favorites.products.map((product) => (
              <article className="libraryCard" key={product.external_id}>
                <div className="libraryVisual"><ProductVisual product={product} /></div>
                <div className="libraryCardCopy">
                  <span className="stepPill">{STEP_LABELS[product.routine_step] || product.category}</span>
                  <h3>{product.name}</h3>
                  <p className="cardBrand">{product.brand}</p>
                  <p className="libraryUsage">{product.how_to_use}</p>
                  <ProductPrice product={product} />
                </div>
                <div className="libraryCardActions">
                  <button className="button primary" onClick={() => {
                    bag.toggle(product);
                    setNotice(bag.has(product.external_id) ? "Убрано из косметички" : "Добавлено в косметичку");
                  }}>
                    <ShoppingBag size={17} />
                    {bag.has(product.external_id) ? "В косметичке ✓" : "В косметичку"}
                  </button>
                  {product.product_url ? (
                    <a className="button secondary" href={product.product_url} target="_blank" rel="noreferrer" onClick={() => trackStoreOpen(product, "favorites")}>Магазин</a>
                  ) : null}
                  <button className="iconButton libraryRemove" onClick={() => removeFavorite(product)} aria-label={`Убрать ${product.name} из избранного`}>
                    <Heart size={18} fill="currentColor" />
                  </button>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="libraryEmpty">
            <Heart size={30} />
            <h3>Пока ничего не сохранено</h3>
            <p>Нажми на сердечко в каталоге — средство появится здесь.</p>
            <button className="button primary" onClick={() => go("catalog")}>Открыть каталог</button>
          </div>
        )}
      </section>

      <section className="librarySection bagLibrarySection" aria-labelledby="bag-heading">
        <div className="librarySectionHeading">
          <div>
            <span className="eyebrow">Готово к покупке</span>
            <h2 id="bag-heading">Косметичка</h2>
          </div>
          {bag.count ? <ProductPrice product={{ price_rub: bag.total }} /> : null}
        </div>
        {bag.error ? <div className="notice errorNotice">{bag.error}</div> : null}
        {bag.loading ? (
          <div className="libraryLoading" role="status">Загружаем косметичку…</div>
        ) : bag.products.length ? (
          <div className="libraryBagList">
            {bag.products.map((product) => (
              <article key={product.external_id}>
                <ProductVisual product={product} compact />
                <div><b>{product.name}</b><span>{product.brand}</span></div>
                <ProductPrice product={product} />
                {product.product_url ? <a href={product.product_url} target="_blank" rel="noreferrer" onClick={() => trackStoreOpen(product, "cosmetic_bag")}>Открыть магазин</a> : null}
                <button onClick={() => bag.remove(product.external_id)} aria-label={`Убрать ${product.name} из косметички`}><Trash2 size={17} /></button>
              </article>
            ))}
          </div>
        ) : (
          <div className="libraryEmpty compact">
            <ShoppingBag size={28} />
            <h3>Список покупок пуст</h3>
            <p>Добавляй продукты из каталога, избранного или персонального подбора.</p>
          </div>
        )}
        {bag.count ? (
          <div className="libraryBagFooter">
            <p>Цена и наличие окончательно подтверждаются на сайте магазина.</p>
            <button className="textButton" onClick={bag.clear}>Очистить косметичку</button>
          </div>
        ) : null}
      </section>
      {notice ? <div className="catalogToast" role="status">{notice}</div> : null}
    </main>
  );
}
