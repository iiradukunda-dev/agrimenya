"""Progressive Web App (PWA) and offline support utilities for agrimenya."""
import os
import shutil
import streamlit as st
import streamlit.components.v1 as components


def ensure_pwa_assets() -> None:
    """Synchronize PWA assets into static serving folders and Streamlit static root."""
    frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_dir = os.path.dirname(frontend_dir)
    src_static = os.path.join(frontend_dir, "static")
    root_static = os.path.join(root_dir, "static")

    os.makedirs(root_static, exist_ok=True)

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

    for fname in files_to_sync:
        s_file = os.path.join(src_static, fname)
        if os.path.exists(s_file):
            r_file = os.path.join(root_static, fname)
            if not os.path.exists(r_file):
                try:
                    shutil.copy2(s_file, r_file)
                except Exception:
                    pass

    # Attempt to sync into Streamlit's core static folder for root /sw.js and /manifest.json serving
    try:
        from streamlit import file_util
        pkg_static = file_util.get_static_dir()
        if os.path.isdir(pkg_static):
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


def render_pwa_support() -> None:
    """Inject PWA manifest, service worker registration, install banner, and offline indicator."""
    ensure_pwa_assets()

    pwa_script = """
    <script>
    (function initAgrimenyaPWA() {
      try {
        const parentDoc = window.parent.document;
        if (!parentDoc) return;

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

        // 4. Register Service Worker with fallback
        if ('serviceWorker' in window.parent.navigator) {
          const swUrl = '/sw.js';
          const fallbackSwUrl = '/app/static/sw.js';

          window.parent.navigator.serviceWorker.register(swUrl, { scope: '/' })
            .then(reg => {
              console.log('[PWA] ServiceWorker registered with scope:', reg.scope);
            })
            .catch(err => {
              console.log('[PWA] Scope / registration deferred, trying fallback path...', err);
              window.parent.navigator.serviceWorker.register(fallbackSwUrl)
                .then(reg => {
                  console.log('[PWA] Fallback ServiceWorker registered with scope:', reg.scope);
                })
                .catch(fallbackErr => {
                  console.warn('[PWA] ServiceWorker registration notice:', fallbackErr);
                });
            });
        }

        // 5. Offline & Online connectivity toast banner
        let toast = parentDoc.getElementById('ag-pwa-connectivity-toast');
        if (!toast) {
          toast = parentDoc.createElement('div');
          toast.id = 'ag-pwa-connectivity-toast';
          toast.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(100px);z-index:999999;padding:0.65rem 1.25rem;border-radius:12px;font-family:"Plus Jakarta Sans",sans-serif;font-size:0.88rem;font-weight:700;display:flex;align-items:center;gap:0.6rem;box-shadow:0 12px 32px rgba(0,0,0,0.45);transition:transform 0.35s cubic-bezier(0.16,1,0.3,1),opacity 0.35s ease;opacity:0;pointer-events:none;';
          parentDoc.body.appendChild(toast);
        }

        function showToast(isOnline) {
          if (!isOnline) {
            toast.style.background = '#d97706';
            toast.style.border = '1px solid #fbbf24';
            toast.style.color = '#021824';
            toast.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg><span>Offline Mode Active - Local Agro Data Ready</span>';
            toast.style.transform = 'translateX(-50%) translateY(0)';
            toast.style.opacity = '1';
          } else {
            toast.style.background = '#06283b';
            toast.style.border = '1px solid #00E599';
            toast.style.color = '#00E599';
            toast.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg><span>Back Online - Real-time Agro Stream Connected</span>';
            toast.style.transform = 'translateX(-50%) translateY(0)';
            toast.style.opacity = '1';
            setTimeout(() => {
              toast.style.transform = 'translateX(-50%) translateY(100px)';
              toast.style.opacity = '0';
            }, 3500);
          }
        }

        window.parent.addEventListener('offline', () => showToast(false));
        window.parent.addEventListener('online', () => showToast(true));

        if (!window.parent.navigator.onLine) {
          showToast(false);
        }

        // 6. Handle beforeinstallprompt for native Install App action
        window.parent.addEventListener('beforeinstallprompt', (e) => {
          e.preventDefault();
          window.parent.__agrimenya_deferred_prompt = e;

          // Display smooth install button badge in navbar if not already installed
          let installBtn = parentDoc.getElementById('ag-pwa-install-badge');
          if (!installBtn) {
            installBtn = parentDoc.createElement('button');
            installBtn.id = 'ag-pwa-install-badge';
            installBtn.title = 'Install agrimenya as Progressive Web App';
            installBtn.style.cssText = 'position:fixed;bottom:24px;left:24px;z-index:99999;padding:0.45rem 0.95rem;border-radius:10px;background:#061a26;border:1px solid rgba(56,189,248,0.5);color:#38bdf8;font-family:"Plus Jakarta Sans",sans-serif;font-size:0.82rem;font-weight:700;display:flex;align-items:center;gap:0.45rem;cursor:pointer;box-shadow:0 8px 24px rgba(0,0,0,0.4);transition:all 0.2s;';
            installBtn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg><span>Install App</span>';
            installBtn.addEventListener('click', async () => {
              if (window.parent.__agrimenya_deferred_prompt) {
                window.parent.__agrimenya_deferred_prompt.prompt();
                const { outcome } = await window.parent.__agrimenya_deferred_prompt.userChoice;
                if (outcome === 'accepted') {
                  installBtn.remove();
                }
                window.parent.__agrimenya_deferred_prompt = null;
              }
            });
            parentDoc.body.appendChild(installBtn);
          }
        });

      } catch (err) {
        console.error('PWA initialization error:', err);
      }
    })();
    </script>
    """

    components.html(pwa_script, height=0)
