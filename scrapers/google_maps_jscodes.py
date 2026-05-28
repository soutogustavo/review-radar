"""JavaScript codes to support in the scrapping process"""

JS_ACCEPT_COOKIES = """
    (() => {
    function clickAcceptAll() {
        // Try in the top document
        const btn =
        document.querySelector('button[aria-label="Accept all"]') ||
        document.querySelector('button[jsname="b3VHJd"]'); // fallback by jsname

        if (btn) {
        btn.click();
        return true;
        }

        // If consent is inside an iframe (common for Google)
        const iframes = document.querySelectorAll('iframe');
        for (const frame of iframes) {
        try {
            const doc = frame.contentDocument || frame.contentWindow?.document;
            if (!doc) continue;

            const iframeBtn =
            doc.querySelector('button[aria-label="Accept all"]') ||
            doc.querySelector('button[jsname="b3VHJd"]');

            if (iframeBtn) {
            iframeBtn.click();
            return true;
            }
        } catch (e) {
            // cross-origin iframe – ignore
        }
        }

        return false;
    }

    // Try immediately and a few times after (in case of late load)
    const maxTries = 10;
    let tries = 0;

    const intervalId = setInterval(() => {
        if (clickAcceptAll() || ++tries >= maxTries) {
        clearInterval(intervalId);
        }
    }, 500);
    })();
"""

JS_SORT_BY_RECENT = """
(() => {
  const sortButton =
    [...document.querySelectorAll('button')].find(b =>
      b.textContent.trim().match(/Most relevant|Mais relevantes|Sort|Ordenar/i)
    ) ||
    document.querySelector('button[aria-label*="Sort"]') ||
    document.querySelector('button[aria-label*="sort"]');

  if (!sortButton) {
    console.log('sort_state: {"status": "button_not_found"}');
    document.body.setAttribute("data-sort-ready", "1");
    return;
  }

  sortButton.click();

  const waitForMenu = (attempts = 0) => {
    // seletor correto: DIV com role="menuitemradio"
    const menuItems = [...document.querySelectorAll('div[role="menuitemradio"]')];

    const recentItem = menuItems.find(el =>
      el.textContent.trim().match(/Newest|Most recent/i)
    );

    if (recentItem) {
      recentItem.click();
      console.log('sort_state: {"status": "sorted"}');
      setTimeout(() => {
        document.body.setAttribute("data-sort-ready", "1");
      }, 3000);
    } else if (attempts < 20) {
      setTimeout(() => waitForMenu(attempts + 1), 200);
    } else {
      console.log('sort_state: {"status": "menu_item_not_found"}');
      document.body.setAttribute("data-sort-ready", "1");
    }
  };

  waitForMenu();
})();
"""


JS_SCROLL_LOAD = """
(() => {
  function reviewCards() {
    return [...document.querySelectorAll('[data-review-id], .jftiEf, div[role="article"]')]
      .filter(el => (el.innerText || "").trim().length > 0);
  }

  function isScrollable(el) {
    if (!el) return false;
    const s = getComputedStyle(el);
    return ["auto", "scroll"].includes(s.overflowY) &&
           el.scrollHeight > el.clientHeight + 100;
  }

  function findPanel() {
    const cards = reviewCards();
    for (const card of cards.slice(0, 5)) {
      let p = card.parentElement;
      while (p && p !== document.body) {
        if (isScrollable(p)) return p;
        p = p.parentElement;
      }
    }
    return null;
  }

  function parseTotalReviews() {
    const texts = [...document.querySelectorAll("button, div, span, h1, h2, h3, h4")]
      .map(el => (el.innerText || "").trim())
      .filter(Boolean);
    for (const t of texts) {
      const m = t.match(/([\\d.,]+)\\s+reviews?/i);
      if (m) {
        const n = parseInt(m[1].replace(/[.,]/g, ""), 10);
        if (!Number.isNaN(n)) return n;
      }
    }
    return null;
  }

  const panel = findPanel();
  const loadedBefore = reviewCards().length;
  const total = parseTotalReviews();

  if (!panel) {
    window.__gm_state = { status: "no-panel", loaded: loadedBefore, total };
    document.body.setAttribute("data-crawl-ready", "1");
    return;
  }

  // Scrolla
  panel.click();
  panel.focus();
  for (let i = 0; i < 6; i++) {
    panel.scrollBy(0, 700);
  }

  // Aguarda novos reviews renderizarem antes de sinalizar ready
  const waitForNewReviews = (attempts = 0) => {
    const loadedNow = reviewCards().length;
    const newLoaded = loadedNow > loadedBefore;
    const atBottom  = panel.scrollTop + panel.clientHeight >= panel.scrollHeight - 50;
    const maxWait   = 15; // ~3 segundos

    if (newLoaded || atBottom || attempts >= maxWait) {
      window.__gm_state = {
        status:        "ok",
        loaded_before: loadedBefore,
        loaded_after:  loadedNow,
        new_reviews:   loadedNow - loadedBefore,
        at_bottom:     atBottom,
        total,
      };
      console.log("gm_state", JSON.stringify(window.__gm_state));
      document.body.setAttribute("data-crawl-ready", "1");
    } else {
      setTimeout(() => waitForNewReviews(attempts + 1), 200); // checa a cada 200ms
    }
  };

  waitForNewReviews();
})();
"""
