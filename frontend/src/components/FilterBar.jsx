import { useMemo, useState } from "react";
import {
  TEMPO_POLLUTANTS,
  getPollutantLabel,
  getPollutantUnit,
} from "../constants/pollutants";

export default function FilterBar({ pollutant, onChange }) {
  const [query, setQuery] = useState("");

  // Show search bar if the list is long
  const threshold = 8;
  const total = Array.isArray(TEMPO_POLLUTANTS) ? TEMPO_POLLUTANTS.length : 0;
  const showSearch = total >= threshold;

  // Filter pollutants based on search query
  const filtered = useMemo(() => {
    const q = (query || "").trim().toLowerCase();
    const list = Array.isArray(TEMPO_POLLUTANTS) ? TEMPO_POLLUTANTS : [];
    if (!q) return list;

    return list.filter((p) => {
      const id = String(p?.id ?? "").toLowerCase();
      const name = String(getPollutantLabel(p?.id) ?? "").toLowerCase();
      const unit = String(getPollutantUnit(p?.id) ?? "").toLowerCase();
      return id.includes(q) || name.includes(q) || unit.includes(q);
    });
  }, [query]);

  // Get the unit of the currently selected pollutant
  const selectedUnit = useMemo(
    () => String(pollutant ? getPollutantUnit(pollutant) ?? "" : ""),
    [pollutant]
  );

  const handleChange = (e) => {
    const value = e?.target?.value ?? "";
    onChange?.(value); // Sends only the ID; unit remains available below
  };

  const selectId = "pollutant-select";

  return (
    <div className="px-4 md:px-0 py-3 flex gap-4 items-center">
      <div className="w-full sm:w-80 text-black">
        <label
          htmlFor={selectId}
          className="block mb-1 text-white text-xl fira-sans-semibold"
        >
          Pollutant
        </label>

        {showSearch && (
          <div className="mb-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search pollutant..."
              className="w-full rounded-md bg-white/95 text-base px-3 py-2 outline-none ring-1 ring-white/20 focus:ring-2 focus:ring-blue-400 fira-sans-regular"
              aria-label="Search pollutant"
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
            Select a pollutant
          </option>
          {filtered.map((item) => {
            const id = String(item?.id ?? "");
            const label = String(getPollutantLabel(id) ?? id);
            const unit = String(getPollutantUnit(id) ?? "");
            return (
              <option key={id} value={id} data-unit={unit}>
                {unit ? `${label} (${unit})` : label}
              </option>
            );
          })}
        </select>

        {/* Unit available for validations/submission without visual rendering */}
        <input type="hidden" name="pollutant_unit" value={selectedUnit} />
      </div>
    </div>
  );
}
