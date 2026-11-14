import assert from "node:assert/strict";
import { test } from "node:test";
import {
  defaultTheme,
  highContrast,
  reducedMotion,
  defineTheme,
  color,
  space,
  font,
  motion,
  target,
  type Theme,
  contrastRatio,
  relativeLuminance,
  toCssVariables,
} from "../src/index.ts";

test("binding design values and spacious scale", () => {
  assert.deepEqual(defaultTheme.color, {
    background: "#FAF7F2",
    foreground: "#1F1B16",
    secondaryText: "#57534E",
    primary: "#9A3412",
    onPrimary: "#FFFFFF",
    accent: "#3F6212",
    onAccent: "#FFFFFF",
    border: "#8A8178",
    ring: "#1D4ED8",
    stop: "#B91C1C",
    onStop: "#FFFFFF",
  });
  assert.deepEqual(defaultTheme.target, { min: 44, head: 64, gap: 16 });
  assert.deepEqual(defaultTheme.space, {
    xs: 4,
    sm: 8,
    md: 24,
    lg: 32,
    xl: 48,
    "2xl": 64,
    "3xl": 96,
  });
  assert.match(defaultTheme.font.family, /^"Atkinson Hyperlegible",.*system-ui/);
  assert.equal(defaultTheme.font.base, 18);
  assert.equal(defaultTheme.font.lineHeight, 1.5);
  assert.equal(defaultTheme.font.regular, 400);
  assert.equal(defaultTheme.font.bold, 700);
  assert.equal(defaultTheme.ring.width, 3);
  assert.equal(highContrast.color.background, "#000000");
  assert.equal(highContrast.color.foreground, "#FFFFFF");
  assert.equal(highContrast.color.primary, "#FFD166");
  assert.equal(highContrast.border.width, 2);
});

test("target floor enforced for dynamic input and literals", () => {
  for (const value of [0, 24, 43, 43.99, -1, NaN, Infinity]) {
    for (const key of ["min", "head"] as const) {
      assert.throws(
        () => defineTheme({ ...defaultTheme, target: { ...defaultTheme.target, [key]: value } }),
        /target/,
      );
    }
  }
  assert.equal(
    defineTheme({ ...defaultTheme, target: { min: 44.5, head: 100, gap: 16 } }).target.min,
    44.5,
  );
  assert.throws(() => {
    // @ts-expect-error literal below the target floor
    defineTheme({ ...defaultTheme, target: { min: 43, head: 64, gap: 16 } });
  });
  assert.throws(() => {
    // @ts-expect-error fractional literal below the head target floor
    defineTheme({ ...defaultTheme, target: { min: 44, head: 43.9, gap: 16 } });
  });
  assert.throws(() => {
    // @ts-expect-error negative literal target
    defineTheme({ ...defaultTheme, target: { min: -44, head: 64, gap: 16 } });
  });
});

test("WCAG reference values, symmetry and invalid input", () => {
  assert.equal(relativeLuminance("#000000"), 0);
  assert.equal(relativeLuminance("#FFFFFF"), 1);
  assert.equal(contrastRatio("#000000", "#FFFFFF"), 21);
  assert.equal(contrastRatio("#123456", "#123456"), 1);
  assert.ok(Math.abs(relativeLuminance("#808080") - 0.2158605001) < 1e-9);
  assert.ok(Math.abs(relativeLuminance("#0A0A0A") - 0.0030352698) < 1e-9);
  assert.equal(contrastRatio("#abcdef", "#123456"), contrastRatio("#123456", "#abcdef"));
  assert.throws(() => relativeLuminance("not a color"), /hex/i);
});

for (const [name, theme] of Object.entries({ defaultTheme, highContrast })) {
  test(`${name}: every semantic text and component pair meets WCAG`, () => {
    const c = theme.color;
    for (const [fg, bg] of [
      [c.foreground, c.background],
      [c.secondaryText, c.background],
      [c.onPrimary, c.primary],
      [c.onAccent, c.accent],
      [c.onStop, c.stop],
    ] as const) {
      assert.ok(contrastRatio(fg, bg) >= 4.5, `${fg}/${bg}`);
    }
    for (const component of [c.border, c.ring, c.primary, c.accent, c.stop]) {
      assert.ok(contrastRatio(component, c.background) >= 3, component);
    }
  });
}

test("text scaling, motion validation and generated CSS preferences", () => {
  assert.equal(defaultTheme.motion.property, "opacity");
  assert.ok(defaultTheme.motion.duration <= 150);
  assert.equal(reducedMotion.motion.duration, 0);
  for (const textScale of [1, 1.5, 2]) {
    const css = toCssVariables(defineTheme({ ...defaultTheme, textScale }));
    assert.ok(css.includes(`--text-scale: ${textScale};`));
    assert.ok(css.includes("--font-base: calc(1.125rem * var(--text-scale));"));
    assert.ok(css.includes("--target-min: 44px;"));
    assert.ok(css.includes("--color-background: #FAF7F2;"));
    assert.match(css, /@media \(prefers-reduced-motion: reduce\)[\s\S]*--motion-duration: 0ms;/);
  }
  for (const textScale of [0.9, 2.1, NaN, Infinity]) {
    assert.throws(() => defineTheme({ ...defaultTheme, textScale }), /textScale/);
  }
  for (const duration of [-1, 151, NaN, Infinity]) {
    assert.throws(
      () => defineTheme({ ...defaultTheme, motion: { property: "opacity", duration } }),
      /motion/,
    );
  }
  assert.match(toCssVariables(highContrast), /--border-width: 2px;/);
  assert.match(toCssVariables(reducedMotion), /--motion-duration: 0ms;/);
});

test("target.gap must be finite and at least 16", () => {
  for (const gap of [0, 15.99, -1, NaN, Infinity]) {
    assert.throws(
      () => defineTheme({ ...defaultTheme, target: { ...defaultTheme.target, gap } }),
      /target\.gap/,
    );
  }
  assert.equal(
    defineTheme({ ...defaultTheme, target: { min: 44, head: 64, gap: 20 } }).target.gap,
    20,
  );
});

test("base tokens and exported themes are deeply frozen (REQ-00-040 floor cannot be lowered)", () => {
  for (const tokens of [color, space, font, motion, target]) assert.ok(Object.isFrozen(tokens));
  for (const theme of [defaultTheme, highContrast, reducedMotion]) {
    assert.ok(Object.isFrozen(theme));
    for (const section of [
      theme.color,
      theme.space,
      theme.font,
      theme.motion,
      theme.target,
      theme.border,
      theme.ring,
    ]) {
      assert.ok(Object.isFrozen(section));
    }
  }
  // ESM is strict mode: writes to frozen objects throw instead of failing silently.
  assert.throws(() => {
    (defaultTheme.target as { min: number }).min = 10;
  }, TypeError);
  assert.throws(() => {
    (target as { min: number }).min = 10;
  }, TypeError);
  assert.throws(() => {
    (highContrast.target as { min: number }).min = 10;
  }, TypeError);
  assert.equal(defaultTheme.target.min, 44);
  assert.equal(reducedMotion.target.min, 44);
});

test("defineTheme returns a frozen clone, not the caller's object", () => {
  const input = {
    ...defaultTheme,
    target: { min: 44, head: 64, gap: 16 },
    color: { ...defaultTheme.color },
  };
  const theme = defineTheme(input);
  assert.notEqual(theme, input);
  assert.notEqual(theme.target, input.target);
  assert.ok(
    Object.isFrozen(theme) && Object.isFrozen(theme.target) && Object.isFrozen(theme.color),
  );
  (input.target as { min: number }).min = 10; // input remains the caller's to mutate...
  assert.equal(theme.target.min, 44); // ...but never affects the validated theme
});

test("toCssVariables accepts only themes validated by defineTheme", () => {
  const plain: Theme = { ...defaultTheme, target: { min: 10, head: 64, gap: 16 } };
  // @ts-expect-error an unvalidated structural Theme is not a ValidatedTheme
  assert.throws(() => toCssVariables(plain), /validated|defineTheme/i);
  const forged = { ...defaultTheme, target: { min: 10, head: 64, gap: 16 } };
  assert.throws(() => toCssVariables(forged), /validated|defineTheme/i);
});
