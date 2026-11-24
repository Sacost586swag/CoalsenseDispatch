/** Run in the browser (page.evaluate). Includes inactive controls: they must stay reachable. */
export function auditTargetSizes(minimum = 44) {
  const selector =
    'button,a[href],input:not([type="hidden"]),select,textarea,[role="button"],[role="link"],[tabindex]:not([tabindex="-1"])';
  return Array.from(document.querySelectorAll<HTMLElement>(selector)).flatMap((element) => {
    if (element.closest('[inert],[hidden],[aria-hidden="true"]')) return [];
    if (!element.checkVisibility({ visibilityProperty: true })) return [];
    const { width, height } = element.getBoundingClientRect();
    return width + 0.01 < minimum || height + 0.01 < minimum
      ? [{ tag: element.tagName, id: element.id, width, height, minimum }]
      : [];
  });
}
