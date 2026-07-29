---
name: Ethereal Grandeur
colors:
  surface: '#fbf9f8'
  surface-dim: '#dbdad9'
  surface-bright: '#fbf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3f3'
  surface-container: '#efeded'
  surface-container-high: '#e9e8e7'
  surface-container-highest: '#e4e2e2'
  on-surface: '#1b1c1c'
  on-surface-variant: '#444748'
  inverse-surface: '#303031'
  inverse-on-surface: '#f2f0f0'
  outline: '#747878'
  outline-variant: '#c4c7c7'
  surface-tint: '#5f5e5e'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#1c1b1b'
  on-primary-container: '#858383'
  inverse-primary: '#c8c6c5'
  secondary: '#735c00'
  on-secondary: '#ffffff'
  secondary-container: '#fed65b'
  on-secondary-container: '#745c00'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#1c1c1a'
  on-tertiary-container: '#858480'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e5e2e1'
  primary-fixed-dim: '#c8c6c5'
  on-primary-fixed: '#1c1b1b'
  on-primary-fixed-variant: '#474746'
  secondary-fixed: '#ffe088'
  secondary-fixed-dim: '#e9c349'
  on-secondary-fixed: '#241a00'
  on-secondary-fixed-variant: '#574500'
  tertiary-fixed: '#e5e2de'
  tertiary-fixed-dim: '#c8c6c2'
  on-tertiary-fixed: '#1c1c1a'
  on-tertiary-fixed-variant: '#474744'
  background: '#fbf9f8'
  on-background: '#1b1c1c'
  surface-variant: '#e4e2e2'
typography:
  headline-xl:
    fontFamily: Playfair Display
    fontSize: 64px
    fontWeight: '400'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Playfair Display
    fontSize: 40px
    fontWeight: '400'
    lineHeight: '1.2'
  headline-lg:
    fontFamily: Playfair Display
    fontSize: 48px
    fontWeight: '400'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Playfair Display
    fontSize: 32px
    fontWeight: '400'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1.0'
    letterSpacing: 0.1em
spacing:
  base: 8px
  container-max: 1440px
  gutter: 24px
  margin-mobile: 20px
  section-gap-desktop: 120px
  section-gap-mobile: 64px
---

## Brand & Style
The brand personality is rooted in "Quiet Luxury"—an understated yet commanding presence that prioritizes quality over flash. The target audience includes discerning global travelers who value exclusivity, heritage, and modern efficiency. The UI should evoke a sense of calm, timelessness, and meticulous attention to detail.

The design system employs a **Minimalist-Luxury** style. This approach uses generous whitespace to simulate the physical "breathing room" of a high-end suite. Visual interest is generated through high-contrast typography and the strategic use of metallic accents. Photography is the primary storyteller, treated with a cinematic, editorial eye to ground the digital experience in physical reality.

## Colors
The palette is built on the interplay between the deep, authoritative **Charcoal** and the warm, inviting **Cream**. 

- **Primary (Charcoal):** Used for typography and primary structural elements to provide a weighted, premium anchor.
- **Secondary (Champagne Gold):** Used sparingly for high-value accents, active states, and call-to-action details. It should never dominate the screen.
- **Tertiary (Cream):** The canvas color. It replaces pure white to soften the high-contrast experience and evoke the texture of premium stationery.
- **Neutral:** A range of taupe-leaning greys for secondary text and borders to maintain warmth.

## Typography
The typographic hierarchy creates a rhythm of contrast between the expressive, high-contrast serifs of **Playfair Display** and the functional clarity of **Inter**. 

Headlines should be set with tight letter-spacing to emphasize their editorial character. The use of all-caps for labels and small buttons is encouraged to add a touch of formality. Body text prioritizes legibility with ample line heights, ensuring that long-form descriptions of amenities remain accessible and inviting.

## Layout & Spacing
The design system utilizes a **Fixed Grid** on desktop (12 columns) and a **Fluid Grid** on mobile (4 columns). 

The spacing philosophy follows a "Breathe First" rule: sections are separated by significant vertical gaps to ensure no two content blocks compete for attention. Alignment should be primarily centered for landing moments to evoke symmetry and balance, shifting to left-aligned layouts for content-heavy utility pages. Padding within components like cards and modals should be generous to maintain the feeling of luxury.

## Elevation & Depth
Depth is achieved through **Tonal Layers** rather than heavy shadows. The "Cream" base serves as the lowest level, with "White" surfaces used for floating elements like navigation bars or modals to create a subtle lift.

If depth must be emphasized, use **Low-contrast Outlines**: a 1px border in a slightly darker cream or very light taupe (#E5E2DD). This maintains a flat, sophisticated look. Shadows, if necessary, must be "Ambient Shadows"—extremely diffused, with a 32px-64px blur and low opacity (5-8%), tinted with the Primary Charcoal color to avoid a "muddy" appearance.

## Shapes
The design system uses a **Sharp** shape language. 90-degree angles communicate precision, architectural strength, and a classic aesthetic. 

Roundness is strictly reserved for user-generated content (like avatars) or specific functional icons. Buttons, input fields, images, and card containers must remain perfectly rectangular to mirror the sharp lines of modern luxury architecture.

## Components
- **Buttons:** Primary buttons are solid Charcoal with Cream text, using sharp corners. Secondary buttons use a Champagne Gold bottom border (2px) or a Ghost style with thin outlines.
- **Input Fields:** Minimalist design with only a bottom border in Taupe. Labels are always `label-sm` (uppercase) positioned above the field.
- **Cards:** No borders or shadows by default. Content is separated by white space. Use "Full-bleed" imagery within cards to maximize visual impact.
- **Chips/Tags:** Small, sharp-edged rectangles with a Cream background and Charcoal text. Used for "Available" or "Suite Type" indicators.
- **Navigation:** A persistent, high-z-index top bar that transitions from transparent to solid Cream on scroll. Links use `label-sm` with a subtle Champagne Gold underline on hover.
- **Image Carousels:** Use thin, elegant "previous/next" arrows in Champagne Gold. Pagination dots are replaced by a fractional counter (e.g., 01 / 05) in `label-sm`.