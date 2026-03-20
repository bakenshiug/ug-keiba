# Design System Document: The Equestrian Editorial

## 1. Overview & Creative North Star: "The Prestigious Ledger"
This design system moves away from the cluttered, chaotic nature of traditional sports betting apps. Our Creative North Star is **The Prestigious Ledger**—a high-end, editorial experience that treats horse racing data with the reverence of a financial broadsheet and the luxury of a private club.

We break the "standard mobile app" template by utilizing **intentional asymmetry** and **tonal layering**. Instead of rigid grids, we use white space as a structural element. By pairing the authoritative weight of Mincho typography with a "No-Line" philosophy, we create a layout that feels curated, expensive, and laser-focused on high-stakes decision-making.

## 2. Colors & Surface Architecture
The palette is rooted in a deep "Racing Green" and a pristine "Surface White," creating an environment of high contrast and elite sport.

### The "No-Line" Rule
**Standard 1px borders are strictly prohibited for sectioning.** To define boundaries, designers must use background color shifts. For example:
*   A `surface-container-low` (#f2f4f2) section sitting atop a `surface` (#f8faf8) background.
*   Physical separation is achieved through the Spacing Scale, not "fencing" content in with lines.

### Surface Hierarchy & Nesting
Treat the UI as a series of stacked fine-paper sheets. 
*   **Base:** `surface` (#f8faf8)
*   **Secondary Content:** `surface-container` (#eceeec)
*   **Elevated Data/Action Cards:** `surface-container-lowest` (#ffffff)
Use these tiers to create "nested" depth. An inner data table should sit on a `surface-container-high` (#e6e9e7) to naturally distinguish it from the page body without needing a stroke.

### The "Glass & Signature" Polish
*   **Glassmorphism:** Use `surface_variant` at 60% opacity with a `20px` backdrop-blur for floating navigation bars or sticky headers. This allows the high-contrast data to bleed through softly.
*   **Signature Gradients:** For primary CTAs (e.g., "Place Bet" or "View Analysis"), use a subtle vertical gradient from `primary_container` (#006400) to `primary` (#004900). This adds a "jewel-toned" depth that feels premium.

## 3. Typography: The Editorial Contrast
We utilize a stark juxtaposition between traditional Japanese elegance and modern data clarity.

*   **Display & Headlines (Noto Serif / Strong Mincho):** These are the "Voice" of the system. Use `display-md` for race titles and `headline-sm` for horse names. The serif weight conveys authority and history.
*   **Titles & Body (Public Sans):** Used for navigation and general reading. `title-md` provides a clean, neutral anchor to the expressive headlines.
*   **Data & Labels (Inter):** For the "numbers"—odds, weight, times, and ranks. Inter’s tall x-height ensures maximum legibility at `label-sm` (0.6875rem) on small mobile screens.

## 4. Elevation & Depth: Tonal Layering
We reject the heavy drop-shadows of the early web. Elevation is a whisper, not a shout.

*   **The Layering Principle:** Depth is achieved by "stacking." A `surface-container-lowest` (#ffffff) card placed on a `surface-container-low` (#f2f4f2) background provides a natural "lift" through color contrast alone.
*   **Ambient Shadows:** For "Floating Action Buttons" or critical modals, use a diffused shadow: `0px 8px 24px rgba(25, 28, 27, 0.06)`. The tint is derived from `on-surface`, creating a natural ambient light effect.
*   **The "Ghost Border" Fallback:** If a border is required for top-rated horses (per user request), use the `primary` color (#004900) but at a **20% opacity** or as a 2px left-accent bar. Never use a 100% opaque, 1-pixel enclosing box.

## 5. Components

### Cards & Lists (The Core)
*   **Race Cards:** Forbid divider lines. Use `spacing-4` (0.9rem) between items. Top-rated horses receive a `primary_container` (#006400) left-edge accent (3px width) and a `surface-container-lowest` background to pop against the page.
*   **Data Grids:** Use alternating tonal rows (e.g., `surface` and `surface-container-low`) instead of lines to guide the eye across horse statistics.

### Buttons
*   **Primary:** `primary` (#004900) background, `on-primary` (#ffffff) text. Use `rounded-md` (0.375rem) for a modern yet disciplined look.
*   **Secondary/Outlined:** Use a "Ghost Border" (15% opacity of `outline`) with `primary` text.

### Selection Chips
*   **Filter Chips:** Use `surface-container-high` for unselected states. Upon selection, transition to `primary` with `on-primary` text. No borders.

### Input Fields
*   **Search/Predictor Inputs:** Use `surface-container-highest` (#e1e3e1) with a bottom-only focus bar in `primary`. This mimics an editorial underline rather than a software "box."

### Performance Indicators (Custom Component)
*   **The "Vigor" Meter:** A slim horizontal bar using `tertiary` (#790b4a) to represent "hot" horses, providing a sophisticated splash of color against the green/white base.

## 6. Do's and Don'ts

### Do:
*   **Do** use `spacing-10` and `spacing-12` for generous vertical breathing room between race categories.
*   **Do** use `notoSerif` for any text that is meant to be "heard" (opinions, titles, accolades).
*   **Do** use high-contrast `on-surface` (#191c1b) for all body text to ensure readability in bright outdoor sunlight (at the track).

### Don't:
*   **Don't** use 1px solid dividers. Use a `0.5rem` gap or a background color shift.
*   **Don't** use pure black (#000000). Always use `on-surface` (#191c1b) to maintain the "ink on paper" editorial feel.
*   **Don't** use standard "Material Design" rounded corners (e.g., 20px). Stick to the `md` (0.375rem) and `lg` (0.5rem) scale to keep the aesthetic sharp and professional.