# Product

<!-- impeccable:product-schema 1 -->

> Registro inferido de los documentos del proyecto (guía de desarrollo, observaciones de revisión, riesgos NASA HRP) y de las indicaciones del usuario; no pasó por entrevista. Revisar y confirmar.

## Platform

web

## Stack
React 18 · TypeScript · Vite · pnpm (`--ignore-workspace`). Backend FastAPI en `../backend` (solo lectura para el frontend).

## Users
Tripulantes de misiones de espacio profundo (Luna/Marte), que no son médicos, y el médico o comandante a bordo; usan la interfaz en un equipo local, a veces bajo fatiga o emergencia. También el jurado del NASA Space Apps Challenge 2026 durante una demo de 3 minutos.

## Product Purpose
Prototipo de apoyo a la decisión clínica que funciona sin internet: registra signos vitales, calcula NEWS2 en el backend, muestra el estado por zona del cuerpo, ofrece tamizaje PHQ-2 y diario privado, y gestiona una cola de envío a la Tierra con prioridad y modo Eclipse.

## Positioning
Autonomía clínica offline y determinista (sin IA generativa), auditable.

## Operating Context
Sin conexión (prueba con wifi apagado), retardo Tierra-Marte de hasta 20 min por sentido. El frontend no recalcula niveles: muestra los que devuelve la API.

## Capabilities and Constraints
Vistas: Monitor, Bienestar, Enlace. Figura humana SVG con zonas clicables. Prototipo: no sustituye criterio médico; los umbrales están pendientes de validación (el backend expone su estado). Recursos locales: nada de fuentes ni scripts de CDN.

## Brand Commitments
Referencia visual elegida por el usuario: estilo "ElevenLabs" (papel crema #fdfcfc, tinta negra, titulares ligeros, píldoras, sin sombras pesadas). Imagen central: astronauta real (traje EMU de la NASA) con zonas clicables y efectos del vuelo espacial al estilo videojuego. Es una aplicación, no una landing.

## Evidence on Hand
Sin capturas ni logo propio. No inventar testimonios ni métricas.

## Product Principles
- El semáforo clínico nunca depende solo del color: siempre lleva texto.
- Lo local es visible: el diario privado debe indicar que no sale de la nave.
- Honestidad científica: avisos de prototipo y supuestos siempre visibles.

## Accessibility & Inclusion
Uso bajo fatiga: contraste alto, objetivos táctiles amplios, navegación por teclado en la figura. Respetar `prefers-reduced-motion`.
