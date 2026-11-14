import { useEffect, useState } from "react";
import { api } from "../../../shared/api/client";
import type { Tripulante } from "../types/tripulante";

export function useTripulantes() {
  const [tripulantes, setTripulantes] = useState<Tripulante[]>([]);
  const [tid, setTid] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api<Tripulante[]>("/tripulantes")
      .then((t) => { setTripulantes(t); if (t[0]) setTid(t[0].id); })
      .catch((e) => setError(e.message));
  }, []);

  return { tripulantes, tid, setTid, error };
}
