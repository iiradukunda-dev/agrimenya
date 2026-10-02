"""
Animated hero component for the agrimenya landing page.

Uses React 18 + GSAP to render an interactive 3D glass card hero section
with climate-themed floating data particles.
"""
import streamlit.components.v1 as components


def render_react_hero() -> None:
    """
    Renders a premium interactive hero section with:
    - 3D perspective glass card that tracks mouse movement
    - Floating climate data particles (temperature, rain, soil icons)
    - GSAP entrance animations
    - Responsive design
    """
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8" />
        <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
        <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
        <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700;800&display=swap');

            * { margin: 0; padding: 0; box-sizing: border-box; }

            body {
                font-family: 'Inter', sans-serif;
                overflow: hidden;
                background: transparent;
            }

            #root {
                width: 100%;
                min-height: 380px;
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
            }

            .hero-scene {
                width: 100%;
                height: 380px;
                display: flex;
                align-items: center;
                justify-content: center;
                perspective: 1200px;
                position: relative;
                overflow: hidden;
            }

            /* Floating data particles */
            .particle {
                position: absolute;
                font-size: 1.6rem;
                opacity: 0;
                pointer-events: none;
                filter: blur(0.5px);
            }

            .hero-glass {
                background: linear-gradient(
                    135deg,
                    rgba(255, 255, 255, 0.55) 0%,
                    rgba(255, 255, 255, 0.15) 100%
                );
                backdrop-filter: blur(40px) saturate(200%);
                -webkit-backdrop-filter: blur(40px) saturate(200%);
                border: 1px solid rgba(255, 255, 255, 0.5);
                border-radius: 32px;
                padding: 56px 64px;
                max-width: 720px;
                width: 90%;
                text-align: center;
                box-shadow:
                    0 20px 60px rgba(0, 0, 0, 0.1),
                    0 4px 16px rgba(0, 0, 0, 0.05),
                    inset 0 1px 0 rgba(255, 255, 255, 0.7),
                    inset 0 -1px 0 rgba(255, 255, 255, 0.15);
                transform-style: preserve-3d;
                cursor: default;
                position: relative;
                z-index: 2;
                display: flex;
                flex-direction: column;
                align-items: center;
            }

            .hero-icon-container {
                width: 72px;
                height: 72px;
                background: rgba(255, 255, 255, 0.8);
                border-radius: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 24px;
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.05);
                transform: translateZ(40px);
                border: 1px solid rgba(255, 255, 255, 1);
            }

            .hero-title {
                font-family: 'Space Grotesk', sans-serif;
                font-size: 3rem;
                font-weight: 800;
                line-height: 1.15;
                margin-bottom: 12px;
                background: linear-gradient(135deg, #1B3A2D 30%, #2D6A4F 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                transform: translateZ(50px);
            }

            .hero-subtitle {
                font-family: 'Space Grotesk', sans-serif;
                font-size: 1.4rem;
                font-weight: 600;
                color: #2D6A4F;
                line-height: 1.4;
                margin-bottom: 24px;
                transform: translateZ(35px);
            }

            .hero-text {
                font-family: 'Inter', sans-serif;
                font-size: 1.05rem;
                color: #4B5563;
                line-height: 1.6;
                transform: translateZ(25px);
                max-width: 600px;
            }

            .bottom-pill {
                position: absolute;
                bottom: 20px;
                background: rgba(255, 255, 255, 0.4);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.6);
                padding: 10px 24px;
                border-radius: 50px;
                font-family: 'Inter', sans-serif;
                font-size: 0.8rem;
                font-weight: 600;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                color: #1B3A2D;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                z-index: 3;
            }
        </style>
    </head>
    <body>
        <div id="root"></div>
        <script type="text/babel">
            const { useEffect, useRef } = React;

            const particles = [
                { emoji: '🍃', x: '8%',  y: '15%', delay: 0 },
                { emoji: '🌿', x: '85%', y: '20%', delay: 0.3 },
                { emoji: '🌱', x: '12%', y: '75%', delay: 0.6 },
                { emoji: '🌾', x: '88%', y: '70%', delay: 0.9 },
                { emoji: '🍃', x: '50%', y: '8%',  delay: 1.2 },
                { emoji: '🌿', x: '75%', y: '85%', delay: 1.5 },
                { emoji: '🌱', x: '20%', y: '40%', delay: 0.4 },
                { emoji: '🌾', x: '80%', y: '45%', delay: 0.8 },
            ];

            const Hero = () => {
                const cardRef = useRef(null);
                const sceneRef = useRef(null);
                const pillRef = useRef(null);
                const particleRefs = useRef([]);

                useEffect(() => {
                    const card = cardRef.current;
                    const scene = sceneRef.current;
                    const pill = pillRef.current;

                    // Entrance animation
                    gsap.fromTo(card,
                        { opacity: 0, y: 80, rotationX: -12, scale: 0.95 },
                        { opacity: 1, y: 0, rotationX: 0, scale: 1, duration: 1.4, ease: "power4.out", delay: 0.2 }
                    );

                    gsap.fromTo(pill,
                        { opacity: 0, y: 20 },
                        { opacity: 1, y: 0, duration: 1, ease: "power3.out", delay: 1 }
                    );

                    // Animate particles
                    particleRefs.current.forEach((el, i) => {
                        if (!el) return;
                        gsap.fromTo(el,
                            { opacity: 0, scale: 0.3, y: 20 },
                            { opacity: 0.6, scale: 1, y: 0, duration: 1, ease: "back.out(2)", delay: 0.8 + particles[i].delay }
                        );
                        // Gentle float
                        gsap.to(el, {
                            y: `random(-15, 15)`,
                            x: `random(-10, 10)`,
                            duration: `random(3, 5)`,
                            repeat: -1,
                            yoyo: true,
                            ease: "sine.inOut",
                            delay: particles[i].delay
                        });
                    });

                    // 3D mouse tracking
                    const handleMouseMove = (e) => {
                        const rect = scene.getBoundingClientRect();
                        const x = e.clientX - rect.left;
                        const y = e.clientY - rect.top;
                        const cx = rect.width / 2;
                        const cy = rect.height / 2;
                        const rotateX = ((y - cy) / cy) * -6;
                        const rotateY = ((x - cx) / cx) * 6;

                        gsap.to(card, {
                            rotateX, rotateY,
                            duration: 0.6,
                            ease: "power2.out"
                        });
                    };

                    const handleMouseLeave = () => {
                        gsap.to(card, {
                            rotateX: 0, rotateY: 0,
                            duration: 1.2,
                            ease: "elastic.out(1, 0.4)"
                        });
                    };

                    scene.addEventListener('mousemove', handleMouseMove);
                    scene.addEventListener('mouseleave', handleMouseLeave);

                    return () => {
                        scene.removeEventListener('mousemove', handleMouseMove);
                        scene.removeEventListener('mouseleave', handleMouseLeave);
                    };
                }, []);

                return (
                    <div className="hero-scene" ref={sceneRef} style={{ height: '500px' }}>
                        {particles.map((p, i) => (
                            <div
                                key={i}
                                className="particle"
                                ref={el => particleRefs.current[i] = el}
                                style={{ left: p.x, top: p.y, fontSize: '2rem' }}
                            >
                                {p.emoji}
                            </div>
                        ))}
                        <div className="hero-glass" ref={cardRef}>
                            <div className="hero-icon-container">
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2D6A4F" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M12 2v20M12 12c-3-3-6-3-6-3s3 0 6 3c3-3 6-3 6-3s-3 0-6 3M12 6c-3-3-6-3-6-3s3 0 6 3c3-3 6-3 6-3s-3 0-6 3"/>
                                </svg>
                            </div>
                            <h1 className="hero-title">agrimenya</h1>
                            <div className="hero-subtitle">
                                Decision and Planning Support System<br/>for Agricultural Productivity
                            </div>
                            <p className="hero-text">
                                A powerful platform designed to empower agricultural planners and decision-makers in Rwanda. Leveraging data from the Seasonal Agricultural Survey (SAS), Agricultural Household Survey (AHS), and EICV7, agrimenya provides actionable insights to improve crop yields, enhance climate resilience, and optimize resource allocation.
                            </p>
                        </div>
                        <div className="bottom-pill" ref={pillRef}>
                            AGRICULTURE & CLIMATE INTELLIGENCE
                        </div>
                    </div>
                );
            };

            const root = ReactDOM.createRoot(document.getElementById('root'));
            root.render(<Hero />);
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=520)
