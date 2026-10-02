import streamlit.components.v1 as components

def render_react_hero():
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
            body { margin: 0; padding: 0; overflow: hidden; font-family: 'Space Grotesk', sans-serif; }
            #root { width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; background: transparent; }
            .hero-container {
                text-align: center;
                perspective: 1000px;
            }
            .hero-card {
                background: linear-gradient(135deg, rgba(255,255,255,0.4), rgba(255,255,255,0.1));
                backdrop-filter: blur(24px) saturate(180%);
                -webkit-backdrop-filter: blur(24px) saturate(180%);
                border: 1px solid rgba(255,255,255,0.4);
                border-radius: 30px;
                padding: 40px 60px;
                box-shadow: 0 20px 50px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.6);
                transform-style: preserve-3d;
                cursor: pointer;
            }
            .hero-title {
                font-size: 3rem;
                font-weight: 800;
                margin: 0 0 10px 0;
                background: linear-gradient(90deg, #1B2A1E, #2D6A4F);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                transform: translateZ(50px);
            }
            .hero-subtitle {
                font-size: 1.2rem;
                color: #4A5D4E;
                margin: 0 0 30px 0;
                transform: translateZ(30px);
            }
            .hero-button {
                background: linear-gradient(135deg, #52B788, #2D6A4F);
                color: white;
                border: none;
                padding: 15px 35px;
                font-size: 1.1rem;
                font-weight: bold;
                border-radius: 50px;
                cursor: pointer;
                transform: translateZ(40px);
                box-shadow: 0 10px 20px rgba(82, 183, 136, 0.4);
                transition: all 0.3s;
            }
            .hero-button:hover {
                box-shadow: 0 15px 30px rgba(82, 183, 136, 0.6);
            }
        </style>
    </head>
    <body>
        <div id="root"></div>
        <script type="text/babel">
            const { useEffect, useRef, useState } = React;

            const Hero = () => {
                const cardRef = useRef(null);
                const containerRef = useRef(null);

                useEffect(() => {
                    const card = cardRef.current;
                    const container = containerRef.current;
                    
                    // Initial entrance animation with GSAP
                    gsap.fromTo(card, 
                        { opacity: 0, y: 100, rotationX: -15 }, 
                        { opacity: 1, y: 0, rotationX: 0, duration: 1.5, ease: "power4.out" }
                    );

                    // 3D Hover Effect
                    const handleMouseMove = (e) => {
                        const rect = container.getBoundingClientRect();
                        const x = e.clientX - rect.left;
                        const y = e.clientY - rect.top;
                        
                        const centerX = rect.width / 2;
                        const centerY = rect.height / 2;
                        
                        const rotateX = ((y - centerY) / centerY) * -10;
                        const rotateY = ((x - centerX) / centerX) * 10;

                        gsap.to(card, {
                            rotateX: rotateX,
                            rotateY: rotateY,
                            duration: 0.5,
                            ease: "power2.out"
                        });
                    };

                    const handleMouseLeave = () => {
                        gsap.to(card, {
                            rotateX: 0,
                            rotateY: 0,
                            duration: 1,
                            ease: "elastic.out(1, 0.3)"
                        });
                    };

                    container.addEventListener('mousemove', handleMouseMove);
                    container.addEventListener('mouseleave', handleMouseLeave);

                    return () => {
                        container.removeEventListener('mousemove', handleMouseMove);
                        container.removeEventListener('mouseleave', handleMouseLeave);
                    };
                }, []);

                return (
                    <div className="hero-container" ref={containerRef} style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <div className="hero-card" ref={cardRef}>
                            <h1 className="hero-title">Welcome to Agrimenya</h1>
                            <p className="hero-subtitle">Interactive React + GSAP Component in Streamlit</p>
                            <button className="hero-button" onClick={() => alert('React Button Clicked!')}>
                                Get Started
                            </button>
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
    components.html(html_code, height=450)
