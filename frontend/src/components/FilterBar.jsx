import { useMemo, useState } from "react";
import {
  TEMPO_POLLUTANTS,
  getPollutantLabel,
  getPollutantUnit,
} from "../constants/pollutants";

export default function FilterBar({ pollutant, onChange }) {
  const [query, setQuery] = useState("");

  const threshold = 8; // muestra búsqueda si la lista es extensa
  const showSearch = TEMPO_POLLUTANTS.length >= threshold;

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return TEMPO_POLLUTANTS;
    return TEMPO_POLLUTANTS.filter((p) => {
      const name = getPollutantLabel(p.id);
      const unit = getPollutantUnit(p.id);
      return (
        p.id.toLowerCase().includes(q) ||
        name.toLowerCase().includes(q) ||
        unit.toLowerCase().includes(q)
      );
    });
  }, [query]);

  const selectedUnit = pollutant ? getPollutantUnit(pollutant) : "";

  const handleChange = (e) => {
    const value = e.target.value;
    onChange?.(value); // envía solo el id; la unidad queda disponible abajo
  };

  const selectId = "pollutant-select";

  return (
    <div className="px-4 md:px-0 py-3 flex gap-4 items-center">
      <div className="w-full sm:w-80 text-black">
        <label
          htmlFor={selectId}
          className="block mb-1 text-white text-xl fira-sans-semibold"
        >
          Contaminante
        </label>

        {showSearch && (
          <div className="mb-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar contaminante..."
              className="w-full rounded-md bg-white/95 text-base px-3 py-2 outline-none ring-1 ring-white/20 focus:ring-2 focus:ring-blue-400 fira-sans-regular"
              aria-label="Buscar contaminante"
              aria-controls={selectId}
            />
          </div>
        )}

        <select
          id={selectId}
          name="pollutant_id"
          value={pollutant ?? ""}
          onChange={handleChange}
          required
          className="w-full rounded-md bg-white text-xl px-3 py-2 fira-sans-medium outline-none ring-1 ring-white/20 focus:ring-2 focus:ring-blue-400"
          aria-required="true"
        >
          <option value="" disabled>
            Selecciona un contaminante
          </option>
          {filtered.map((item) => (
            <option key={item.id} value={item.id} data-unit={item.unit}>
              {`${getPollutantLabel(item.id)} (${getPollutantUnit(item.id)})`}
            </option>
          ))}
        </select>

        {/* Unidad disponible para validaciones/envío sin renderizarla visualmente */}
        <input type="hidden" name="pollutant_unit" value={selectedUnit} />
      </div>
    </div>
  );
}
