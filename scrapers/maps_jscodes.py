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

JS_SCROLL_LOAD = """
(async () => {
  // 1. Click Sort button
  const sortBtn = document.querySelector('button.AeBiU-LgbsSe, button[data-idom-class*="qpzGs"]');
  if (sortBtn) {
    sortBtn.click();
    console.log('CLICKED Sort');
  }

  // 2. Wait → Click "newest" option
  await new Promise(r => setTimeout(r, 800));
  const newestOption =
    document.querySelector('[data-value="newest"]') ||
    Array.from(document.querySelectorAll('[role="menuitem"]')).find(opt =>
      opt.textContent.includes('Newest') || opt.textContent.includes('Neueste'));
  if (newestOption) {
    newestOption.click();
    console.log('Selected Newest');
  }

  await new Promise(r => setTimeout(r, 3000));

  function getReviewCount() {
    return document.querySelectorAll('.jftiEf').length;
  }

  function scrollReviews() {
    const panel =
      document.querySelector('.m6QErb.DxyBCb') ||
      document.querySelector('[role="main"] section');
    if (!panel || panel.scrollHeight <= panel.clientHeight + 1) return false;
    panel.scrollTop = panel.scrollHeight;
    return true;
  }

  let prevCount = 0;
  let noChangeCount = 0;
  const MAX_NO_CHANGE = 15;
  const MAX_SCROLLS = 1000;

  for (let i = 0; i < MAX_SCROLLS; i++) {
    scrollReviews();
    await new Promise(r => setTimeout(r, 2000));

    const current = getReviewCount();
    console.log(`Reviews no DOM: ${current}`);

    if (current === prevCount) {
      noChangeCount++;
      console.log(`No new reviews (${noChangeCount}/${MAX_NO_CHANGE})`);
      if (noChangeCount >= MAX_NO_CHANGE) {
        console.log(`Scroll finished: ${current} reviews loaded`);
        break;
      }
    } else {
      noChangeCount = 0;
    }
    prevCount = current;
  }

  document.body.setAttribute('data-crawl-ready', '1');
  console.log('data-crawl-ready = 1');
})();
"""
