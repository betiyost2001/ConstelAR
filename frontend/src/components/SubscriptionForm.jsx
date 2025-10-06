import React, { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { searchCitiesInState } from "../lib/citiesApi";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faBell } from "@fortawesome/free-solid-svg-icons";

export default function SubscriptionForm() {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    email: "",
    phone: "",
    city: "",
  });

  const [errors, setErrors] = useState({});
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [cityApiError, setCityApiError] = useState("");
  const cityCacheRef = useRef(new Map());
  const searchDebounceRef = useRef(null); // Debounced city search

  useEffect(() => {
    const q = (formData.city || "").trim();
    if (q.length < 2) {
      setCities([]);
      setCityApiError("");
      return;
    } // Debounce

    if (searchDebounceRef.current) {
      clearTimeout(searchDebounceRef.current);
    }
    searchDebounceRef.current = setTimeout(async () => {
      try {
        const cacheKey = `all:${q.toLowerCase()}`;
        const cache = cityCacheRef.current.get(cacheKey);
        if (cache) {
          setCities(cache);
          setCityApiError("");
          return;
        }
        setLoading(true); // Search cities in all US states
        const results = await searchCitiesInState("US", q, 10);
        const list = Array.isArray(results) ? results : [];
        setCities(list);
        cityCacheRef.current.set(cacheKey, list);
        if (list.length === 0) {
          setCityApiError(
            `No cities matching "${q}" were found.` // No se encontraron ciudades que coincidan con "${q}".
          );
        } else {
          setCityApiError("");
        }
      } catch (err) {
        console.error("City search error:", err);
        setCityApiError(
          "Error loading cities (possible API limit). Please try again." // Error al cargar ciudades (posible límite de API). Intenta nuevamente.
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
  }, [formData.city]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value })); // Clear error on change
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
      newErrors.email = "Invalid email address"; // Correo electrónico inválido
    }
    if (!formData.phone || !validatePhone(formData.phone)) {
      newErrors.phone = "Invalid phone number (minimum 10 digits)"; // Número de teléfono inválido (mínimo 10 dígitos)
    }
    if (!formData.city) {
      newErrors.city = "Please select a city"; // Selecciona una ciudad
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateForm()) {
      console.log("Form data:", formData);
      setSuccessMessage("Request sent! Check your email to confirm."); // ¡Petición enviada! Revisa tu correo para confirmar. // Reset form
      setFormData({
        email: "",
        phone: "",
        city: "",
      });
      setErrors({});
    }
  }; // NOTE: No card/container background here. The parent wrapper (SubscriptionLegend) // provides the translucent dark background, border, and rounded corners.

  return (
    <div className="w-full bg-[#10182bad] rounded-3xl p-8 md:p-12">
           {" "}
      <div className="text-3xl text-center">
               {" "}
        <h2 className="overpass-bold">Do you want to receive alerts?</h2>{" "}
        {/* ¿Quieres recibir avisos? */}     {" "}
      </div>
           {" "}
      <div className="mb-8 text-xl text-center text-gray-400 md:mb-12">
               {" "}
        <h3 className="overpass-medium">
                    We will send you an email to confirm your subscription.{" "}
          {/* Te enviaremos un correo para confirmar tu suscripción. */}       {" "}
        </h3>
               {" "}
        <p>
                    And you will be notified when there are new pollution alerts
          in your city.{" "}
          {/* Y serás notificado cuando haya nuevas alertas de contaminación en tu ciudad. */}
                 {" "}
        </p>
             {" "}
      </div>
           {" "}
      <form
        onSubmit={handleSubmit}
        className="grid grid-cols-1 gap-8 md:grid-cols-2 md:gap-x-12"
      >
                {/* Email */}       {" "}
        <div className="text-black">
                   {" "}
          <label htmlFor="email" className="block mb-3 text-white md:text-lg">
                        Email Address {/* Correo Electrónico */}         {" "}
          </label>
                   {" "}
          <div className="w-full px-4 py-3 bg-white border-0 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                       {" "}
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="Email Address" // Correo Electrónico
              required
            />
                     {" "}
          </div>
                   {" "}
          {errors.email && (
            <p className="mt-1 text-sm text-red-500">{errors.email}</p>
          )}
                 {" "}
        </div>
                {/* Phone */}       {" "}
        <div className="text-black">
                   {" "}
          <label htmlFor="phone" className="block mb-3 text-white md:text-lg">
                        Phone {/* Teléfono */}         {" "}
          </label>
                   {" "}
          <div className="w-full px-4 py-3 bg-white text-[#07173F] border-0 rounded-xl placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500">
                       {" "}
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              placeholder="Phone" // Teléfono
              required
            />
                     {" "}
          </div>
                   {" "}
          {errors.phone && (
            <p className="mt-1 text-sm text-red-500">{errors.phone}</p>
          )}
                 {" "}
        </div>
                {/* Submit Button (left column) */}       {" "}
        <div className="md:col-start-1">
                   {" "}
          <div className="w-full px-6 py-4  rounded-xl text-center bg-[#EAFE07] hover:bg-[#D4E600] cursor-pointer text-black transition-colors duration-200 text-3xl flex items-center justify-center gap-3">
                        <FontAwesomeIcon icon={faBell} />           {" "}
            <button type="submit">Receive Alerts</button> {/* Recibir */}       
             {" "}
          </div>
                   {" "}
          {successMessage && (
            <p className="mt-3 text-center text-green-500">{successMessage}</p>
          )}
                 {" "}
        </div>
                {/* City */}       {" "}
        <div className="text-black">
                   {" "}
          <label htmlFor="city" className="block mb-3 text-white md:text-lg">
                        City {/* Ciudad */}         {" "}
          </label>
                   {" "}
          <div className="w-full px-6 py-3 bg-white text-[#07173F] border-0 rounded-xl placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50">
                       {" "}
            <input
              type="text"
              id="city"
              name="city"
              value={formData.city}
              onChange={handleInputChange}
              list="cities-list"
              placeholder="Select a city" // Selecciona una ciudad
              disabled={loading}
              required
            />
                     {" "}
          </div>
                   {" "}
          <datalist id="cities-list">
                       {" "}
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
                     {" "}
          </datalist>
                   {" "}
          {cityApiError && (
            <p className="mt-1 text-sm text-red-400" aria-live="polite">
                            {cityApiError}           {" "}
            </p>
          )}
                   {" "}
          {errors.city && (
            <p className="mt-1 text-sm text-red-500">{errors.city}</p>
          )}
                 {" "}
        </div>
             {" "}
      </form>
         {" "}
    </div>
  );
}
