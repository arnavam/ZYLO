import React from 'react';

const FloatingShapes = () => {
    // Generate random balloons with 3D props
    const balloons = Array.from({ length: 15 }).map((_, i) => ({
        id: `balloon-${i}`,
        left: `${Math.random() * 100}%`,
        animationDelay: `${Math.random() * 5}s`,
        animationDuration: `${12 + Math.random() * 8}s`,
        size: `${60 + Math.random() * 40}px`,
        color: ['#ff4d4d', '#ff9f43', '#00d2d3', '#54a0ff', '#5f27cd'][Math.floor(Math.random() * 5)],
        z: Math.floor(Math.random() * 200) // Random depth 0 to 200px
    }));

    // Generate random birds
    const birds = Array.from({ length: 6 }).map((_, i) => ({
        id: `bird-${i}`,
        top: `${10 + Math.random() * 50}%`,
        animationDelay: `${Math.random() * 15}s`,
        animationDuration: `${20 + Math.random() * 10}s`,
        size: `${20 + Math.random() * 15}px`,
        z: Math.floor(Math.random() * 100)
    }));

    // Background Clouds (Far away)
    const backClouds = Array.from({ length: 5 }).map((_, i) => ({
        id: `cloud-back-${i}`,
        top: `${5 + Math.random() * 40}%`,
        left: `-${20 + Math.random() * 20}%`,
        animationDuration: `${60 + Math.random() * 20}s`,
        animationDelay: `-${Math.random() * 60}s`,
        scale: 0.6 + Math.random() * 0.4,
        z: -200 - Math.random() * 100 // Pushed back
    }));

    // Foreground Clouds (Close)
    const frontClouds = Array.from({ length: 3 }).map((_, i) => ({
        id: `cloud-front-${i}`,
        top: `${20 + Math.random() * 50}%`,
        left: `-${30 + Math.random() * 20}%`,
        animationDuration: `${35 + Math.random() * 15}s`,
        animationDelay: `-${Math.random() * 40}s`,
        scale: 1.2 + Math.random() * 0.8,
        z: 100 + Math.random() * 50 // Pulled forward
    }));

    return (
        <div className="floating-shapes-container" style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            overflow: 'hidden',
            zIndex: 0,
            pointerEvents: 'none',
            background: 'linear-gradient(180deg, #2980b9 0%, #6dd5fa 50%, #ffffff 100%)', // Realistic Sky
            perspective: '1000px', // key for 3D
            transformStyle: 'preserve-3d'
        }}>
            {/* Sun Effect */}
            <div className="sun-container">
                <div className="sun"></div>
                <div className="sun-flare"></div>
            </div>

            {/* Back Clouds Layer */}
            {backClouds.map(c => (
                <div
                    key={c.id}
                    className="cloud cloud-back"
                    style={{
                        top: c.top,
                        animationDuration: c.animationDuration,
                        animationDelay: c.animationDelay,
                        transform: `translateZ(${c.z}px) scale(${c.scale})`,
                        filter: 'blur(3px)'
                    }}
                >
                    <div className="cloud-bubble"></div>
                    <div className="cloud-bubble"></div>
                    <div className="cloud-bubble"></div>
                </div>
            ))}

            {/* Birds Layer */}
            {birds.map(b => (
                <div
                    key={b.id}
                    className="bird"
                    style={{
                        top: b.top,
                        fontSize: b.size,
                        animationDelay: b.animationDelay,
                        animationDuration: b.animationDuration,
                        transform: `translateZ(${b.z}px)`
                    }}
                >
                    <span style={{ display: 'inline-block', transform: 'scaleX(-1)' }}>🕊️</span>
                </div>
            ))}

            {/* Balloons Layer */}
            {balloons.map(b => (
                <div
                    key={b.id}
                    className="balloon"
                    style={{
                        left: b.left,
                        width: b.size,
                        height: `calc(${b.size} * 1.25)`,
                        // No background color here, handled in CSS for complex gradient
                        animationDelay: b.animationDelay,
                        animationDuration: b.animationDuration,
                        transform: `translateZ(${b.z}px)`,
                        '--balloon-color': b.color
                    }}
                />
            ))}

            {/* Front Clouds Layer */}
            {frontClouds.map(c => (
                <div
                    key={c.id}
                    className="cloud cloud-front"
                    style={{
                        top: c.top,
                        animationDuration: c.animationDuration,
                        animationDelay: c.animationDelay,
                        transform: `translateZ(${c.z}px) scale(${c.scale})`,
                        filter: 'blur(0px)',
                        opacity: 0.9
                    }}
                >
                    <div className="cloud-bubble"></div>
                    <div className="cloud-bubble"></div>
                    <div className="cloud-bubble"></div>
                </div>
            ))}
        </div>
    );
};

export default FloatingShapes;
