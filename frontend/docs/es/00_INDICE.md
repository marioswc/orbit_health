# Documentación del Frontend por Módulo — ORBIT Health

Guía clara y sin tecnicismos de lo que hace el frontend de **ORBIT Health**, cómo se organizó y cómo se resolvió cada parte del sistema.

---

## Módulos y capas documentadas

| Documento | Qué explica |
|---|---|
| [01 — Monitor y Entornos](./01_MONITOR_Y_ENTORNOS.md) | Tablero principal de salud, figura humana por zonas, signos vitales, entornos de gravedad (Tierra/Órbita/Luna/Marte), explicaciones con citas NASA y racha de mediciones. |
| [02 — Banda y Simulación](./02_BANDA_Y_SIMULACION.md) | Reloj/banda interactiva en 3D, envío automático desde sensores/simulador, eliminación de la captura manual y etiquetado honesto de datos `simulado`. |
| [03 — Asistente e IA / Voz Local](./03_ASISTENTE_Y_VOZ_LOCAL.md) | Pestaña de Asistente, resumen clínico explicado sin internet, preferencias de tono y burbuja flotante de voz (*push-to-talk*). |
| [04 — Bienestar y Privacidad](./04_BIENESTAR_Y_PRIVACIDAD.md) | Registro de ánimo, diario personal, tamizaje PHQ-2, protocolo de crisis y avisos con consentimiento revocable para el médico a bordo. |
| [05 — Enlace, Historial y Tierra](./05_ENLACE_HISTORIAL_Y_TIERRA.md) | Manejo de apagones de comunicación, simulador de misión en vivo, informes recibidos en Tierra e historial de mediciones en tabla paginada. |
| [06 — Navegación, Estilo, Idiomas y PWA](./06_NAVEGACION_ESTILO_I18N_Y_PWA.md) | Menú lateral animado, nuevo logo, cambio de idioma ES/EN, modo claro/oscuro, optimización de carga y soporte PWA offline. |

---

## Versión en inglés / English version
- [English Documentation Index](../en/00_INDEX.md)


---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Claude (Anthropic)** mediante **Claude Code**.
> - **Justificación de uso:** Se utilizó como asistente técnico durante el hackathon para redactar y estructurar la documentación de frontend, arquitectura de interfaz y componentes, bajo el diseño visual, criterio de experiencia de usuario y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
