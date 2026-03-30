/**
 * WhisperLeaf Signal Board — React shell (hybrid repo).
 * Logo: /owl.png from whisperleaf-site/public/ (Vite dev server).
 */

export default function WhisperLeafSignalBoard() {
  return (
    <main
      style={{
        minHeight: "100vh",
        padding: "1.5rem",
        background: "#0d1117",
        color: "#e6edf3",
        fontFamily: "system-ui, Segoe UI, Roboto, sans-serif",
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
          marginBottom: "0.5rem",
        }}
      >
        <img
          src="/owl.png"
          alt=""
          width={48}
          height={48}
          style={{ width: 48, height: 48, objectFit: "contain", display: "block" }}
        />
        <h1 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 600 }}>
          WhisperLeaf Signal Board
        </h1>
      </header>
      <p style={{ margin: "0.5rem 0 0", fontSize: "0.82rem", color: "#8b949e", maxWidth: "36rem" }}>
        Local-first view. Connect routing or data when you are ready.
      </p>
    </main>
  );
}
