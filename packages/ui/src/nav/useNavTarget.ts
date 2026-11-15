import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useId,
  useLayoutEffect,
  useMemo,
  useRef,
} from "react";
import type { ReactNode, Ref } from "react";
import { NavTargetRegistry, navTargetRegistry } from "./NavTargetRegistry.ts";
import type { NavTargetMeasure } from "./NavTargetRegistry.ts";

const NavTargetContext = createContext<{
  registry: NavTargetRegistry;
  measure?: NavTargetMeasure;
}>({ registry: navTargetRegistry });

export interface NavTargetProviderProps {
  children: ReactNode;
  registry?: NavTargetRegistry;
  /** Tests supply geometry here because jsdom does not perform layout. */
  measure?: NavTargetMeasure;
}

export function NavTargetProvider({ children, registry, measure }: NavTargetProviderProps) {
  const ownedRegistry = useMemo(() => new NavTargetRegistry(), []);
  const value = useMemo(
    () => ({ registry: registry ?? ownedRegistry, measure }),
    [registry, ownedRegistry, measure],
  );
  return createElement(NavTargetContext.Provider, { value }, children);
}

/** Returns a ref to put on the control; a consumer `ref` is merged in, never replaced. */
export function useNavTarget<T extends HTMLElement>({
  id,
  role,
  ref: consumerRef,
}: {
  id?: string;
  role: string;
  ref?: Ref<T>;
}) {
  const generatedId = useId();
  const targetId = id || generatedId;
  const inner = useRef<T | null>(null);
  const { registry, measure } = useContext(NavTargetContext);
  const merged = useCallback(
    (node: T | null) => {
      inner.current = node;
      const cleanup = typeof consumerRef === "function" ? consumerRef(node) : undefined;
      if (consumerRef && typeof consumerRef === "object") consumerRef.current = node;
      return () => {
        inner.current = null;
        if (typeof cleanup === "function") cleanup();
        else if (typeof consumerRef === "function") consumerRef(null);
        else if (consumerRef) consumerRef.current = null;
      };
    },
    [consumerRef],
  );
  useLayoutEffect(() => {
    if (inner.current) return registry.register(targetId, inner.current, role, measure);
  }, [registry, targetId, role, measure]);
  useLayoutEffect(() => {
    registry.refresh();
  });
  return merged;
}
