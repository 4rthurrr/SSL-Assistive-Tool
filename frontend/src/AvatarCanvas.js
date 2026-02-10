import React, { useRef, useEffect, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { useGLTF, OrbitControls, Environment, ContactShadows } from '@react-three/drei';
import * as THREE from 'three';

function AvatarModel({ url, landmarks }) {
    const { scene } = useGLTF(url);
    const modelRef = useRef();
    const bones = useRef({});

    // Map common Mixamo/GLB bone names to our internal standardized names
    // This helps if the model has different naming conventions
    const boneMap = useMemo(() => ({
        // Mixamo / Standard
        'Hips': 'Hips',
        'Spine': 'Spine',
        'Spine1': 'Spine1',
        'Spine2': 'Spine2',
        'Neck': 'Neck',
        'Head': 'Head',

        'LeftShoulder': 'LeftShoulder',
        'LeftArm': 'LeftArm',
        'LeftForeArm': 'LeftForeArm',
        'LeftHand': 'LeftHand',

        'RightShoulder': 'RightShoulder',
        'RightArm': 'RightArm',
        'RightForeArm': 'RightForeArm',
        'RightHand': 'RightHand',

        'LeftUpLeg': 'LeftUpLeg',
        'LeftLeg': 'LeftLeg',
        'LeftFoot': 'LeftFoot',

        'RightUpLeg': 'RightUpLeg',
        'RightLeg': 'RightLeg',
        'RightFoot': 'RightFoot'
    }), []);

    useEffect(() => {
        if (modelRef.current) {
            modelRef.current.traverse((child) => {
                if (child.isBone) {
                    // console.log("Found Bone:", child.name); // Debugging
                    bones.current[child.name] = child;
                }
            });
        }
    }, [scene]);

    useFrame((state, delta) => {
        const smoothSpeed = 15;
        const lerpFactor = THREE.MathUtils.clamp(1 - Math.exp(-smoothSpeed * delta), 0, 1);

        // Idle Animation
        if (modelRef.current && (!landmarks || landmarks.length === 0)) {
            const time = state.clock.elapsedTime;
            // Breathe
            modelRef.current.position.y = Math.sin(time) * 0.02 - 1;
            // Slight sway
            if (bones.current['Spine']) {
                bones.current['Spine'].rotation.z = Math.sin(time * 0.5) * 0.05;
            }
            return;
        }

        // Animate from Landmarks
        if (landmarks && landmarks.length > 0) {
            const fps = 24;
            const frameIndex = Math.floor(state.clock.elapsedTime * fps) % landmarks.length;
            const currentFrame = landmarks[frameIndex];

            // Prefer World Landmarks (Metric 3D) for better rotation calcs
            const lm = currentFrame.pose_world || currentFrame.pose;
            const isWorld = !!currentFrame.pose_world;

            if (lm) {
                // Helper to get vector from landmark
                const getVec = (index) => {
                    const p = lm[index];
                    if (!p) return new THREE.Vector3();
                    // MediaPipe coords: 
                    // World: x (right), y (up), z (backward)? No, typically MP world is:
                    // x range approx -1 to 1 (left/right)
                    // y range approx -1 to 1 (up/down)
                    // z range (depth)
                    // We need to map this to ThreeJS (y-up)
                    if (isWorld) {
                        // Invert X for mirroring self-view
                        // Damping Z axis to prevent "zombie reaching" effect
                        return new THREE.Vector3(-p.x, -p.y, -p.z * 0.6);
                    } else {
                        // Screen norms (y is down in screen space)
                        return new THREE.Vector3(
                            (p.x - 0.5) * -1,
                            (p.y - 0.5) * -1,
                            (p.z || 0) * -1
                        );
                    }
                };

                const rigBone = (boneName, startIdx, endIdx, restDir) => {
                    let bone = bones.current[boneName];
                    if (!bone) {
                        const keys = Object.keys(bones.current);
                        const match = keys.find(k => k.includes(boneName));
                        if (match) bone = bones.current[match];
                    }
                    if (!bone) return;

                    const start = getVec(startIdx);
                    const end = getVec(endIdx);

                    // 1. Current Direction in World Space
                    const currentDir = new THREE.Vector3().subVectors(end, start).normalize();

                    // 2. Convert to Parent's Local Space
                    // If the bone has a parent, we must calculate the rotation relative to it.
                    if (bone.parent) {
                        const parentQuat = new THREE.Quaternion();
                        bone.parent.getWorldQuaternion(parentQuat);
                        const invParentQuat = parentQuat.clone().invert();
                        currentDir.applyQuaternion(invParentQuat);
                    }

                    // 3. Calculate Rotation from Rest Direction to Local Target Direction
                    const targetQ = new THREE.Quaternion().setFromUnitVectors(restDir, currentDir);

                    // 4. Apply Rotation
                    bone.quaternion.slerp(targetQ, lerpFactor);
                };

                // --- Upper Body Rigging ---

                // Spine/Torso (Approximate using shoulders/hips)
                const leftHip = getVec(23);
                const rightHip = getVec(24);
                const leftShoulder = getVec(11);
                const rightShoulder = getVec(12);

                const midHip = new THREE.Vector3().addVectors(leftHip, rightHip).multiplyScalar(0.5);
                const midShoulder = new THREE.Vector3().addVectors(leftShoulder, rightShoulder).multiplyScalar(0.5);
                const spineDir = new THREE.Vector3().subVectors(midShoulder, midHip).normalize();

                // Mixamo Spines usually point UP (+Y)
                // Mixamo Spines usually point UP (+Y)
                if (bones.current['Spine']) {
                    const targetQ = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), spineDir);
                    bones.current['Spine'].quaternion.slerp(targetQ, lerpFactor);
                }

                // Head
                const nose = getVec(0);
                const headDir = new THREE.Vector3().subVectors(nose, midShoulder).normalize();
                // Usually points UP (+Y) or Forward (+Z) depending on bone roll. 
                // Mixamo Hips->Head chain is typically Y-axis aligned.
                if (bones.current['Head'] || bones.current['Neck']) {
                    const b = bones.current['Head'] || bones.current['Neck'];
                    const targetQ = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), headDir);
                    b.quaternion.slerp(targetQ, lerpFactor);
                }

                // Arms (Rest Pose: T-Pose)
                // Right Arm: Points +X
                rigBone('RightArm', 12, 14, new THREE.Vector3(1, 0, 0));
                rigBone('RightForeArm', 14, 16, new THREE.Vector3(1, 0, 0));

                // Left Arm: Points -X
                rigBone('LeftArm', 11, 13, new THREE.Vector3(-1, 0, 0));
                rigBone('LeftForeArm', 13, 15, new THREE.Vector3(-1, 0, 0));
            }
        }
    });

    return <primitive object={scene} ref={modelRef} position={[0, -1, 0]} scale={2} />;
}

export default function AvatarCanvas({ landmarks }) {
    return (
        <div style={{ width: '100%', height: '500px', background: 'linear-gradient(to bottom, #dbe4f0 0%, #ffffff 100%)', borderRadius: '20px', overflow: 'hidden', boxShadow: '0 10px 30px rgba(0,0,0,0.1)' }}>
            <Canvas camera={{ position: [0, 1.5, 4], fov: 45 }}>
                <ambientLight intensity={0.6} />
                <directionalLight position={[5, 10, 5]} intensity={1} castShadow />
                <spotLight position={[0, 5, 2]} intensity={0.5} angle={0.3} penumbra={1} />

                <AvatarModel url="/avatar.glb" landmarks={landmarks} />

                <ContactShadows opacity={0.4} scale={10} blur={2} far={4} resolution={256} color="#000000" />
                <OrbitControls
                    enableZoom={true}
                    minPolarAngle={Math.PI / 4}
                    maxPolarAngle={Math.PI / 2}
                    target={[0, 1, 0]}
                    enablePan={false}
                />
                <Environment preset="city" />
            </Canvas>
        </div>
    );
}
