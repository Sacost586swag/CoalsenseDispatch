/** WCAG sRGB relative luminance for opaque six-digit hex colors. */
export function relativeLuminance(hex: string): number {
  if (!/^#[0-9a-f]{6}$/i.test(hex)) throw new TypeError("Expected a six-digit hex color");
  const linear = (offset: number): number => {
    const channel = Number.parseInt(hex.slice(offset, offset + 2), 16) / 255;
    return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * linear(1) + 0.7152 * linear(3) + 0.0722 * linear(5);
}

export function contrastRatio(first: string, second: string): number {
  const a = relativeLuminance(first);
  const b = relativeLuminance(second);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}
