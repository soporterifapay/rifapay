// TEMPORAL: pagina de prototipos de fondos (/fondos). Se elimina al elegir ganador.
const GRAIN = "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)' opacity='0.5'/%3E%3C/svg%3E\")"
const DOTS = "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24'%3E%3Ccircle cx='2' cy='2' r='1.2' fill='%23047857'/%3E%3C/svg%3E\")"

const BACKGROUNDS = {
  A: {
    nombre: 'A — Grano + Resplandor superior',
    desc: 'Ruido de papel al 3% + halo esmeralda arriba. Calidez sutil, cero distracción.',
    style: {
      backgroundColor: '#faf9f7',
      backgroundImage: `${GRAIN}, radial-gradient(1200px 320px at 50% -80px, rgba(4,120,87,0.10), transparent 70%)`,
      backgroundBlendMode: 'multiply, normal',
    },
    grainOpacity: 0.035,
  },
  B: {
    nombre: 'B — Aurora Mesh',
    desc: 'Manchas radiales esmeralda/ámbar difuminadas + grano leve. Moderno y cálido.',
    style: {
      backgroundColor: '#faf9f7',
      backgroundImage: `${GRAIN}, radial-gradient(600px 380px at 12% 8%, rgba(4,120,87,0.10), transparent 70%), radial-gradient(700px 420px at 88% 20%, rgba(217,119,6,0.08), transparent 70%), radial-gradient(900px 500px at 50% 110%, rgba(4,120,87,0.05), transparent 70%)`,
      backgroundBlendMode: 'multiply, normal, normal, normal',
    },
    grainOpacity: 0.03,
  },
  C: {
    nombre: 'C — Grilla de puntos + Viñeta cálida',
    desc: 'Puntos esmeralda cada 24px + bordes levemente cálidos. Técnico y ordenado.',
    style: {
      backgroundColor: '#faf9f7',
      backgroundImage: `${DOTS}, radial-gradient(120% 90% at 50% 40%, transparent 60%, rgba(120,90,40,0.06))`,
    },
    grainOpacity: 0,
  },
}

function Muestra() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <p className="badge badge-ok">Sorteo 15 de octubre</p>
      <h2 className="text-3xl font-extrabold mt-2">Tus rifas en piloto automático</h2>
      <p className="text-slate-600 mt-1">Comprá tu número, transferí y listo. Sin registros, sin vueltas.</p>
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
        <h1 className="text-2xl font-extrabold">Prototipos de fondo</h1>
        <p className="text-slate-600 text-sm">Página temporal — se elimina al elegir el ganador. Bajá para comparar las 3 opciones con contenido real.</p>
      </div>
      {Object.entries(BACKGROUNDS).map(([key, bg]) => (
        <section key={key} style={bg.style} className="border-y border-slate-200 relative">
          {bg.grainOpacity > 0 && (
            <div aria-hidden="true" style={{ position: 'absolute', inset: 0, backgroundImage: GRAIN, opacity: bg.grainOpacity, pointerEvents: 'none' }} />
          )}
          <div className="max-w-5xl mx-auto p-4 relative">
            <p className="font-bold text-lg">{bg.nombre}</p>
            <p className="text-slate-600 text-sm mb-2">{bg.desc}</p>
          </div>
          <Muestra />
        </section>
      ))}
    </div>
  )
}
