import { useState, useEffect, useCallback } from "react";

// ═══════════════════════════════════════════════════════════
//  MOTORE SCIENTIFICO
// ═══════════════════════════════════════════════════════════
const FTP_FACTORS = { "Manuale": 1.0, "Test 20'": 0.95, "Test 8'": 0.90, "Incrementale": 0.75 };

const Bio = {
  calcFtp: (tipo, v) => Math.round(v * (FTP_FACTORS[tipo] ?? 1.0)),
  estTime: (w, p, km, pend, bk) => {
    const fr = (p + bk) * 9.81 * (pend / 100 + 0.005);
    if (!fr || !w) return 0;
    return (km * 1000 / (w / fr)) / 60;
  },
  zones: (ftp, lthr) => [
    { name: "Z1 – Recupero",  wMin: 0,               wMax: Math.round(ftp * 0.55), hMin: 0,               hMax: Math.round(lthr * 0.68), color: "#64748b" },
    { name: "Z2 – Endurance", wMin: Math.round(ftp * 0.56), wMax: Math.round(ftp * 0.75), hMin: Math.round(lthr * 0.69), hMax: Math.round(lthr * 0.83), color: "#3b82f6" },
    { name: "Z3 – Tempo",     wMin: Math.round(ftp * 0.76), wMax: Math.round(ftp * 0.90), hMin: Math.round(lthr * 0.84), hMax: Math.round(lthr * 0.94), color: "#22c55e" },
    { name: "Z4 – Soglia",    wMin: Math.round(ftp * 0.91), wMax: Math.round(ftp * 1.05), hMin: Math.round(lthr * 0.95), hMax: Math.round(lthr * 1.05), color: "#f59e0b" },
    { name: "Z5 – VO₂max",   wMin: Math.round(ftp * 1.06), wMax: Math.round(ftp * 1.30), hMin: Math.round(lthr * 1.06), hMax: 220,                     color: "#ef4444" },
  ],
  benchmarks: [
    { cat: "World Tour",      fm: "5–7%",   wkg: "6.0 – 6.5", peso: 65 },
    { cat: "Pro Continental", fm: "7–9%",   wkg: "5.5 – 6.0", peso: 68 },
    { cat: "Elite / U23",     fm: "8–11%",  wkg: "4.5 – 5.5", peso: 70 },
    { cat: "Amatore Top",     fm: "10–14%", wkg: "3.5 – 4.5", peso: 72 },
    { cat: "Cicloturista",    fm: "> 15%",  wkg: "< 3.0",     peso: 78 },
  ],
};

// ═══════════════════════════════════════════════════════════
//  HELPERS UI
// ═══════════════════════════════════════════════════════════
const fmt1 = (n) => Number(n).toFixed(1);
const fmt2 = (n) => Number(n).toFixed(2);

function Card({ children, className = "" }) {
  return (
    <div className={`bg-gray-900 border border-gray-700 rounded-2xl p-5 ${className}`}>
      {children}
    </div>
  );
}

function SectionTitle({ icon, children }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <span className="text-xl">{icon}</span>
      <h3 className="text-sm font-bold uppercase tracking-widest text-cyan-400">{children}</h3>
    </div>
  );
}

function MetricBlock({ label, current, target, unit = "", delta = null, color = "text-white" }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-gray-400 uppercase tracking-wider">{label}</span>
      <span className={`text-2xl font-extrabold ${color}`}>{current}{unit}</span>
      {target !== undefined && (
        <span className="text-xs text-cyan-400">
          Target: <strong>{target}{unit}</strong>
          {delta !== null && (
            <span className={`ml-2 ${delta >= 0 ? "text-green-400" : "text-red-400"}`}>
              ({delta >= 0 ? "+" : ""}{fmt2(delta)})
            </span>
          )}
        </span>
      )}
    </div>
  );
}

function NumInput({ label, value, onChange, min, max, step = 0.1, unit = "" }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs text-gray-400">{label}{unit ? ` (${unit})` : ""}</span>
      <input
        type="number"
        min={min} max={max} step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"
      />
    </label>
  );
}

function SelectInput({ label, value, onChange, options }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs text-gray-400">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors"
      >
        {options.map((o) => <option key={o}>{o}</option>)}
      </select>
    </label>
  );
}

function Tab({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`px-6 py-2 rounded-xl text-sm font-semibold transition-all ${
        active
          ? "bg-cyan-500 text-gray-950 shadow-lg shadow-cyan-500/30"
          : "text-gray-400 hover:text-white hover:bg-gray-800"
      }`}
    >
      {children}
    </button>
  );
}

// ═══════════════════════════════════════════════════════════
//  COMPONENTE PRINCIPALE
// ═══════════════════════════════════════════════════════════
export default function PerformanceLab() {
  const [tab, setTab] = useState("new");
  const [result, setResult] = useState(null);
  const [athletes, setAthletes] = useState([]);
  const [saved, setSaved] = useState(false);
  const [selectedAthlete, setSelectedAthlete] = useState(null);

  // Form state
  const [cognome, setCognome] = useState("");
  const [nome, setNome] = useState("");
  const [altezza, setAltezza] = useState(175);
  const [profilo, setProfilo] = useState("Scalatore");
  const [pAtt, setPAtt] = useState(70.0);
  const [fmAtt, setFmAtt] = useState(15.0);
  const [tipoTest, setTipoTest] = useState("Manuale");
  const [valTest, setValTest] = useState(250);
  const [lthr, setLthr] = useState(160);
  const [pTar, setPTar] = useState(68.0);
  const [fmTar, setFmTar] = useState(10.0);
  const [ftpTar, setFtpTar] = useState(280);
  const [dist, setDist] = useState(10.0);
  const [grad, setGrad] = useState(7.0);
  const [bike, setBike] = useState(7.5);

  // Load from storage
  useEffect(() => {
    (async () => {
      try {
        const r = await window.storage.get("plp_athletes");
        if (r) setAthletes(JSON.parse(r.value));
      } catch (_) {}
    })();
  }, []);

  const ftpAtt = Bio.calcFtp(tipoTest, valTest);
  const bmiAtt = pAtt / Math.pow(altezza / 100, 2);
  const bmiTar = pTar / Math.pow(altezza / 100, 2);

  const handleElabora = () => {
    const tA = Bio.estTime(ftpAtt, pAtt, dist, grad, bike);
    const tT = Bio.estTime(ftpTar, pTar, dist, grad, bike);
    setResult({
      nome, cognome, altezza, profilo,
      data: new Date().toLocaleDateString("it-IT"),
      pA: pAtt, fmA: fmAtt, ftpA: ftpAtt, lthr, bmiA: bmiAtt, test: tipoTest,
      pT: pTar, fmT: fmTar, ftpT: ftpTar, bmiT: bmiTar,
      dist, grad, bike, tA, tT,
      zones: Bio.zones(ftpTar, lthr),
      wkgA: ftpAtt / pAtt,
      wkgT: ftpTar / pTar,
    });
    setSaved(false);
  };

  const handleSalva = async () => {
    if (!result) return;
    const record = {
      id: Date.now(),
      nome: result.nome,
      cognome: result.cognome,
      altezza: result.altezza,
      profilo: result.profilo,
      data: result.data,
      peso: result.pA, fm: result.fmA, ftp: result.ftpA, lthr: result.lthr,
      peso_t: result.pT, fm_t: result.fmT, ftp_t: result.ftpT,
      dist: result.dist, grad: result.grad, bike: result.bike,
      t_att: result.tA, t_tar: result.tT,
      wkgA: result.wkgA, wkgT: result.wkgT,
    };
    const updated = [...athletes, record];
    setAthletes(updated);
    try {
      await window.storage.set("plp_athletes", JSON.stringify(updated));
    } catch (_) {}
    setSaved(true);
  };

  const handleDelete = async (id) => {
    const updated = athletes.filter((a) => a.id !== id);
    setAthletes(updated);
    try { await window.storage.set("plp_athletes", JSON.stringify(updated)); } catch (_) {}
    if (selectedAthlete?.id === id) setSelectedAthlete(null);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white font-sans">
      {/* ── HEADER ── */}
      <div className="border-b border-gray-800 bg-gray-900/80 sticky top-0 z-10 backdrop-blur">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🧬</span>
            <div>
              <h1 className="text-lg font-extrabold tracking-tight text-white">Performance Lab Pro</h1>
              <p className="text-xs text-gray-400">Nutrition & Performance Analysis</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Tab active={tab === "new"} onClick={() => setTab("new")}>➕ Nuova Valutazione</Tab>
            <Tab active={tab === "archive"} onClick={() => setTab("archive")}>
              📂 Archivio {athletes.length > 0 && <span className="ml-1 bg-cyan-500 text-gray-950 rounded-full text-xs px-1.5">{athletes.length}</span>}
            </Tab>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">

        {/* ══════════════ TAB: NUOVA VALUTAZIONE ══════════════ */}
        {tab === "new" && (
          <div className="space-y-6">

            {/* Anagrafica */}
            <Card>
              <SectionTitle icon="👤">Anagrafica Atleta</SectionTitle>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <label className="flex flex-col gap-1">
                  <span className="text-xs text-gray-400">Cognome</span>
                  <input value={cognome} onChange={e => setCognome(e.target.value)}
                    placeholder="Rossi"
                    className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors" />
                </label>
                <label className="flex flex-col gap-1">
                  <span className="text-xs text-gray-400">Nome</span>
                  <input value={nome} onChange={e => setNome(e.target.value)}
                    placeholder="Mario"
                    className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-500 transition-colors" />
                </label>
                <NumInput label="Altezza" unit="cm" value={altezza} onChange={setAltezza} min={120} max={230} step={1} />
                <SelectInput label="Profilo Atleta" value={profilo} onChange={setProfilo}
                  options={["Scalatore", "Passista", "Triatleta", "Granfondista"]} />
              </div>
            </Card>

            {/* 3 colonne: Attuale / Target / Salita */}
            <div className="grid md:grid-cols-3 gap-6">

              {/* Stato Attuale */}
              <Card>
                <SectionTitle icon="📊">1. Stato Attuale</SectionTitle>
                <div className="space-y-3">
                  <NumInput label="Peso" unit="kg" value={pAtt} onChange={setPAtt} min={40} max={150} />
                  <NumInp
