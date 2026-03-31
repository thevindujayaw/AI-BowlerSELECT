(function () {
  const isLocal =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";

  const storedApiBase = window.localStorage.getItem("apiBaseUrl");
  const productionApiBase = "https://ai-bowlerselect-backend.onrender.com";

  window.API_BASE = isLocal
    ? "http://localhost:5001"
    : (storedApiBase || productionApiBase);
})();
