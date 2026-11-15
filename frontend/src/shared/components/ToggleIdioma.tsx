import { useLanguage, useTranslation } from "../../i18n";

/** Un solo boton circular: muestra el idioma actual (ES / EN) y al pulsarlo cambia al otro. Se recuerda y se refleja en <html lang>. */
export default function ToggleIdioma() {
  const { language, setLanguage } = useLanguage();
  const { t } = useTranslation();
  const otro = language === "es" ? "en" : "es";
  return (
    <button type="button" className="idioma-boton" lang={language}
      aria-label={`${t("topbar.language")}: ${language.toUpperCase()} → ${otro.toUpperCase()}`}
      title={`${t("topbar.language")}: ${language.toUpperCase()} → ${otro.toUpperCase()}`}
      onClick={() => setLanguage(otro)}>
      {language.toUpperCase()}
    </button>
  );
}
