"""Creative, animated agro-intelligence hero with full-page background video for agrimenya."""
import os
import shutil
import streamlit as st
import streamlit.components.v1 as components


def _ensure_landing_video() -> str:
    """Ensure landing video is linked in static directories for streaming."""
    frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_dir = os.path.dirname(frontend_dir)
    assets_dir = os.path.join(frontend_dir, "assets")
    src = os.path.join(assets_dir, "landing video.mp4")

    # Static destinations: frontend/static and root/static
    destinations = [
        os.path.join(frontend_dir, "static", "landing_video.mp4"),
        os.path.join(root_dir, "static", "landing_video.mp4"),
    ]

    if os.path.exists(src):
        for dst in destinations:
            if not os.path.exists(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    os.link(src, dst)
                except Exception:
                    try:
                        shutil.copy2(src, dst)
                    except Exception:
                        pass

    # Ensure config.toml with enableStaticServing exists in both locations
    config_content = "[server]\nenableStaticServing = true\n"
    for cdir in [os.path.join(frontend_dir, ".streamlit"), os.path.join(root_dir, ".streamlit")]:
        cpath = os.path.join(cdir, "config.toml")
        if not os.path.exists(cpath):
            os.makedirs(cdir, exist_ok=True)
            try:
                with open(cpath, "w", encoding="utf-8") as f:
                    f.write(config_content)
            except Exception:
                pass

    return "/app/static/landing_video.mp4"


def render_home_hero() -> None:
    """Render full-page background video and a floating glassmorphic hero command center."""
    video_url = _ensure_landing_video()

    # Apply parent-page transparency so the full-page video shows across the entire viewport
    st.html("""
    <style>
      html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
        background: transparent !important;
      }
      iframe[title="streamlit.components.v1.custom_component"] {
        border: none !important;
        background: transparent !important;
        width: 100% !important;
        border-radius: 22px !important;
        overflow: hidden !important;
      }
      div[data-testid="stCustomComponentV1"] {
        margin-bottom: 1.5rem !important;
      }
      /* Action workflow cards: high-gloss translucent glass cards */
      [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.90) !important;
        backdrop-filter: blur(16px) saturate(190%) !important;
        -webkit-backdrop-filter: blur(16px) saturate(190%) !important;
        border: 1px solid rgba(255, 255, 255, 0.7) !important;
        box-shadow: 0 12px 32px rgba(2, 24, 36, 0.22) !important;
      }
    </style>
    """)

    hero_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
      <style>
        * {{
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }}
        html, body {{
          background: transparent;
          font-family: 'Plus Jakarta Sans', sans-serif;
          overflow: hidden;
          width: 100%;
          height: 100%;
        }}

        /* Floating glassmorphic command center card (no video inside - video is full page background) */
        .ag-hero-wrapper {{
          position: relative;
          overflow: hidden;
          width: 100%;
          min-height: 380px;
          color: #ffffff;
          background: linear-gradient(
            135deg,
            rgba(2, 24, 36, 0.72) 0%,
            rgba(3, 34, 46, 0.58) 42%,
            rgba(6, 56, 48, 0.58) 78%,
            rgba(4, 40, 32, 0.68) 100%
          );
          backdrop-filter: blur(20px) saturate(190%);
          -webkit-backdrop-filter: blur(20px) saturate(190%);
          border-radius: 22px;
          border: 1px solid rgba(56, 189, 248, 0.38);
          border-top: 1.5px solid rgba(255, 255, 255, 0.55);
          box-shadow: 0 20px 50px rgba(2, 24, 36, 0.45), 0 0 40px rgba(56, 189, 248, 0.16), inset 0 1px 0 rgba(255, 255, 255, 0.25);
        }}

        /* Ambient Cyan Bulb & Tree Emerald Light Orbs inside hero card */
        .ag-hero-glow-1 {{
          position: absolute;
          top: -60px;
          right: 18%;
          width: 320px;
          height: 320px;
          background: radial-gradient(circle, rgba(56, 189, 248, 0.24) 0%, rgba(14, 165, 233, 0) 70%);
          border-radius: 50%;
          filter: blur(35px);
          pointer-events: none;
          z-index: 1;
          animation: ag-hero-orb-float 7s ease-in-out infinite alternate;
        }}
        .ag-hero-glow-2 {{
          position: absolute;
          bottom: -80px;
          left: 20%;
          width: 360px;
          height: 360px;
          background: radial-gradient(circle, rgba(74, 222, 128, 0.20) 0%, rgba(34, 197, 94, 0) 70%);
          border-radius: 50%;
          filter: blur(40px);
          pointer-events: none;
          z-index: 1;
          animation: ag-hero-orb-float-2 9s ease-in-out infinite alternate;
        }}

        @keyframes ag-hero-orb-float {{
          0% {{ transform: translate(0, 0) scale(1); }}
          100% {{ transform: translate(-30px, 25px) scale(1.15); }}
        }}
        @keyframes ag-hero-orb-float-2 {{
          0% {{ transform: translate(0, 0) scale(1); }}
          100% {{ transform: translate(35px, -20px) scale(1.12); }}
        }}

        /* Grid Content Layer */
        .ag-hero-grid {{
          position: relative;
          z-index: 2;
          display: grid;
          grid-template-columns: 1.35fr 0.65fr;
          gap: 2.2rem;
          align-items: center;
          padding: 2.5rem 3rem;
          min-height: 380px;
        }}

        .ag-hero-content {{
          position: relative;
        }}

        /* Live Beacon Badge - Cyan & Emerald */
        .ag-hero-badge {{
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: linear-gradient(135deg, rgba(56, 189, 248, 0.26) 0%, rgba(74, 222, 128, 0.22) 100%);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border: 1px solid rgba(125, 211, 252, 0.5);
          padding: 5px 14px;
          border-radius: 9999px;
          font-size: 0.76rem;
          font-weight: 750;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: #e0f2fe;
          margin-bottom: 0.85rem;
          box-shadow: 0 4px 14px rgba(14, 165, 233, 0.25);
        }}
        .ag-hero-beacon {{
          width: 8px;
          height: 8px;
          background-color: #38bdf8;
          border-radius: 50%;
          display: inline-block;
          box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.8);
          animation: ag-beacon-radar 2s infinite;
        }}
        @keyframes ag-beacon-radar {{
          0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.8); }}
          50% {{ box-shadow: 0 0 0 6px rgba(74, 222, 128, 0.35); }}
          100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }}
        }}

        /* Headline with High Contrast Glow */
        .ag-hero-title {{
          margin: 0 0 0.8rem !important;
          color: #ffffff !important;
          font-size: clamp(2rem, 3.5vw, 3.1rem) !important;
          line-height: 1.1 !important;
          font-weight: 800 !important;
          letter-spacing: -0.04em !important;
          text-shadow: 0 2px 14px rgba(0, 0, 0, 0.7) !important;
        }}
        .ag-hero-glow-text {{
          background: linear-gradient(135deg, #7dd3fc 0%, #38bdf8 35%, #4ade80 75%, #a7f3d0 100%) !important;
          -webkit-background-clip: text !important;
          -webkit-text-fill-color: transparent !important;
          display: inline-block !important;
          filter: drop-shadow(0 0 16px rgba(56, 189, 248, 0.5)) !important;
        }}

        .ag-hero-copy {{
          max-width: 640px;
          margin: 0 0 1.5rem;
          color: #f0fdfa;
          font-size: 0.98rem;
          line-height: 1.6;
          font-weight: 500;
          text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7);
        }}

        /* Stats Ticker Strip */
        .ag-hero-stats {{
          display: flex;
          flex-wrap: wrap;
          gap: 1.4rem;
          align-items: center;
          padding-top: 1rem;
          border-top: 1px solid rgba(56, 189, 248, 0.3);
        }}
        .ag-hero-stat-item {{
          display: flex;
          flex-direction: column;
        }}
        .ag-hero-stat-val {{
          font-size: 1.15rem;
          font-weight: 800;
          color: #ffffff;
          letter-spacing: -0.02em;
          text-shadow: 0 2px 8px rgba(0, 0, 0, 0.7), 0 0 12px rgba(56, 189, 248, 0.4);
        }}
        .ag-hero-stat-lbl {{
          font-size: 0.72rem;
          font-weight: 650;
          color: #7dd3fc;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          text-shadow: 0 1px 4px rgba(0, 0, 0, 0.6);
        }}

        /* Right Column: Liquid Glass Bulb Horizon Card */
        .ag-hero-glass-card {{
          position: relative;
          background: linear-gradient(135deg, rgba(2, 24, 36, 0.75) 0%, rgba(4, 38, 51, 0.65) 40%, rgba(6, 56, 54, 0.65) 100%);
          backdrop-filter: blur(20px) saturate(190%);
          -webkit-backdrop-filter: blur(20px) saturate(190%);
          border: 1px solid rgba(125, 211, 252, 0.4);
          border-top: 1.5px solid rgba(255, 255, 255, 0.7);
          border-radius: 18px;
          padding: 1.4rem 1.5rem;
          box-shadow: 0 16px 40px rgba(2, 24, 36, 0.55), inset 0 1.5px 2px rgba(255, 255, 255, 0.35);
        }}
        .ag-hero-card-header {{
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 0.75rem;
        }}
        .ag-hero-card-title {{
          font-size: 0.92rem;
          font-weight: 750;
          color: #ffffff;
          letter-spacing: -0.01em;
          text-shadow: 0 1px 4px rgba(0, 0, 0, 0.5);
        }}
        .ag-hero-card-tag {{
          font-size: 0.72rem;
          font-weight: 700;
          background: rgba(56, 189, 248, 0.25);
          color: #bae6fd;
          border: 1px solid rgba(56, 189, 248, 0.5);
          padding: 2px 8px;
          border-radius: 9999px;
          text-transform: uppercase;
        }}
        .ag-hero-card-desc {{
          color: #e0f2fe;
          font-size: 0.85rem;
          line-height: 1.5;
          margin-bottom: 0.9rem;
          text-shadow: 0 1px 4px rgba(0, 0, 0, 0.5);
        }}
        .ag-hero-card-row {{
          display: flex;
          flex-direction: column;
          gap: 0.45rem;
        }}
        .ag-hero-pill-info {{
          display: flex;
          align-items: center;
          gap: 8px;
          background: rgba(2, 24, 36, 0.6);
          border: 1px solid rgba(56, 189, 248, 0.25);
          padding: 6px 10px;
          border-radius: 8px;
          font-size: 0.78rem;
          color: #f0fdfa;
        }}

        @media (max-width: 900px) {{
          .ag-hero-grid {{
            grid-template-columns: 1fr;
            padding: 1.8rem 1.5rem;
            gap: 1.5rem;
          }}
        }}
      </style>
    </head>
    <body>
      <section class="ag-hero-wrapper" aria-label="agrimenya overview">
        <div class="ag-hero-glow-1"></div>
        <div class="ag-hero-glow-2"></div>

        <div class="ag-hero-grid">
          <div class="ag-hero-content">
            <div class="ag-hero-badge">
              <span class="ag-hero-beacon"></span>
              Rwanda Agro-Climate Decision Engine
            </div>
            <h1 class="ag-hero-title">
              Make the next<br/>
              <span class="ag-hero-glow-text">field decision</span> clearer.
            </h1>
            <p class="ag-hero-copy">
              Explore spatial zone intelligence, evaluate seasonal crop recommendations, and turn data-grounded insights into synchronized field plans.
            </p>

            <div class="ag-hero-stats">
              <div class="ag-hero-stat-item">
                <span class="ag-hero-stat-val">30 Districts</span>
                <span class="ag-hero-stat-lbl">Spatial Coverage</span>
              </div>
              <div class="ag-hero-stat-item">
                <span class="ag-hero-stat-val">10+ Key Crops</span>
                <span class="ag-hero-stat-lbl">SAS Baselines</span>
              </div>
              <div class="ag-hero-stat-item">
                <span class="ag-hero-stat-val">Real-time Weather</span>
                <span class="ag-hero-stat-lbl">Satellite Indicators</span>
              </div>
              <div class="ag-hero-stat-item">
                <span class="ag-hero-stat-val">CAT (UTC+2)</span>
                <span class="ag-hero-stat-lbl">System Timezone</span>
              </div>
            </div>
          </div>

          <aside class="ag-hero-glass-card">
            <div class="ag-hero-card-header">
              <span class="ag-hero-card-title">Seasonal Horizon</span>
              <span class="ag-hero-card-tag">2026 Season A</span>
            </div>
            <p class="ag-hero-card-desc">
              Active 2026 Season A campaign. Tracking soil moisture and conformal yield bounds.
            </p>
            <div class="ag-hero-card-row">
              <div class="ag-hero-pill-info">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                <span>Priority Zones: Gasabo, Bugesera, Musanze</span>
              </div>
              <div class="ag-hero-pill-info">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"></path></svg>
                <span>Optimal planting window actively tracked</span>
              </div>
              <div class="ag-hero-pill-info">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
                <span>AI Assistant available via corner bulb</span>
              </div>
            </div>
          </aside>
        </div>
      </section>

      <script>
        (function initFullPageBackgroundVideo() {{
          try {{
            const parentDoc = window.parent.document;
            if (!parentDoc) return;

            // 1. Inject or update full-page background video
            let video = parentDoc.getElementById('ag-landing-fullpage-video');
            if (!video) {{
              video = parentDoc.createElement('video');
              video.id = 'ag-landing-fullpage-video';
              video.autoplay = true;
              video.muted = true;
              video.loop = true;
              video.playsInline = true;
              video.preload = 'auto';
              video.setAttribute('autoplay', '');
              video.setAttribute('muted', '');
              video.setAttribute('loop', '');
              video.setAttribute('playsinline', '');
              video.style.cssText = 'position:fixed;top:0;left:-1%;width:138vw;height:100vh;object-fit:cover;object-position:left center;z-index:-2;pointer-events:none;filter:brightness(0.80) contrast(1.1) saturate(1.25);';
              
              const source = parentDoc.createElement('source');
              source.src = '{video_url}';
              source.type = 'video/mp4';
              video.appendChild(source);
              
              parentDoc.body.prepend(video);
            }} else {{
              video.style.display = 'block';
            }}

            // Ensure autoplay and muted state
            video.muted = true;
            var promise = video.play();
            if (promise !== undefined) {{
              promise.catch(function(e) {{
                console.log('Video autoplay deferred:', e);
                parentDoc.addEventListener('click', function() {{ video.muted = true; video.play(); }}, {{ once: true }});
              }});
            }}

            // 2. Inject or update cinematic full-page overlay
            let overlay = parentDoc.getElementById('ag-landing-fullpage-overlay');
            if (!overlay) {{
              overlay = parentDoc.createElement('div');
              overlay.id = 'ag-landing-fullpage-overlay';
              overlay.style.cssText = 'position:fixed;inset:0;background:radial-gradient(circle at 50% 15%, rgba(2,24,36,0.45) 0%, rgba(2,24,36,0.78) 100%);z-index:-1;pointer-events:none;';
              parentDoc.body.prepend(overlay);
            }} else {{
              overlay.style.display = 'block';
            }}

            // 3. Monitor page location: hide video when user navigates away from Home
            const checkRoute = function() {{
              try {{
                const p = window.parent.location.pathname;
                const isHome = p === '/' || p.endsWith('/Home') || p.endsWith('/Home/');
                if (!isHome) {{
                  if (video) video.style.display = 'none';
                  if (overlay) overlay.style.display = 'none';
                }} else {{
                  if (video) video.style.display = 'block';
                  if (overlay) overlay.style.display = 'block';
                }}
              }} catch (err) {{}}
            }};
            setInterval(checkRoute, 400);

          }} catch (err) {{
            console.error('Full-page video background error:', err);
          }}
        }})();
      </script>
    </body>
    </html>
    """

    components.html(hero_html, height=420)
