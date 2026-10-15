import js from "@eslint/js";
import tseslint from "typescript-eslint";
export default tseslint.config(
  { ignores: ["**/dist/**", "packages/contracts/generated/**"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  { files: ["**/*.ts", "**/*.tsx"], languageOptions: { globals: { console: "readonly", process: "readonly", Buffer: "readonly", fetch: "readonly", setTimeout: "readonly", clearTimeout: "readonly", setInterval: "readonly", clearInterval: "readonly", AbortController: "readonly", AbortSignal: "readonly", TextDecoder: "readonly", document: "readonly", URL: "readonly", Blob: "readonly" } } },
);
