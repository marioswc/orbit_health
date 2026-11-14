# Seguridad pensada para operar a bordo

Principio: el sistema vive sin internet, con una tripulación pequeña y con la posibilidad real de que alguien quede incapacitado. Por eso no se copió el modelo de una aplicación web.

## Decisiones según el entorno

| Realidad a bordo | Decisión |
|---|---|
| Sin internet ni correo | Sin recuperación por email ni identidad externa; todo local y con librería estándar |
| 4 a 6 personas | Tres roles: tripulante, médico y comandante |
| Un tripulante puede quedar incapacitado | Lo clínico lo **ven y registran todos** los autenticados; registrar a un compañero queda auditado |
| Un bloqueo permanente podría impedir atender una emergencia | Bloqueos **temporales** (5 min tras 5 fallos), nunca permanentes |
| Guantes y pantalla táctil | PIN numérico de 6 a 10 dígitos |
| Sin soporte desde Tierra para restablecer accesos | Código de recuperación entregado al alta, o reinicio por médico o comandante |
| Turnos largos y reinicios de equipo | Sesión de 12 h guardada en la base, revocable |
| Nadie puede auditar desde fuera | Auditoría con hash encadenado, verificable sin red |
| Privacidad de salud mental | Diario, PHQ-2 y ánimo: solo su dueño, **sin excepción de rol**. Única vía de salida: un aviso que el propio tripulante decide enviar (con consentimiento, revocable y auditado) al médico o al comandante, sin diario ni puntaje |

## Permisos

| Acción | Tripulante | Médico | Comandante |
|---|---|---|---|
| Ver y registrar signos de cualquiera | Sí | Sí | Sí |
| Diario y PHQ-2 propios | Sí | Sí | Sí |
| Diario y PHQ-2 de otra persona | No | No | No |
| Ver los avisos de salud mental que un tripulante decidió enviar | No | Sí | Sí |
| Cambiar el enlace, escenarios de demo | No | Sí | Sí |
| Reiniciar el PIN de otro, ver auditoría | No | Sí | Sí |

## Cómo activarla

```bash
ORBIT_AUTH=1 ./run.sh
scripts/inscribir_tripulante.sh T1 comandante     # muestra PIN y código de recuperación una sola vez
```

Con `ORBIT_AUTH=0` (por defecto, demo en una estación) el comportamiento es el de siempre. `ORBIT_HOST` distinto de `127.0.0.1` exige `ORBIT_AUTH=1`.

## Para quien hace el frontend

| Endpoint | Uso |
|---|---|
| `GET /api/auth/estado` | `activa: true` indica que hay que mostrar el acceso |
| `POST /api/auth/login` `{tripulante_id, pin}` | Devuelve `token`; enviarlo como `Authorization: Bearer <token>` |
| `401` / `403` / `423` | Sesión vencida / sin permiso / bloqueado temporalmente (`bloqueado_hasta`) |
| `POST /api/auth/recuperar` | Con código de recuperación y PIN nuevo |

## Límites actuales (sin ocultarlos)

- **Sin TLS:** el tráfico dentro de la cabina viaja en HTTP. Solo debe usarse en una red aislada y confiable.
- **Base sin cifrar:** quien tenga acceso al archivo de la base puede leerla. Falta cifrado en reposo.
- **PIN de 6 dígitos:** resiste intentos por la API gracias al bloqueo, pero no un ataque contra el archivo robado.
- **Reloj del equipo:** expiración de sesiones y bloqueos dependen de la hora local; sin sincronización externa, un reloj desfasado los altera.
- Los roles y permisos son decisiones de diseño pendientes de revisión del equipo y de un profesional.
