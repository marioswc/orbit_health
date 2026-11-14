import { useLanguage, useTranslation } from "../../i18n";

/** Conmutador ES | EN. El idioma se recuerda y se refleja en <html lang>. */
export default function ToggleIdioma() {
  const { language, setLanguage } = useLanguage();
  const { t } = useTranslation();
  return (
    <div className="idioma" role="group" aria-label={t("topbar.language")}>
      {(["es", "en"] as const).map((l) => (
        <button key={l} type="button" className={language === l ? "activo" : ""} aria-pressed={language === l} lang={l} onClick={() => setLanguage(l)}>
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
