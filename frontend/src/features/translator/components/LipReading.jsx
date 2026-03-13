import { useMemo } from "react";

export default function LipReading() {
  const drills = useMemo(
    () => [
      { id: 1, level: "Beginner", focus: "Single syllables", duration: "5 min" },
      { id: 2, level: "Intermediate", focus: "Common words", duration: "8 min" },
      { id: 3, level: "Advanced", focus: "Short phrases", duration: "12 min" },
    ],
    []
  );

  return (
    <div
      style={{
        minHeight: "calc(100vh - 74px)",
        background: "linear-gradient(160deg,#FFF7F3 0%,#FFEDE5 45%,#FFF9F5 100%)",
        padding: "40px 20px 60px",
        fontFamily: "'Fredoka', 'Comic Neue', cursive",
      }}
    >
      <div
        style={{
          maxWidth: "980px",
          margin: "0 auto",
          background: "#fff",
          border: "2px solid #FFD9CC",
          borderRadius: "24px",
          boxShadow: "0 10px 35px rgba(242, 78, 30, 0.14)",
          padding: "28px",
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: "clamp(1.8rem, 4vw, 2.6rem)",
            color: "#F24E1E",
            fontWeight: 900,
          }}
        >
          Lip Reading Studio 👄
        </h1>

        <p style={{ margin: "10px 0 0", color: "#6B7280", fontSize: "1rem" }}>
          Train visual speech understanding using structured practice drills.
          This tab is now connected to your main interface and ready for feature expansion.
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "14px",
            marginTop: "22px",
          }}
        >
          {drills.map((drill) => (
            <div
              key={drill.id}
              style={{
                borderRadius: "16px",
                border: "1px solid #FFD9CC",
                background: "linear-gradient(145deg,#FFF,#FFF6F2)",
                padding: "16px",
              }}
            >
              <div style={{ color: "#F24E1E", fontWeight: 800, fontSize: ".85rem" }}>
                {drill.level}
              </div>
              <div style={{ marginTop: "4px", color: "#111827", fontWeight: 700 }}>
                {drill.focus}
              </div>
              <div style={{ marginTop: "6px", color: "#6B7280", fontSize: ".9rem" }}>
                Duration: {drill.duration}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
