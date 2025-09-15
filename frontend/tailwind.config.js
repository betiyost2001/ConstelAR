/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        "spaceapps-blue": "#0042a6",
        "spaceapps-dark": "#07173f",
      },
      backgroundImage: {
        "spaceapps-gradient":
          "linear-gradient(45deg, #0042a6 0%, #07173f 100%)",
      },
    },
  },
  plugins: [],
};
