# NDtech UX/UI Review

Date: 2026-10-02 · Branch: `arena/01a0fcf8-ndtech`

You're right that the UI is the weak point. But the problem isn't the colour palette —
I measured the core tokens and they're genuinely good. The problem is that **there is no
single design system. There are three, and they're all live.**

---

## The evidence

| Metric | Found | Healthy target |
| --- | --- | --- |
| Distinct font sizes | **49** | 6–8 |
| Inline `style=""` attributes | **207** | ~0 |
| CSS living in per-page `<style>` blocks | **~3,300 lines** | 0 |
| Shared, reusable CSS | 1,082 lines | all of it |
| `@media` rules in the whole app | **27** | 60+ |
| Text smaller than 14px | **79 instances** | few |
| Live, visually different POS screens | **2** (`/` and `/pos/`) | 1 |

### The palette itself is fine

I checked contrast against the dark page background:

```
--text    #e9efff   16.28:1   PASS AA
--muted   #9fb0d0    8.55:1   PASS AA
--primary #4f8cff    5.82:1   PASS AA
--danger  #ff4f6d    5.88:1   PASS AA
```

So don't repaint the palette. The failure is coherence and execution.

---

## Problem 1 — Two competing POS screens, two different design languages

Both are routed and reachable today:

- **`/` → `home.html`** — dark "glassmorphic". Navy `#0b1220`, blurred translucent cards,
  blue `#4f8cff` accent, FontAwesome icons, Outfit font.
- **`/pos/` → `spaza_pos.html`** — light and modern. `#f4f7fb` background, white cards,
  soft 16–20px radii, orange `#ff5a3c` accent, **Inter** font, completely different spacing.

A cashier moving between them sees two different products. And `/pos/` isn't even in the
navbar, so the light POS is effectively orphaned. On top of that,
`dreampos-style-demo.html` (641 lines) is a *third* design that nothing routes to — dead
weight.

## Problem 2 — Four pages have invisible text (actual bug)

`completed_orders.html`, `order_details.html`, `pending_orders.html` and
`completed_order_details.html` are **light-theme pages rendered inside the dark shell**.
They `{% extends 'nano/base.html' %}` but hard-code light-theme colours:

```django
<div style="padding: 20px; max-width: 1100px; margin: 0 auto; color:#111;">
```

`#111` text on the `#0b1220` page background is **1.01:1 contrast — literally unreadable**.

All four:

```
#111 heading/back-link on #0b1220  =  1.01:1   INVISIBLE
#333 back-link text on #0b1220     =  1.48:1   INVISIBLE
```

The white cards *inside* those pages render fine (18.88:1), so it looks like a rendering
glitch rather than a design choice — which is exactly why it reads as "the app is broken".

## Problem 3 — The POS screen isn't built for a POS

This is a till used hundreds of times a day, often on a tablet in a bright shop. Findings:

- **79 text instances under 14px**, some at 0.7rem (11px). Prices and totals are the most
  important pixels on the screen and they're set in the same small type as captions.
- **Only 27 media queries** — tablet and phone layouts are largely unhandled.
- Button padding is all over the place (`12px 14px` ×45, `1rem` ×24, `0.22rem 0.65rem` ×5,
  `0.35rem 0.75rem` ×6) — some targets will be well under the 44px minimum touch size.
- **Inputs are mostly below 16px**, so iOS will auto-zoom the page on every tap.
- The navbar shows **8 links to everyone** — a cashier sees *Manage Users*, *Add Stock*,
  *Price Comparisons* and *Airtime* regardless of role, and no link to `/pos/`.

---

## What I recommend

### 1. Fix the invisible text today (30 minutes, no design decisions) — ✅ DONE

Point the four order pages at the theme tokens instead of hard-coded `#111` / `#666` / `#fff`.
Highest severity, lowest cost, zero opinion required.

**Completed.** Rather than patching the hex values in place, I built the first slice of the
token/component layer (step 3) and rebuilt the four pages on it:

- **New:** `nano/static/nano/css/components.css` — design tokens (6-step type scale with a
  16px input floor, 6-step spacing scale, semantic colour roles) plus shared components:
  `.page`, `.surface`, `.stat`, `.data-table`, `.btn`/`.btn-primary`/`.btn-success`/
  `.btn-ghost`, `.field`, `.pill-badge`, `.pager`, `.empty-state`. Included from `base.html`
  after `app.css` so it wins.
- **Rebuilt on those components:** `pending_orders.html`, `completed_orders.html`,
  `order_details.html`, `completed_order_details.html`.

Result on those four pages: inline styles went from **113 → 16** (and the 16 that remain are
just token-based spacing nudges, not colours), and legacy light-theme hex
(`#111/#666/#333/#fff/#eee/#f2f2f2/#f6f6f6`) went to **zero**. Contrast is now token-driven:
`--text` on the dark surface is **14.9:1**, `--muted` is **7.8:1**, both comfortably AA.

Side benefits that came with it: tables now scroll horizontally on narrow screens instead of
overflowing, buttons are a 48px minimum touch target, and inputs are 16px so mobile browsers
stop zooming on focus. 138/138 Django tests still pass.

The remaining work below still assumes a theme decision.

### 2. Consolidate on ONE design language

This is the decision everything else depends on. My recommendation: **go light, and use the
`spaza_pos.html` direction as the base.**

Reasoning:
- A till lives in a **bright shop**. Light backgrounds with dark text hold up under glare;
  dark-on-dark glassmorphism is the worst case for that environment.
- The spaza design is genuinely the better-executed of the two — Inter instead of a webfont
  round-trip, softer and larger radii, a real accent colour, card shadows instead of blur.
- Blur (`backdrop-filter`) is expensive on the cheap Android tablets these shops actually use.

If you'd rather keep the dark shell (brand recognition, staff familiarity), that's defensible —
but then commit fully and convert `spaza_pos.html` to it. **One theme, everywhere.** The
current split is what produced this mess.

### 3. Build a token + component layer, then delete the inline styles

One `tokens.css` with a real scale:

- **Type:** 6 sizes only (e.g. 12 / 14 / 16 / 20 / 28 / 40), and nothing under 14px for
  anything a cashier must read.
- **Spacing:** 4 / 8 / 12 / 16 / 24 / 32 — kills the 20-odd padding variants.
- **Radius:** 2 values. **Shadow:** 2 values. **Colour:** keep the existing palette.
- **Components:** `.btn` (+ `--primary/--ghost/--danger`), `.card`, `.field`, `.badge`,
  `.stat`, `.table`. Then migrate the 207 inline styles and the 3,300 embedded lines into them.

Do this **incrementally, page by page** — start with the POS screen, the cart, and the airtime
dashboards (the daily-use surfaces). Don't attempt a big-bang rewrite.

### 4. Then make it work like a till

- Prices/totals to 24–40px, tabular figures so digits don't jitter.
- Touch targets minimum **48×48px**; primary actions (Charge / Complete Sale) bigger.
- Raise all input font sizes to **16px** to stop iOS zoom-on-focus.
- Add a numeric keypad for cash-received — a cashier shouldn't need a keyboard.
- Role-filter the navbar; make `/pos/` the obvious home for cashiers.
- Make the offline/queued state **visible in the shell**, not just a fallback page — this app
  explicitly queues sales offline, and right now the user can't tell if a sale synced.
- Mobile-first breakpoints at 480 / 768 / 1024.

### Suggested order

1. Invisible-text fix on the four order pages *(bug fix, do now)*
2. One theme decision, applied to the shell *(unblocks everything)*
3. Token file + button/card/field components
4. Rebuild the POS screen + cart on those components
5. The airtime dashboards
6. Mobile breakpoints and touch sizing
7. Remaining management pages

---

## Note on the 20 missing templates

Don't hand-write those 20 missing pages (see `APP_HEALTH_CHECK.md`) against the current
mess — they'd just add more inline styles and more one-off font sizes. Build the token layer
and components **first**, then the missing pages become assembly rather than invention.
The exception is anything you need working immediately.
