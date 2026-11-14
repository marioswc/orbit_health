# Misión simulada en vivo

Para que la demo no sea manual: una tripulación cuyas bandas "envían" datos solas, con una historia que contar. Usa **el mismo canal que una banda real** (el flujo continuo de sensores, con sus ventanas y su paso inmediato de lo extremo), así que lo que se ve es el sistema trabajando de verdad. Solo los valores son inventados.

## Cómo se usa

```bash
./run.sh                                                                   # en una terminal
curl -X POST "localhost:3000/api/demo/simulacion/iniciar"                  # 34 min de misión en ~2 min y medio
curl "localhost:3000/api/demo/simulacion/estado"                           # progreso, línea de tiempo narrada y hitos
curl -X POST "localhost:3000/api/demo/simulacion/detener"                  # detiene y devuelve el enlace a la normalidad
```

| Parámetro | Por defecto | Qué hace |
|---|---|---|
| `ritmo` | 15 | Segundos de misión que avanzan por cada tick. Debe ser **menor o igual a la ventana de sensores** (60 s); si no, el estado trae un `aviso` y solo se registra una de cada dos rondas |
| `tick_s` | 1 | Segundos reales entre ticks (de 0.01 a 10) |
| `semilla` | 7 | Con la misma semilla salen los mismos valores |

Con `ritmo=15` y `tick_s=1`, la misión dura unos 2 minutos y medio. Para una demo más corta, sube `tick_s` o `ritmo` (por ejemplo `ritmo=30&tick_s=0.5`).

Para empezar de cero, arranca con una base nueva: `ORBIT_DB_PATH=/tmp/demo.db ./run.sh`. La simulación **no borra nada**.

## La historia (minutos de misión)

| Min | Qué pasa | Qué se ve |
|---|---|---|
| 0 | Tripulación estable, bandas conectadas | Todo en verde |
| 6 | El CO₂ de la cabina empieza a subir | El CO₂ sube hacia el umbral |
| 8 a 11 | T1 respira más rápido | La **línea base personal** de T1 avisa (amarillo) antes de que las reglas estándar lo marquen |
| 12.5 | T2 también se ve afectado y el CO₂ ya está alto | Salta la **alerta colectiva** |
| 14 | Conjunción solar: se pierde el enlace | Modo eclipse: la cola retiene los eventos (cientos al final del apagón) |
| 16 | T1 pasa a rojo con el enlace caído | La tripulación lo ve al instante; su alerta espera a bordo |
| 22 | Vuelve el enlace | Sale **primero lo urgente** |
| 26 a 32 | Se corrige el CO₂ y todos se recuperan | Vuelve al verde |

T3 y T4 se mantienen sanos todo el tiempo, para que se vea que el sistema no da falsas alarmas.

## Qué devuelve `/api/demo/simulacion/estado`
`activa`, `finalizada`, `minuto_mision`, `progreso_pct`, `eventos` (la historia, con `ocurrido: true` según avanza), `hitos` (niveles actuales, primer rojo, alerta colectiva y máximo de eventos retenidos a bordo) y `aviso`. Para el frontend basta con consultarlo cada segundo.

## Qué NO es
- No es una banda real: los valores salen de un guion. La conexión con una banda real está en [BANDA_BLE.md](BANDA_BLE.md).
- No es una predicción: el guion es ilustrativo y los umbrales son supuestos pendientes de validación médica.
- Un detalle de diseño que sale a la vista: **durante un apagón largo se acumulan muchos eventos de rutina**. Hoy salen todos al volver el enlace, ordenados por urgencia. Resumir lo rutinario antes de enviar sigue pendiente.
