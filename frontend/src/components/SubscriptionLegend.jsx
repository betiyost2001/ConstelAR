import React from "react";
import SubscriptionForm from "./SubscriptionForm";

export default function SubscriptionLegend({ position = "top-left" }) {
  const posClasses = {
    "bottom-right": "bottom-4 right-4",
    "bottom-left": "bottom-4 left-4",
    "top-right": "top-4 right-4",
    "top-left": "top-4 left-4",
  }[position];

  return (
    <div className={`absolute ${posClasses} z-50`}>
      <div
        className="p-6 w-[360px] sm:w-[460px] md:w-[640px]"
        aria-label="Formulario de suscripción a avisos"
        role="region"
      >
        <SubscriptionForm />
      </div>
    </div>
  );
}
