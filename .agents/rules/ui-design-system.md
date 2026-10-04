# UI Design System & Theme Rules — agrimenya

## Core Philosophy: "Liquid Glass" & Agriculture Intelligence

The entire agrimenya application MUST adhere strictly to the "Liquid Glass" design language provided by the user. This is a premium, modern aesthetic that relies heavily on glassmorphism, depth, and nature-forward imagery.

Whenever you add a new component, page, or UI element, it MUST look cohesive with this design. 

## 1. Backgrounds & Environment
- The app should NOT use flat solid colors for the main background.
- It MUST use rich, high-quality, blurred agricultural imagery (e.g., macro shots of tea leaves, green fields, sunlight) as a full-viewport ambient background.
- Elements float on top of this environment.

## 2. Glassmorphism (The "Glass" Effect)
All major container elements (navbars, cards, modals, sidebars) MUST be implemented as frosted glass surfaces:
- **Background:** Semi-transparent white or very light green (e.g., `rgba(255, 255, 255, 0.15)` to `0.3`).
- **Backdrop Filter:** Strong blur effect (`backdrop-filter: blur(16px)` to `blur(24px)`).
- **Borders:** Subtle, semi-transparent white borders to create a refractive edge (`border: 1px solid rgba(255, 255, 255, 0.4)`).
- **Shadows:** Soft, diffused drop shadows to create elevation (`box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1)`).
- **Highlights:** Subtle top/left inner highlights to simulate light hitting the glass edge.

## 3. Typography & Colors
- **Font Families:** Modern sans-serif (e.g., Inter, Space Grotesk, or system UI fonts).
- **Text Colors:** 
  - Primary text: Deep, legible forest greens (e.g., `#064E3B`, `#1B3A2D`) or very dark grays.
  - Secondary text: Softer greens or grays.
- **Accents:** Emerald greens, vibrant leaf greens for active states and highlights.
- **Avoid:** Generic pure blacks, blues, or reds unless strictly semantic (e.g., error states), but even semantic colors should be tweaked to fit the earthy, premium palette.

## 4. Component Specifics
- **Navbar:** Floating, pill-shaped, or detached glass header (not edge-to-edge flush). It should house the brand mark, navigation links, and a language selector.
- **Cards & Containers:** Rounded corners (e.g., `border-radius: 16px` to `24px`). Content inside should have ample padding.
- **Buttons & Interactive Elements:** Should have hover states that slightly increase opacity, blur, or elevate the element. Active states should feel tactile.
- **Icons:** Use elegant, consistent icons (like the wheat or leaf SVGs). 3D-like, embossed, or inner-shadowed icon containers (as seen in the agrimenya logo mark on the hero card) are highly encouraged.
- **Animations:** Subtle micro-animations (GSAP or CSS transitions) for floating elements, particles (like leaves), and hover states.

## 5. Streamlit Integration
When working within Streamlit:
- Inject these styles globally via `st.html` or `st.markdown(..., unsafe_allow_html=True)`.
- Use custom HTML/CSS wrappers for major structural elements if native Streamlit components cannot be styled to meet this premium standard.
- Hide default Streamlit chrome (like the default header and footer) to maintain the immersive app experience.

**CRITICAL RULE:** If an interface looks basic, flat, or like a default Streamlit app, you have failed the UI constraint. It must always look like a premium, state-of-the-art web application.
