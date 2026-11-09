// Use the frontend origin so the dev proxy can reach the backend and the
// session cookie remains first-party, including when the frontend is tunneled.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";
