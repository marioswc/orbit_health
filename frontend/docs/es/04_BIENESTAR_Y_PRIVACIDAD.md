# 04 — Bienestar Psicológico y Privacidad

## Qué problema había
Los datos de salud mental (cómo se siente el astronauta, su diario personal o un tamizaje de depresión) son sumamente sensibles: no deben mezclarse con la telemetría técnica ni enviarse automáticamente a Tierra sin permiso. Además, en una cabina espacial la falta de oxígeno puede provocar o agravar crisis psicológicas.

## Cómo se resolvió
- **Separación estricta de privacidad ([BienestarPage.tsx](../../src/features/bienestar/routes/BienestarPage.tsx), commits `901bc30`, `c9f1081`, `eca3fc9`):**
  - La pantalla deja visible desde el encabezado que el ánimo, el diario y el tamizaje son privados y **no entran a la cola hacia la Tierra**.
  - Al mover las preferencias del asistente a su propia pestaña (`feef45a`), Bienestar quedó enfocado exclusivamente en salud mental y acompañamiento.
- **Ánimo diario y diario con filtros (commits `b2b942c`, `c9f1081`):**
  - Registro rápido de ánimo (1 a 5) con gráfica de tendencia personal de los últimos días y avisos amables cuando cambia respecto al promedio habitual.
  - Diario personal con buscador, filtro por mes/periodo y lectura en ventana modal sin salir de la vista.
- **Tamizaje PHQ-2, oxígeno de cabina y protocolo de crisis (commit `ce363f8`):**
  - Si el tamizaje sale positivo o el tripulante indica estar en crisis, se despliega el protocolo de apoyo inmediato y se verifica la calidad de oxígeno en cabina (`% O₂`) por si un problema ambiental está influyendo.
  - **Consentimiento explícito y revocable:** el tripulante decide si quiere avisar al médico a bordo con una nota opcional, y puede **revocar su consentimiento** en cualquier momento desde la misma pantalla.
