import { useEffect, useState } from "react";

export default function ProductPage({ apiBase }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;

    (async () => {
      try {
        setError("");
        setLoading(true);

        const res = await fetch(`${apiBase}/products`);
        if (!res.ok) throw new Error(await res.text());

        const data = await res.json();
        if (alive) setProducts(Array.isArray(data) ? data : []);
      } catch (e) {
        if (alive) {
          setError(e?.message || "Failed to load products");
          setProducts([]);
        }
      } finally {
        if (alive) setLoading(false);
      }
    })();

    return () => {
      alive = false;
    };
  }, [apiBase]);

  return (
    <div style={styles.page}>
      <div style={styles.hero}>
        <div>
          <div style={styles.kicker}>ElectroMart</div>
          <h1 style={styles.h1}>Product Catalog</h1>
          <p style={styles.p}>
            Browse the demo products. Use the chatbot (bottom-right) to ask about pricing,
            stock, promos, troubleshooting, or orders.
          </p>
        </div>
      </div>

      <div style={styles.metaRow}>
        {loading ? (
          <div style={styles.muted}>Loading…</div>
        ) : error ? (
          <div style={styles.error}>Couldn’t load products: {error}</div>
        ) : (
          <div style={styles.muted}>
            Showing <b>{products.length}</b> products
          </div>
        )}
      </div>

      <div style={styles.grid}>
        {products.map((p) => (
          <div key={p.sku} style={styles.card}>
            <div style={styles.cardTop}>
              <div style={styles.badges}>
                <span style={styles.badge}>{p.category}</span>
                <span
                  style={{
                    ...styles.stockBadge,
                    ...(p.stock > 0 ? styles.inStock : styles.outOfStock),
                  }}
                >
                  {p.stock > 0 ? `${p.stock} in stock` : "Out of stock"}
                </span>
              </div>
            </div>

            <div style={styles.cardBody}>
              <div style={styles.name}>{p.name}</div>
              <div style={styles.sku}>SKU: {p.sku}</div>

              <div style={styles.priceRow}>
                <div style={styles.price}>${Number(p.price).toLocaleString()}</div>
              </div>
            </div>
          </div>
        ))}

        {!loading && !error && products.length === 0 ? (
          <div style={styles.empty}>No products found.</div>
        ) : null}
      </div>
    </div>
  );
}

const styles = {
  page: {
    padding: "28px 18px 120px",
    maxWidth: 1100,
    margin: "0 auto",
    color: "white",
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
    boxSizing: "border-box",
  },
  hero: {
    padding: "18px 18px",
    borderRadius: 16,
    border: "1px solid rgba(255,255,255,0.08)",
    background:
      "radial-gradient(900px 300px at 0% 0%, rgba(79,70,229,0.22), transparent), rgba(15, 23, 42, 0.85)",
  },
  kicker: { fontSize: 12, opacity: 0.75, letterSpacing: 0.4 },
  h1: { margin: "6px 0 6px", fontSize: 28 },
  p: { margin: 0, opacity: 0.8, maxWidth: 720, lineHeight: 1.4 },

  metaRow: { marginTop: 12 },
  muted: { opacity: 0.75, fontSize: 13 },
  error: {
    fontSize: 13,
    color: "#fecaca",
    background: "rgba(239, 68, 68, 0.12)",
    border: "1px solid rgba(239, 68, 68, 0.25)",
    padding: "10px 12px",
    borderRadius: 12,
  },

  grid: {
    marginTop: 16,
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))",
    gap: 14,
  },
  card: {
    borderRadius: 14,
    border: "1px solid rgba(255,255,255,0.08)",
    background: "rgba(15, 23, 42, 0.82)",
    overflow: "hidden",
    boxShadow: "0 14px 34px rgba(0,0,0,0.28)",
  },
  cardTop: {
    height: 64,
    background:
      "linear-gradient(135deg, rgba(79,70,229,0.25), rgba(34,197,94,0.08))",
    padding: 12,
    boxSizing: "border-box",
  },
  badges: { display: "flex", gap: 8, flexWrap: "wrap" },
  badge: {
    fontSize: 12,
    padding: "4px 10px",
    borderRadius: 999,
    border: "1px solid rgba(255,255,255,0.16)",
    background: "rgba(0,0,0,0.12)",
    opacity: 0.95,
    textTransform: "capitalize",
  },
  stockBadge: {
    fontSize: 12,
    padding: "4px 10px",
    borderRadius: 999,
    border: "1px solid rgba(255,255,255,0.16)",
  },
  inStock: { background: "rgba(34,197,94,0.16)" },
  outOfStock: { background: "rgba(239,68,68,0.16)" },

  cardBody: { padding: 12 },
  name: { fontSize: 15, fontWeight: 650, marginBottom: 6 },
  sku: { fontSize: 12, opacity: 0.7, marginBottom: 10 },
  priceRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  price: { fontSize: 18, fontWeight: 700 },
  empty: {
    gridColumn: "1 / -1",
    padding: 16,
    borderRadius: 12,
    border: "1px dashed rgba(255,255,255,0.18)",
    opacity: 0.75,
  },
};
