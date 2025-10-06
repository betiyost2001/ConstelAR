import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  TEMPO_POLLUTANTS,
  getPollutantLabel,
  getPollutantUnit,
} from "../constants/pollutants";

export default function FilterBar({ pollutant, onChange }) {
  const { t } = useTranslation();
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
    <div className="flex items-center gap-4 px-4 py-3 md:px-0">
      <div className="w-full text-black sm:w-80">
        <label
          htmlFor={selectId}
          className="block mb-1 text-xl text-white fira-sans-semibold"
        >
          {t("filterBar.pollutant")}
        </label>

        {showSearch && (
          <div className="mb-2">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("filterBar.search")}
              className="w-full px-3 py-2 text-base rounded-md outline-none bg-white/95 ring-1 ring-white/20 focus:ring-2 focus:ring-blue-400 fira-sans-regular"
              aria-label={t("filterBar.search")}
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
          className="w-full px-3 py-2 text-xl bg-white rounded-md outline-none fira-sans-medium ring-1 ring-white/20 focus:ring-2 focus:ring-blue-400"
          aria-required="true"
        >
          <option value="" disabled>
            {t("filterBar.select")}
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
