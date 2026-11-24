import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  {
    ignores: [
      "**/dist/**",
      "**/.next/**",
      "**/catalog-dist/**",
      "**/test-results/**",
      "**/playwright-report/**",
      "**/node_modules/**",
      "**/.venv/**",
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.strict,
);
