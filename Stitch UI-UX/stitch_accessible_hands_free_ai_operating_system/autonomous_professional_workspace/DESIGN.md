---
name: Autonomous Professional Workspace
colors:
  surface: '#fcf9f4'
  surface-dim: '#dcdad5'
  surface-bright: '#fcf9f4'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3ee'
  surface-container: '#f0ede9'
  surface-container-high: '#ebe8e3'
  surface-container-highest: '#e5e2dd'
  on-surface: '#1c1c19'
  on-surface-variant: '#3f4947'
  inverse-surface: '#31302d'
  inverse-on-surface: '#f3f0eb'
  outline: '#6f7977'
  outline-variant: '#bec9c6'
  surface-tint: '#226963'
  primary: '#00433f'
  on-primary: '#ffffff'
  primary-container: '#0f5c57'
  on-primary-container: '#8fd2cb'
  inverse-primary: '#90d3cc'
  secondary: '#805600'
  on-secondary: '#ffffff'
  secondary-container: '#feba49'
  on-secondary-container: '#704b00'
  tertiary: '#004522'
  on-tertiary: '#ffffff'
  tertiary-container: '#005f31'
  on-tertiary-container: '#86d79c'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#abefe8'
  primary-fixed-dim: '#90d3cc'
  on-primary-fixed: '#00201e'
  on-primary-fixed-variant: '#00504b'
  secondary-fixed: '#ffddb0'
  secondary-fixed-dim: '#feba49'
  on-secondary-fixed: '#281800'
  on-secondary-fixed-variant: '#614000'
  tertiary-fixed: '#a2f5b7'
  tertiary-fixed-dim: '#87d89d'
  on-tertiary-fixed: '#00210d'
  on-tertiary-fixed-variant: '#00522a'
  background: '#fcf9f4'
  on-background: '#1c1c19'
  surface-variant: '#e5e2dd'
typography:
  headline-xl:
    fontFamily: Atkinson Hyperlegible Next
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 60px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Atkinson Hyperlegible Next
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.005em
  headline-md:
    fontFamily: Atkinson Hyperlegible Next
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 38px
  body-xl:
    fontFamily: Atkinson Hyperlegible Next
    fontSize: 24px
    fontWeight: '400'
    lineHeight: 36px
  body-lg:
    fontFamily: Atkinson Hyperlegible Next
    fontSize: 20px
    fontWeight: '400'
    lineHeight: 30px
  body-md:
    fontFamily: Atkinson Hyperlegible Next
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  label-lg:
    fontFamily: Atkinson Hyperlegible Next
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 26px
  label-voice:
    fontFamily: Atkinson Hyperlegible Next
    fontSize: 16px
    fontWeight: '700'
    lineHeight: 22px
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-desktop: 2rem
  margin: 1.5rem
  margin-desktop: 3rem
  space-xs: 0.5rem
  space-sm: 1rem
  space-md: 1.5rem
  space-lg: 2rem
  space-xl: 3rem
---

## Brand & Style

This design system centers on dignity, autonomy, and professional empowerment. Designed for high-consequence remote knowledge work, it provides users navigating motor impairments, quadriplegia, ALS, and mental fatigue with an interface that communicates executive capability rather than clinical assistance. The aesthetic rejects patronizing tropes, toy-like simplifications, and sterile hospital motifs. Instead, it balances high-efficiency enterprise software standards with warm, ergonomically calibrated elements.

The visual direction blends **Humanist Functionalism** with **High-Legibility Modernism**. It prioritizes extreme cognitive clarity, predictable target acquisition, physical spaciousness, and calm chromatic grounding. Every structural choice directly honors alternative input dynamics (head tracking, eye gaze, switch control, and speech commands) without sacrificing high-density informational rigor.

## Colors

The palette establishes an authoritative, calm environment with distinct functional roles for every hue. Contrast thresholds consistently exceed WCAG AAA standards (7:1) across body typography and primary interaction surfaces.

- **Canvas & Structural Surfaces**: The base canvas is `#FAF7F2` (Warm Canvas), an organic off-white that reduces eye fatigue caused by glare during extended dwell-time sessions. Primary elevated cards and interaction containers utilize pure `#FFFFFF` bounded by structural borders of `#E3DED7`.
- **Text & Hierarchy**: Primary labels and reading text use `#1C2321` (Deep Ink), ensuring stark contrast against white and warm canvas backgrounds. Supporting metadata, secondary instructions, and voice cues use `#4A5552` (Muted Charcoal).
- **Primary Work Action (`#0F5C57`)**: A deep, focused teal used for standard system actions, state commits, and primary focus indicators. Hover/Dwell transition rests at `#0B4541` with pure `#FFFFFF` text.
- **External Confirmation (`#E0A030`)**: A warm amber designated exclusively for operations that transmit data beyond the local environment (e.g., sending client deliverables, submitting billed hours, external API triggers). Foreground text remains `#1C2321` for peak readability.
- **System Feedback**: `#3E8E5A` (Soft Green) denotes verified outputs and completed tasks; `#B5413A` (Muted Red) designates immediate halt commands, switch cancellations, and destructive state warnings.

Do not use color as the single channel for interaction status. State changes must pair color shifts with a 3px solid border change and clear typographic labels.

## Typography

The type system is powered entirely by **Atkinson Hyperlegible Next**. Engineered specifically to remove letterform ambiguity (differentiating 'I', '1', and 'l', or '0' and 'O'), it provides effortless scannability for users reading across varied distances and monitor setups.

- The baseline standard for all body copy and user-generated text is fixed at **20px** (`body-lg`) with an expansive `1.5` line-height (`30px`) to prevent visual crowding during long continuous reading tasks.
- Headers are weighted strongly (`700` and `600`) to anchor scanning paths for eye-gaze and head-tracking fixation points.
- **Voice Command Prompts (`label-voice`)**: Explicitly styled affordance markers always appear adjacent to or directly beneath interactive controls. These markers format spoken commands in uppercase tracking (e.g., `SAY: "APPROVE"`), distinguishing execution phrases from descriptive content.
- Text scaling must respect browser zoom levels up to 400% without layout clipping, content truncation, or horizontal scrolling.

## Layout & Spacing

Layout geometry is structured around a predictable, distraction-free grid optimized for alternative inputs:

- **Target Separation Discipline**: A mandatory minimum gap of **24px** (`1.5rem` / `space-md`) separates any two clickable, gaze-targetable, or switch-selectable elements. This prevents mis-triggers caused by tremor, gaze drift, or switch double-strikes.
- **Grid Structure**: A balanced 12-column desktop grid with wide gutters (`2rem` / `gutter-desktop`) and outer canvas margins (`3rem` / `margin-desktop`). The interface avoids deep nesting; main content regions and tool panels occupy dedicated, locked regions to eliminate unexpected viewport shifting.
- **Zero Timers and Sliders**: Layout structures must never rely on time-based auto-collapsing panels, timed toast notifications, or horizontal scrub bars/sliders. Content revelation is strictly driven by explicit, user-commanded stepper controls and static multi-column splits.

## Elevation & Depth

To maintain clarity and support motor precision, depth is articulated through **tonal layering and structural outlines** rather than heavy, blurry drop shadows. Atmospheric blur effects and complex skeuomorphic depth maps are prohibited, as they introduce visual noise that complicates gaze-fixation feedback.

- **Resting Canvas**: The base level sits on `#FAF7F2`.
- **Containers & Workspaces**: Elevated content panels sit on `#FFFFFF` with a crisp 1.5px solid border of `#E3DED7`.
- **Dwell / Hover States**: When an eye gaze, head cursor, or pointer dwells on an interactive node, the surface does not lift with an ambiguous shadow. Instead, it displays an immediate 3px solid high-contrast ring in `#0F5C57` with an inner background shift.
- **Modals & Overlays**: Modals use a flat `#FFFFFF` surface bordered by `#1C2321` (2px), surrounded by an opaque `#1C2321` backdrop at 40% opacity. This preserves orientation without visually distorting background context.

## Shapes

The design uses a balanced roundedness configuration (`roundedness: 2`). 

- **Primary Cards & Large Work Containers**: Built strictly with **16px border-radius** (`rounded-lg` / `1rem`), delivering a soft, non-hostile perimeter that comfortably defines the content boundaries.
- **Buttons, Switch Nodes, and Interactive Targets**: Utilize **8px border-radius** (`rounded` / `0.5rem`). This slight rounding retains clean geometry, ensuring that target perimeters remain clearly identifiable during gaze calibration and switch step-throughs.
- **Status Indicators & Voice Badges**: Use smaller 6px to 8px radii. Circular elements are reserved strictly for binary status dots and switch step-markers.

## Components

### Interactive Target Dimensions
Every button, switch target, tab, and card control must meet a strict minimum footprint of **64x64px**. No interactive boundary may fall below this threshold.

### Buttons & Voice Affordances
- **Primary Button**: Base size >= 64px height. Solid `#0F5C57` surface, white Atkinson Hyperlegible text (`label-lg`), 8px border-radius. Beneath or within the button layout, a dedicated subtitle pill features the speech prompt: `SAY: "EXECUTE"` (`label-voice`) with deep contrast.
- **External Action Button**: Solid `#E0A030` surface with `#1C2321` text, indicating irreversible or outbound communication. Features voice prompt `SAY: "TRANSMIT"`.
- **Safety / Halt Button**: Solid `#B5413A` surface, white text. Always locked to a predictable screen anchor or persistent toolbar for instantaneous voice or switch emergency stop (`SAY: "STOP"`).
- **Dwell Ring**: For eye-gaze and head-tracker workflows, interactive targets show an unmistakable radial progress stroke or perimeter boundary fill (3px solid `#0F5C57`) indicating activation timing without sudden jumps.

### Inputs & Form Controls
- **No Drag Sliders or Scrubbers**: All numeric adjustments and range operations use discreet **Stepper Modules**. A stepper consists of a 64x64px decrement button (`-`), a centrally rendered large text field displaying the state, and a 64x64px increment button (`+`).
- **Text Inputs**: Crisp `#FFFFFF` surface, 64px minimum height, bordered by `#E3DED7` (1.5px). Focus shifts the border to 3px solid `#0F5C57`. Input prompts are accompanied by direct voice commands (`SAY: "EDIT [FIELD NAME]"`).

### Selection Controls (Checkboxes & Radios)
- Checkboxes and radio targets feature an external 64x64px hit container.
- The visual selector box is an enlarged 32x32px element with thick 3px boundary strokes, utilizing `#0F5C57` checkmarks on a high-contrast white ground.
- Options never cluster together; they maintain a 24px vertical and horizontal gap.

### Cards & Dispatch Panels
- Background: `#FFFFFF`.
- Border: 1.5px solid `#E3DED7`.
- Border-radius: 16px.
- Internal padding: 32px (`space-xl`).
- Panels feature clearly designated voice IDs in their top-right quadrant (e.g., `CARD 01`, `SAY: "OPEN 1"`) to allow switch and voice navigators to focus sections without sequential scanning.