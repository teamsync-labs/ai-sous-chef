(function () {
  var KEY = "ai-sous-chef_cookie_consent_v1";
  var ACCEPTED = "accepted";
  var NECESSARY = "necessary";
  var TAG_SRC = "https://mc.yandex.ru/metrika/tag.js";
  var TAG_SCRIPT_ID = "yandex-metrika-tag";
  /** Счётчик Яндекс.Метрики для ai-sous-chef.ru. Пусто — «Принять» запоминается, скрипт не грузится. */
  var DEFAULT_METRIKA_ID = "111661284";

  var script = document.currentScript;
  if (!script) {
    var scripts = document.getElementsByTagName("script");
    script = scripts[scripts.length - 1];
  }
  var policyHref = (script && script.getAttribute("data-policy-href")) || "legal/policy.html";
  var overlayOn = !(script && script.getAttribute("data-overlay") === "0");
  var metrikaId = (script && script.getAttribute("data-metrika-id")) || DEFAULT_METRIKA_ID;

  function readChoice() {
    try {
      var value = window.localStorage.getItem(KEY);
      if (value === ACCEPTED || value === NECESSARY) return value;
    } catch (e) {
      /* private mode */
    }
    return null;
  }

  function writeChoice(choice) {
    try {
      window.localStorage.setItem(KEY, choice);
    } catch (e) {
      /* ignore */
    }
  }

  function loadMetrika() {
    var id = Number(metrikaId);
    if (!isFinite(id) || id <= 0) return;

    if (!window.ym) {
      var stub = function () {
        stub.a = stub.a || [];
        stub.a.push(arguments);
      };
      window.ym = stub;
    }
    window.ym.l = window.ym.l || Date.now();

    var alreadyLoaded = false;
    var list = document.scripts;
    for (var i = 0; i < list.length; i++) {
      if (list[i].src === TAG_SRC || list[i].id === TAG_SCRIPT_ID) {
        alreadyLoaded = true;
        break;
      }
    }
    if (!alreadyLoaded) {
      var el = document.createElement("script");
      el.id = TAG_SCRIPT_ID;
      el.async = true;
      el.src = TAG_SRC;
      document.head.appendChild(el);
    }

    window.ym(id, "init", {
      clickmap: true,
      trackLinks: true,
      accurateTrackBounce: true,
    });
  }

  function dismiss(root) {
    document.body.classList.remove("cookie-notice-lock");
    if (root && root.parentNode) root.remove();
  }

  var stored = readChoice();
  if (stored === ACCEPTED) {
    loadMetrika();
    return;
  }
  if (stored === NECESSARY) return;

  var root = document.createElement("div");
  root.className = "cookie-notice" + (overlayOn ? " cookie-notice--overlay" : "");
  root.setAttribute("data-cookie-notice", "");
  root.innerHTML =
    (overlayOn ? '<div class="cookie-notice-backdrop" aria-hidden="true"></div>' : "") +
    '<div class="cookie-notice-bar" role="dialog" aria-modal="' +
    (overlayOn ? "true" : "false") +
    '" aria-labelledby="cookie-notice-title">' +
    '<p id="cookie-notice-title" class="cookie-notice-text">' +
    "Сайт сохраняет служебные cookie, чтобы страницы открывались. " +
    "Чтобы понять, как им пользуются, можем включить Яндекс.Метрику — только если согласитесь. " +
    'Подробнее — в <a href="' +
    policyHref +
    '">политике конфиденциальности</a>.' +
    "</p>" +
    '<div class="cookie-notice-actions">' +
    '<button type="button" class="cookie-notice-btn cookie-notice-btn--ghost" data-cookie-choice="' +
    NECESSARY +
    '">Только служебные</button>' +
    '<button type="button" class="cookie-notice-btn" data-cookie-choice="' +
    ACCEPTED +
    '">Принять</button>' +
    "</div>" +
    "</div>";

  function mount() {
    document.body.appendChild(root);
    if (overlayOn) document.body.classList.add("cookie-notice-lock");
  }

  if (document.body) mount();
  else document.addEventListener("DOMContentLoaded", mount);

  root.addEventListener("click", function (event) {
    var btn = event.target.closest("[data-cookie-choice]");
    if (!btn) return;
    var choice = btn.getAttribute("data-cookie-choice");
    if (choice !== ACCEPTED && choice !== NECESSARY) return;
    writeChoice(choice);
    if (choice === ACCEPTED) loadMetrika();
    dismiss(root);
  });
})();
