/* ArgentinaCS — utilidades del sitio */

(function () {
  "use strict";

  /* Toast de confirmación */
  var toastEl = null;
  var toastTimer = null;

  function toast(msg) {
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.className = "toast";
      toastEl.setAttribute("role", "status");
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      toastEl.classList.remove("show");
    }, 2600);
  }

  /* Copiar texto al portapapeles (con fallback para navegadores viejos) */
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).catch(function () {
        return copyTextLegacy(text);
      });
    }
    return copyTextLegacy(text);
  }

  function copyTextLegacy(text) {
    return new Promise(function (resolve, reject) {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      try {
        document.execCommand("copy") ? resolve() : reject(new Error("copy failed"));
      } catch (err) {
        reject(err);
      } finally {
        ta.remove();
      }
    });
  }

  function copyFrom(el) {
    var ip = el.getAttribute("data-copy");
    copyText(ip)
      .then(function () { toast("✅ IP copiada: " + ip); })
      .catch(function () { toast("⚠️ No se pudo copiar. IP: " + ip); });
  }

  /* Cualquier elemento con data-copy copia su IP al hacer clic */
  document.addEventListener("click", function (e) {
    var el = e.target.closest("[data-copy]");
    if (el) copyFrom(el);
  });

  /* Y también con Enter o Espacio (los <code>/<div> no son botones nativos) */
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Enter" && e.key !== " ") return;
    var el = e.target.closest("[data-copy]");
    if (!el || el.tagName === "BUTTON" || el.tagName === "A") return;
    e.preventDefault();
    copyFrom(el);
  });

  /* Los elementos con data-copy que no son botones se vuelven
     enfocables y anunciables para teclado y lectores de pantalla */
  function initCopyTargets() {
    var els = document.querySelectorAll("[data-copy]");
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      if (el.tagName === "BUTTON" || el.tagName === "A") continue;
      el.setAttribute("role", "button");
      el.setAttribute("tabindex", "0");
      if (!el.hasAttribute("aria-label")) {
        el.setAttribute("aria-label", "Copiar IP " + el.getAttribute("data-copy"));
      }
    }
  }

  /* Clic en cualquier parte libre de la tarjeta abre la página de detalle
     del servidor (servidor.html, dentro del sitio) */
  document.addEventListener("click", function (e) {
    var card = e.target.closest(".server-card");
    if (!card) return;
    if (e.target.closest("a, button, [data-copy]")) return;
    var link = card.querySelector(".gt-link");
    if (link) location.href = link.getAttribute("href");
  });

  /* Jugadores online de Minecraft (api.mcsrvstat.us).
     Una sola consulta al server Java: los jugadores de Bedrock entran por
     Geyser al mismo servidor, así que el conteo y la lista cubren a todos. */
  function refreshMcStatus() {
    var countEl = document.getElementById("mc-players");
    var listEl = document.getElementById("mc-online-list");
    if (!countEl) return;
    fetch("https://api.mcsrvstat.us/2/45.235.98.41:25565")
      .then(function (r) { return r.json(); })
      .then(function (d) {
        countEl.classList.remove("on", "off");
        if (d && d.online && d.players) {
          countEl.textContent = "🟢 " + d.players.online + "/" + d.players.max + " jugadores online";
          countEl.classList.add("on");
          var names = [];
          if (d.players.list) {
            for (var i = 0; i < d.players.list.length; i++) {
              var item = d.players.list[i];
              names.push(typeof item === "string" ? item : item.name);
            }
          }
          if (listEl) {
            listEl.innerHTML = "";
            for (var j = 0; j < names.length; j++) {
              var li = document.createElement("li");
              li.textContent = names[j];
              listEl.appendChild(li);
            }
            listEl.hidden = names.length === 0;
          }
        } else {
          countEl.textContent = "🔴 Servidor fuera de línea";
          countEl.classList.add("off");
          if (listEl) listEl.hidden = true;
        }
      })
      .catch(function () {
        countEl.classList.remove("on", "off");
        countEl.textContent = "Jugadores: consultá en el juego";
        if (listEl) listEl.hidden = true;
      });
  }

  /* Banners de GameTracker: recargar cada 5 min para mantener el dato fresco */
  function refreshBanners() {
    var imgs = document.querySelectorAll("img.gt-banner");
    for (var i = 0; i < imgs.length; i++) {
      var base = imgs[i].src.split("?")[0];
      imgs[i].src = base + "?_=" + Date.now();
    }
  }

  function initLiveStatus() {
    if (document.getElementById("mc-players")) {
      refreshMcStatus();
      setInterval(refreshMcStatus, 120000);
    }
    if (document.querySelector("img.gt-banner")) {
      setInterval(refreshBanners, 300000);
    }
  }

  /* Video de fondo sutil. Se inyecta por JS a propósito: sin JS, o si el
     navegador bloquea la reproducción, queda la imagen estática de siempre. */
  function initVideoFondo() {
    var v = document.createElement("video");
    v.className = "bg-video";
    v.muted = true;
    v.loop = true;
    v.autoplay = true;
    v.setAttribute("muted", "");
    v.setAttribute("loop", "");
    v.setAttribute("playsinline", "");
    v.setAttribute("aria-hidden", "true");
    v.src = "assets/fondo-video.mp4";
    document.body.insertBefore(v, document.body.firstChild);

    // La imagen estática se oculta recién cuando el video arranca de verdad.
    v.addEventListener("playing", function () {
      document.body.classList.add("con-video");
    });

    function intentarReproducir() {
      var p = v.play();
      if (p && p.catch) p.catch(function () {});
    }

    intentarReproducir();

    // Si el navegador bloquea la reproducción automática, se reintenta en
    // cuanto la persona interactúa con la página (mientras tanto se ve la
    // imagen estática, así que nunca queda un fondo vacío).
    var eventos = ["pointerdown", "keydown", "touchstart", "scroll"];
    function reintento() {
      if (!v.paused) return quitarEscuchas();
      intentarReproducir();
    }
    function quitarEscuchas() {
      for (var i = 0; i < eventos.length; i++) {
        window.removeEventListener(eventos[i], reintento);
      }
    }
    for (var i = 0; i < eventos.length; i++) {
      window.addEventListener(eventos[i], reintento, { passive: true });
    }
    v.addEventListener("playing", quitarEscuchas);
  }

  function init() {
    initCopyTargets();
    initLiveStatus();
    initVideoFondo();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
