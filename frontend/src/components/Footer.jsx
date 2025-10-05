export default function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="mt-8 border-t border-white/10 bg-[#0B2E6B] text-[#B8C0DD]">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4 text-sm flex flex-col sm:flex-row items-center justify-between gap-2">
        <span>
          <b className="text-white">ConstelAR</b> – NASA Space Apps Challenge
        </span>
        <span>© {year} Todos los derechos reservados</span>
      </div>
    </footer>
  );
}
