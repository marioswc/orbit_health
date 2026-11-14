# Documentación del frontend — ORBIT Health

Índice de la documentación del frontend (React 18 · TypeScript · Vite · pnpm).

| Documento | Contenido |
|---|---|
| [ARQUITECTURA.md](./ARQUITECTURA.md) | Screaming architecture por features, reglas de dependencia, mapa de migración desde el código actual |
| [ESTILO_PLATAFORMA.md](./ESTILO_PLATAFORMA.md) | Sistema de diseño **vigente**: tokens, modo oscuro, liquid glass, componentes, escenario del astronauta, movimiento, accesibilidad, licencias |
| [DISENO.md](./DISENO.md) | Sistema de diseño (referencia Dala): tokens, tipografía, componentes, adaptaciones para ORBIT |
| [FIGURA_HUMANA.md](./FIGURA_HUMANA.md) | Especificación del SVG clicable: zonas, indicadores, estados, accesibilidad |
| [API.md](./API.md) | Endpoints del backend que consume el frontend y sus tipos |
| [AVANCE_FRONTEND_SANTI.md](./AVANCE_FRONTEND_SANTI.md) | Registro del trabajo en curso en la rama `frontend-santi`: cambios, supuestos y pendientes |
| [`../AGENTS.md`](../AGENTS.md) | Reglas persistentes del frontend para el agente: estilo vigente, diseño, estructura y offline |

## Cómo correr el frontend

```bash
cd frontend
pnpm install --ignore-workspace   # --ignore-workspace: hay un pnpm-workspace.yaml en la carpeta de usuario
pnpm dev                          # http://localhost:3000 (proxy /api -> http://localhost:8000)
pnpm build                        # tsc --noEmit && vite build
```

Requiere el backend FastAPI en el puerto 8000 (ver `backend/`).

## Reglas de trabajo

- Documentar aquí cada decisión de arquitectura o diseño relevante.
- Lo marcado como **Supuesto** no tiene fuente y debe revisarse con el equipo.
- No se hace commit ni push sin que lo indique el responsable del repo.
