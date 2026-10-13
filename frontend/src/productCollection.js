import React from "react";
import * as api from "./api.js";

export const GUEST_FAVORITES_KEY = "koyash_guest_favorites";
export const COSMETIC_BAG_KEY = "koyash_cosmetic_bag";

export function readStoredIds(key) {
  try {
    const value = JSON.parse(localStorage.getItem(key) || "[]");
    return Array.isArray(value)
      ? value.filter((item) => typeof item === "string" && item.trim())
      : [];
  } catch {
    return [];
  }
}

export function writeStoredIds(key, ids) {
  try {
    localStorage.setItem(key, JSON.stringify([...new Set(ids)]));
  } catch {
    // Storage can be unavailable in private mode. The in-memory state still works.
  }
}

function normalizeFavoriteProduct(product) {
  if (!product || typeof product.external_id !== "string") return null;
  return product;
}

export function useFavorites(auth) {
  const [ids, setIds] = React.useState(
    () => new Set(readStoredIds(GUEST_FAVORITES_KEY)),
  );
  const [products, setProducts] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");
  const authKey = auth?.user?.user_id || (api.getToken() ? "authenticated" : "guest");

  React.useEffect(() => {
    let alive = true;

    const load = async () => {
      setLoading(true);
      setError("");

      if (!api.getToken()) {
        const guestIds = readStoredIds(GUEST_FAVORITES_KEY);
        const settled = await Promise.allSettled(
          guestIds.map((productId) => api.getProduct(productId)),
        );
        if (!alive) return;
        const loadedProducts = settled
          .filter((result) => result.status === "fulfilled")
          .map((result) => result.value)
          .filter(normalizeFavoriteProduct);
        setIds(new Set(loadedProducts.map((product) => product.external_id)));
        setProducts(loadedProducts);
        writeStoredIds(
          GUEST_FAVORITES_KEY,
          loadedProducts.map((product) => product.external_id),
        );
        return;
      }

      const guestIds = readStoredIds(GUEST_FAVORITES_KEY);
      if (guestIds.length) {
        const migration = await Promise.allSettled(
          guestIds.map((productId) => api.addFavorite(productId)),
        );
        if (migration.every((result) => result.status === "fulfilled")) {
          writeStoredIds(GUEST_FAVORITES_KEY, []);
        }
      }

      const data = await api.getFavorites();
      if (!alive) return;
      const loadedProducts = (data.items || [])
        .map((item) => item.product)
        .filter(normalizeFavoriteProduct);
      setIds(new Set(loadedProducts.map((product) => product.external_id)));
      setProducts(loadedProducts);
    };

    load()
      .catch((requestError) => {
        if (alive) {
          setError(requestError.message || "Не удалось загрузить избранное.");
        }
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [authKey]);

  const has = React.useCallback((productId) => ids.has(productId), [ids]);

  const toggle = React.useCallback(
    async (product) => {
      const productId =
        typeof product === "string" ? product : product?.external_id;
      if (!productId) return { added: false };

      const active = ids.has(productId);
      const previousIds = ids;
      const previousProducts = products;
      const nextIds = new Set(ids);
      if (active) nextIds.delete(productId);
      else nextIds.add(productId);
      setIds(nextIds);
      setProducts((current) => {
        if (active) {
          return current.filter((item) => item.external_id !== productId);
        }
        const normalized = normalizeFavoriteProduct(product);
        return normalized
          ? [...current.filter((item) => item.external_id !== productId), normalized]
          : current;
      });

      if (!api.getToken()) {
        writeStoredIds(GUEST_FAVORITES_KEY, [...nextIds]);
        api.trackEvent(active ? "favorite_removed" : "favorite_added", {
          product_external_id: productId,
          metadata: { surface: "favorites" },
        });
        return { added: !active };
      }

      try {
        if (active) await api.removeFavorite(productId);
        else await api.addFavorite(productId);
        api.trackEvent(active ? "favorite_removed" : "favorite_added", {
          product_external_id: productId,
          metadata: { surface: "favorites" },
        });
        return { added: !active };
      } catch (requestError) {
        setIds(new Set(previousIds));
        setProducts(previousProducts);
        throw requestError;
      }
    },
    [ids, products],
  );

  return {
    ids,
    products,
    count: ids.size,
    loading,
    error,
    has,
    toggle,
  };
}

function normalizeBagProduct(product) {
  return {
    external_id: product.external_id,
    name: product.name,
    brand: product.brand,
    price_rub: Number(product.price_rub) || 0,
    routine_step: product.routine_step || "other",
    category: product.category || "",
    image_url: product.image_url || null,
    product_url: product.product_url || null,
  };
}

export function readStoredBag() {
  try {
    const value = JSON.parse(localStorage.getItem(COSMETIC_BAG_KEY) || "[]");
    if (!Array.isArray(value)) return [];
    const unique = new Map();
    value.forEach((product) => {
      if (product && typeof product.external_id === "string") {
        unique.set(product.external_id, normalizeBagProduct(product));
      }
    });
    return [...unique.values()];
  } catch {
    return [];
  }
}

function writeStoredBag(products) {
  try {
    localStorage.setItem(COSMETIC_BAG_KEY, JSON.stringify(products));
  } catch {
    // Storage can be unavailable in private mode. The in-memory state still works.
  }
}

export function useCosmeticBag(auth) {
  const [products, setProducts] = React.useState(readStoredBag);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");
  const authKey = auth?.user?.user_id || (api.getToken() ? "authenticated" : "guest");

  React.useEffect(() => {
    let alive = true;

    const load = async () => {
      setLoading(true);
      setError("");

      if (!api.getToken()) {
        if (alive) setProducts(readStoredBag());
        return;
      }

      const guestProducts = readStoredBag();
      if (guestProducts.length) {
        const migration = await Promise.allSettled(
          guestProducts.map((product) => api.addCosmeticBagItem(product.external_id)),
        );
        if (migration.every((result) => result.status === "fulfilled")) {
          writeStoredBag([]);
        }
      }

      const data = await api.getCosmeticBag();
      if (!alive) return;
      setProducts(
        (data.items || [])
          .map((item) => item.product)
          .filter((product) => product?.external_id)
          .map(normalizeBagProduct),
      );
    };

    load()
      .catch((requestError) => {
        if (alive) {
          setError(
            requestError.message || "Не удалось загрузить косметичку.",
          );
        }
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [authKey]);

  React.useEffect(() => {
    if (!api.getToken()) writeStoredBag(products);
  }, [products]);

  const has = React.useCallback(
    (productId) => products.some((product) => product.external_id === productId),
    [products],
  );

  const add = React.useCallback(
    async (product) => {
      if (!product?.external_id) return false;
      const previous = products;
      const nextProduct = normalizeBagProduct(product);
      setProducts([
        ...products.filter((item) => item.external_id !== nextProduct.external_id),
        nextProduct,
      ]);
      setError("");

      try {
        if (api.getToken()) await api.addCosmeticBagItem(product.external_id);
        api.trackEvent("cosmetic_bag_added", {
          product_external_id: product.external_id,
          metadata: { surface: "cosmetic_bag" },
        });
        return true;
      } catch (requestError) {
        setProducts(previous);
        setError(requestError.message || "Не удалось добавить средство.");
        return false;
      }
    },
    [products],
  );

  const remove = React.useCallback(
    async (productId) => {
      const previous = products;
      setProducts(products.filter((product) => product.external_id !== productId));
      setError("");

      try {
        if (api.getToken()) await api.removeCosmeticBagItem(productId);
        api.trackEvent("cosmetic_bag_removed", {
          product_external_id: productId,
          metadata: { surface: "cosmetic_bag" },
        });
        return true;
      } catch (requestError) {
        setProducts(previous);
        setError(requestError.message || "Не удалось убрать средство.");
        return false;
      }
    },
    [products],
  );

  const refresh = React.useCallback((latestProducts) => {
    const latest = new Map(
      latestProducts.map((product) => [product.external_id, product]),
    );
    setProducts((current) =>
      current.map((product) =>
        latest.has(product.external_id)
          ? normalizeBagProduct(latest.get(product.external_id))
          : product,
      ),
    );
  }, []);

  const toggle = React.useCallback(
    async (product) => {
      if (has(product.external_id)) return remove(product.external_id);
      return add(product);
    },
    [add, has, remove],
  );

  const clear = React.useCallback(async () => {
    const previous = products;
    setProducts([]);
    setError("");
    try {
      if (api.getToken()) await api.clearCosmeticBag();
      return true;
    } catch (requestError) {
      setProducts(previous);
      setError(requestError.message || "Не удалось очистить косметичку.");
      return false;
    }
  }, [products]);
  const total = products.reduce((sum, product) => sum + product.price_rub, 0);

  return {
    products,
    count: products.length,
    total,
    loading,
    error,
    has,
    add,
    remove,
    toggle,
    clear,
    refresh,
  };
}
