# Trelity Brand Spec — Prospect Scout Dashboard
*Confirmed April 9, 2026 — sourced from trelity.com DevTools inspection + logo assets*

---

## Typography

Two fonts. Both are Google Fonts — load via `next/font/google`.

| Role | Font | Weights | Confirmed |
|---|---|---|---|
| Headings | **Signika Negative** | 400, 600, 700 | ✅ DevTools |
| Body / UI | **Nunito Sans** | 400, 500, 600 | ✅ DevTools |

### Next.js font setup (drop into `app/layout.tsx`)

```ts
import { Nunito_Sans, Signika_Negative } from 'next/font/google'

const nunitoSans = Nunito_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-body',
})

const signikaNegative = Signika_Negative({
  subsets: ['latin'],
  weight: ['400', '600', '700'],
  variable: '--font-heading',
})
```

### Usage rules

- **Signika Negative** — page title, drawer firm name, section headings
- **Nunito Sans** — table rows, labels, column headers, AI summary text, badges, filter tabs, meta text
- Heading weight: 600 for primary, 400 for subheadings
- Body confirmed at 16px on site; use 14px for table rows, 13px for labels, 12px for meta
- Nav/label text: uppercase + `letter-spacing: 0.08em` + weight 500
- Line height: ~1.8 for body, ~1.3 for headings

---

## Color Palette

### Core brand colors

| Name | Hex | Role |
|---|---|---|
| Navy | `#1B3A6B` | Primary — topbar, nav bg, filter active state |
| Chartreuse | `#C5D82E` | Accent — score highlights, badges, "Prospect Scout" wordmark, graphic elements |
| Teal | `#3DA89A` | Action — CTA buttons, primary interactive elements |
| Teal Dark | `#2D7A7A` | Button hover state |
| Off-white | `#F0EFE8` | Page background |
| White | `#FFFFFF` | Card surfaces, drawer background |
| Near-black | `#1A1A2E` | Wordmark text on light bg, primary body text |

### Color role rules — important
- **Chartreuse = signal/highlight.** Never use on buttons.
- **Teal = action/interaction.** Use for "Run Scoring", "Add Firm", any primary CTA button.
- **Navy = structure.** Topbar, filter tabs, column headers, labels.
- These three roles must stay distinct. Do not swap them.

### Score cell color ramp (1–5)

| Score | Background | Text |
|---|---|---|
| 5 | `#C5D82E` | `#2d3a00` |
| 4 | `#DDE87A` | `#3a4800` |
| 3 | `#F0F4C2` | `#555c00` |
| 2 | `#FDDDC5` | `#7a3600` |
| 1 | `#F9C0B0` | `#7a2200` |

---

## Logo

- **Icon mark:** Architectural grid — outlined square frame with interior cross structure (like a structural floor plan grid). Not filled squares.
- **Wordmark:** "TRELITY" all-caps, geometric sans, wide-tracked
- **On light bg:** Navy mark + near-black wordmark
- **On dark bg:** White mark + white wordmark
- **In topbar:** White mark + "Trelity" in white + "Prospect Scout" in chartreuse (`#C5D82E`)
- SVG file for the icon mark is still needed from Trelity for pixel-perfect rendering

---

## Buttons & Interactive Elements

| Button type | Style |
|---|---|
| Primary CTA (Run Scoring, Add Firm) | Teal `#3DA89A` bg, white text, pill shape (`border-radius: 100px`) |
| Hover on primary CTA | Teal dark `#2D7A7A` |
| Filter tab (active) | Navy `#1B3A6B` bg, white text, pill shape |
| Filter tab (inactive) | White bg, navy `#1B3A6B` border + text, pill shape |
| Button text case | All-caps for standalone CTAs; mixed case for inline controls |

---

## UI Patterns

| Element | Spec |
|---|---|
| Topbar | Full-width navy `#1B3A6B` · summary stats bar inline |
| Stat bar values | White bold numbers · muted labels · chartreuse for "% complete" value only |
| Page background | `#F0EFE8` — warm off-white, not pure white |
| Card/table surface | White `#FFFFFF` · 0.5px border · `border-radius: 12px` |
| Table row hover | Light navy tint `#EEF2F8` |
| Score circle (composite) | Chartreuse fill for ≥4.0 · cream/peach for lower · navy number inside |
| Score cells | Color-coded 1–5 per ramp above · number centered · `border-radius: 6px` |
| Source badges (ENR) | Navy bg + white text · pill |
| Source badges (CB '24/'25) | Navy outline + navy text · pill |
| Stage labels | Light gray pill · 12px · exact BD funnel names |
| Right panel / drawer | White bg · slides in on row click · AI summary in light gray card |
| Missing data flag | Muted score cell · score defaults to 2 |
| Corner radius | Cells: 6px · badges/pills: 100px · cards/drawer: 12px |

---

## BD Funnel Stage Labels (use exactly)
Meet · Met · Get Pilot · Develop · Expand · Maintain

---

## What's Still Needed from Trelity
- SVG file for the grid-mark icon (for clean topbar rendering)
