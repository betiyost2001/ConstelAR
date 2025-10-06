import React from "react";
import { useTranslation } from "react-i18next";
export default function Footer() {
  const { t } = useTranslation();
  const year = new Date().getFullYear();
  return (
    <footer className="  bg-[#0B2E6B] text-[#B8C0DD]">
      <div className="flex flex-col items-center justify-between gap-2 px-4 py-4 mx-auto text-sm max-w-7xl sm:px-6 lg:px-8 sm:flex-row">
        <span>
          <b className="text-white">ConstelAR</b> – {t("footer.text")}
        </span>
        <span>
          © {year} {t("footer.copyright")}
        </span>
      </div>
    </footer>
  );
}
