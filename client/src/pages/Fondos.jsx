// TEMPORAL: pagina de prototipos de fondos (/fondos). Se elimina al elegir ganador.
// Ronda 2: solo opciones LISAS (sin grano ni puntos) por feedback visual.
const BACKGROUNDS = {
  A: {
    nombre: 'A — Degradado cálido vertical',
    desc: 'Marfil arriba que funde a crema melocotón pálido abajo. Calidez pura, nada que canse la vista.',
    style: { background: 'linear-gradient(180deg, #faf9f7 0%, #faf6ef 55%, #f5ecdd 100%)' },
  },
  B: {
    nombre: 'B — Ondas suaves',
    desc: 'Bandas curvas anchas esmeralda 4% + ámbar 3%. Movimiento liso, estética fintech amigable.',
    style: {
      backgroundColor: '#faf9f7',
      backgroundImage: 'radial-gradient(1200px 500px at -10% 20%, rgba(4,120,87,0.06), transparent 70%), radial-gradient(1000px 480px at 110% 55%, rgba(217,119,6,0.06), transparent 70%), radial-gradient(900px 420px at 30% 95%, rgba(4,120,87,0.04), transparent 70%)',
    },
  },
  C: {
    nombre: 'C — Halo superior limpio',
    desc: 'Luz esmeralda difuminada arriba sobre marfil liso. Profundidad mínima, sin textura.',
    style: {
      backgroundColor: '#faf9f7',
      backgroundImage: 'radial-gradient(1100px 300px at 50% -90px, rgba(4,120,87,0.12), transparent 70%)',
    },
  },
  D: {
    nombre: 'D — Hero bosque + resto marfil',
    desc: 'Bloque hero en verde profundo con texto blanco + resto liso. Contraste profesional.',
    style: { backgroundColor: '#faf9f7' },
    heroDark: true,
  },
}

function Muestra({ heroDark }) {
  const heroStyle = heroDark
    ? { background: 'linear-gradient(135deg, #064e3b 0%, #047857 100%)', color: '#fff' }
    : {}
  const subStyle = heroDark ? { color: 'rgba(255,255,255,0.85)' } : {}
  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <div className="rounded-2xl p-6" style={heroStyle}>
        <p className="badge badge-ok">Sorteo 15 de octubre</p>
        <h2 className="text-3xl font-extrabold mt-2">Tus rifas en piloto automático</h2>
        <p className="mt-1" style={heroDark ? subStyle : { color: '#475569' }}>Comprá tu número, transferí y listo. Sin registros, sin vueltas.</p>
      </div>
      <div className="grid sm:grid-cols-2 gap-4 mt-6">
        <div className="card">
          <div className="skel h-28 mb-3" aria-hidden="true" />
          <p className="font-bold">TV 55&quot; 4K</p>
          <p className="text-sm text-slate-600 tnum">$5.000,00 · 100 números</p>
          <div className="mt-2 h-2 rounded-full bg-slate-200"><div className="h-2 rounded-full bg-emerald-600" style={{ width: '42%' }} /></div>
          <button className="btn mt-3 w-full" type="button" tabIndex={-1}>Ver rifa</button>
        </div>
        <div className="card">
          <div className="skel h-28 mb-3" aria-hidden="true" />
          <p className="font-bold">Premio sorpresa 🎁</p>
          <p className="text-sm text-slate-600 tnum">$20,00 · 150 números</p>
          <div className="mt-2 h-2 rounded-full bg-slate-200"><div className="h-2 rounded-full bg-emerald-600" style={{ width: '68%' }} /></div>
          <button className="btn mt-3 w-full" type="button" tabIndex={-1}>Ver rifa</button>
        </div>
      </div>
    </div>
  )
}

export default function Fondos() {
  return (
    <div className="-m-4">
      <div className="max-w-5xl mx-auto p-4">
        <h1 className="text-2xl font-extrabold">Prototipos de fondo — ronda 2 (lisos)</h1>
        <p className="text-slate-600 text-sm">Página temporal — se elimina al elegir el ganador. Bajá para comparar las 4 opciones con contenido real.</p>
      </div>
      {Object.entries(BACKGROUNDS).map(([key, bg]) => (
        <section key={key} style={bg.style} className="border-y border-slate-200">
          <div className="max-w-5xl mx-auto p-4">
            <p className="font-bold text-lg">{bg.nombre}</p>
            <p className="text-slate-600 text-sm mb-2">{bg.desc}</p>
          </div>
          <Muestra heroDark={bg.heroDark} />
        </section>
      ))}
    </div>
  )
}
