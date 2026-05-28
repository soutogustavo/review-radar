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
  // --- 1. Find and click the sort button ---
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

  // --- 2. Wait for menu to open and click "Newest" ---
  const waitForMenu = (attempts = 0) => {
    const menuItems = [...document.querySelectorAll('div[role="menuitemradio"]')];
    const recentItem = menuItems.find(el =>
      el.textContent.trim().match(/Newest|Most recent/i)
    );

    if (recentItem) {
      const firstReviewBefore = document.querySelector('.jftiEf')?.innerText?.trim() || "";
      recentItem.click();
      console.log('sort_state: {"status": "clicked_newest"}');

      // --- 3. Wait for the reviews to reload ---
      const waitForReload = (attempts = 0) => {
        const firstReviewNow = document.querySelector('.jftiEf')?.innerText?.trim() || "";
        const reloaded = firstReviewNow !== firstReviewBefore && firstReviewNow.length > 0;

        if (reloaded || attempts >= 40) {
          console.log(`sort_state: {"status": "reloaded", "confirmed": ${reloaded}, "attempts": ${attempts}}`);

          // --- 4. Initial scroll to "wake up" the panel ---
          const findPanel = () => {
            // Known selectors for the Google Maps reviews container
            const candidates = [
              document.querySelector('.m6QErb.DxyBCb.kA9KIf'),
              document.querySelector('.m6QErb.DxyBCb'),
              document.querySelector('.m6QErb[aria-label]'),
              document.querySelector('div[role="main"] .m6QErb'),
              // fallback: any scrollable div inside the main panel
              ...[...document.querySelectorAll('div[role="main"] div')].filter(el => {
                const s = getComputedStyle(el);
                return ["auto", "scroll"].includes(s.overflowY) &&
                      el.scrollHeight > el.clientHeight + 200;
              })
            ];

            return candidates.find(el => el != null) || null;
          };

          const triggerInitialScroll = (attempts = 0) => {
            const panel = findPanel();

            if (panel) {
              // Gentle and progressive scroll to force rendering
              panel.scrollTop = 0;
              setTimeout(() => { panel.scrollBy(0, 300); }, 200);
              setTimeout(() => { panel.scrollBy(0, 300); }, 500);
              setTimeout(() => { panel.scrollBy(0, 300); }, 800);
              setTimeout(() => { panel.scrollBy(0, 300); }, 1100);

              console.log('sort_state: {"status": "initial_scroll_done"}');
              setTimeout(() => {
                document.body.setAttribute("data-sort-ready", "1");
              }, 2000);  // Wait for rendering after initial scroll

            } else if (attempts < 15) {
              // Panel not yet available - try again
              console.log(`sort_state: {"status": "waiting_panel", "attempts": ${attempts}}`);
              setTimeout(() => triggerInitialScroll(attempts + 1), 300);
            } else {
              console.log('sort_state: {"status": "panel_not_found"}');
              document.body.setAttribute("data-sort-ready", "1");
            }
          };

          triggerInitialScroll();

        } else {
          setTimeout(() => waitForReload(attempts + 1), 200);
        }
      };

      waitForReload();

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

  // Wait for new reviews to render before signaling ready
  const waitForNewReviews = (attempts = 0) => {
    const loadedNow = reviewCards().length;
    const newLoaded = loadedNow > loadedBefore;
    const atBottom  = panel.scrollTop + panel.clientHeight >= panel.scrollHeight - 50;
    const maxWait   = 15; // ~3 seconds

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
      setTimeout(() => waitForNewReviews(attempts + 1), 200); // Check every 200ms
    }
  };

  waitForNewReviews();
})();
"""
