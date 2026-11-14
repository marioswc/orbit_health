import { FormEvent, memo, useState } from "react";
import Alerta from "../../../shared/components/Alerta";
import Selector, { type Opcion } from "../../../shared/components/Selector";

interface Props {
  tripulantes: Opcion[];
  alEntrar: (tid: string, pin: string) => Promise<unknown>;
  alRecuperar: (tid: string, codigo: string, pinNuevo: string) => Promise<void>;
}

/** Pantalla de acceso a bordo con PIN numerico (pensada para pantalla tactil / guantes). */
function AccesoTripulante({ tripulantes, alEntrar, alRecuperar }: Props) {
  const [tid, setTid] = useState(tripulantes[0]?.valor ?? "");
  const [pin, setPin] = useState("");
  const [modoRec, setModoRec] = useState(false);
  const [codigo, setCodigo] = useState("");
  const [pinNuevo, setPinNuevo] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; texto: string } | null>(null);

  const elegido = tid || tripulantes[0]?.valor || "";

  async function enviarLogin(e: FormEvent) {
    e.preventDefault();
    if (!elegido || !pin) return setMsg({ ok: false, texto: "Selecciona tu perfil e ingresa tu PIN" });
    setMsg(null);
    try {
      await alEntrar(elegido, pin);
    } catch (err) {
      setMsg({ ok: false, texto: (err as Error).message });
    }
  }

  async function enviarRecuperar(e: FormEvent) {
    e.preventDefault();
    if (!elegido || !codigo || !pinNuevo) return setMsg({ ok: false, texto: "Completa código de recuperación y PIN nuevo" });
    setMsg(null);
    try {
      await alRecuperar(elegido, codigo, pinNuevo);
      setModoRec(false);
      setCodigo("");
      setPinNuevo("");
      setPin("");
      setMsg({ ok: true, texto: "PIN actualizado. Ahora puedes iniciar sesión." });
    } catch (err) {
      setMsg({ ok: false, texto: (err as Error).message });
    }
  }

  return (
    <section className="tarjeta acceso" aria-label="Acceso a bordo">
      <p className="etiqueta-pagina">Seguridad a bordo</p>
      <h1>Iniciar sesión</h1>
      <p className="suave">Ingresa con tu PIN numérico (6 a 10 dígitos). Tras 5 intentos fallidos se aplica bloqueo temporal de 5 minutos.</p>

      {!modoRec ? (
        <form onSubmit={enviarLogin} className="acceso-form">
          <label className="campo-form">
            <span>Tripulante</span>
            <Selector opciones={tripulantes} valor={elegido} alCambiar={setTid} etiqueta="Tripulante" />
          </label>
          <label className="campo-form">
            <span>PIN</span>
            <input type="password" inputMode="numeric" pattern="[0-9]{6,10}" maxLength={10} value={pin} onChange={(e) => setPin(e.target.value)} placeholder="6 a 10 dígitos" autoComplete="current-password" />
          </label>
          <div className="fila">
            <button type="submit">Entrar</button>
            <button type="button" className="ghost" onClick={() => { setModoRec(true); setMsg(null); }}>Recuperar PIN</button>
          </div>
        </form>
      ) : (
        <form onSubmit={enviarRecuperar} className="acceso-form">
          <label className="campo-form">
            <span>Tripulante</span>
            <Selector opciones={tripulantes} valor={elegido} alCambiar={setTid} etiqueta="Tripulante" />
          </label>
          <label className="campo-form">
            <span>Código de recuperación</span>
            <input value={codigo} onChange={(e) => setCodigo(e.target.value)} placeholder="Código entregado al alta" />
          </label>
          <label className="campo-form">
            <span>PIN nuevo</span>
            <input type="password" inputMode="numeric" pattern="[0-9]{6,10}" maxLength={10} value={pinNuevo} onChange={(e) => setPinNuevo(e.target.value)} placeholder="6 a 10 dígitos" />
          </label>
          <div className="fila">
            <button type="submit">Cambiar PIN</button>
            <button type="button" className="ghost" onClick={() => { setModoRec(false); setMsg(null); }}>Volver</button>
          </div>
        </form>
      )}

      {msg && <Alerta tono={msg.ok ? "ok" : "error"} titulo={msg.ok ? "Listo" : "Error de acceso"}>{msg.texto}</Alerta>}
    </section>
  );
}

export default memo(AccesoTripulante);

