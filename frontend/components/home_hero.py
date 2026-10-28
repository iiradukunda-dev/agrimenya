"""Welcoming home page introduction for agrimenya."""
import streamlit as st
import streamlit.components.v1 as components
from utils.i18n import t


def _ensure_landing_video() -> str:
    """Legacy helper maintained for backward compatibility."""
    return ""


def render_home_hero() -> None:
    """Render a welcoming introduction to the tools available on the home page."""
    badge_text = t("hero.badge", "Here for Rwanda’s farming seasons")
    title_pre = t("hero.title_pre", "A clearer picture of")
    title_glow = t("hero.title_glow", "your growing season")
    title_post = t("hero.title_post", ".")
    copy_text = t("hero.copy", "Start with your district. Explore the information available for your crops, then make a plan your team can put into action.")
    stat_districts_val = t("hero.stat.districts_val", "30 districts")
    stat_districts_lbl = t("hero.stat.districts_lbl", "Across Rwanda")
    stat_crops_val = t("hero.stat.crops_val", "10+ crops")
    stat_crops_lbl = t("hero.stat.crops_lbl", "Crop baselines")
    card_title = t("hero.card.title", "A good place to begin")
    card_tag = t("hero.card.tag", "Start here")
    card_desc = t("hero.card.desc", "Choose an area to explore, check the information available, and agree on next steps with your team.")
    pill_priority = t("hero.pill.priority", "Explore zones and local context")
    pill_window = t("hero.pill.window", "Review crop and seasonal information")
    pill_ai = t("hero.pill.ai", "Make a plan and share it with your team")

    st.html("""
    <style>
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
      @media (max-width: 900px) {
        iframe[title="streamlit.components.v1.custom_component"] {
          height: 680px !important;
        }
      }
      /* Action workflow cards: structured modern cards with classic motion */
      [data-testid="stVerticalBlockBorderWrapper"] {
        position: relative !important;
        overflow: hidden !important;
        background: #ffffff !important;
        border: 1px solid rgba(47, 94, 67, 0.14) !important;
        border-top: 2px solid #729277 !important;
        box-shadow: 0 4px 18px rgba(32, 60, 42, 0.06), 0 1px 3px rgba(0, 0, 0, 0.03) !important;
        border-radius: 18px !important;
        transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1),
                    box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1),
                    border-color 0.3s ease,
                    background 0.3s ease !important;
        will-change: transform, box-shadow;
      }
      [data-testid="stVerticalBlockBorderWrapper"]:hover {
        background: #fbfcfa !important;
        border-color: rgba(47, 94, 67, 0.22) !important;
        border-top-color: #527c5d !important;
        box-shadow: 0 10px 25px rgba(32, 60, 42, 0.10), 0 2px 6px rgba(0, 0, 0, 0.03) !important;
        transform: translateY(-3px) !important;
      }
      [data-testid="stVerticalBlockBorderWrapper"]:active {
        transform: translateY(-1px) scale(0.998) !important;
        box-shadow: 0 4px 14px rgba(32, 60, 42, 0.08) !important;
        transition: transform 0.12s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.12s ease !important;
      }

      /* Headings & Text inside cards */
      [data-testid="stVerticalBlockBorderWrapper"] h1,
      [data-testid="stVerticalBlockBorderWrapper"] h2,
      [data-testid="stVerticalBlockBorderWrapper"] h3,
      [data-testid="stVerticalBlockBorderWrapper"] h4 {
        color: #0f172a !important;
        text-shadow: none !important;
      }
      [data-testid="stVerticalBlockBorderWrapper"] p,
      [data-testid="stVerticalBlockBorderWrapper"] span:not([style*="color"]) {
        color: #475569 !important;
        text-shadow: none !important;
      }

      /* Structured Card Buttons - High specificity override */
      [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:not([role="tab"]):not([data-baseweb="tab"]),
      [data-testid="stVerticalBlockBorderWrapper"] button:not([role="tab"]):not([data-baseweb="tab"]):not([aria-selected]),
      [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stBaseButton-secondary"]:not([role="tab"]):not([data-baseweb="tab"]):not([aria-selected]) {
        background: #f4f7f3 !important;
        border: 1px solid rgba(47, 94, 67, 0.18) !important;
        border-radius: 10px !important;
        color: #426b4e !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        text-shadow: none !important;
        transition: all 0.25s ease !important;
        box-shadow: none !important;
      }
      [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:not([role="tab"]):not([data-baseweb="tab"]) *,
      [data-testid="stVerticalBlockBorderWrapper"] button:not([role="tab"]):not([data-baseweb="tab"]):not([aria-selected]) * {
        color: #426b4e !important;
        font-weight: 700 !important;
      }
      [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:not([role="tab"]):not([data-baseweb="tab"]):hover,
      [data-testid="stVerticalBlockBorderWrapper"] button:not([role="tab"]):not([data-baseweb="tab"]):not([aria-selected]):hover,
      [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stBaseButton-secondary"]:not([role="tab"]):not([data-baseweb="tab"]):not([aria-selected]):hover {
        background: #527c5d !important;
        border-color: #527c5d !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(32, 60, 42, 0.12) !important;
        transform: translateY(-1px) !important;
      }
      [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:hover *,
      [data-testid="stVerticalBlockBorderWrapper"] button:hover * {
        color: #ffffff !important;
      }

      /* Clean section titles & subtitles */
      .ag-section-title, h2.ag-section-title {
        color: #0a1f26 !important;
        -webkit-text-fill-color: #0a1f26 !important;
        text-shadow: none !important;
      }
      .ag-section-subtitle, p.ag-section-subtitle {
        color: #48656c !important;
        -webkit-text-fill-color: #48656c !important;
        text-shadow: none !important;
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

        /* Command center card */
        .ag-hero-wrapper {{
          position: relative;
          overflow: hidden;
          width: 100%;
          min-height: 380px;
          color: #0f172a;
          background: linear-gradient(135deg, #ffffff 0%, #f7faf7 58%, #edf5ef 100%);
          border-radius: 22px;
          border: 1px solid rgba(47, 94, 67, 0.12);
          box-shadow: 0 12px 30px rgba(32, 60, 42, 0.07);
          animation: ag-hero-enter 0.7s cubic-bezier(0.16, 1, 0.3, 1);
        }}

        @keyframes ag-hero-enter {{
          from {{ opacity: 0; transform: translateY(16px) scale(0.99); }}
          to {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}

        @keyframes ag-text-shimmer {{
          0% {{ filter: drop-shadow(0 0 14px rgba(56, 189, 248, 0.45)); }}
          50% {{ filter: drop-shadow(0 0 24px rgba(56, 189, 248, 0.75)); }}
          100% {{ filter: drop-shadow(0 0 18px rgba(56, 189, 248, 0.6)); }}
        }}

        @keyframes ag-hero-card-float {{
          0% {{ transform: translateY(0); }}
          100% {{ transform: translateY(-5px); }}
        }}

        /* Ambient Cyan Bulb & Tree Emerald Light Orbs inside hero card */
        .ag-hero-glow-1 {{
          position: absolute;
          top: -60px;
          right: 18%;
          width: 320px;
          height: 320px;
          background: radial-gradient(circle, rgba(122, 157, 108, 0.12) 0%, rgba(122, 157, 108, 0) 70%);
          border-radius: 50%;
          filter: blur(35px);
          pointer-events: none;
          z-index: 1;
          animation: none;
        }}
        .ag-hero-glow-2 {{
          position: absolute;
          bottom: -80px;
          left: 20%;
          width: 360px;
          height: 360px;
          background: radial-gradient(circle, rgba(213, 178, 111, 0.10) 0%, rgba(213, 178, 111, 0) 70%);
          border-radius: 50%;
          filter: blur(40px);
          pointer-events: none;
          z-index: 1;
          animation: none;
        }}

        @keyframes ag-hero-orb-float {{
          0% {{ transform: translate(0, 0) scale(1); }}
          100% {{ transform: translate(-30px, 25px) scale(1.15); }}
        }}
        @keyframes ag-hero-orb-float-2 {{
          0% {{ transform: translate(0, 0) scale(1); }}
          100% {{ transform: translate(35px, -20px) scale(1.12); }}
        }}

        /* Symmetrical 2-Column Grid Layout */
        .ag-hero-grid {{
          position: relative;
          z-index: 2;
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 2.5rem;
          align-items: center;
          padding: 2.6rem 3rem;
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
          background: #ffffff;
          border: 1px solid rgba(47, 94, 67, 0.15);
          padding: 5px 14px;
          border-radius: 9999px;
          font-size: 0.76rem;
          font-weight: 750;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: #386448;
          margin-bottom: 0.85rem;
          box-shadow: none;
          transition: transform 0.25s ease;
        }}
        .ag-hero-badge:hover {{
          transform: scale(1.03);
        }}
        .ag-hero-beacon {{
          width: 8px;
          height: 8px;
          background-color: #527c5d;
          border-radius: 50%;
          display: inline-block;
          box-shadow: none;
          animation: none;
        }}
        @keyframes ag-beacon-radar {{
          0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(2, 132, 199, 0.8); }}
          50% {{ box-shadow: 0 0 0 6px rgba(2, 132, 199, 0.35); }}
          100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(2, 132, 199, 0); }}
        }}

        /* Headline with High Contrast */
        .ag-hero-title {{
          margin: 0 0 0.8rem !important;
          color: #0f172a !important;
          font-size: clamp(2rem, 3.5vw, 3.1rem) !important;
          line-height: 1.1 !important;
          font-weight: 800 !important;
          letter-spacing: -0.04em !important;
          text-shadow: none !important;
        }}
        .ag-hero-glow-text {{
          background: linear-gradient(135deg, #426b4e 0%, #527c5d 100%) !important;
          -webkit-background-clip: text !important;
          -webkit-text-fill-color: transparent !important;
          display: inline-block !important;
          filter: none !important;
        }}

        .ag-hero-copy {{
          max-width: 640px;
          margin: 0 0 1.5rem;
          color: #334155;
          font-size: 0.98rem;
          line-height: 1.6;
          font-weight: 500;
          text-shadow: none;
        }}

        /* Stats Ticker Strip with Hover Lift */
        .ag-hero-stats {{
          display: flex;
          flex-wrap: wrap;
          gap: 1.4rem;
          align-items: center;
          padding-top: 1rem;
          border-top: 1px solid rgba(47, 94, 67, 0.13);
        }}
        .ag-hero-stat-item {{
          display: flex;
          flex-direction: column;
          transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
          cursor: default;
        }}
        .ag-hero-stat-item:hover {{
          transform: translateY(-3px) scale(1.04);
        }}
        .ag-hero-stat-val {{
          font-size: 1.15rem;
          font-weight: 800;
          color: #0f172a;
          letter-spacing: -0.02em;
          text-shadow: none;
          transition: color 0.2s ease;
        }}
        .ag-hero-stat-item:hover .ag-hero-stat-val {{
          color: #527c5d;
        }}
        .ag-hero-stat-lbl {{
          font-size: 0.72rem;
          font-weight: 650;
          color: #527c5d;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          text-shadow: none;
        }}

        /* Right Column: Structured Horizon Card with Subtle Float */
        .ag-hero-horizon-card {{
          position: relative;
          background: #ffffff;
          border: 1px solid rgba(47, 94, 67, 0.15);
          border-top: 2px solid #729277;
          border-radius: 18px;
          padding: 1.5rem 1.6rem;
          box-shadow: 0 8px 22px rgba(32, 60, 42, 0.07);
          animation: none;
          transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        .ag-hero-horizon-card:hover {{
          transform: translateY(-4px);
          box-shadow: 0 12px 28px rgba(32, 60, 42, 0.11);
          border-color: rgba(47, 94, 67, 0.3);
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
          color: #0f172a;
          letter-spacing: -0.01em;
          text-shadow: none;
        }}
        .ag-hero-card-tag {{
          font-size: 0.72rem;
          font-weight: 700;
          background: #e7efe5;
          color: #426b4e;
          border: 1px solid rgba(47, 94, 67, 0.14);
          padding: 2px 8px;
          border-radius: 9999px;
          text-transform: uppercase;
        }}
        .ag-hero-card-desc {{
          color: #475569;
          font-size: 0.85rem;
          line-height: 1.5;
          margin-bottom: 0.9rem;
          text-shadow: none;
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
          background: #f7faf6;
          border: 1px solid rgba(47, 94, 67, 0.10);
          padding: 6px 10px;
          border-radius: 8px;
          font-size: 0.78rem;
          color: #3d5543;
          transition: background 0.2s ease, transform 0.2s ease;
        }}
        .ag-hero-pill-info:hover {{
          background: #edf3eb;
          transform: translateX(2px);
        }}

        @media (max-width: 900px) {{
          .ag-hero-grid {{
            grid-template-columns: 1fr;
            padding: 1.8rem 1.5rem;
            gap: 1.5rem;
            min-height: auto;
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
              {badge_text}
            </div>
            <h1 class="ag-hero-title">
              {title_pre}<br/>
              <span class="ag-hero-glow-text">{title_glow}</span> {title_post}
            </h1>
            <p class="ag-hero-copy">
              {copy_text}
            </p>

            <div class="ag-hero-stats">
              <div class="ag-hero-stat-item">
                <span class="ag-hero-stat-val">{stat_districts_val}</span>
                <span class="ag-hero-stat-lbl">{stat_districts_lbl}</span>
              </div>
              <div class="ag-hero-stat-item">
                <span class="ag-hero-stat-val">{stat_crops_val}</span>
                <span class="ag-hero-stat-lbl">{stat_crops_lbl}</span>
              </div>
            </div>
          </div>

          <aside class="ag-hero-horizon-card">
            <div class="ag-hero-card-header">
              <span class="ag-hero-card-title">{card_title}</span>
              <span class="ag-hero-card-tag">{card_tag}</span>
            </div>
            <p class="ag-hero-card-desc">
              {card_desc}
            </p>
            <div class="ag-hero-card-row">
              <div class="ag-hero-pill-info">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                <span>{pill_priority}</span>
              </div>
              <div class="ag-hero-pill-info">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"></path></svg>
                <span>{pill_window}</span>
              </div>
              <div class="ag-hero-pill-info">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
                <span>{pill_ai}</span>
              </div>
            </div>
          </aside>
        </div>
      </section>

      <script>
        (function cleanupVideoBackground() {{
          try {{
            const parentDoc = window.parent.document;
            if (!parentDoc) return;
            const video = parentDoc.getElementById('ag-landing-fullpage-video');
            if (video) video.remove();
            const overlay = parentDoc.getElementById('ag-landing-fullpage-overlay');
            if (overlay) overlay.remove();
          }} catch (err) {{
            console.debug('Video cleanup note:', err);
          }}
        }})();
      </script>
    </body>
    </html>
    """

    components.html(hero_html, height=420)

