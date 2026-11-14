# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Coalsense Dispatch
**Generated:** 2026-11-14 15:55:25
**Category:** Productivity Tool
**Design Dials:** Variance 2/10 (Centered / Minimal) | Motion 2/10 (Subtle) | Density 2/10 (Spacious)

---

## Global Rules

### Color Palette

| Role | Hex | CSS Variable |
|------|-----|--------------|
| Primary | `#0D9488` | `--color-primary` |
| On Primary | `#000000` | `--color-on-primary` |
| Secondary | `#14B8A6` | `--color-secondary` |
| On Secondary | `#0F172A` | `--color-on-secondary` |
| Accent/CTA | `#EA580C` | `--color-accent` |
| On Accent/CTA | `#000000` | `--color-on-accent` |
| Background | `#F0FDFA` | `--color-background` |
| Foreground | `#134E4A` | `--color-foreground` |
| Card | `#FFFFFF` | `--color-card` |
| Card Foreground | `#134E4A` | `--color-card-foreground` |
| Muted | `#E8F1F4` | `--color-muted` |
| Muted Foreground | `#475569` | `--color-muted-foreground` |
| Border | `#99F6E4` | `--color-border` |
| Destructive | `#DC2626` | `--color-destructive` |
| On Destructive | `#FFFFFF` | `--color-on-destructive` |
| Ring | `#0D9488` | `--color-ring` |

**Color Notes:** Teal focus + action orange [Accent adjusted from #F97316]

### Typography

- **Heading Font:** Plus Jakarta Sans
- **Body Font:** Plus Jakarta Sans
- **Mood:** friendly, modern, saas, clean, approachable, professional
- **Google Fonts:** [Plus Jakarta Sans + Plus Jakarta Sans](https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap)

**CSS Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
```

### Spacing Variables

*Density: 2/10 — Spacious*

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `4px` / `0.25rem` | Tight gaps |
| `--space-sm` | `8px` / `0.5rem` | Icon gaps, inline spacing |
| `--space-md` | `24px` / `1.5rem` | Standard padding |
| `--space-lg` | `32px` / `2rem` | Section padding |
| `--space-xl` | `48px` / `3rem` | Large gaps |
| `--space-2xl` | `64px` / `4rem` | Section margins |
| `--space-3xl` | `96px` / `6rem` | Hero padding |

### Shadow Depths

| Level | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle lift |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | Cards, buttons |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Modals, dropdowns |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.15)` | Hero images, featured cards |

---

## Component Specs

### Buttons

```css
/* Primary Button */
.btn-primary {
  background: #EA580C;
  color: #000000;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* Secondary Button */
.btn-secondary {
  background: transparent;
  color: #134E4A;
  border: 2px solid #0D9488;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}
```

### Cards

```css
.card {
  background: #F0FDFA;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-md);
  transition: all 200ms ease;
  cursor: pointer;
}

.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
```

### Inputs

```css
.input {
  padding: 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 200ms ease;
}

.input:focus {
  border-color: #0D9488;
  outline: none;
  box-shadow: 0 0 0 3px #0D948820;
}
```

### Modals

```css
.modal-overlay {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 90%;
}
```

---

## Style Guidelines

**Style:** Minimalism & Swiss Style

**Keywords:** Clean, simple, spacious, functional, white space, high contrast, geometric, sans-serif, grid-based, essential

**Best For:** Enterprise apps, dashboards, documentation sites, SaaS platforms, professional tools

**Key Effects:** Subtle hover (200-250ms), smooth transitions, sharp shadows if any, clear type hierarchy, fast loading

### Page Pattern

**Pattern Name:** Product Demo + Features

- **Conversion Strategy:** Use an interactive demo only when it explains value better than static media. Provide captions, transcript, visible play/pause controls, and a non-video fallback; do not autoplay under reduced motion. Pause media when offscreen or hidden and keep the final product state available as static content.
- **CTA Placement:** Video center + CTA right/bottom
- **Section Order:** Hero > Product video/mockup (center) > Feature breakdown per section > Comparison (optional) > CTA

---

## Motion

**Scroll Reveal** (Subtle) — Trigger: scroll (viewport enter) | Duration: 300-400ms | Easing: `power1.out`

```js
gsap.from(el, { opacity: 0, y: 12, duration: 0.35, ease: 'power1.out', scrollTrigger: { trigger: el, start: 'top 90%', toggleActions: 'play none none reverse' } });
```

**Framework notes:** Requires the ScrollTrigger plugin registered once via gsap.registerPlugin(ScrollTrigger); Use matchMedia('(prefers-reduced-motion: reduce)') to skip non-essential motion and render the final state immediately

- ✅ Keep the y offset small (8-16px) so it reads as a fade, not a slide
- ❌ Don't reveal below-the-fold content needed for SEO/crawlers as invisible-by-default without a no-JS fallback
- ⚡ toggleActions 'play none none reverse' avoids re-triggering on every scroll direction change

---

## Anti-Patterns (Do NOT Use)

- ❌ Complex onboarding
- ❌ Slow performance

### Additional Forbidden Patterns

- ❌ **Emojis as icons** — Use SVG icons (Heroicons, Lucide, Simple Icons)
- ❌ **Missing cursor:pointer** — All clickable elements must have cursor:pointer
- ❌ **Layout-shifting hovers** — Avoid scale transforms that shift layout
- ❌ **Low contrast text** — Maintain 4.5:1 minimum contrast ratio
- ❌ **Instant state changes** — Always use transitions (150-300ms)
- ❌ **Invisible focus states** — Focus states must be visible for a11y

---

## Pre-Delivery Checklist

Before delivering any UI code, verify:

- [ ] No emojis used as icons (use SVG instead)
- [ ] All icons from consistent icon set (Heroicons/Lucide)
- [ ] `cursor-pointer` on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard navigation
- [ ] `prefers-reduced-motion` respected
- [ ] Responsive: 375px, 768px, 1024px, 1440px
- [ ] No content hidden behind fixed navbars
- [ ] No horizontal scroll on mobile

---

## Decisiones del orquestador (prevalecen sobre todo lo anterior)

Fecha: 2026-11-14. Orden de precedencia: `safety.md` y `product.md` → `accessibility.md` → requisitos de la spec → este archivo. Si algo de arriba choca con `accessibility.md`, gana `accessibility.md`.

**Por qué se corrige la salida generada.** La base de datos no tiene una paleta "cálida, serena y capaz". Las búsquedas devolvieron paletas de salud y meditación (chocan con SF-01: el producto no es terapia ni debe parecerlo) o de productos infantiles (chocan con la dirección: nunca infantilizar). Se conserva la estructura verificada (Minimalism & Swiss, densidad espaciosa, movimiento sutil) y se reemplazan paleta, tipografía, patrón y efectos.

### Dirección `[SUPUESTO]`

Cálido, sereno y capaz. Transmite dignidad y competencia, nunca lástima ni infantilización. Es una herramienta de trabajo profesional.

### Paleta clara `[SUPUESTO]` (contraste medido sobre el fondo)

| Rol | Hex | Contraste |
| --- | --- | --- |
| Fondo | `#FAF7F2` (hueso cálido) | — |
| Texto | `#1F1B16` | 16.0:1 |
| Texto secundario | `#57534E` | 7.1:1 |
| Primario (arcilla) | `#9A3412` | 6.8:1 sobre fondo; texto blanco encima 7.3:1 |
| Acento (salvia oscura) | `#3F6212` | texto blanco encima 7.1:1 |
| Borde de componente | `#8A8178` | 3.6:1 (≥ 3:1, 1.4.11) |
| Anillo de foco | `#1D4ED8` | 6.3:1, 3 px, nunca se quita |
| Alto | `#B91C1C` con texto blanco | 6.5:1 |

### Alto contraste `[SUPUESTO]`

Fondo `#000000`, texto `#FFFFFF` (21:1), primario `#FFD166` (14.6:1). Bordes de 2 px en todos los controles.

### Tipografía `[SUPUESTO]`

Atkinson Hyperlegible (Braille Institute, SIL OFL) para todo, con pesos 400 y 700. Diseñada para baja visión; distingue bien caracteres parecidos. **Autoalojada en el paquete**, sin Google Fonts CDN: el companion funciona sin conexión y no se hacen peticiones a terceros. Base 18 px, interlineado 1.5, escalable al 200% sin pérdida.

### Tamaños y espacio

Objetivos de 44 px como mínimo (piso no configurable, REQ-00-040) y 64 px en modo cabeza `[SUPUESTO]`. Separación mínima de 16 px entre objetivos adyacentes `[SUPUESTO]`.

### Movimiento

Solo transiciones de opacidad de 150 ms o menos, y ninguna con `prefers-reduced-motion: reduce`. **Se descarta el "scroll reveal" con GSAP** de la salida generada: el contenido nunca empieza invisible y no se agrega GSAP como dependencia.

### Patrón

Se descarta "Product Demo + Features" (es de landing). La app sigue el modo **Operate** de Impeccable: una acción principal por pantalla (AX-13), barra de Alto y Deshacer siempre visible (AX-05) y estados obligatorios (AX-11).

### Lista previa a entregar: correcciones

- `cursor-pointer` y estados hover son opcionales: **nunca** son la única señal (AX-02, REQ-00-048).
- Sin emojis como iconos. Todo icono va con etiqueta visible: no hay botones de solo icono (AX-06).
- Sin logo ni ilustraciones inventadas: se usan marcadores hasta que el operador entregue los assets.
