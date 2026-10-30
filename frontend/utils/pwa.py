"""Progressive Web App (PWA) and offline support utilities for agrimenya."""
import os
import shutil
import streamlit as st
import streamlit.components.v1 as components


def ensure_pwa_assets() -> None:
    """Synchronize PWA assets into static serving folders and Streamlit static root."""
    try:
        frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        root_dir = os.path.dirname(frontend_dir)
        src_static = os.path.join(frontend_dir, "static")

        # In Docker or container setups, frontend_dir is /app and root_dir is /
        # We must never write to /static at the OS root
        is_sys_root = (
            not root_dir
            or root_dir in ("/", "\\")
            or os.path.splitdrive(root_dir)[1] in ("", "/", "\\")
            or os.path.abspath(root_dir) == os.path.abspath(os.sep)
        )

        files_to_sync = [
            "manifest.json",
            "sw.js",
            "offline.html",
            "icon-192.png",
            "icon-512.png",
            "icon-maskable-512.png",
            "apple-touch-icon.png",
            "favicon.png",
            "wheat.svg",
            "ai_assistant_bulb.png",
        ]

        if not is_sys_root:
            root_static = os.path.join(root_dir, "static")
            try:
                os.makedirs(root_static, exist_ok=True)
                if os.path.isdir(src_static):
                    for fname in files_to_sync:
                        s_file = os.path.join(src_static, fname)
                        if os.path.exists(s_file):
                            r_file = os.path.join(root_static, fname)
                            if not os.path.exists(r_file):
                                try:
                                    shutil.copy2(s_file, r_file)
                                except Exception:
                                    pass
            except (PermissionError, OSError):
                pass

        # Attempt to sync into Streamlit's core static folder for root /sw.js and /manifest.json serving
        try:
            from streamlit import file_util
            pkg_static = file_util.get_static_dir()
            if os.path.isdir(pkg_static) and os.path.isdir(src_static):
                for fname in files_to_sync:
                    s_file = os.path.join(src_static, fname)
                    if os.path.exists(s_file):
                        pkg_file = os.path.join(pkg_static, fname)
                        if not os.path.exists(pkg_file):
                            try:
                                shutil.copy2(s_file, pkg_file)
                            except Exception:
                                pass
        except Exception:
            pass
    except Exception:
        # Never crash navbar or app if asset synchronization encounters permission or filesystem limits
        pass


def render_pwa_support() -> None:
    """Inject PWA metadata, service worker, offline state, and error screens."""
    ensure_pwa_assets()

    pwa_script = """
    <script>
    (function initAgrimenyaPWA() {
      try {
        const parentDoc = window.parent.document;
        if (!parentDoc) return;

        // Remove persistent loaders from earlier app versions. Loading UI is
        // reserved for explicit actions that are actually fetching data.
        ['ag-top-progress', 'ag-page-loader'].forEach(id => {
          const staleLoader = parentDoc.getElementById(id);
          if (staleLoader) staleLoader.remove();
        });

        // Cleanup any stale background video elements
        try {
          const staleVideo = parentDoc.getElementById('ag-landing-fullpage-video');
          if (staleVideo) staleVideo.remove();
          const staleOverlay = parentDoc.getElementById('ag-landing-fullpage-overlay');
          if (staleOverlay) staleOverlay.remove();
        } catch (_) {}

        // 1. Inject or update Web App Manifest
        let manifest = parentDoc.querySelector('link[rel="manifest"]');
        if (!manifest) {
          manifest = parentDoc.createElement('link');
          manifest.rel = 'manifest';
          manifest.href = '/app/static/manifest.json';
          parentDoc.head.appendChild(manifest);
        }

        // 2. Inject mobile & iOS meta tags
        const metaTags = [
          { name: 'theme-color', content: '#05303f' },
          { name: 'mobile-web-app-capable', content: 'yes' },
          { name: 'apple-mobile-web-app-capable', content: 'yes' },
          { name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' },
          { name: 'apple-mobile-web-app-title', content: 'agrimenya' },
          { name: 'application-name', content: 'agrimenya' }
        ];

        metaTags.forEach(meta => {
          let el = parentDoc.querySelector(`meta[name="${meta.name}"]`);
          if (!el) {
            el = parentDoc.createElement('meta');
            el.name = meta.name;
            el.content = meta.content;
            parentDoc.head.appendChild(el);
          }
        });

        // 3. Inject Apple Touch Icon
        let appleIcon = parentDoc.querySelector('link[rel="apple-touch-icon"]');
        if (!appleIcon) {
          appleIcon = parentDoc.createElement('link');
          appleIcon.rel = 'apple-touch-icon';
          appleIcon.href = '/app/static/apple-touch-icon.png';
          parentDoc.head.appendChild(appleIcon);
        }

        // 4. Inject Dynamic Global Styles for Modals and Animations
        if (!parentDoc.getElementById('ag-dynamic-runtime-styles')) {
          const styleEl = parentDoc.createElement('style');
          styleEl.id = 'ag-dynamic-runtime-styles';
          styleEl.textContent = `
            @keyframes agFadeInUp {
              from { opacity: 0; transform: translateY(16px); }
              to { opacity: 1; transform: translateY(0); }
            }
            @keyframes agPulseDot {
              0%, 100% { opacity: 1; transform: scale(1); }
              50% { opacity: 0.35; transform: scale(0.85); }
            }
            /* Permanently suppress native header, sidebar, and toolbar on client */
            header[data-testid="stHeader"],
            .stApp > header,
            [data-testid="stHeader"] {
              display: none !important;
              height: 0 !important;
              min-height: 0 !important;
              padding: 0 !important;
              margin: 0 !important;
              visibility: hidden !important;
            }
            .block-container,
            [data-testid="stMainBlockContainer"],
            [data-testid="stAppViewBlockContainer"],
            .main .block-container {
              padding-top: 0.35rem !important;
              margin-top: 0 !important;
            }
            .st-key-ag_navbar {
              position: sticky !important;
              top: 0.35rem !important;
              z-index: 999990 !important;
              margin: 0 auto 0.45rem auto !important;
            }
            /* Ensure NO black background on navbar buttons, popovers, or tabs */
            .st-key-ag_navbar button,
            .st-key-ag_navbar [data-testid="stHorizontalBlock"] button,
            .st-key-ag_navbar [data-testid="stHorizontalBlock"] .stPopover > button,
            .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button,
            [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) button,
            [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) .stPopover > button,
            [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) [data-testid="stPopover"] button,
            [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) [data-testid="stBaseButton-secondary"] {
              background: transparent !important;
              background-color: transparent !important;
              border: none !important;
              color: #0a1f26 !important;
              box-shadow: none !important;
            }
            .st-key-ag_navbar [data-testid="stHorizontalBlock"] button p,
            .st-key-ag_navbar [data-testid="stHorizontalBlock"] .stPopover > button p,
            .st-key-ag_navbar [data-testid="stHorizontalBlock"] [data-testid="stPopover"] button p,
            [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) button p,
            [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) .stPopover > button p {
              color: #0a1f26 !important;
              text-shadow: none !important;
            }
            .st-key-ag_navbar .st-key-lang_cycle_btn button,
            .st-key-ag_navbar [data-testid="stHorizontalBlock"] .st-key-lang_cycle_btn button,
            [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) .st-key-lang_cycle_btn button,
            [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) [data-testid="column"]:last-child button,
            [data-testid="stHorizontalBlock"]:has(.st-key-lang_cycle_btn) [data-testid="stColumn"]:last-child button {
              background: transparent !important;
              background-color: transparent !important;
              border: none !important;
              border-radius: 50% !important;
              box-shadow: none !important;
            }
            /* Universal light styling for Streamlit tabs (st.tabs) */
            [data-testid="stTabs"] button[role="tab"],
            [data-testid="stTabs"] [data-baseweb="tab"],
            [data-testid="stTabs"] button,
            .stTabs button[role="tab"],
            .stTabs [data-baseweb="tab"],
            .stTabs button,
            [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stTabs"] button {
              background: transparent !important;
              background-color: transparent !important;
              border: none !important;
              color: #334155 !important;
              box-shadow: none !important;
            }
            [data-testid="stTabs"] button[role="tab"][aria-selected="true"],
            [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"],
            .stTabs button[role="tab"][aria-selected="true"] {
              background: #ffffff !important;
              background-color: #ffffff !important;
              color: #0284c7 !important;
              border-bottom: 2.5px solid #0284c7 !important;
            }
            [data-testid="stSidebar"],
            [data-testid="collapsedControl"],
            section[data-testid="stSidebar"],
            aside[data-testid="stSidebar"],
            [data-testid="stSidebarNav"],
            [data-testid="stSidebarNavItems"] {
              display: none !important;
              width: 0 !important;
              max-width: 0 !important;
              min-width: 0 !important;
              visibility: hidden !important;
              pointer-events: none !important;
            }
            [data-testid="stDeployButton"],
            button[data-testid="stDeployButton"],
            button[data-testid="stToolbarActions"],
            [data-testid="stToolbar"] {
              display: none !important;
            }
            /* Style Streamlit native connection status dialogs */
            div[data-testid="stConnectionStatus"],
            .stConnectionStatus {
              border-radius: 16px !important;
              background: #021824 !important;
              border: 1px solid rgba(56, 189, 248, 0.35) !important;
              box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6) !important;
              color: #f0fdf4 !important;
            }
            /* Persistent non-animated AI bulb styles */
            .ag-floating-ai-fab {
              position: fixed !important;
              bottom: 24px !important;
              right: 24px !important;
              width: 72px !important;
              height: 104px !important;
              z-index: 9999999 !important;
              display: flex !important;
              align-items: center !important;
              justify-content: center !important;
              background: transparent !important;
              border: none !important;
              box-shadow: none !important;
              padding: 0 !important;
              cursor: pointer !important;
              animation: none !important;
              text-decoration: none !important;
            }
            .ag-floating-ai-fab img {
              width: 58px !important;
              height: auto !important;
              max-height: 92px !important;
              object-fit: contain !important;
              animation: none !important;
              filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.75))
                      drop-shadow(0 4px 12px rgba(0, 0, 0, 0.3)) !important;
            }
          `;
          parentDoc.head.appendChild(styleEl);
        }

        // 5. Register Service Worker with fallback
        if ('serviceWorker' in window.parent.navigator) {
          const swUrl = '/sw.js';
          const fallbackSwUrl = '/app/static/sw.js';

          window.parent.navigator.serviceWorker.register(swUrl, { scope: '/' })
            .then(reg => {
              console.log('[PWA] ServiceWorker registered with scope:', reg.scope);
            })
            .catch(err => {
              window.parent.navigator.serviceWorker.register(fallbackSwUrl)
                .then(reg => {
                  console.log('[PWA] Fallback ServiceWorker registered with scope:', reg.scope);
                })
                .catch(fallbackErr => {
                  console.warn('[PWA] ServiceWorker registration notice:', fallbackErr);
                });
            });
        }

        // 6. CUSTOMIZED DESIGNED NETWORK LOST (OFFLINE) SCREEN
        let offlineScreen = parentDoc.getElementById('ag-network-lost-screen');
        if (!offlineScreen) {
          offlineScreen = parentDoc.createElement('div');
          offlineScreen.id = 'ag-network-lost-screen';
          offlineScreen.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(2,24,36,0.92);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);z-index:9999998;display:none;align-items:center;justify-content:center;padding:1.5rem;animation:agFadeInUp 0.35s ease;';
          offlineScreen.innerHTML = `
            <div style="max-width:540px;width:100%;background:#031d2b;border:1px solid rgba(245,158,11,0.45);border-radius:24px;padding:2.2rem;box-shadow:0 24px 64px rgba(0,0,0,0.7),0 0 32px rgba(245,158,11,0.15);text-align:center;display:flex;flex-direction:column;align-items:center;">
              <div style="position:relative;margin-bottom:1.25rem;">
                <img src="/app/static/ai_assistant_bulb.png" alt="agrimenya" style="width:76px;height:76px;filter:drop-shadow(0 0 20px rgba(245,158,11,0.55));">
              </div>
              <div id="ag-offline-beacon" style="display:inline-flex;align-items:center;gap:0.5rem;padding:0.35rem 0.95rem;border-radius:9999px;background:rgba(245,158,11,0.14);border:1px solid rgba(245,158,11,0.45);color:#fbbf24;font-size:0.82rem;font-weight:700;margin-bottom:1rem;">
                <span style="width:8px;height:8px;border-radius:50%;background:#fbbf24;box-shadow:0 0 8px #fbbf24;animation:agPulseDot 1.8s infinite;"></span>
                <span id="ag-offline-beacon-text">Network Connection Interrupted</span>
              </div>
              <h2 id="ag-offline-title" style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.6rem;font-weight:800;color:#f0fdf4;letter-spacing:-0.02em;margin:0 0 0.6rem 0;">You Are Currently Offline</h2>
              <p id="ag-offline-desc" style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.92rem;color:#94a3b8;line-height:1.55;margin:0 0 1.8rem 0;">
                Live connection to the agrimenya server was interrupted. Cached Rwanda district baselines, seasonal crop calendars, and emergency field tools remain ready.
              </p>
              <div style="display:flex;flex-direction:column;gap:0.75rem;width:100%;">
                <a href="/app/static/offline.html" target="_self" style="display:flex;align-items:center;justify-content:center;gap:0.55rem;padding:0.75rem 1.4rem;border-radius:12px;background:linear-gradient(135deg, #10b981 0%, #059669 100%);color:#ffffff;text-decoration:none;font-weight:700;font-size:0.92rem;box-shadow:0 4px 16px rgba(16,185,129,0.35);transition:all 0.2s;">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path></svg>
                  <span>Open Offline Field Hub</span>
                </a>
                <button id="ag-btn-retry-offline" style="display:flex;align-items:center;justify-content:center;gap:0.55rem;padding:0.75rem 1.4rem;border-radius:12px;background:rgba(2,132,199,0.15);border:1.5px solid rgba(2,132,199,0.45);color:#38bdf8;font-weight:700;font-size:0.92rem;cursor:pointer;transition:all 0.2s;">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                  <span id="ag-retry-offline-text">Retry Live Connection</span>
                </button>
                <button id="ag-btn-dismiss-offline" style="background:transparent;border:none;color:#64748b;font-size:0.84rem;font-weight:600;padding:0.4rem;cursor:pointer;text-decoration:underline;">
                  Dismiss and keep viewing current screen
                </button>
              </div>
            </div>
          `;
          parentDoc.body.appendChild(offlineScreen);

          // Wire Retry Action
          parentDoc.getElementById('ag-btn-retry-offline').addEventListener('click', () => {
            const btnText = parentDoc.getElementById('ag-retry-offline-text');
            btnText.textContent = 'Testing connection...';
            fetch('/_stcore/health', { cache: 'no-store' })
              .then(res => {
                if (res.ok) {
                  btnText.textContent = 'Reconnected! Reloading...';
                  setTimeout(() => window.parent.location.reload(), 400);
                } else {
                  btnText.textContent = 'Server not reachable yet. Try again';
                }
              })
              .catch(() => {
                btnText.textContent = 'Still offline. Check network';
                setTimeout(() => { btnText.textContent = 'Retry Live Connection'; }, 2200);
              });
          });

          // Wire Dismiss Action
          parentDoc.getElementById('ag-btn-dismiss-offline').addEventListener('click', () => {
            offlineScreen.style.display = 'none';
          });
        }

        function handleNetworkChange(isOnline) {
          if (!offlineScreen) return;
          if (!isOnline) {
            offlineScreen.style.display = 'flex';
            const beacon = parentDoc.getElementById('ag-offline-beacon');
            const beaconText = parentDoc.getElementById('ag-offline-beacon-text');
            const title = parentDoc.getElementById('ag-offline-title');
            if (beacon) {
              beacon.style.background = 'rgba(245,158,11,0.14)';
              beacon.style.borderColor = 'rgba(245,158,11,0.45)';
              beacon.style.color = '#fbbf24';
            }
            if (beaconText) beaconText.textContent = 'Network Connection Interrupted';
            if (title) title.textContent = 'You Are Currently Offline';
          } else {
            const beacon = parentDoc.getElementById('ag-offline-beacon');
            const beaconText = parentDoc.getElementById('ag-offline-beacon-text');
            const title = parentDoc.getElementById('ag-offline-title');
            if (beacon) {
              beacon.style.background = 'rgba(16,185,129,0.18)';
              beacon.style.borderColor = 'rgba(16,185,129,0.45)';
              beacon.style.color = '#34d399';
            }
            if (beaconText) beaconText.textContent = 'Connection Restored';
            if (title) title.textContent = 'Back Online!';
            setTimeout(() => {
              offlineScreen.style.display = 'none';
            }, 1400);
          }
        }

        window.parent.addEventListener('offline', () => handleNetworkChange(false));
        window.parent.addEventListener('online', () => handleNetworkChange(true));
        if (!window.parent.navigator.onLine) {
          handleNetworkChange(false);
        }

        // 9. CUSTOMIZED UNUSUAL EVENT & RUNTIME ERROR RECOVERY SCREEN
        let unusualScreen = parentDoc.getElementById('ag-unusual-error-screen');
        if (!unusualScreen) {
          unusualScreen = parentDoc.createElement('div');
          unusualScreen.id = 'ag-unusual-error-screen';
          unusualScreen.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(2,24,36,0.92);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);z-index:9999997;display:none;align-items:center;justify-content:center;padding:1.5rem;animation:agFadeInUp 0.35s ease;';
          unusualScreen.innerHTML = `
            <div style="max-width:520px;width:100%;background:#031d2b;border:1px solid rgba(56,189,248,0.4);border-radius:24px;padding:2.2rem;box-shadow:0 24px 64px rgba(0,0,0,0.7),0 0 32px rgba(56,189,248,0.15);text-align:center;display:flex;flex-direction:column;align-items:center;">
              <div style="margin-bottom:1.2rem;">
                <img src="/app/static/ai_assistant_bulb.png" alt="agrimenya" style="width:72px;height:72px;filter:drop-shadow(0 0 20px rgba(56,189,248,0.55));">
              </div>
              <div style="display:inline-flex;align-items:center;gap:0.5rem;padding:0.35rem 0.95rem;border-radius:9999px;background:rgba(2,132,199,0.15);border:1px solid rgba(56,189,248,0.35);color:#38bdf8;font-size:0.82rem;font-weight:700;margin-bottom:1rem;">
                <span style="width:8px;height:8px;border-radius:50%;background:#38bdf8;box-shadow:0 0 8px #38bdf8;"></span>
                <span>System Stability Protection</span>
              </div>
              <h2 style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.55rem;font-weight:800;color:#f0fdf4;letter-spacing:-0.02em;margin:0 0 0.6rem 0;">agrimenya Interruption Detected</h2>
              <p id="ag-unusual-msg" style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.92rem;color:#94a3b8;line-height:1.55;margin:0 0 1.8rem 0;">
                An unexpected event was detected in the active session stream. Your cached records and local tools remain safe.
              </p>
              <div style="display:flex;flex-direction:column;gap:0.75rem;width:100%;">
                <button id="ag-btn-reload-unusual" style="display:flex;align-items:center;justify-content:center;gap:0.55rem;padding:0.75rem 1.4rem;border-radius:12px;background:linear-gradient(135deg, #0284c7 0%, #0369a1 100%);color:#ffffff;border:none;font-weight:700;font-size:0.92rem;cursor:pointer;box-shadow:0 4px 16px rgba(2,132,199,0.35);transition:all 0.2s;">
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
                  <span>Reload agrimenya</span>
                </button>
                <a href="/app/static/offline.html" target="_self" style="display:flex;align-items:center;justify-content:center;gap:0.55rem;padding:0.75rem 1.4rem;border-radius:12px;background:rgba(16,185,129,0.12);border:1.5px solid rgba(16,185,129,0.35);color:#34d399;text-decoration:none;font-weight:700;font-size:0.92rem;transition:all 0.2s;">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path></svg>
                  <span>Open Offline Field Hub</span>
                </a>
                <button id="ag-btn-dismiss-unusual" style="background:transparent;border:none;color:#64748b;font-size:0.84rem;font-weight:600;padding:0.4rem;cursor:pointer;text-decoration:underline;">
                  Continue active session
                </button>
              </div>
            </div>
          `;
          parentDoc.body.appendChild(unusualScreen);

          parentDoc.getElementById('ag-btn-reload-unusual').addEventListener('click', () => {
            window.parent.location.reload();
          });
          parentDoc.getElementById('ag-btn-dismiss-unusual').addEventListener('click', () => {
            unusualScreen.style.display = 'none';
          });
        }

        // Global Error Interceptor for Unusual Events
        window.parent.addEventListener('error', (event) => {
          if (event && event.message && (event.message.includes('WebSocket') || event.message.includes('disconnected') || event.message.includes('Failed to fetch'))) {
            if (unusualScreen && offlineScreen.style.display !== 'flex') {
              const msg = parentDoc.getElementById('ag-unusual-msg');
              if (msg) msg.textContent = 'Network or server stream encountered an unexpected disconnection. Please reload to resume live tracking.';
              unusualScreen.style.display = 'flex';
            }
          }
        });

        // 10. SYNCHRONIZE ACTIVE NAVBAR TAB HIGHLIGHT (#c8d7cc)
        function syncActiveNavbarTab() {
          try {
            const path = window.parent.location.pathname || '';
            const navLinks = parentDoc.querySelectorAll('.st-key-ag_navbar [data-testid="stPageLink"], .st-key-ag_navbar a');
            if (!navLinks || navLinks.length === 0) return;

            let isHome = path === '/' || path.endsWith('Home') || path === '' || path === '/Home';
            let isDashboard = path.includes('Dashboard') || path.includes('Overview');
            let isZones = path.includes('Zones');
            let isDecisions = path.includes('Decision');

            navLinks.forEach(link => {
              const href = (link.getAttribute('href') || link.querySelector('a')?.getAttribute('href') || '').toLowerCase();
              const text = (link.textContent || '').trim().toLowerCase();
              let shouldBeActive = false;

              if (isHome && (href === '/' || href === 'home' || href === 'home.py' || text === 'home' || text === 'ahabanza')) {
                shouldBeActive = true;
              } else if (isDashboard && (href.includes('dashboard') || text.includes('overview') || text.includes('incamake'))) {
                shouldBeActive = true;
              } else if (isZones && (href.includes('zones') || text.includes('zones') || text.includes('uduce'))) {
                shouldBeActive = true;
              } else if (isDecisions && (href.includes('decision') || text.includes('decision') || text.includes('ibyemezo'))) {
                shouldBeActive = true;
              }

              if (shouldBeActive) {
                link.classList.add('ag-nav-active');
                link.setAttribute('aria-current', 'page');
                const innerAnchor = link.tagName === 'A' ? link : link.querySelector('a');
                if (innerAnchor) {
                  innerAnchor.classList.add('ag-nav-active');
                  innerAnchor.setAttribute('aria-current', 'page');
                }
              } else {
                link.classList.remove('ag-nav-active');
                if (link.getAttribute('aria-current') === 'page' && !shouldBeActive && (isDashboard || isZones || isDecisions || isHome)) {
                  // Only remove if not the matched target
                  link.removeAttribute('aria-current');
                }
                const innerAnchor = link.tagName === 'A' ? link : link.querySelector('a');
                if (innerAnchor && !shouldBeActive) {
                  innerAnchor.classList.remove('ag-nav-active');
                }
              }
            });
          } catch (syncErr) {
            console.debug('Navbar tab sync note:', syncErr);
          }
        }

        // Run tab sync on load and monitor mutations
        setTimeout(syncActiveNavbarTab, 100);
        setTimeout(syncActiveNavbarTab, 400);
        setTimeout(syncActiveNavbarTab, 900);

        // 11. Custom Install App button and modal themed to the agrimenya logo
        window.parent.addEventListener('beforeinstallprompt', (e) => {
          e.preventDefault();
          window.parent.__agrimenya_deferred_prompt = e;
        });

        // Global install trigger function
        window.parent.__agrimenya_trigger_install = function() {
          if (window.parent.__agrimenya_deferred_prompt) {
            window.parent.__agrimenya_deferred_prompt.prompt();
            window.parent.__agrimenya_deferred_prompt.userChoice.then((choice) => {
              if (choice.outcome === 'accepted') {
                const btn = parentDoc.getElementById('ag-pwa-install-badge');
                if (btn) btn.style.display = 'none';
              }
              window.parent.__agrimenya_deferred_prompt = null;
            });
            return;
          }
          // If native prompt is not active, display the themed instructions modal
          let modal = parentDoc.getElementById('ag-install-modal');
          if (!modal) {
            modal = parentDoc.createElement('div');
            modal.id = 'ag-install-modal';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(3,29,42,0.85);backdrop-filter:blur(10px);z-index:99999999;display:flex;align-items:center;justify-content:center;padding:1.5rem;box-sizing:border-box;';
            modal.innerHTML = `
              <div style="background:#041f26;border:1.5px solid rgba(56,189,248,0.65);border-radius:20px;max-width:440px;width:100%;padding:2rem 1.8rem;box-shadow:0 24px 60px rgba(0,0,0,0.7), 0 0 30px rgba(56,189,248,0.35);color:#ffffff;font-family:\'Plus Jakarta Sans\',sans-serif;position:relative;text-align:center;">
                <button id="ag-modal-close" style="position:absolute;top:14px;right:16px;background:transparent;border:none;color:#94a3b8;font-size:1.5rem;cursor:pointer;line-height:1;padding:4px 8px;border-radius:6px;transition:color 0.2s;">&times;</button>
                <div style="display:flex;align-items:center;justify-content:center;margin-bottom:1rem;">
                  <img src="/app/static/ai_assistant_bulb.png" alt="agrimenya logo" style="width:58px;height:58px;object-fit:contain;filter:drop-shadow(0 0 16px rgba(56,189,248,0.85));">
                </div>
                <h3 style="margin:0 0 0.35rem 0;font-size:1.45rem;font-weight:800;letter-spacing:-0.02em;color:#ffffff;text-shadow:0 2px 10px rgba(0,0,0,0.5);">Install agrimenya</h3>
                <p style="color:#7dd3fc;font-size:0.86rem;margin:0 0 1.4rem 0;font-weight:600;">Fast offline field access &amp; instant satellite intelligence</p>
                <div style="text-align:left;background:#082736;border:1px solid rgba(56,189,248,0.25);border-radius:12px;padding:1rem;margin-bottom:1.4rem;font-size:0.85rem;line-height:1.55;color:#e0f2fe;">
                  <div style="margin-bottom:0.75rem;"><strong style="color:#38bdf8;display:block;margin-bottom:2px;">Desktop (Chrome, Edge):</strong> Click the install icon (&#8853;) in the address bar or browser menu &gt; <em>Install agrimenya</em>.</div>
                  <div style="margin-bottom:0.75rem;"><strong style="color:#4ade80;display:block;margin-bottom:2px;">iPhone &amp; iPad (Safari):</strong> Tap the <strong>Share</strong> button (&#9083;), scroll down and choose <strong>Add to Home Screen</strong>.</div>
                  <div><strong style="color:#f59e0b;display:block;margin-bottom:2px;">Android (Chrome):</strong> Tap the three-dot menu (&vellip;) and tap <strong>Install app</strong> or <strong>Add to Home screen</strong>.</div>
                </div>
                <button id="ag-modal-gotit" style="width:100%;padding:0.75rem;border-radius:10px;background:linear-gradient(135deg,#0284c7 0%,#0369a1 100%);border:1px solid rgba(56,189,248,0.8);color:#ffffff;font-size:0.92rem;font-weight:750;cursor:pointer;box-shadow:0 4px 16px rgba(14,165,233,0.4);transition:all 0.2s;">Got It</button>
              </div>
            `;
            parentDoc.body.appendChild(modal);
            const closeBtn = modal.querySelector('#ag-modal-close');
            const gotItBtn = modal.querySelector('#ag-modal-gotit');
            const closeModal = () => modal.remove();
            if (closeBtn) closeBtn.addEventListener('click', closeModal);
            if (gotItBtn) gotItBtn.addEventListener('click', closeModal);
            modal.addEventListener('click', (ev) => {
              if (ev.target === modal) closeModal();
            });
          }
        };

        // Unconditionally remove any floating App icon / install badge on the bottom left
        function purgeBottomLeftBadges() {
          try {
            const el = parentDoc.getElementById('ag-pwa-install-badge');
            if (el) el.remove();
            const bad = parentDoc.querySelectorAll('#ag-pwa-install-badge, [id*="pwa-install"], [class*="viewerBadge"], [data-testid="manage-app-button"]');
            bad.forEach(b => b.remove());
          } catch (_) {}
        }
        purgeBottomLeftBadges();
        setInterval(purgeBottomLeftBadges, 400);

        // 12. STRICT SAME-TAB NAVIGATION ENFORCEMENT
        // Ensure no links, buttons, or window.open calls ever open in a new tab
        (function enforceStrictSameTabNavigation() {
          try {
            function sanitizeLinks(root) {
              if (!root || !root.querySelectorAll) return;
              const blankLinks = root.querySelectorAll('a[target="_blank"], a[target="_BLANK"]');
              for (let i = 0; i < blankLinks.length; i++) {
                blankLinks[i].target = '_self';
              }
            }
            sanitizeLinks(parentDoc);
            sanitizeLinks(document);

            // Intercept all link clicks in capture phase on parent and iframe documents
            function interceptClicks(doc) {
              if (!doc || doc.__ag_same_tab_enforced) return;
              doc.__ag_same_tab_enforced = true;
              doc.addEventListener('click', function(e) {
                const anchor = e.target.closest('a');
                if (anchor) {
                  if (anchor.target === '_blank' || anchor.getAttribute('target') === '_blank') {
                    anchor.target = '_self';
                    anchor.removeAttribute('target');
                  }
                }
              }, true);
            }
            interceptClicks(parentDoc);
            interceptClicks(document);

            // MutationObserver to sanitize dynamically injected links (e.g. st.link_button)
            if (!parentDoc.__ag_same_tab_observer && parentDoc.body) {
              const obs = new MutationObserver(function(mutations) {
                for (let m = 0; m < mutations.length; m++) {
                  const nodes = mutations[m].addedNodes;
                  for (let n = 0; n < nodes.length; n++) {
                    const node = nodes[n];
                    if (node.nodeType === 1) {
                      if (node.tagName === 'A' && (node.target === '_blank' || node.getAttribute('target') === '_blank')) {
                        node.target = '_self';
                        node.removeAttribute('target');
                      }
                      sanitizeLinks(node);
                    }
                  }
                }
              });
              obs.observe(parentDoc.body, { childList: true, subtree: true });
              parentDoc.__ag_same_tab_observer = obs;
            }

            // Override window.open across both contexts
            const sameTabOpen = function(url) {
              if (url) {
                window.parent.location.href = url;
              }
              return window.parent;
            };
            try { window.open = sameTabOpen; } catch(_) {}
            try { if (window.parent) window.parent.open = sameTabOpen; } catch(_) {}
          } catch(sameTabErr) {
            console.debug('Same-tab navigation note:', sameTabErr);
          }
        })();

      } catch (err) {
        console.error('PWA initialization error:', err);
      }
    })();
    </script>
    """

    components.html(pwa_script, height=0)
