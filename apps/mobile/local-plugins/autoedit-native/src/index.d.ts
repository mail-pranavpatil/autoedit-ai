// Native-only plugin — no callable JS methods. Behaviour is entirely in the
// iOS `shouldOverrideLoad` hook (OAuth intercept, download → share sheet,
// external links, session-cookie injection).
export interface AutoEditNativePlugin {}

export declare const AutoEditNative: AutoEditNativePlugin;
