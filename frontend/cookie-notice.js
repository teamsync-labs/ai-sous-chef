(function () {
  var KEY = "ai-sous-chef_cookie_consent_v1";
  var SUBJECT_KEY = "ai-sous-chef_subject_id_v1";
  var ACCEPTED = "accepted";
  var NECESSARY = "necessary";
  var TAG_SRC = "https://mc.yandex.ru/metrika/tag.js";
  var TAG_SCRIPT_ID = "yandex-metrika-tag";
  var CONSENT_API = "/app/api/consent";
  var API_KEY_SITE = "local-site-key";
  var METRIKA_ID = 111661284;

  var script = document.currentScript;
  if (!script) {
    var scripts = document.getElementsByTagName("script");
    script = scripts[scripts.length - 1];
  }
  var policyHref = (script && script.getAttribute("data-policy-href")) || "";
  var overlayOn = !(script && script.getAttribute("data-overlay") === "0");

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

  function subjectId() {
    try {
      var existing = window.localStorage.getItem(SUBJECT_KEY);
      if (existing) return existing;
      var created =
        window.crypto && crypto.randomUUID
          ? crypto.randomUUID()
          : String(Date.now()) + "-" + Math.random().toString(16).slice(2);
      window.localStorage.setItem(SUBJECT_KEY, created);
      return created;
    } catch (e) {
      return "anon-" + String(Date.now());
    }
  }

  function recordAnalytics(choice) {
    return fetch(CONSENT_API, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Api-Key": API_KEY_SITE,
      },
      body: JSON.stringify({
        subject_id: subjectId(),
        channel: "site",
        consent_type: "analytics",
        action: choice === ACCEPTED ? "granted" : "withdrawn",
      }),
    }).then(function (res) {
      if (!res.ok) throw new Error("consent_" + res.status);
    });
  }

  function loadMetrika() {
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

    window.ym(METRIKA_ID, "init", {
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
    "На сайте используются cookie. Можно оставить только служебные или включить аналитику — Яндекс.Метрику. " +
    'Подробнее — в <a href="' +
    policyHref +
    '" target="_blank" rel="noopener">политике конфиденциальности</a>.' +
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

  function setBusy(busy) {
    var buttons = root.querySelectorAll("[data-cookie-choice]");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].disabled = busy;
    }
  }

  root.addEventListener("click", function (event) {
    var btn = event.target.closest("[data-cookie-choice]");
    if (!btn || btn.disabled) return;
    var choice = btn.getAttribute("data-cookie-choice");
    if (choice !== ACCEPTED && choice !== NECESSARY) return;

    setBusy(true);
    recordAnalytics(choice)
      .then(function () {
        writeChoice(choice);
        if (choice === ACCEPTED) loadMetrika();
        dismiss(root);
      })
      .catch(function (err) {
        setBusy(false);
        console.warn("cookie consent journal", err);
      });
  });
})();
