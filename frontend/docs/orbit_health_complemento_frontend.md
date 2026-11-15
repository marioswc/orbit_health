> **Nota de estilo (acordada 14/11/2026):** todos los componentes de este documento se construyen con el estilo vigente de [ESTILO_PLATAFORMA.md](./ESTILO_PLATAFORMA.md) (tokens de `src/shared/styles/`, paneles liquid glass, semáforo con texto, modo claro y oscuro). Estructura por features (`src/features/<nombre>/`, ver [ARQUITECTURA.md](./ARQUITECTURA.md)).
> Rutas actuales: `FiguraHumana.tsx` está en `src/features/monitor/components/`; `PanelMedicion.tsx` en `src/features/mediciones/`; `DiarioTripulante.tsx` y `Tamizaje.tsx` en `src/features/bienestar/`; `ConsolaEnlace.tsx` en `src/features/enlace/`. **Decisión (14/11/2026): nos quedamos con el layout y el diseño de Santi.** Se eliminó la propuesta de layout de consola (`DashboardNave`); lo que sigue son solo ideas que se suman sin cambiar su diseño. Los componentes nuevos (`HeaderMision`, `MonitorCabina`, `TarjetaSignoVital`) aún **no existen**; el checklist de la sección 4 describe la intención, no verifica el código.

# ORBIT Health: Complementos de Interfaz (Alineación NASA HRP & CSA)

Este documento complementa la guía maestra (`orbit-health-guia-desarrollo-v2.md`) incorporando los elementos visuales y de experiencia de usuario (UX) derivados de las investigaciones oficiales de la NASA (*Human Research Program*) y la Agencia Espacial Canadiense (                                                                            CSA).

Su objetivo es hacer visibles en la interfaz web las correlaciones fisiológicas y ambientales sin alterar la arquitectura del backend ni requerir conexión a internet.

## 1. Reloj de Sol Marciano y Ritmo Circadiano (`HeaderMision.tsx`)

### Fundamento Científico (NASA HRP - *Isolation & Confinement* / Proyecto *ARCHeR*)

En Marte, el día solar (*Sol*) dura aproximadamente **24 horas y 39 minutos**, lo que desplaza el reloj biológico de la tripulación respecto a la Tierra y altera la arquitectura del sueño. El proyecto *ARCHeR* de la NASA monitorea continuamente estos ciclos para prevenir fatiga y deterioro cognitivo.

### Especificación Visual en Frontend

* **Ubicación:** Barra superior fija existente (`.barra`, la de Santi); se suma el reloj sin cambiar su estructura.

* **Elementos:**

  * **Reloj Dual:** Hora UTC de Tierra vs. Tiempo Solar Marciano (`Sol +00:39m` de desfase diario).

  * **Indicador de Descanso del Tripulante:** Badge compacto con las horas dormidas en el último ciclo (ej. `Sueño: 5.2h / Meta: 7.5h`), cambiando a color ámbar si cae por debajo de las 6 horas.

## 2. Monitor Ambiental de Cabina y Correlación Corporal (`MonitorCabina.tsx`)

### Fundamento Científico (NASA HRP - *5 Hazards* & CSA - Espectrómetro *CANS*)

Los peligros espaciales no actúan de forma aislada: se potencian entre sí. Un aumento en el $\text{CO}_2$ del sistema cerrado de soporte vital o un evento de partículas solares (medido de forma continua por el espectrómetro canadiense *CANS*) impacta directamente en el sistema nervioso central y respiratorio del tripulante.

### Especificación Visual en Frontend

* **Ubicación:** Una tarjeta más (`.panel`) en la columna izquierda del escenario, junto a Zonas, Capas y Estados.

* **Elementos:**

  1. **Medidor de** $\text{CO}_2$ **en Cabina (mmHg):**

     * $\le 3.0\text{ mmHg}$ $\rightarrow$ Verde (*Nominal*).

     * $3.1 - 4.0\text{ mmHg}$ $\rightarrow$ Amarillo (*Saturación parcial de filtros*).

     * $> 4.0\text{ mmHg}$ $\rightarrow$ Rojo (*Riesgo de cefalea/acidosis*).

  2. **Dosimetría Acumulada CANS (% Límite de Carrera):**

     * Barra de progreso continua que muestra el porcentaje acumulado de radiación respecto al límite biológico de la misión (ej. `42% del límite de carrera`).

     * Alerta amarilla al superar el $70\%$ y roja al alcanzar el $90\%$.

  3. **Efecto Visual Cruzado en `FiguraHumana.tsx`:**

     * Si el $\text{CO}_2$ o la radiación entran en estado amarillo/rojo, la silueta humana muestra un contorno o pulso preventivo en las zonas de **Cabeza (SNC)** y **Sistema Respiratorio**, reflejando visualmente la interacción entre el entorno cerrado y el cuerpo humano.

## 3. Tarjetas de Comparación con Línea Base Individual (`TarjetaSignoVital.tsx`)

### Fundamento Científico (NASA HRP - *Standard Measures*)

Bajo el enfoque de *Standard Measures* de la NASA (aplicado en la ISS y *Artemis II*), cada astronauta es su propio grupo de control. Un valor aparentemente normal en la Tierra puede representar un desvío crítico en microgravedad si se aleja más de dos desviaciones estándar ($\pm 2\sigma$) de su promedio móvil de 14 días ($\mu_{14}$).

### Especificación Visual en Frontend

* **Ubicación:** Dentro del panel de detalle de zona (columna derecha del escenario) y en el resumen del Monitor.

* **Elementos por cada signo vital:**

  * **Valor Actual:** Lectura más reciente en tipografía grande y legible (ej. `88 lpm`).

  * **Referencia Personal (**$\mu_{14}$**):** Subtexto comparativo directo debajo del valor principal (ej. `Tu base 14d: 68 lpm (+20 lpm)`).

  * **Indicador de Tendencia:** Flecha sutil (`↑`, `↓`, `→`) y etiqueta de estado (`Normal`, `Desvío > 2σ`, `Alerta NEWS2`).

## 4. Checklist Rápido de Integración Frontend (Offline-Ready)

* \[ \] **Cero fuentes o iconos externos por CDN:** Todos los iconos (SVG inline o paquete local como `lucide-react`) y tipografías deben empaquetarse en el build local para pasar el *Wi-Fi Off Test*.

* \[ \] **Props puras en SVG:** Mantener `FiguraHumana.tsx` envuelta en `React.memo`, recibiendo únicamente el estado de alerta (`'verde' | 'amarillo' | 'rojo'`) de cada una de las 5 zonas y el estado ambiental de cabina.

* \[ \] **Validación inmediata en formularios:** Bloquear envíos con valores fuera de rango humano plausible antes de hacer `fetch` a `http://localhost:8000/lecturas`.

* \[ \] **Badge de Privacidad Permanente:** En la pestaña de `DiarioTripulante.tsx`, mantener visible el candado e indicador de almacenamiento 100% local sin cola de salida.


---

> **Firma de IA y Justificación (SI Disclosure):**
> - **Herramienta utilizada:** **Claude (Anthropic)** mediante **Claude Code**.
> - **Justificación de uso:** Se utilizó como asistente técnico durante el hackathon para redactar y estructurar la documentación de frontend, arquitectura de interfaz y componentes, bajo el diseño visual, criterio de experiencia de usuario y validación del equipo humano (conforme a las reglas del *NASA Space Apps Challenge*).
