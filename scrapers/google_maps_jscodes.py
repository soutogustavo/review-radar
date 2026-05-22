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

JS_SCROLL_LOAD_OLD = """
// 1. Accept cookies (unchanged)
(() => {
  function clickAcceptAll() {
    const btn = document.querySelector('button[aria-label=\"Accept all\"]') ||
                document.querySelector('button[jsname=\"b3VHJd\"]');
    if (btn) { btn.click(); return true; }

    const iframes = document.querySelectorAll('iframe');
    for (const frame of iframes) {
      try {
        const doc = frame.contentDocument || frame.contentWindow?.document;
        if (!doc) continue;
        const iframeBtn = doc.querySelector('button[aria-label=\"Accept all\"]') ||
                          doc.querySelector('button[jsname=\"b3VHJd\"]');
        if (iframeBtn) { iframeBtn.click(); return true; }
      } catch (e) {}
    }
    return false;
  }
  clickAcceptAll();
})();

// 2. Dynamic infinite scroll - stops when no new reviews
setTimeout(() => {
  function getReviewCount() {
    return document.querySelectorAll('[data-review-id], [data-result-index], .jftiEf').length;
  }

  function scrollReviews() {
    const panel = document.querySelector('[role=\"main\"] section') ||
                  document.querySelector('.m6QErb.DxyBCb') ||
                  document.querySelector('[data-result-index]')?.closest('section') ||
                  document.querySelector('.section-result');

    if (!panel || panel.scrollHeight <= panel.clientHeight + 1) {
      return false;  // No more scrollable content
    }

    panel.scrollTop = panel.scrollHeight;
    return true;
  }

  let prevCount = 0;
  let noChangeCount = 0;
  const maxNoChange = 3;  // Stop after 3 scrolls with no new reviews
  const maxTotalScrolls = 50;  // Safety limit (~100 reviews)

  const scrollLoop = async () => {
    let scrolls = 0;
    while (scrolls < maxTotalScrolls) {
      const scrolled = scrollReviews();
      await new Promise(r => setTimeout(r, 1500));  // Wait for load

      const currentCount = getReviewCount();
      if (currentCount === prevCount) {
        noChangeCount++;
        if (noChangeCount >= maxNoChange) {
          console.log(`Stopped: No new reviews after ${scrolls} scrolls (${currentCount} total)`);
          break;
        }
      } else {
        noChangeCount = 0;  // Reset on new content
        console.log(`New reviews: ${currentCount - prevCount} (total: ${currentCount})`);
      }

      prevCount = currentCount;
      scrolls++;
    }
  };

  scrollLoop();
}, 3000);
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
  const loaded = reviewCards().length;
  const total = parseTotalReviews();

  if (!panel) {
    window.__gm_state = {
      status: "no-panel",
      loaded,
      total,
      height: null
    };
    document.body.setAttribute("data-crawl-ready", "1");
    return;
  }

  panel.click();
  panel.focus();
  panel.style.outline = "3px solid red";

  for (let i = 0; i < 6; i++) {
    panel.scrollBy(0, 700);
  }

  window.__gm_state = {
    status: "ok",
    loaded_before: loaded,
    loaded_after: reviewCards().length,
    total,
    height: panel.scrollHeight,
    top: panel.scrollTop
  };

  console.log("gm_state", JSON.stringify(window.__gm_state));
  document.body.setAttribute("data-crawl-ready", "1");
})();
"""
