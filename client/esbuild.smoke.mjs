import { build } from './node_modules/esbuild/lib/main.js'
await build({
  entryPoints: ['smoke.jsx'],
  bundle: true,
  platform: 'node',
  format: 'cjs',
  jsx: 'automatic',
  define: { 'import.meta.env.VITE_API_URL': JSON.stringify('http://localhost:8000') },
  outfile: './smoke.cjs',
  logLevel: 'error',
})
console.log('BUNDLED')
