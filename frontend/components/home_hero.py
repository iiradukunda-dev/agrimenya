"""Lightweight, static welcome panel for the landing page."""
import streamlit as st


def render_home_hero() -> None:
    """Render the welcome panel without external JavaScript or asset requests."""
    st.html("""
    <style>
      .ag-home-hero { position:relative; overflow:hidden; display:grid; grid-template-columns:1.4fr .6fr;
        gap:2rem; align-items:center; min-height:255px; padding:2.5rem 3rem; margin:.4rem 0 1.4rem;
        color:#f7fbf7; background:linear-gradient(112deg,#194b36 0%,#276749 65%,#3d7656 100%);
        border-radius:18px; }
      .ag-home-hero:after { content:""; position:absolute; width:300px;height:300px; right:-45px;top:-100px;
        border:1px solid rgba(255,255,255,.18); border-radius:50%; box-shadow:0 0 0 36px rgba(255,255,255,.035),0 0 0 72px rgba(255,255,255,.025); }
      .ag-home-kicker { color:#c9dfcc; font-size:.75rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; }
      .ag-home-title { margin:.65rem 0 .8rem; color:white; font-size:clamp(2rem,4vw,3.25rem); line-height:1.05; font-weight:750; letter-spacing:-.05em; }
      .ag-home-copy { max-width:660px; margin:0; color:#e3eee5; font-size:1rem; line-height:1.65; }
      .ag-home-side { z-index:1; justify-self:end; max-width:245px; padding:1.15rem 1.3rem; border-left:2px solid #d4b078; }
      .ag-home-side strong { display:block; margin-bottom:.35rem; color:white; font-size:.9rem; }
      .ag-home-side span { color:#dce9df; font-size:.84rem; line-height:1.55; }
      @media(max-width:700px) { .ag-home-hero { grid-template-columns:1fr; padding:1.7rem; gap:1rem; } .ag-home-side { justify-self:start; } }
    </style>
    <section class="ag-home-hero" aria-label="agrimenya overview">
      <div>
        <div class="ag-home-kicker">Agricultural planning | Rwanda</div>
        <div class="ag-home-title">Make the next<br>field decision clearer.</div>
        <p class="ag-home-copy">Explore zone data, review seasonal priorities, and turn recommendations into plans your teams can follow.</p>
      </div>
      <aside class="ag-home-side"><strong>From insight to action</strong><span>Start with a district or crop, check the available evidence, then coordinate the next step.</span></aside>
    </section>
    """)
