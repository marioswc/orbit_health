# 03 — Asistente Clínico e IA / Voz Local

## Qué problema había
En una misión espacial un astronauta puede tener las manos ocupadas o necesitar una explicación rápida y entendible de su estado sin depender de internet, pero una IA nunca debe inventar diagnósticos ni alterar el nivel de emergencia médica.

## Cómo se resolvió
- **Pestaña dedicada de Asistente ([AsistentePage.tsx](../../src/features/asistente/routes/AsistentePage.tsx), [ExplicacionEstado.tsx](../../src/features/asistente/components/ExplicacionEstado.tsx), commit `feef45a`):**
  - Se movieron aquí las preferencias de comunicación (*tono directo o cálido, nivel de detalle, frecuencia de recordatorios*) que antes estaban dentro de Bienestar, para dejar cada tema en su lugar.
  - Se conectó el resumen explicado del estado (`GET /api/estado/{tid}/explicacion`): si hay un modelo local encendido en la estación lo redacta con lenguaje natural y muestra el aviso de que es generado por IA; si no hay modelo corriendo, responde de forma inmediata usando las reglas locales deterministas.
- **Burbuja flotante de voz *push-to-talk* ([BurbujaVoz.tsx](../../src/features/voz/components/BurbujaVoz.tsx), commits `feef45a`, `507c8aa`, `2eb001e`):**
  - Se integró una burbuja flotante para hablar por turnos con el sistema usando el micrófono (`POST /api/voz/chat/{tid}`), mostrando claramente los estados (*Listo, Escuchando, Procesando, Hablando*) y etiquetas de IA.
  - Se corrigieron errores de doble montaje en React (`StrictMode`) para que la burbuja nunca se quede trabada en *"Procesando"*, y se eliminó un botón flotante duplicado en `App.tsx` para dejar una sola burbuja limpia.
- **Nota honesta de operación:**
  - La transcripción y síntesis de voz en el servidor solo se activan cuando el equipo tiene configuradas las variables de voz y los modelos locales descargados (`ORBIT_VOZ_ACTIVA=1`); si están apagados, la interfaz informa con claridad que el servicio de voz local no está activo sin afectar el resto de la aplicación.
