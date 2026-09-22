# RifaPay - MVP conciliación automática (MP mock)

## Arquitectura (10 líneas)
1. Marketplace multi-organizador: cada rifa concilia contra su propia cuenta.
2. Solo transferencia CBU/CVU, 0% comisión; MP solo lectura, nunca checkout.
3. Orden con monto único (base + centavos) como ID de match.
4. Reserva 30min, ventana match 24h, liberación sola.
5. Worker + webhook corren matcher monto+fecha+no reutilizado.
6. Comprobante opcional, nunca da pagado (hash para Fase 2).
7. Tokens MP cifrados Fernet, JWT organizador.
8. Provider abstraído para Fase 2/3 (Belvo/CSV).
9. Backend Render + Postgres, front estático.
10. Mock MP para QA sin credenciales reales.

## Dev local
```powershell
cd server
python -m venv .venv; .\.venv\Scripts\Activate
pip install -r requirements.txt
copy .env.example .env
python -m app.seed
uvicorn app.main:app --reload --port 8000
```
```powershell
cd client
npm install
npm run dev
```
Probar: login demo@rifapay.local/demo1234 -> Conectar MP (mock) -> abrir rifa demo -> reservar -> `POST /api/dev/mock-credit {"organizer_id":"...","amount":<monto exacto>}` -> ver check verde.

## Deploy Render
Build: `pip install -r requirements.txt && alembic upgrade head`
Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
Vars: DATABASE_URL (managed), JWT_SECRET, FERNET_KEY (`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`), MP_MOCK_MODE=True, FRONTEND_URL.
