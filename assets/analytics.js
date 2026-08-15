/* ArgentinaCS — medición de visitas (Google Analytics 4)
   ---------------------------------------------------------------
   Para activarlo: pegá abajo el ID de medición de Google Analytics
   (lo ves en Analytics → Administrar → Flujos de datos, con formato
   G-XXXXXXXXXX). Mientras diga G-XXXXXXXXXX no se carga nada.
   --------------------------------------------------------------- */

(function () {
  "use strict";

  var ID = "G-XXXXXXXXXX";

  // Sin ID configurado, el sitio funciona igual y no se mide nada.
  if (!/^G-[A-Z0-9]{6,}$/.test(ID)) return;

  var host = location.hostname;

  // En la computadora de quien edita el sitio no se mide.
  if (host === "localhost" || host === "127.0.0.1" || host === "") return;

  // Solo los dominios oficiales cuentan como visitas reales; los entornos
  // de prueba (GitHub Pages y el de despliegue) se marcan como tráfico
  // interno para que Analytics pueda excluirlos de los informes.
  var esSitioOficial = /(^|\.)argentinacs\.com(\.ar)?$/.test(host);

  var s = document.createElement("script");
  s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + ID;
  document.head.appendChild(s);

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = gtag;

  gtag("js", new Date());

  var config = { send_page_view: false };
  if (!esSitioOficial) config.traffic_type = "internal";
  gtag("config", ID, config);

  // La vista se envía cuando la página terminó de armarse, así el detalle
  // de cada servidor (servidor.html) queda registrado con su nombre real.
  function enviarVista() {
    gtag("event", "page_view", {
      page_title: document.title,
      page_location: location.href
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", enviarVista);
  } else {
    enviarVista();
  }
})();
