import type { HTMLAttributes, ReactNode } from "react";

export interface NumberedListProps extends Omit<HTMLAttributes<HTMLOListElement>, "children"> {
  items: readonly { key: string; content: ReactNode }[];
}

/**
 * Items carry a large, always visible number so the person can say or target "3".
 * role="list" is explicit because list-style: none drops list semantics in some browsers.
 */
export function NumberedList({ items, className, ...rest }: NumberedListProps) {
  return (
    <ol {...rest} role="list" className={["cs-numbered-list", className].filter(Boolean).join(" ")}>
      {items.map((item, index) => (
        <li key={item.key} className="cs-numbered-list__item">
          <span className="cs-numbered-list__number" aria-hidden="true">
            {index + 1}
          </span>
          <div className="cs-numbered-list__content">{item.content}</div>
        </li>
      ))}
    </ol>
  );
}
