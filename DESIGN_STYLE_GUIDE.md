# PrayerStreak PH Front-End Style Guide

## Design Direction

PrayerStreak PH should feel like a premium devotional workspace: calm, reverent, focused, and easy to return to every day. The visual language uses deep navy for trust and spiritual quiet, warm paper surfaces for reading comfort, and restrained gold accents for moments of emphasis.

## Layout System

- Framework: Bootstrap 5.3.
- Container: Use Bootstrap `.container` for primary page width.
- Grid: Use Bootstrap `.row` and `.col-*` for responsive sections.
- Card radius: 8px for cards, panels, previews, and content surfaces.
- Section spacing: Use generous vertical rhythm with `py-5` and larger desktop spacing where needed.
- Mobile behavior: Stack content vertically, keep buttons full-width only when space is tight, and preserve 44px minimum tap targets.

## Color Tokens

| Token | Hex | Usage |
| --- | --- | --- |
| Deep Navy | `#123047` | Header, hero overlay, primary dark sections |
| Devotional Blue | `#1E4D66` | Supporting text and calm emphasis |
| Prayer Gold | `#B58B2B` | Primary CTA, highlights, icons |
| Soft Gold | `#F1DFB8` | Dark-section labels and subtle emphasis |
| Warm Paper | `#FBF7EE` | Main page background and card fill |
| Cream | `#F4ECDD` | Secondary surfaces and quiet blocks |
| Ink | `#17212B` | Primary text |
| Muted Text | `#6D6252` | Body copy and secondary labels |
| Border | `#DED2BA` | Card borders and dividers |
| Sage | `#6F8477` | Secondary icon accent |
| Clay Rose | `#AD6F62` | Tertiary icon accent |

## Typography

- Primary font: Poppins for interface text, navigation, labels, and CTAs.
- Devotional font: IM Fell English for Scripture quotes only.
- Headlines: 700-800 weight, tight line-height, no negative letter spacing.
- Body copy: 1.6-1.8 line-height for comfortable reading.
- Labels: Uppercase, 700-800 weight, small size, with letter spacing kept at 0.

## Components

### Navigation

- Use a fixed Bootstrap navbar with deep navy background.
- Primary navigation links should be white at reduced opacity and brighten on hover.
- The highest-priority action uses the gold `.btn-primary` treatment.
- Mobile navigation uses Bootstrap collapse behavior.

### Buttons

- All buttons use pill radius for a warm, approachable action style.
- Minimum height: 44px.
- Primary: gold background with white text.
- Secondary on dark: outline-light.
- Secondary on light: outline-primary.

### Cards and Panels

- Use 8px radius with warm paper fill and soft navy shadow.
- Avoid nesting decorative cards unless the inner element has a distinct functional purpose.
- Use borders in `#DED2BA` to preserve a tactile paper quality.

### Icons

- Use Tabler icons already included in the app.
- Place icons in 48px square tiles for feature and metric cards.
- Use gold as the default icon color, with sage or clay rose for variety.

### Imagery

- Use real product or app preview imagery where available.
- Keep screenshots clear, unblurred, and framed in a simple 8px preview container.
- Avoid purely decorative gradients or abstract illustrations as primary content.

## Responsive Rules

- Hero content stacks under 992px.
- Cards stack into one column on mobile.
- Buttons can stack vertically on narrow screens.
- Use `clamp()` for large display headings only, with fixed/rem-based type elsewhere.
- Do not let text overlap imagery or controls.

## Accessibility Notes

- Maintain strong color contrast on navy sections.
- Preserve visible focus states for Bootstrap controls.
- Keep link destinations semantic and unchanged.
- Use descriptive image alt text for product previews.
- Maintain 44px minimum tap targets for interactive controls.
