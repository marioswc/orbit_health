import { FormEvent, memo, useState } from "react";
import { useTranslation } from "../../../i18n";
import Alerta from "../../../shared/components/Alerta";
import Logo from "../../../shared/components/Logo";
import Selector, { type Opcion } from "../../../shared/components/Selector";

interface Props {
  tripulantes: Opcion[];
  alEntrar: (tid: string, pin: string) => Promise<unknown>;
  alRecuperar: (tid: string, codigo: string, pinNuevo: string) => Promise<void>;
}

/** Pantalla de acceso a bordo con PIN numerico (pensada para pantalla tactil / guantes). */
function AccesoTripulante({ tripulantes, alEntrar, alRecuperar }: Props) {
  const { t } = useTranslation("seguridad");
  const [tid, setTid] = useState(tripulantes[0]?.valor ?? "");
  const [pin, setPin] = useState("");
  const [modoRec, setModoRec] = useState(false);
  const [codigo, setCodigo] = useState("");
  const [pinNuevo, setPinNuevo] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; texto: string } | null>(null);

  const elegido = tid || tripulantes[0]?.valor || "";

  async function enviarLogin(e: FormEvent) {
    e.preventDefault();
    if (!elegido || !pin) return setMsg({ ok: false, texto: t("err.login") });
    setMsg(null);
    try {
      await alEntrar(elegido, pin);
    } catch (err) {
      setMsg({ ok: false, texto: (err as Error).message });
    }
  }

  async function enviarRecuperar(e: FormEvent) {
    e.preventDefault();
    if (!elegido || !codigo || !pinNuevo) return setMsg({ ok: false, texto: t("err.recover") });
    setMsg(null);
    try {
      await alRecuperar(elegido, codigo, pinNuevo);
      setModoRec(false);
      setCodigo("");
      setPinNuevo("");
      setPin("");
      setMsg({ ok: true, texto: t("ok.updated") });
    } catch (err) {
      setMsg({ ok: false, texto: (err as Error).message });
    }
  }

  return (
    <section className="tarjeta acceso" aria-label={t("aria")}>
      <div className="acceso-marca">
        <Logo />
        <span>ORBIT Health</span>
      </div>
      <p className="etiqueta-pagina">{t("kicker")}</p>
      <h1>{t("title")}</h1>
      <p className="suave">{t("desc")}</p>

      {!modoRec ? (
        <form onSubmit={enviarLogin} className="acceso-form">
          <label className="campo-form">
            <span>{t("crew")}</span>
            <Selector opciones={tripulantes} valor={elegido} alCambiar={setTid} etiqueta={t("crew")} />
          </label>
          <label className="campo-form">
            <span>{t("pin")}</span>
            <input type="password" inputMode="numeric" pattern="[0-9]{6,10}" maxLength={10} value={pin} onChange={(e) => setPin(e.target.value)} placeholder={t("pin_ph")} autoComplete="current-password" />
          </label>
          <div className="fila">
            <button type="submit">{t("enter")}</button>
            <button type="button" className="ghost" onClick={() => { setModoRec(true); setMsg(null); }}>{t("recover")}</button>
          </div>
        </form>
      ) : (
        <form onSubmit={enviarRecuperar} className="acceso-form">
          <label className="campo-form">
            <span>{t("crew")}</span>
            <Selector opciones={tripulantes} valor={elegido} alCambiar={setTid} etiqueta={t("crew")} />
          </label>
          <label className="campo-form">
            <span>{t("code")}</span>
            <input value={codigo} onChange={(e) => setCodigo(e.target.value)} placeholder={t("code_ph")} />
          </label>
          <label className="campo-form">
            <span>{t("pin_new")}</span>
            <input type="password" inputMode="numeric" pattern="[0-9]{6,10}" maxLength={10} value={pinNuevo} onChange={(e) => setPinNuevo(e.target.value)} placeholder={t("pin_ph")} />
          </label>
          <div className="fila">
            <button type="submit">{t("change")}</button>
            <button type="button" className="ghost" onClick={() => { setModoRec(false); setMsg(null); }}>{t("back")}</button>
          </div>
        </form>
      )}

      {msg && <Alerta tono={msg.ok ? "ok" : "error"} titulo={msg.ok ? t("alert.ok") : t("alert.error")}>{msg.texto}</Alerta>}
    </section>
  );
}

export default memo(AccesoTripulante);

