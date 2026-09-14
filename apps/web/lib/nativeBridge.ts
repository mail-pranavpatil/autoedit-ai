/** Bridge to the Eren iOS shell's native Photos/Files picker (see
 * apps/mobile/lib/webview_shell.dart). Only defined when running inside that
 * WebView — a plain browser never sees `window.ErenNative`. */
declare global {
  interface Window {
    ErenNative?: { postMessage: (message: string) => void };
    onErenNativeUpload?: (result: { id: string; filename: string; status: string } | { error: string } | null) => void;
  }
}

export function hasNativePicker() {
  return typeof window !== "undefined" && !!window.ErenNative;
}

export type NativeUploadResult = { id: string; filename: string; status: string } | { error: string } | null;

/** Resolves the uploaded video's server record, an {error} if the upload failed, or null if the user cancelled. */
export function pickNativeVideo(projectId: string, source: "photos" | "files"): Promise<NativeUploadResult> {
  return new Promise((resolve) => {
    if (!window.ErenNative) return resolve(null);
    window.onErenNativeUpload = (result) => {
      delete window.onErenNativeUpload;
      resolve(result ?? null);
    };
    window.ErenNative.postMessage(JSON.stringify({ type: "pickVideo", source, projectId }));
  });
}
