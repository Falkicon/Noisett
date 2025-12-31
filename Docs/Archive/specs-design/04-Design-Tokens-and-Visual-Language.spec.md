# Design Tokens & Visual Language

Design tokens and visual language for the Brand Asset Generator. These should be implemented as CSS custom properties or a design token system.

---

## Color Palette

### Primary Colors

| Token                   | Value     | Usage                  |
| ----------------------- | --------- | ---------------------- |
| `$color-primary`        | `#0078D4` | Primary actions, links |
| `$color-primary-hover`  | `#106EBE` | Primary hover state    |
| `$color-primary-active` | `#005A9E` | Primary active/pressed |
| `$color-primary-light`  | `#DEECF9` | Primary backgrounds    |

### Semantic Colors

| Token                  | Value     | Usage                         |
| ---------------------- | --------- | ----------------------------- |
| `$color-success`       | `#107C10` | Success states, confirmations |
| `$color-success-light` | `#DFF6DD` | Success backgrounds           |
| `$color-warning`       | `#FFB900` | Warnings, cautions            |
| `$color-warning-light` | `#FFF4CE` | Warning backgrounds           |
| `$color-error`         | `#D13438` | Errors, destructive actions   |
| `$color-error-light`   | `#FDE7E9` | Error backgrounds             |

### Neutral Colors

| Token             | Value     | Usage              |
| ----------------- | --------- | ------------------ |
| `$color-gray-900` | `#201F1E` | Primary text       |
| `$color-gray-700` | `#605E5C` | Secondary text     |
| `$color-gray-500` | `#8A8886` | Placeholder text   |
| `$color-gray-300` | `#C8C6C4` | Borders, dividers  |
| `$color-gray-200` | `#E1DFDD` | Disabled states    |
| `$color-gray-100` | `#F3F2F1` | Backgrounds        |
| `$color-gray-50`  | `#FAF9F8` | Subtle backgrounds |
| `$color-white`    | `#FFFFFF` | Cards, inputs      |

### Background Colors

| Token         | Value             | Usage            |
| ------------- | ----------------- | ---------------- |
| `$bg-page`    | `#FAF9F8`         | Page background  |
| `$bg-card`    | `#FFFFFF`         | Card backgrounds |
| `$bg-input`   | `#FFFFFF`         | Input fields     |
| `$bg-overlay` | `rgba(0,0,0,0.4)` | Modal overlays   |

---

## Typography

### Font Family

| Token               | Value                                                       |
| ------------------- | ----------------------------------------------------------- |
| `$font-family`      | `'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif` |
| `$font-family-mono` | `'Cascadia Code', 'Consolas', monospace`                    |

### Font Sizes

| Token             | Size | Line Height | Usage                  |
| ----------------- | ---- | ----------- | ---------------------- |
| `$font-size-xs`   | 11px | 16px        | Captions, badges       |
| `$font-size-sm`   | 13px | 18px        | Secondary text, labels |
| `$font-size-base` | 15px | 22px        | Body text              |
| `$font-size-md`   | 17px | 24px        | Emphasis text          |
| `$font-size-lg`   | 20px | 28px        | Section headers        |
| `$font-size-xl`   | 24px | 32px        | Page titles            |
| `$font-size-xxl`  | 32px | 40px        | Hero text              |

### Font Weights

| Token                   | Value | Usage           |
| ----------------------- | ----- | --------------- |
| `$font-weight-regular`  | 400   | Body text       |
| `$font-weight-semibold` | 600   | Buttons, labels |
| `$font-weight-bold`     | 700   | Headings        |

---

## Spacing

### Base Unit

All spacing is based on a 4px grid.

| Token       | Value | Usage           |
| ----------- | ----- | --------------- |
| `$space-1`  | 4px   | Tight spacing   |
| `$space-2`  | 8px   | Default gap     |
| `$space-3`  | 12px  | Form spacing    |
| `$space-4`  | 16px  | Section padding |
| `$space-5`  | 20px  | Card padding    |
| `$space-6`  | 24px  | Section margins |
| `$space-8`  | 32px  | Large sections  |
| `$space-10` | 40px  | Page sections   |
| `$space-12` | 48px  | Major sections  |

---

## Border Radius

| Token          | Value  | Usage                  |
| -------------- | ------ | ---------------------- |
| `$radius-sm`   | 4px    | Small elements, badges |
| `$radius-md`   | 8px    | Buttons, inputs        |
| `$radius-lg`   | 12px   | Cards, modals          |
| `$radius-xl`   | 16px   | Large cards            |
| `$radius-full` | 9999px | Pills, avatars         |

---

## Shadows

| Token           | Value                            | Usage             |
| --------------- | -------------------------------- | ----------------- |
| `$shadow-sm`    | `0 1px 2px rgba(0,0,0,0.05)`     | Subtle depth      |
| `$shadow-md`    | `0 4px 6px rgba(0,0,0,0.07)`     | Cards at rest     |
| `$shadow-lg`    | `0 8px 16px rgba(0,0,0,0.1)`     | Cards on hover    |
| `$shadow-xl`    | `0 12px 24px rgba(0,0,0,0.15)`   | Modals, dropdowns |
| `$shadow-focus` | `0 0 0 2px $color-primary-light` | Focus rings       |

---

## Borders

| Token             | Value                       | Usage            |
| ----------------- | --------------------------- | ---------------- |
| `$border-default` | `1px solid $color-gray-300` | Input borders    |
| `$border-hover`   | `1px solid $color-gray-500` | Input hover      |
| `$border-focus`   | `2px solid $color-primary`  | Input focus      |
| `$border-error`   | `1px solid $color-error`    | Validation error |

---

## Animation & Motion

### Durations

| Token              | Value | Usage                |
| ------------------ | ----- | -------------------- |
| `$duration-fast`   | 100ms | Micro-interactions   |
| `$duration-normal` | 200ms | Standard transitions |
| `$duration-slow`   | 300ms | Larger animations    |
| `$duration-slower` | 500ms | Page transitions     |

### Easing

| Token           | Value                               | Usage            |
| --------------- | ----------------------------------- | ---------------- |
| `$ease-default` | `cubic-bezier(0.4, 0, 0.2, 1)`      | Standard ease    |
| `$ease-in`      | `cubic-bezier(0.4, 0, 1, 1)`        | Enter animations |
| `$ease-out`     | `cubic-bezier(0, 0, 0.2, 1)`        | Exit animations  |
| `$ease-bounce`  | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Playful bounce   |

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Z-Index Scale

| Token         | Value | Usage               |
| ------------- | ----- | ------------------- |
| `$z-base`     | 0     | Default content     |
| `$z-dropdown` | 100   | Dropdowns, tooltips |
| `$z-sticky`   | 200   | Sticky headers      |
| `$z-overlay`  | 300   | Overlays            |
| `$z-modal`    | 400   | Modals              |
| `$z-toast`    | 500   | Toast notifications |

---

## Component Tokens

### Buttons

| Token                 | Value                   |
| --------------------- | ----------------------- |
| `$button-height-sm`   | 32px                    |
| `$button-height-md`   | 40px                    |
| `$button-height-lg`   | 48px                    |
| `$button-padding-x`   | 16px                    |
| `$button-radius`      | `$radius-md`            |
| `$button-font-weight` | `$font-weight-semibold` |

### Inputs

| Token              | Value             |
| ------------------ | ----------------- |
| `$input-height`    | 40px              |
| `$input-padding-x` | 12px              |
| `$input-padding-y` | 8px               |
| `$input-radius`    | `$radius-md`      |
| `$input-font-size` | `$font-size-base` |

### Cards

| Token                | Value        |
| -------------------- | ------------ |
| `$card-padding`      | `$space-5`   |
| `$card-radius`       | `$radius-lg` |
| `$card-shadow`       | `$shadow-md` |
| `$card-shadow-hover` | `$shadow-lg` |

---

## Breakpoints

| Token            | Value  | Description    |
| ---------------- | ------ | -------------- |
| `$breakpoint-sm` | 640px  | Small screens  |
| `$breakpoint-md` | 768px  | Tablets        |
| `$breakpoint-lg` | 1024px | Desktops       |
| `$breakpoint-xl` | 1280px | Large desktops |

---

## Icon Sizes

| Token      | Value | Usage                  |
| ---------- | ----- | ---------------------- |
| `$icon-xs` | 12px  | Inline with small text |
| `$icon-sm` | 16px  | Buttons, inputs        |
| `$icon-md` | 20px  | Default                |
| `$icon-lg` | 24px  | Prominent icons        |
| `$icon-xl` | 32px  | Empty states           |

---

## Dark Mode (Future)

If dark mode is implemented, these tokens would be overridden:

| Token             | Light     | Dark      |
| ----------------- | --------- | --------- |
| `$color-gray-900` | `#201F1E` | `#F3F2F1` |
| `$color-gray-100` | `#F3F2F1` | `#292827` |
| `$bg-page`        | `#FAF9F8` | `#1B1A19` |
| `$bg-card`        | `#FFFFFF` | `#292827` |

---

## Implementation Notes

### CSS Custom Properties

```css
:root {
  --color-primary: #0078d4;
  --color-primary-hover: #106ebe;
  --font-family: "Segoe UI", -apple-system, sans-serif;
  --space-4: 16px;
  --radius-md: 8px;
  /* ... etc */
}
```

### Tailwind Config (if using)

```jsx
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#0078D4",
          hover: "#106EBE",
        },
      },
    },
  },
};
```

### Figma Styles

These tokens should be mirrored in a Figma design system file with matching style names for designer-developer handoff.
