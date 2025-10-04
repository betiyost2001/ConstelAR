/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        fira: ["Fira Sans", "sans-serif"],
        overpass: ["Overpass", "sans-serif"],
      },
      colors: {
        space: {
          blue: "#0042A6",
          dark: "#07173F",
          neonYel: "#D4E600",
        },
      },
      backgroundImage: {
        spaceapps: "linear-gradient(45deg, #0042a6 0%, #07173f 100%)",
      },
    },
  },
  plugins: [],
};
