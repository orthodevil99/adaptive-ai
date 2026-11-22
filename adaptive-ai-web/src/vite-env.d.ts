/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_API_KEY?: string;
  readonly VITE_APP_ENV?: string;
  readonly VITE_REQUEST_TIMEOUT_MS?: string;
  readonly VITE_MAX_MESSAGE_LENGTH?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
