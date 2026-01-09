import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Cloud, Environment, Sparkles, Sky } from '@react-three/drei';
import * as THREE from 'three';

const Balloon = ({ position, color, speed, offset }) => {
    const mesh = useRef();

    useFrame((state) => {
        const t = state.clock.getElapsedTime();
        const yBase = position[1];
        const travel = (t * speed + offset) % 35;
        mesh.current.position.y = yBase + travel - 15;
        mesh.current.position.x = position[0] + Math.sin(t * 0.5 + offset) * 1.5;
        mesh.current.rotation.x = Math.sin(t * 0.3 + offset) * 0.1;
        mesh.current.rotation.z = Math.sin(t * 0.5 + offset) * 0.1;
    });

    return (
        <group ref={mesh} position={position}>
            <mesh castShadow receiveShadow>
                <sphereGeometry args={[0.8, 64, 64]} />
                <meshPhysicalMaterial
                    color={color}
                    clearcoat={1}
                    clearcoatRoughness={0.15}
                    metalness={0.1}
                    roughness={0.2}
                    transmission={0.1}
                    thickness={2}
                    envMapIntensity={1.5}
                />
            </mesh>
            <mesh position={[0, -0.8, 0]} rotation={[Math.PI, 0, 0]}>
                <coneGeometry args={[0.12, 0.2, 32]} />
                <meshStandardMaterial color={color} />
            </mesh>
            <mesh position={[0, -2, 0]}>
                <cylinderGeometry args={[0.01, 0.01, 2.5]} />
                <meshBasicMaterial color="#fff" transparent opacity={0.4} />
            </mesh>
        </group>
    );
};

// Procedural Seagull/Bird
const Bird = ({ position, speed, range, scale = 1 }) => {
    const group = useRef();
    const leftWing = useRef();
    const rightWing = useRef();

    useFrame((state) => {
        const t = state.clock.getElapsedTime();
        // Flight path
        group.current.position.x = position[0] + Math.sin(t * speed) * range;
        group.current.position.z = position[2] + Math.cos(t * speed) * (range * 0.4);
        group.current.position.y = position[1] + Math.sin(t * speed * 4) * 0.5;

        // Orientation
        group.current.rotation.y = Math.atan2(
            Math.cos(t * speed) * (range * 0.4),
            Math.sin(t * speed) * range
        ) + Math.PI / 2;
        group.current.rotation.z = Math.sin(t * speed * 4) * 0.1; // Banking

        // Flapping (Sine wave for wings)
        const flap = Math.sin(t * 15);
        if (leftWing.current && rightWing.current) {
            leftWing.current.rotation.z = flap * 0.5;
            rightWing.current.rotation.z = -flap * 0.5;
        }
    });

    return (
        <group ref={group} scale={scale}>
            {/* Body */}
            <mesh position={[0, 0, 0.2]} rotation={[1.5, 0, 0]} castShadow>
                <coneGeometry args={[0.15, 0.6, 16]} />
                <meshStandardMaterial color="#fff" />
            </mesh>
            {/* Head */}
            <mesh position={[0, 0.1, 0.5]}>
                <sphereGeometry args={[0.12, 16, 16]} />
                <meshStandardMaterial color="#fff" />
            </mesh>
            {/* Beak */}
            <mesh position={[0, 0.08, 0.65]} rotation={[1.5, 0, 0]}>
                <coneGeometry args={[0.04, 0.15, 16]} />
                <meshStandardMaterial color="#f1c40f" />
            </mesh>

            {/* Wings Container */}
            <group position={[0, 0.1, 0.1]}>
                {/* Left Wing */}
                <group ref={leftWing} position={[0.1, 0, 0]}>
                    <mesh position={[0.4, 0, 0]} rotation={[0, 0, -0.2]}>
                        <boxGeometry args={[0.8, 0.05, 0.3]} />
                        <meshStandardMaterial color="#eee" />
                    </mesh>
                </group>
                {/* Right Wing */}
                <group ref={rightWing} position={[-0.1, 0, 0]}>
                    <mesh position={[-0.4, 0, 0]} rotation={[0, 0, 0.2]}>
                        <boxGeometry args={[0.8, 0.05, 0.3]} />
                        <meshStandardMaterial color="#eee" />
                    </mesh>
                </group>
            </group>
        </group>
    )
}

const ThreeDBackground = ({ show = true }) => {
    const balloonData = useMemo(() => Array.from({ length: 25 }).map(() => ({
        position: [(Math.random() - 0.5) * 20, -10, (Math.random() - 0.5) * 10 - 5],
        // Vibrant Palette
        color: ['#FF0055', '#00E5FF', '#FFD500', '#00FF99', '#AA00FF', '#FF5500'][Math.floor(Math.random() * 6)],
        speed: 0.5 + Math.random() * 0.8,
        offset: Math.random() * 100
    })), []);

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            zIndex: 0,
            pointerEvents: 'none',
            background: '#87CEEB',
            opacity: show ? 1 : 0,
            visibility: show ? 'visible' : 'hidden', // Hide completely when not needed to prevent GPU churn if possible, though opacity 0 might still render.
            transition: 'opacity 0.8s ease-in-out' // Smooth fade
        }}>
            <Canvas shadows camera={{ position: [0, 0, 8], fov: 60 }} dpr={[1, 2]} gl={{ toneMapping: THREE.ACESFilmicToneMapping, toneMappingExposure: 0.8 }}>
                <fog attach="fog" args={['#87CEEB', 5, 25]} />

                {/* Realistic Sun & Sky */}
                <ambientLight intensity={0.8} />
                <directionalLight
                    position={[50, 50, 25]}
                    intensity={2}
                    castShadow
                    shadow-bias={-0.0001}
                />
                <Environment preset="city" />

                {/*
            Real World Sky Config:
            - Rayleigh: Controls the "blueness". Lower = Darker/Space-like, Higher = Redder/Sunset. ~0.5-1 is deep blue.
            - Turbidity: Haze. Lower = Clearer.
        */}
                <Sky
                    distance={450000}
                    sunPosition={[50, 50, 25]}
                    inclination={0}
                    azimuth={0.25}
                    turbidity={0.1}
                    rayleigh={0.5}
                    mieCoefficient={0.005}
                    mieDirectionalG={0.8}
                />

                {/* Clouds - White and Fluffy */}
                <Cloud position={[-8, 2, -10]} speed={0.1} opacity={0.8} segments={20} bounds={[10, 2, 2]} color="#ffffff" />
                <Cloud position={[8, 4, -15]} speed={0.1} opacity={0.6} segments={20} bounds={[10, 2, 2]} color="#ffffff" />
                <Cloud position={[0, 8, -12]} speed={0.05} opacity={0.5} segments={20} bounds={[10, 2, 2]} color="#ffffff" />

                {/* Floating Particles - Sun Motes */}
                <Sparkles count={200} scale={20} size={2} speed={0.4} opacity={0.6} color="#FFF" />

                {balloonData.map((b, i) => (
                    <Balloon key={i} {...b} />
                ))}

                {/* Birds */}
                <Bird position={[0, 3, -2]} speed={0.4} range={5} scale={0.4} />
                <Bird position={[3, 5, -5]} speed={0.3} range={8} scale={0.3} />
                <Bird position={[-4, 1, -8]} speed={0.5} range={3} scale={0.3} />

            </Canvas>
        </div>
    );
};

export default ThreeDBackground;