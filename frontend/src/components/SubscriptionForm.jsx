import React, { useState, useEffect, useRef } from "react";
import {
  fetchUSRegions,
  fetchStatesInRegion,
  searchCitiesInState,
} from "../lib/citiesApi";

export default function SubscriptionForm() {
  const [formData, setFormData] = useState({
    email: "",
    phone: "",
    region: "",
    state: "",
    city: "",
  });

  const [errors, setErrors] = useState({});
  const [regions, setRegions] = useState([]);
  const [states, setStates] = useState([]);
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [cityApiError, setCityApiError] = useState("");
  const cityCacheRef = useRef(new Map());
  const searchDebounceRef = useRef(null);

  // Load regions on mount
  useEffect(() => {
    const loadRegions = async () => {
      setLoading(true);
      const data = await fetchUSRegions();
      setRegions(data);
      setLoading(false);
    };
    loadRegions();
  }, []);

  // Load states when region changes
  useEffect(() => {
    if (formData.region) {
      const loadStates = async () => {
        setLoading(true);
        const data = await fetchStatesInRegion(formData.region);
        setStates(data);
        setFormData((prev) => ({ ...prev, state: "", city: "" }));
        setCities([]);
        setLoading(false);
      };
      loadStates();
    } else {
      setStates([]);
      setCities([]);
    }
  }, [formData.region]);

  // Reset city list when state changes; do not prefetch to avoid rate limits
  useEffect(() => {
    setCities([]);
    setFormData((prev) => ({ ...prev, city: "" }));
    setCityApiError("");
  }, [formData.state]);

  // Debounced city search within selected state
  useEffect(() => {
    if (!formData.state) {
      setCities([]);
      setCityApiError("");
      return;
    }
    const q = (formData.city || "").trim();
    if (q.length < 2) {
      setCities([]);
      setCityApiError("");
      return;
    }

    // Debounce
    if (searchDebounceRef.current) {
      clearTimeout(searchDebounceRef.current);
    }
    searchDebounceRef.current = setTimeout(async () => {
      try {
        const cacheKey = `${formData.state}:${q.toLowerCase()}`;
        const cache = cityCacheRef.current.get(cacheKey);
        if (cache) {
          setCities(cache);
          setCityApiError("");
          return;
        }
        setLoading(true);
        const results = await searchCitiesInState(formData.state, q, 10);
        const list = Array.isArray(results) ? results : [];
        setCities(list);
        cityCacheRef.current.set(cacheKey, list);
        if (list.length === 0) {
          setCityApiError(
            `No se encontraron ciudades que coincidan con "${q}" en el estado seleccionado.`
          );
        } else {
          setCityApiError("");
        }
      } catch (err) {
        console.error("City search error:", err);
        setCityApiError(
          "Error al cargar ciudades (posible límite de API). Intenta nuevamente."
        );
      } finally {
        setLoading(false);
      }
    }, 350);

    return () => {
      if (searchDebounceRef.current) {
        clearTimeout(searchDebounceRef.current);
      }
    };
  }, [formData.state, formData.city]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error on change
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validatePhone = (phone) => {
    const phoneRegex = /^\d{10,}$/;
    return phoneRegex.test(phone.replace(/\D/g, ""));
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.email || !validateEmail(formData.email)) {
      newErrors.email = "Correo electrónico inválido";
    }
    if (!formData.phone || !validatePhone(formData.phone)) {
      newErrors.phone = "Número de teléfono inválido (mínimo 10 dígitos)";
    }
    if (!formData.region) {
      newErrors.region = "Selecciona una región";
    }
    if (!formData.state) {
      newErrors.state = "Selecciona un estado";
    }
    if (!formData.city) {
      newErrors.city = "Selecciona una ciudad";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateForm()) {
      console.log("Form data:", formData);
      setSuccessMessage("¡Petición enviada! Revisa tu correo para confirmar.");
      // Reset form
      setFormData({
        email: "",
        phone: "",
        region: "",
        state: "",
        city: "",
      });
      setErrors({});
    }
  };

  // NOTE: No card/container background here. The parent wrapper (SubscriptionLegend)
  // provides the translucent dark background, border, and rounded corners.

  return (
    <div className="w-full bg-[#10182bad] rounded-3xl p-8 md:p-12">
      <div className="text-center text-3xl">
        <h2 className="overpass-bold">¿Quieres recibir avisos?</h2>
      </div>
      <div className="text-center mb-8 md:mb-12 text-xl text-gray-400">
        <h3 className="overpass-medium">
          Te enviaremos un correo para confirmar tu suscripción.
        </h3>
        <p>
          Y serás notificado cuando haya nuevas alertas de contaminación en tu
          ciudad.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-x-12"
      >
        {/* Email */}
        <div className="text-black">
          <label htmlFor="email" className="block text-white md:text-lg mb-3">
            Correo Electrónico
          </label>
          <div className="w-full px-4 py-3 bg-white border-0 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="Correo Electrónico"
              required
            />
          </div>

          {errors.email && (
            <p className="text-red-500 text-sm mt-1">{errors.email}</p>
          )}
        </div>

        {/* Region */}
        <div className="text-black">
          <label htmlFor="region" className="block text-white  md:text-lg mb-3">
            Región
          </label>
          <div className="w-full px-4 py-3 bg-white text-[#07173F] border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
            <select
              id="region"
              name="region"
              value={formData.region}
              onChange={handleInputChange}
              required
            >
              <option value="">Selecciona una región</option>
              {regions.map((region, idx) => (
                <option
                  key={region.code || region.wikiDataId || region.name || idx}
                  value={region.code}
                >
                  {region.name}
                </option>
              ))}
            </select>
          </div>

          {errors.region && (
            <p className="text-red-500 text-sm mt-1">{errors.region}</p>
          )}
        </div>

        {/* Phone */}
        <div className="text-black">
          <label htmlFor="phone" className="block text-white  md:text-lg mb-3">
            Teléfono
          </label>
          <div className="w-full px-4 py-3 bg-white text-[#07173F] border-0 rounded-xl placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500">
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              placeholder="Teléfono"
              required
            />
          </div>

          {errors.phone && (
            <p className="text-red-500 text-sm mt-1">{errors.phone}</p>
          )}
        </div>

        {/* State */}
        <div className="text-black">
          <label htmlFor="state" className="block text-white  md:text-lg mb-3">
            Estado
          </label>
          <div className="w-full px-4 py-3 bg-white text-[#07173F] border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50">
            <select
              id="state"
              name="state"
              value={formData.state}
              onChange={handleInputChange}
              disabled={!formData.region || loading}
              required
            >
              <option value="">Selecciona un estado</option>
              {states.map((state, idx) => (
                <option
                  key={state.code || state.wikiDataId || state.name || idx}
                  value={state.code}
                >
                  {state.name}
                </option>
              ))}
            </select>
          </div>
          {errors.state && (
            <p className="text-red-500 text-sm mt-1">{errors.state}</p>
          )}
        </div>

        {/* Submit Button (left column) */}
        <div className="md:col-start-1">
          <div className="w-full px-6 py-4  rounded-xl text-center bg-[#EAFE07] hover:bg-[#D4E600] cursor-pointer text-black transition-colors duration-200 text-3xl">
            <button type="submit">Recibir</button>
          </div>

          {successMessage && (
            <p className="text-green-500 text-center mt-3">{successMessage}</p>
          )}
        </div>

        {/* City (right column under State) */}
        <div className="text-black">
          <label htmlFor="city" className="block text-white  md:text-lg mb-3">
            Ciudad
          </label>
          <div className="w-full px-6 py-3 bg-white text-[#07173F] border-0 rounded-xl placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50">
            <input
              type="text"
              id="city"
              name="city"
              value={formData.city}
              onChange={handleInputChange}
              list="cities-list"
              placeholder="Selecciona una ciudad"
              disabled={!formData.state || loading}
              required
            />
          </div>
          <datalist id="cities-list">
            {cities.map((city, idx) => (
              <option
                key={`${
                  city.id || city.wikiDataId || city.placeId || city.name || idx
                }-${idx}`}
                value={`${city.name || city.city}, ${
                  city.regionCode || city.regionCodeShort || ""
                }`}
              />
            ))}
          </datalist>
          {cityApiError && (
            <p className="text-red-400 text-sm mt-1" aria-live="polite">
              {cityApiError}
            </p>
          )}
          {errors.city && (
            <p className="text-red-500 text-sm mt-1">{errors.city}</p>
          )}
        </div>
      </form>
    </div>
  );
}
