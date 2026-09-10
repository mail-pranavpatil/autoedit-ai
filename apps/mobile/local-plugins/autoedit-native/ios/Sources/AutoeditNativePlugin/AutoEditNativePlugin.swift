import AuthenticationServices
import Capacitor
import Foundation
import UIKit
import WebKit

/// Native glue for the AutoEdit AI WebView shell.
///
/// A bare WKWebView can't do three things the web app needs:
///   1. Google OAuth — Google rejects its consent screen inside an embedded
///      webview ("disallowed_useragent"). Run it in ASWebAuthenticationSession
///      and inject the returned session token as the `autoedit_session` cookie.
///   2. File downloads — `GET /api/videos/{id}/download` sends
///      `Content-Disposition: attachment`; WKWebView just ignores it. Fetch it
///      with URLSession (carrying the cookie) and hand it to a share sheet.
///   3. External links — YouTube watch URLs etc. should open in Safari, not
///      replace the app's webview.
///
/// Shipped as a local Capacitor plugin (`apps/mobile/local-plugins/autoedit-native`).
/// `npx cap sync ios` links it via CocoaPods, so it compiles as part of the App
/// with no manual Xcode step. Capacitor calls `shouldOverrideLoad` on every
/// registered plugin before each navigation; returning `true` cancels the
/// default load.
@objc(AutoEditNativePlugin)
public class AutoEditNativePlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "AutoEditNativePlugin"
    public let jsName = "AutoEditNative"
    public let pluginMethods: [CAPPluginMethod] = []

    /// Registrable domain of the deployment. Must match `server.url` in
    /// capacitor.config.js. EDIT ME.
    private static let appHost = "REPLACE-with-your-domain.example"
    private static let authScheme = "autoedit"
    private static let cookieName = "autoedit_session"

    private var appOrigin: String { "https://\(Self.appHost)" }

    private var authSession: ASWebAuthenticationSession?
    private let downloadQueue = DownloadQueue()

    // MARK: - Navigation interception

    override public func shouldOverrideLoad(_ navigationAction: WKNavigationAction) -> NSNumber? {
        guard let url = navigationAction.request.url else { return nil }

        // Google's own consent host, or our OAuth entry point (the web login
        // button navigates to /api/auth/google). Divert to the auth session.
        if url.host == "accounts.google.com" || url.path.hasPrefix("/api/auth/google") {
            startAuthSession()
            return true
        }

        // Finished-reel download: /api/videos/<id>/download
        if isDownloadPath(url.path) {
            downloadQueue.enqueue(url: url, cookie: sessionCookie())
            return true
        }

        // Anything off our origin over http(s) → system browser.
        if let scheme = url.scheme, scheme == "http" || scheme == "https",
           url.host != nil, url.host != Self.appHost {
            DispatchQueue.main.async { UIApplication.shared.open(url) }
            return true
        }

        return nil
    }

    private func isDownloadPath(_ path: String) -> Bool {
        path.range(of: #"^/api/videos/[^/]+/download$"#, options: .regularExpression) != nil
    }

    // MARK: - OAuth

    private func startAuthSession() {
        let authURL = URL(string: "\(appOrigin)/api/auth/google?platform=ios")!
        let session = ASWebAuthenticationSession(
            url: authURL,
            callbackURLScheme: Self.authScheme
        ) { [weak self] callbackURL, error in
            guard let self else { return }
            self.authSession = nil
            guard error == nil, let callbackURL,
                  let token = URLComponents(url: callbackURL, resolvingAgainstBaseURL: false)?
                      .queryItems?.first(where: { $0.name == "token" })?.value,
                  !token.isEmpty
            else { return }
            self.injectSession(token: token)
        }
        session.presentationContextProvider = self
        session.prefersEphemeralWebBrowserSession = false
        self.authSession = session
        DispatchQueue.main.async { session.start() }
    }

    private func injectSession(token: String) {
        var props: [HTTPCookiePropertyKey: Any] = [
            .name: Self.cookieName,
            .value: token,
            .domain: Self.appHost,
            .path: "/",
            .secure: "TRUE",
            .expires: Date(timeIntervalSinceNow: 60 * 60 * 24 * 14),
        ]
        props[HTTPCookiePropertyKey("HttpOnly")] = "YES"
        guard let cookie = HTTPCookie(properties: props) else { return }

        DispatchQueue.main.async {
            guard let webView = self.bridge?.webView else { return }
            let store = webView.configuration.websiteDataStore.httpCookieStore
            store.setCookie(cookie) {
                HTTPCookieStorage.shared.setCookie(cookie)
                webView.reload()
            }
        }
    }

    private func sessionCookie() -> HTTPCookie? {
        HTTPCookieStorage.shared.cookies?.first {
            $0.name == Self.cookieName && $0.domain.contains(Self.appHost)
        }
    }
}

// MARK: - ASWebAuthenticationSession presentation

extension AutoEditNativePlugin: ASWebAuthenticationPresentationContextProviding {
    public func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        DispatchQueue.main.sync {
            bridge?.viewController?.view.window
                ?? UIApplication.shared.windows.first { $0.isKeyWindow }
                ?? ASPresentationAnchor()
        }
    }
}

// MARK: - Serial download → share sheet

/// "Download all ready videos" fires several `<a>` navigations back to back.
/// Run them one at a time so the user gets a single share sheet per file
/// instead of a stack.
private final class DownloadQueue: NSObject {
    private var pending: [(URL, HTTPCookie?)] = []
    private var running = false

    func enqueue(url: URL, cookie: HTTPCookie?) {
        pending.append((url, cookie))
        pump()
    }

    private func pump() {
        guard !running, !pending.isEmpty else { return }
        running = true
        let (url, cookie) = pending.removeFirst()

        var request = URLRequest(url: url)
        if let cookie {
            request.allHTTPHeaderFields = HTTPCookie.requestHeaderFields(with: [cookie])
        }

        let task = URLSession.shared.downloadTask(with: request) { [weak self] tempURL, response, _ in
            defer {
                self?.running = false
                DispatchQueue.main.async { self?.pump() }
            }
            guard let tempURL else { return }

            let name = Self.filename(from: response, fallback: url)
            let dest = FileManager.default.temporaryDirectory.appendingPathComponent(name)
            try? FileManager.default.removeItem(at: dest)
            do {
                try FileManager.default.moveItem(at: tempURL, to: dest)
            } catch {
                return
            }
            DispatchQueue.main.async { Self.present(dest) }
        }
        task.resume()
    }

    private static func filename(from response: URLResponse?, fallback: URL) -> String {
        if let http = response as? HTTPURLResponse,
           let disp = http.value(forHTTPHeaderField: "Content-Disposition"),
           let range = disp.range(of: #"filename="?([^"]+)"?"#, options: .regularExpression) {
            let raw = String(disp[range])
            if let eq = raw.firstIndex(of: "=") {
                return raw[raw.index(after: eq)...].trimmingCharacters(in: CharacterSet(charactersIn: "\" "))
            }
        }
        // /api/videos/<id>/download → "<id>-autoedit.mp4"
        let id = fallback.pathComponents.dropLast().last ?? "video"
        return "\(id)-autoedit.mp4"
    }

    private static func present(_ fileURL: URL) {
        guard let root = UIApplication.shared.windows.first(where: { $0.isKeyWindow })?.rootViewController else { return }
        var top = root
        while let presented = top.presentedViewController { top = presented }
        let sheet = UIActivityViewController(activityItems: [fileURL], applicationActivities: nil)
        sheet.popoverPresentationController?.sourceView = top.view
        sheet.popoverPresentationController?.sourceRect = CGRect(
            x: top.view.bounds.midX, y: top.view.bounds.midY, width: 0, height: 0
        )
        top.present(sheet, animated: true)
    }
}
