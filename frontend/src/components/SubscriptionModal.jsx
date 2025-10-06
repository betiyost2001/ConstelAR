import React, { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faXmark } from "@fortawesome/free-solid-svg-icons";
import SubscriptionForm from "./SubscriptionForm";

/**
 * Accesible modal rendered into a portal on document.body.
 * - Fullscreen fixed overlay (rgba(0,0,0,.5)) that captures clicks.
 * - Body scroll is locked while open.
 * - Rest of the app is aria-hidden + inert, and pointer-events are disabled via CSS.
 * - Focus is moved inside the dialog and restored to the opener on close.
 * - Focus is trapped within the dialog while open.
 */
export default function SubscriptionModal({ isOpen, onClose }) {
  const dialogRef = useRef(null);
  const initialFocusRef = useRef(null);
  const lastActiveRef = useRef(null);

  const appRoot =
    typeof document !== "undefined" ? document.getElementById("root") : null;

  const handleClose = () => {
    onClose?.();
    // Restaura foco al elemento que abrió el modal
    setTimeout(() => {
      const el = lastActiveRef.current;
      if (el && typeof el.focus === "function") {
        el.focus();
      }
    }, 0);
  };

  // Efectos al abrir/cerrar: bloquear scroll, aria-hidden/inert, foco inicial y trap
  useEffect(() => {
    if (!isOpen) return;

    // Guarda el elemento activo para restaurar el foco al cerrar
    lastActiveRef.current = document.activeElement;

    // Bloquea scroll y marca el cuerpo como 'modal-open' (también se usa para ocultar la leyenda por CSS)
    document.body.classList.add("modal-open");

    // Oculta semánticamente el resto de la app
    if (appRoot) {
      appRoot.setAttribute("aria-hidden", "true");
      appRoot.setAttribute("inert", "");
    }

    // Foco inicial dentro del modal
    const focusTimer = setTimeout(() => {
      if (initialFocusRef.current) {
        initialFocusRef.current.focus?.();
      } else if (dialogRef.current) {
        dialogRef.current.focus?.();
      }
    }, 0);

    // Trap de foco con Tab/Shift+Tab
    const focusableSelectors = [
      "a[href]",
      "button:not([disabled])",
      "textarea:not([disabled])",
      "input:not([disabled])",
      "select:not([disabled])",
      '[tabindex]:not([tabindex="-1"])',
    ].join(",");

    const onKeyDown = (e) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        handleClose();
        return;
      }
      if (e.key !== "Tab") return;
      const root = dialogRef.current;
      if (!root) return;

      const focusables = Array.from(
        root.querySelectorAll(focusableSelectors)
      ).filter((el) => el.offsetParent !== null || el === root);

      if (focusables.length === 0) {
        e.preventDefault();
        root.focus();
        return;
      }

      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const current = document.activeElement;

      if (!e.shiftKey && current === last) {
        e.preventDefault();
        first.focus();
      } else if (e.shiftKey && (current === first || current === root)) {
        e.preventDefault();
        last.focus();
      }
    };

    document.addEventListener("keydown", onKeyDown, true);

    return () => {
      clearTimeout(focusTimer);
      document.removeEventListener("keydown", onKeyDown, true);
    };
  }, [isOpen]);

  // Limpieza visual/semántica al cerrar o desmontar
  useEffect(() => {
    if (!isOpen) {
      document.body.classList.remove("modal-open");
      if (appRoot) {
        appRoot.removeAttribute("aria-hidden");
        appRoot.removeAttribute("inert");
      }
    }
    return () => {
      document.body.classList.remove("modal-open");
      if (appRoot) {
        appRoot.removeAttribute("aria-hidden");
        appRoot.removeAttribute("inert");
      }
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const modalNode = (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center">
      {/* Overlay: semitransparente, ocupa toda la pantalla y captura clics */}
      <div
        className="modal-overlay bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Contenedor del diálogo. pointer-events bloqueado en overlay, activo aquí */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Subscription dialog"
        className="outline-none modal-container"
        tabIndex={-1}
      >
        {/* Contenido del modal por encima del overlay */}
        <div className="modal-content relative w-full max-w-4xl mx-4 max-h-[90vh] overflow-y-auto animate-[slideInUp_0.4s_ease-out]">
          {/* Botón de cerrar */}
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 z-[1002] bg-white/20 hover:bg-white/30 rounded-full p-2 text-white transition-all duration-200 hover:scale-110 focus:outline-none focus:ring-2 focus:ring-white/60"
            aria-label="Cerrar"
          >
            <FontAwesomeIcon icon={faXmark} className="text-xl" />
          </button>

          {/* Contenido */}
          <div className="bg-transparent">
            {/* Foco inicial en el primer campo del formulario */}
            <SubscriptionForm ref={initialFocusRef} />
          </div>
        </div>
      </div>

      {/* Animaciones (mantener compatibles con el diseño actual) */}
      <style>{`
        @keyframes slideInUp {
          from { opacity: 0; transform: translateY(30px) scale(0.95); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>
    </div>
  );

  // Portal: evita problemas de stacking context/z-index y asegura overlay por encima de todo
  return createPortal(modalNode, document.body);
}
