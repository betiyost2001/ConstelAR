import React, { useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faBell } from "@fortawesome/free-solid-svg-icons";

export default function FloatingNotificationButton({ onOpenModal }) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      className={`
        fixed bottom-8 left-8 z-50 
        px-6 py-4 rounded-full 
        flex items-center gap-3
        text-white font-medium
        transition-all duration-300 ease-in-out
        transform hover:scale-105
        shadow-lg hover:shadow-xl
        ${
          isHovered
            ? "bg-[#EAFE07] text-black"
            : "bg-blue-600 hover:bg-blue-700"
        }
      `}
      style={{
        background: isHovered
          ? "linear-gradient(135deg, #EAFE07 0%, #D4E600 100%)"
          : "linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)",
        boxShadow: isHovered
          ? "0 10px 25px rgba(234, 254, 7, 0.3)"
          : "0 4px 15px rgba(59, 130, 246, 0.3)",
      }}
    >
      <button
        onClick={onOpenModal}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <FontAwesomeIcon
          icon={faBell}
          className={`transition-transform duration-300 ${
            isHovered ? "scale-110 text-black" : "scale-100 "
          } `}
        />
        <span className="text-lg font-semibold hover:text-black">
          Quiero recibir notificaciones
        </span>
      </button>
    </div>
  );
}
