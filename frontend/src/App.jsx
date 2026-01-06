import ProductPage from "./components/ProductPage";
import ChatWidget from "./components/ChatWidget";

const API_BASE = "http://localhost:8000";

export default function App() {
  return (
    <div style={styles.shell}>
      <ProductPage apiBase={API_BASE} />
      <ChatWidget apiBase={API_BASE} />
    </div>
  );
}

const styles = {
  shell: {
    minHeight: "100vh",
    width: "100%",
    background: "radial-gradient(1200px 600px at 10% 10%, #111827, #060712)",
  },
};
