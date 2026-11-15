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

> **Ojo:** con `ORBIT_SEED_DEMO=1` (el valor por defecto) el arranque ya crea estas cuentas solo, aunque no corras el script. En una instalación real pon `ORBIT_SEED_DEMO=0` y da de alta cuentas con `scripts/inscribir_tripulante.sh` (PIN aleatorio): un PIN público no protege nada. La auditoría de seguridad lo avisa.

## Probar el login y tu asistente
1. En `.env`: `ORBIT_AUTH=1` y `ORBIT_IA_PROVEEDOR=local` (con Ollama corriendo).
2. `scripts/cuentas_demo.sh`, luego `./run.sh` y abre `http://127.0.0.1:3000`.
3. Entra como T3 (`333333`), abre **Asistente**: cuéntale tus intereses y conversa. El perfil y el chat son privados: T4 o el comandante no pueden verlos.

## Tripulación ficticia (todo simulado, no son personas reales)
| Id | Nombre | Profesión | Cómo es (resumen que usa su asistente) | Trato |
|---|---|---|---|---|
| T1 | Valeria Montoya | Comandante | Serena y disciplinada; le cuesta pedir ayuda. Le gustan el ajedrez y correr | Directo, completo |
| T2 | Mateo Ríos | Especialista de misión | Curioso y bromista; se apaga si se siente aislado. Guitarra, cocina, su familia | Cálido, completo |
| T3 | Camila Ortega | Ingeniero | Analítica y tranquila; necesita pausas. Ciencia ficción, astronomía, rompecabezas | Directo, breve |
| T4 | Andrés Leal | Piloto | Sociable y competitivo; el encierro le pesa. Fútbol, música, retos | Cálido, breve |

Cada persona puede cambiar su perfil y su trato desde la pantalla **Asistente**; lo sembrado solo se aplica a quien aún no tiene el suyo, y en bases anteriores solo reemplaza los nombres genéricos ("Tripulante Uno"…). Los rasgos y los intereses solo se usan con el modelo **local**, nunca con DeepSeek.
