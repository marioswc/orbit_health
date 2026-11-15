# Cuentas de demostración

Para ensayar el acceso con PIN (`ORBIT_AUTH=1`) sin inventar credenciales cada vez. **Son solo para demos: PIN fáciles y públicos, nunca en una misión real.**

```bash
scripts/cuentas_demo.sh          # crea las cuentas (requiere ORBIT_DEMO_API=1); no toca las que ya existan
ORBIT_AUTH=1 ./run.sh            # arranca pidiendo PIN
```

| Tripulante | Rol | PIN | Qué puede hacer |
|---|---|---|---|
| T1 | Comandante | `111111` | Ver y capturar; reiniciar el PIN de otros, cambiar el enlace, ver auditoría y avisos |
| T2 | Tripulante | `222222` | Ver y capturar lo suyo |
| T3 | Tripulante | `333333` | Ver y capturar lo suyo |
| T4 | Tripulante | `444444` | Ver y capturar lo suyo |

El PIN debe tener de 6 a 10 dígitos. Un PIN equivocado repetido bloquea la cuenta un rato (ver [SEGURIDAD_A_BORDO.md](SEGURIDAD_A_BORDO.md)). Para una cuenta real usa `scripts/inscribir_tripulante.sh`, que genera un PIN aleatorio y lo muestra una sola vez.
