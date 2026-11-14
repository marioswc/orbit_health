import { useEffect, useRef, useState } from "react";

/** Numero que cuenta hasta su valor (600 ms). Con "reducir movimiento" salta directo. */
export default function Contador({ valor }: { valor: number }) {
  const [mostrado, setMostrado] = useState(valor);
  const previo = useRef(valor);

  useEffect(() => {
    const desde = previo.current;
    previo.current = valor;
    if (desde === valor || window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) { setMostrado(valor); return; }
    let id = 0;
    const t0 = performance.now();
    const paso = (t: number) => {
      const p = Math.min((t - t0) / 600, 1);
      const e = 1 - Math.pow(1 - p, 3); // ease-out cubico
      setMostrado(Math.round(desde + (valor - desde) * e));
      if (p < 1) id = requestAnimationFrame(paso);
    };
    id = requestAnimationFrame(paso);
    return () => cancelAnimationFrame(id);
  }, [valor]);

  return <span className="num-contador">{mostrado}</span>;
}
