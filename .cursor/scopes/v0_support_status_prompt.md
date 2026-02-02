    # v0 Prompt: Support + Status Pages (In N' Out fitness)

    **Use this prompt in v0 to generate a 2-page static site that matches the dashboards.**

    ---

    ## Copy-paste prompt (below)

    ---

    Build a static multi-page website for **"In N' Out fitness"** — a fitness and court monitoring SaaS for facilities and gyms. Create exactly **2 pages** with a shared header/nav so users can switch between **Support** and **Status**. Apply the design system below so the pages match our existing dashboards (Vercel-inspired, minimal, crafted).

    ---

    ### Design system (match dashboards — use these exact tokens)

    **Layout & spacing**
    - 4px base grid: use 8px, 12px, 16px, 20px, 24px, 28px, 32px for spacing.
    - Section padding: 20–28px inside cards; gap between cards 20–24px.
    - Symmetrical padding (same on all sides per component). No asymmetric padding unless content demands it.

    **Colors**
    - Background: `#fafafa` (page), cards: `white`.
    - Border: `#e5e5e5`, border hover: `#d4d4d4`.
    - Text primary: `#171717`, secondary: `#737373`, tertiary: `#a3a3a3`.
    - Status only when meaning: success `#16a34a`, error `#dc2626`, warning `#ea580c`, info `#2563eb`. Gray for structure; color for status/actions only.

    **Typography**
    - Font: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Roboto`.
    - Headings: 600 weight, letter-spacing `-0.02em`. H1 ~1.875rem, panel titles 1.25rem, section titles 1.125rem.
    - Body: 0.875rem (14px), weight 400–500; small 0.813rem, tiny 0.75rem. Letter-spacing body `-0.01em`.
    - Labels: 500 weight.

    **Surfaces**
    - Border radius: cards 12px, buttons 8px, badges 6px, small elements 4px.
    - Shadow: default `0 1px 3px rgba(0,0,0,0.04)`; hover `0 4px 12px rgba(0,0,0,0.05)`. Minimal; no heavy shadows or gradients.
    - Borders: `0.5px solid` or `1px solid` with the border color above. Prefer subtle borders over heavy shadows.

    **Craft (from skill)**
    - Every pixel on the 4px grid. No 1px or 3px gaps.
    - Contrast hierarchy: primary → secondary → muted → faint text.
    - No decorative color; no spring/bouncy animation. Transitions 150–250ms if any.
    - Cards: consistent surface treatment (same border, radius, shadow) even if layout inside varies.

    ---

    ### Page 1 — Support / Help

    - **Hero:** "Support" (h1) and short tagline (e.g. "We're here to help").
    - **Quick links:** Contact us, Submit a ticket, Knowledge base, FAQ — as clear actions/cards or buttons.
    - **FAQ:** Accordion with 4–5 placeholder items (e.g. "How do I report an outage?", "Who is my Registered Support Contact?", "What are your response times?").
    - **Contact card:** email, support portal link, note "24/7 web-based support for Registered Support Contacts".
    - Use cards with 12px radius, 20–28px padding, subtle border; same typography and spacing as above.

    ---

    ### Page 2 — Status

    - **Header:** "System Status" and overall status badge (e.g. "All systems operational" in success green, or "Partial outage" in warning).
    - **Component list:** Each row/card with status indicator. Components: Cloud server, Module connectivity, Guest portal, Personnel dashboard, API. Each shows status: Operational (green) / Degraded (amber) / Outage (red) and optional "Last checked" time.
    - **Past incidents:** 1–2 placeholder rows (date, title, "Resolved"). Muted text for dates.
    - **Footer line:** "Subscribe to updates" (button or link; no functionality).
    - Same card treatment, spacing, and status colors as above.

    ---

    ### Shared chrome

    - **Header:** Site name "In N' Out fitness" (left), nav links "Support" and "Status" (right). Same font and weights; active page indicated (e.g. bolder or underline).
    - **Footer:** Minimal (e.g. © In N' Out fitness, link to Support). Same border and spacing system.
    - **Overall:** Clean, minimal, professional. Match the dashboards: Vercel-inspired, no gradients, no heavy effects. Static only; no backend.

    ---

    *End of prompt. Paste the whole block above into v0.*
