import React from "react";
import { legendFor } from "../constants/aqi";
import { DEFAULT_POLLUTANT } from "../constants/pollutants";
import FilterBar from "./FilterBar";

export default function Legend({
  pollutant: selectedPollutant,
  position = "bottom-right",
  onChange,
}) {
  const effectivePollutant = selectedPollutant ?? DEFAULT_POLLUTANT;
  const items = legendFor(effectivePollutant);
  const posClasses = {
    "bottom-right": "bottom-4 right-4",
    "bottom-left": "bottom-4 left-4",
    "top-right": "top-4 right-4",
    "top-left": "top-4 left-4",
  }[position];

  const originClasses = {
    "bottom-right": "origin-bottom-right",
    "bottom-left": "origin-bottom-left",
    "top-right": "origin-top-right",
    "top-left": "origin-top-left",
  }[position];

  return (
    <div className={`legend-root absolute ${posClasses} z-50`}>
      <div
        className={`p-4 bg-[rgba(7,23,63,0.85)] border border-[rgba(255,255,255,0.10)] rounded-xl min-w-60 transform-gpu transition-transform duration-200 ease-out hover:scale-[1.50] ${originClasses}`}
      >
        <FilterBar pollutant={selectedPollutant} onChange={onChange} />
        <div className="space-y-2">
          {items.map((it, i) => (
            <div key={i} className="flex items-center gap-3">
              <div
                className="w-4.5 h-4.5 rounded-sm border border-[rgba(255,255,255,0.25)]"
                style={{ background: it.color }}
              />
              <div className="text-sm text-white opacity-95 fira-sans-regular">
                {it.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
