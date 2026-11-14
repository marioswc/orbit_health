# 06 — Seguridad a Bordo, Simulación en Vivo y Pruebas de Calidad

Este documento explica cómo se protegió el acceso al sistema para operar dentro de una nave sin internet, cómo se construyeron las herramientas de demostración en vivo y cómo las pruebas automáticas garantizan que el código y la documentación no se contradigan.

---

## 1. Seguridad Pensada para Operar a Bordo (`ORBIT_AUTH=1`)

### Qué problema había
No se podía copiar el sistema de usuarios de una página web normal porque:
1. En el espacio profundo **no hay internet ni servidor de correo** para enviar enlaces de "olvidé mi contraseña".
2. Si un tripulante falla su clave varias veces y la cuenta se bloquea para siempre, **podría impedir atender una emergencia médica a bordo**.
3. Si el tripulante T1 queda inconsciente, su compañero T2 necesita poder registrarle sus signos vitales desde su propia sesión.

### Cómo se solucionó (`commits 55c45bb`, `484fbcc`, `ce1e339`, `58ae017`)
En `backend/app/dominio/seguridad.py`, `backend/app/servicios/auth.py` y `backend/app/api/auth.py`:
- **PIN numérico de 6 a 10 dígitos (`POST /api/auth/login`):** cómodo para pantallas táctiles o uso con guantes. Los PIN nunca se guardan en texto plano, sino protegidos criptográficamente (`PBKDF2-HMAC-SHA256` con sal única).
- **Bloqueos temporales, nunca permanentes:** tras 5 intentos fallidos, la cuenta se bloquea solo por **5 minutos** (`423 Locked`) para frenar intentos adivinatorios sin dejar inutilizable el acceso a bordo.
- **Recuperación 100 % sin internet:**
  - Al inscribir a un tripulante por terminal (`scripts/inscribir_tripulante.sh`), se entrega un **código de recuperación de un solo uso** con el que puede cambiar su PIN en `POST /api/auth/recuperar`.
  - Si también perdió su código, el **médico o el comandante** pueden reiniciárselo en `POST /api/auth/reiniciar-pin/{tid}`.
- **Permisos adaptados a emergencias y privacidad:**
  - **Datos clínicos (`POST /api/lecturas`, `GET /api/estado/{tid}`):** cualquier tripulante con sesión iniciada puede ver y registrar signos vitales de un compañero incapacitado, pero cuando registra datos de otra persona queda grabado en la **auditoría**.
  - **Datos privados (`diario`, `animo`, `tamizajes`, `preferencias`):** exclusivos de su dueño, sin excepción de rol.
  - **Operaciones críticas (cambiar el enlace `/api/enlace`, ver auditoría `/api/auditoria`, correr demos):** reservadas al **médico** y al **comandante**.
- **Auditoría con cadena de hash (`GET /api/auditoria` y `GET /api/auditoria/verificar`):** igual que la cola hacia Tierra, cada acción sensible (inicios de sesión, fallos, registros a nombre de otro, avisos médicos) queda sellada con el hash del registro anterior para que nadie pueda borrar sus huellas.
- **Guardia de red (`run.sh`):** si alguien intenta exponer el servidor fuera de la computadora local (`ORBIT_HOST` distinto de `127.0.0.1`), el sistema exige obligatoriamente que la autenticación (`ORBIT_AUTH=1`) esté encendida.

---

## 2. Misión Simulada en Vivo y Herramientas de Demo

### Qué problema había
Durante una presentación o evaluación, teclear lecturas a mano una por una para mostrar cómo sube el CO₂, cómo avisa la línea base personal, cómo se corta el enlace y cómo se priorizan las emergencias tomaba demasiado tiempo y distraía de la explicación.

### Cómo se solucionó (`commits 0d3a952`, `c5eec69`, `f73798b`, `a798de4`)
1. **Misión simulada en vivo (`POST /api/demo/simulacion/iniciar`, `GET /api/demo/simulacion/estado`, `POST /api/demo/simulacion/detener`):**
   - Implementada en `backend/app/fuentes/guion_vivo.py` y `backend/app/servicios/simulacion_viva.py`.
   - Corre en segundo plano una historia de **34 minutos de misión** (en unos 2 minutos y medio reales) enviando muestras **por el mismo canal de flujo continuo que usaría una banda real**.
   - **La historia que cuenta sola:** todo inicia en verde → sube el CO₂ de la cabina → la línea base personal de T1 avisa en amarillo antes que las reglas fijas → T2 empeora y salta la **alerta colectiva** → ocurre una conjunción solar y cae el enlace (acumulando más de cien eventos retenidos) → T1 cae en **rojo** en pleno apagón → vuelve el enlace y salen primero las urgencias → se repara el aire y todos vuelven a verde. Mientras tanto, T3 y T4 se mantienen sanos todo el tiempo para demostrar que no hay falsas alarmas.
   - Al detenerse o finalizar, limpia las ventanas en memoria para que el reloj adelantado de la simulación no afecte el uso normal posterior.
2. **Escenarios instantáneos (`GET /api/demo/escenarios` y `POST /api/demo/escenarios/{nombre}`):** permiten reproducir en menos de un segundo casos puntuales (`hipoxia_eclipse` y `co2_colectivo`).
3. **Comparativa "Con ORBIT vs Sin ORBIT" (`GET /api/demo/comparativa`):** calcula y muestra qué ocurre desde el segundo cero cuando hay un evento crítico en la Luna o en Marte si la tripulación depende de esperar la respuesta de Tierra frente a contar con triaje autónomo a bordo.
4. **Calibración sin internet con datos reales (`backend/app/fuentes/calibracion.py`):** carga series fisiológicas públicas de *PhysioNet BIDMC* (resumidas por mediana cada 20 s) como historial previo de los tripulantes con `origen = 'calibracion'`, permitiendo que la línea base de 14 días funcione desde el primer minuto sin ensuciar la cola de salida.

---

## 3. Pruebas Automáticas que Vigilan la Seguridad y la Documentación

### Qué problema había
A medida que el proyecto creció a **60 rutas en la API**, era muy fácil que al agregar una ruta nueva se olvidara ponerle candado de sesión, o que los documentos `.md` se quedaran con rutas o cifras viejas.

### Cómo se solucionó (`commit 213d8c1`)
En `backend/tests/test_documentacion.py` y `backend/app/api/referencia.py`:
- **Candado automático de rutas públicas:** existe una lista única (`RUTAS_PUBLICAS`, 13 rutas que no contienen datos médicos personales, como el login o las explicaciones educativas). Una prueba automática recorre las **60 operaciones de la API** con la autenticación activada: si alguien crea una ruta nueva y olvida protegerla, la prueba falla inmediatamente.
- **Referencia de la API autogenerada (`scripts/generar_api_doc.py`):** genera [API_REFERENCIA.md](../../docs/API_REFERENCIA.md) directamente desde el código real y una prueba falla si alguien cambia una ruta y no actualiza el documento.
- **Verificación de la verdad en los documentos:** las pruebas revisan todos los archivos `.md` del proyecto para comprobar que todas las rutas `/api/...` mencionadas existan de verdad, que ningún enlace local esté roto, que todas las variables `ORBIT_*` estén en `.env.example` y que las cifras de cobertura del HRP coincidan exactamente con las del código.
