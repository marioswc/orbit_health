import type { Nivel } from "../../shared/types/nivel";
import type { LecturaEstado } from "./types/estado";

export type NivelZona = Nivel | "sin_datos";
export type Capa = "traje" | "musculo" | "hueso" | "organos";

export const CAPAS: { id: Capa; etiqueta: string }[] = [
  { id: "traje", etiqueta: "Traje" },
  { id: "musculo", etiqueta: "Músculo" },
  { id: "hueso", etiqueta: "Hueso" },
  { id: "organos", etiqueta: "Órganos" },
];

export interface Zona {
  id: string;
  etiqueta: string;
  indicadores: string[];
  /** Punto de la zona sobre el dibujo (px del dibujo original del astronauta) y acercamiento de la camara. */
  x: number;
  y: number;
  zoom: number;
  /** Capa que se revela al elegir la zona. */
  capaInicial: Capa;
  /** Titulo del bloque de efectos. */
  peligro: string;
  /** Efectos generales del vuelo espacial en esta zona. Fuente: NASA HRP, "Hazards of Human Spaceflight". */
  efectos: string[];
  /** Que se ve en cada capa (solo lo que respalda la fuente). */
  anatomia: Partial<Record<Capa, string>>;
}

export const FUENTE_EFECTOS = "NASA HRP · Hazards of Human Spaceflight";

export const ZONAS: Zona[] = [
  {
    id: "snc", etiqueta: "Cabeza / SNC", indicadores: ["avpu", "sueno_horas", "sueno_eficiencia_pct", "sueno_despertares_min"], x: 239, y: 76, zoom: 2.2, capaInicial: "organos",
    peligro: "Radiación, aislamiento y sueño",
    efectos: [
      "Radiación espacial: daño al sistema nervioso central, con alteraciones cognitivas, menor función motora y cambios de comportamiento.",
      "Aislamiento y confinamiento: deterioro del ánimo, la cognición, la moral y la interacción entre la tripulación.",
      "Sueño: un entorno pequeño y ruidoso, un día marciano más largo y el estrés prolongado pueden alterarlo.",
    ],
    anatomia: {
      organos: "La radiación espacial puede dañar el sistema nervioso central: alteraciones cognitivas, menor función motora y cambios de comportamiento.",
      hueso: "El casco y el traje protegen, pero fuera de la magnetosfera la radiación sigue siendo uno de los peligros principales.",
    },
  },
  {
    id: "resp", etiqueta: "Respiratorio", indicadores: ["spo2", "frecuencia_respiratoria"], x: 239, y: 138, zoom: 2.2, capaInicial: "organos",
    peligro: "Aire y entorno cerrado",
    efectos: [
      "La nave es un entorno cerrado que recicla el aire, incluido el CO₂ de la tripulación.",
      "Por eso la calidad del aire se monitorea de forma continua.",
      "Hipoxia: riesgo del catálogo HRP que aquí se vigila con la saturación de oxígeno (mapeo del equipo).",
    ],
    anatomia: { organos: "El aire de la nave se recicla y su calidad se monitorea sin pausa; la hipoxia es uno de los riesgos del catálogo HRP." },
  },
  {
    id: "cardio", etiqueta: "Cardiovascular", indicadores: ["presion_sistolica", "presion_diastolica", "frecuencia_cardiaca", "variabilidad_cardiaca"], x: 237, y: 194, zoom: 2.3, capaInicial: "organos",
    peligro: "Radiación y gravedad alterada",
    efectos: [
      "Radiación espacial: mayor riesgo de enfermedades cardíacas y circulatorias.",
      "Gravedad alterada (ingravidez en tránsito y 3/8 g en Marte): compromete el sistema cardiovascular, además de músculos y huesos.",
    ],
    anatomia: { organos: "La radiación aumenta el riesgo de enfermedades cardíacas y circulatorias; la gravedad alterada compromete además al corazón." },
  },
  {
    id: "metab", etiqueta: "Tronco / Metabólico", indicadores: ["glucosa", "temperatura"], x: 239, y: 233, zoom: 2.2, capaInicial: "organos",
    peligro: "Inmunidad, nutrición y radiación",
    efectos: [
      "Entornos cerrados: suben las hormonas del estrés y el sistema inmunológico se altera, con más susceptibilidad a alergias, enfermedades e infecciones.",
      "Sin alimentos frescos ni variedad: monotonía y posibles deficiencias nutricionales.",
      "Radiación: náuseas, vómitos, anorexia y fatiga.",
    ],
    anatomia: { organos: "En entornos cerrados suben las hormonas del estrés y el sistema inmunológico se altera; sin alimentos frescos hay riesgo de deficiencias nutricionales." },
  },
  {
    id: "brazos", etiqueta: "Brazos", indicadores: [], x: 155, y: 207, zoom: 2.0, capaInicial: "musculo",
    peligro: "Gravedad alterada",
    efectos: [
      "Afecta a los músculos y a los huesos.",
      "Desadaptación sensorimotora: coordinación mano-ojo y habilidades motoras finas.",
    ],
    anatomia: {
      musculo: "La gravedad alterada afecta a los músculos: es parte de la pérdida muscular que NASA HRP estudia con protocolos de ejercicio.",
      hueso: "Sin la carga de la gravedad, la densidad mineral ósea disminuye (no aumenta).",
    },
  },
  {
    id: "piernas", etiqueta: "Piernas", indicadores: ["ejercicio_min"], x: 211, y: 323, zoom: 1.8, capaInicial: "musculo",
    peligro: "Pérdida ósea y locomoción",
    efectos: [
      "La densidad mineral ósea baja alrededor de 1 % por mes en microgravedad según el video de NASA HRP; la página de gravedad indica entre 1 % y 1.5 %.",
      "Locomoción y equilibrio se ven afectados cada vez que cambia el campo gravitatorio (1 g, ingravidez, 3/8 g en Marte).",
    ],
    anatomia: {
      musculo: "Las piernas sostienen el cuerpo en 1 g; en ingravidez dejan de hacerlo y el músculo se debilita. El ejercicio es la contramedida que NASA estudia.",
      hueso: "Los huesos de carga, como los de las piernas, son los que más se resienten cuando falta la gravedad.",
    },
  },
];

/** Donde queda el brazo en cada capa (el esqueleto, los musculos y los organos tienen otra postura que el traje). */
const ANCLA_BRAZO: Partial<Record<Capa, [number, number]>> = { musculo: [172, 186], hueso: [184.7, 176.6], organos: [170.6, 216.3] };

/** En las capas de anatomia, cada zona apunta a donde esta el organo o musculo (no a las marcas del traje). */
const ANCLA_ANATOMIA: Record<string, [number, number]> = { snc: [239, 76], resp: [239, 148], cardio: [247, 152], metab: [239, 212], piernas: [224, 320] };

/** Punto de la zona para la capa visible. */
export function ancla(z: Zona, capa: Capa): [number, number] {
  if (capa === "traje") return [z.x, z.y];
  if (z.id === "brazos") return ANCLA_BRAZO[capa] ?? [z.x, z.y];
  return ANCLA_ANATOMIA[z.id] ?? [z.x, z.y];
}

const ORDEN: Record<Nivel, number> = { verde: 0, amarillo: 1, rojo: 2 };

export function nivelZona(indicadores: string[], lecturas: LecturaEstado[]): NivelZona {
  const dentro = lecturas.filter((l) => indicadores.includes(l.indicador));
  if (dentro.length === 0) return "sin_datos";
  return dentro.reduce<Nivel>((peor, l) => (ORDEN[l.nivel] > ORDEN[peor] ? l.nivel : peor), "verde");
}
