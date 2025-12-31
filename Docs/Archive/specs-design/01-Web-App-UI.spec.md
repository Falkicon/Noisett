# Web App UI (MVP)

**Status:** MVP (January 2026)

**Platform:** Web (React)

**Responsive:** Desktop-first, tablet-friendly

---

## Layout Overview

### Page Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Header                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ [Logo] Brand Asset Generator                    [User] ▼  [Sign Out]││
│  └─────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                           Main Content                                   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                                                                      ││
│  │                      Input Section                                   ││
│  │                      (centered, max-width 600px)                     ││
│  │                                                                      ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                                                                      ││
│  │                      Results Section                                 ││
│  │                      (2×2 grid, max-width 800px)                     ││
│  │                                                                      ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│  Footer (minimal)                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### Dimensions

| Element | Width | Notes |
| --- | --- | --- |
| Page max-width | 1200px | Centered with auto margins |
| Input section | 600px max | Comfortable reading width |
| Results grid | 800px max | 2×2 at 380px each + gap |
| Header height | 64px | Fixed |

---

## Screen States

### State 1: Empty (Initial)

User has just loaded the app, no generation yet.

```
┌─────────────────────────────────────────────────┐
│                                                 │
│         🎨                                      │
│                                                 │
│    Describe what you need                       │
│    ┌───────────────────────────────────────┐   │
│    │                                       │   │
│    │ e.g., "A person collaborating with   │   │
│    │ AI on a creative project"            │   │
│    │                                       │   │
│    └───────────────────────────────────────┘   │
│                                                 │
│              [ Generate ]                       │
│                                                 │
│    ─────────────────────────────────────────   │
│                                                 │
│    💡 Tip: Be specific about the subject,      │
│    composition, and style you want.            │
│                                                 │
└─────────────────────────────────────────────────┘
```

### State 2: Generating (Loading)

Generation in progress.

```
┌─────────────────────────────────────────────────┐
│                                                 │
│    Your prompt:                                 │
│    "A person collaborating with AI..."         │
│                                                 │
│    ┌───────────────────────────────────────┐   │
│    │                                       │   │
│    │         ◐ Generating...               │   │
│    │                                       │   │
│    │    Creating 4 variations              │   │
│    │    This takes about 30 seconds        │   │
│    │                                       │   │
│    │    ████████████░░░░░░░░  60%          │   │
│    │                                       │   │
│    └───────────────────────────────────────┘   │
│                                                 │
│              [ Cancel ]                         │
│                                                 │
└─────────────────────────────────────────────────┘
```

### State 3: Results

Generation complete, showing 4 images.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Your prompt:                                                   │
│  "A person collaborating with AI on a creative project"        │
│                                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │                     │  │                     │              │
│  │                     │  │                     │              │
│  │       Image 1       │  │       Image 2       │              │
│  │                     │  │                     │              │
│  │                     │  │                     │              │
│  │  [⬇ Download]       │  │  [⬇ Download]       │              │
│  └─────────────────────┘  └─────────────────────┘              │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │                     │  │                     │              │
│  │                     │  │                     │              │
│  │       Image 3       │  │       Image 4       │              │
│  │                     │  │                     │              │
│  │                     │  │                     │              │
│  │  [⬇ Download]       │  │  [⬇ Download]       │              │
│  └─────────────────────────────────────────────┘              │
│                                                                 │
│  [ Generate More ]              [ New Prompt ]                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### State 4: Error

Generation failed.

```
┌─────────────────────────────────────────────────┐
│                                                 │
│    ⚠️ Generation failed                         │
│                                                 │
│    Something went wrong. Please try again.      │
│                                                 │
│    [ Try Again ]    [ Edit Prompt ]             │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Components

### Prompt Input

| Property | Value |
| --- | --- |
| Type | Textarea |
| Rows | 3 (expandable) |
| Max characters | 500 |
| Placeholder | See UI Text Strings |
| Border | 1px solid `$border-default` |
| Border radius | 8px |
| Padding | 12px 16px |
| Font | 16px `$font-body` |

**States:**

- Default: Gray border
- Focus: Blue border, subtle shadow
- Error: Red border (if validation fails)

### Generate Button

| Property | Value |
| --- | --- |
| Type | Primary button |
| Width | Auto (min 160px) |
| Height | 48px |
| Border radius | 8px |
| Font | 16px semi-bold |
| Background | `$color-primary` |
| Text | White |

**States:**

- Default: Solid blue
- Hover: Slightly darker
- Disabled: Gray, 50% opacity
- Loading: Show spinner, disable clicks

### Image Card

| Property | Value |
| --- | --- |
| Size | Square, flexible (280-380px) |
| Border radius | 12px |
| Shadow | Subtle (`$shadow-card`) |
| Hover | Slight lift, stronger shadow |

**Overlay on hover:**

- Semi-transparent dark gradient at bottom
- Download button appears

### Download Button (on image)

| Property | Value |
| --- | --- |
| Type | Icon + text button |
| Icon | Download arrow (16px) |
| Text | "Download" |
| Position | Bottom-left of image |
| Visibility | On hover (or always on touch) |

### Progress Indicator

| Property | Value |
| --- | --- |
| Type | Horizontal progress bar |
| Height | 4px |
| Border radius | 2px |
| Background | `$color-gray-200` |
| Fill | `$color-primary` |
| Animation | Smooth fill transition |

---

## Responsive Behavior

### Breakpoints

| Breakpoint | Width | Layout |
| --- | --- | --- |
| Desktop | ≥1024px | 2×2 grid, side-by-side buttons |
| Tablet | 768-1023px | 2×2 grid, narrower |
| Mobile | <768px | 1 column stack, full-width images |

### Mobile Adaptations

- Header: Hamburger menu (if needed for future features)
- Input: Full width with 16px padding
- Images: Single column, full width
- Download buttons: Always visible (no hover)

---

## Interactions

### Generate Flow

1. User types prompt → character count updates
2. User clicks Generate → button shows spinner
3. Prompt input becomes read-only
4. Progress bar animates
5. Images fade in as they complete (or all at once)
6. Generate button changes to "Generate More"

### Download Flow

1. User hovers image → overlay appears
2. User clicks Download → browser download dialog
3. File saves as `brand-asset-{timestamp}.png`

### Keyboard Navigation

| Key | Action |
| --- | --- |
| Tab | Move between interactive elements |
| Enter | Submit form / activate button |
| Escape | Cancel generation (if in progress) |

---

## Empty & Error States

### No Results Yet

- Show helpful tip about writing good prompts
- Example prompt as placeholder text

### Generation Failed

- Clear error message (not technical)
- Retry button
- Option to edit prompt

### Session Expired

- "Your session has expired. Please sign in again."
- Sign in button

---

## Accessibility

| Requirement | Implementation |
| --- | --- |
| Color contrast | WCAG AA (4.5:1 for text) |
| Focus indicators | Visible focus ring on all interactive elements |
| Alt text | Generated images: "Generated illustration: {prompt}" |
| Screen reader | Progress announced ("Generating, 60% complete") |
| Reduced motion | Respect `prefers-reduced-motion` for animations |

---

## v2+ Additions (Future)

When v2 features ship, these UI elements will be added:

### Asset Type Selector (v2.0)

- Dropdown above prompt input
- Options: Icons, Product, Logo, Premium
- Default: Product Illustrations

### Model Selector (v2.0)

- Secondary dropdown or toggle
- Show license badge inline
- Warning modal for non-commercial models

### Quality Selector (v2.1)

- Radio buttons or segmented control
- Options: Draft, Standard, High
- Show estimated time for each

### History Sidebar (v2.1)

- Left sidebar, collapsible
- Thumbnail + prompt preview
- Click to restore/view