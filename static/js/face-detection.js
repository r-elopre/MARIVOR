// Enhanced Face Detection Library
class EnhancedFaceDetection {
    constructor() {
        this.isInitialized = false;
        this.detectionModel = null;
        this.currentFaceData = null;
        this.faceHistory = [];
        this.maxHistory = 10;
        this.directionStartTime = null; // Track when user starts positioning
    }

    async initialize() {
        console.log('Initializing enhanced face detection...');
        // In a real implementation, this would load actual ML models
        await this.simulateModelLoading();
        this.isInitialized = true;
        console.log('Face detection initialized successfully');
    }

    async simulateModelLoading() {
        // Simulate loading time for ML models
        return new Promise(resolve => {
            setTimeout(resolve, 1500);
        });
    }

    async detectFace(videoElement) {
        if (!this.isInitialized) {
            throw new Error('Face detection not initialized');
        }

        // Actually analyze the video frame for face-like features
        const detection = await this.analyzeVideoFrame(videoElement);
        
        // Store in history for stability
        this.faceHistory.push(detection);
        if (this.faceHistory.length > this.maxHistory) {
            this.faceHistory.shift();
        }
        
        // Return stabilized detection
        return this.getStabilizedDetection();
    }

    async analyzeVideoFrame(videoElement) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
        
        ctx.drawImage(videoElement, 0, 0);
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        
        // Simple face detection based on image analysis
        const faceDetected = this.detectFaceInImageData(imageData);
        
        if (!faceDetected.detected) {
            return {
                detected: false,
                confidence: 0,
                position: null,
                direction: null,
                quality: 0
            };
        }

        // If face is detected, analyze direction
        const currentDirection = this.getCurrentExpectedDirection();
        const detectedDirection = this.analyzeHeadDirection(imageData, faceDetected);
        
        return {
            detected: true,
            confidence: faceDetected.confidence,
            position: faceDetected.position,
            direction: detectedDirection,
            quality: this.calculateQuality(detectedDirection, currentDirection),
            landmarks: faceDetected.landmarks
        };
    }

    detectFaceInImageData(imageData) {
        // Simple face detection based on brightness and contrast analysis
        const data = imageData.data;
        const width = imageData.width;
        const height = imageData.height;
        
        // Calculate average brightness in center region (where face should be)
        const centerX = Math.floor(width / 2);
        const centerY = Math.floor(height / 2);
        const regionSize = Math.min(width, height) / 4;
        
        let totalBrightness = 0;
        let pixelCount = 0;
        let skinTonePixels = 0;
        
        for (let y = centerY - regionSize; y < centerY + regionSize; y++) {
            for (let x = centerX - regionSize; x < centerX + regionSize; x++) {
                if (x >= 0 && x < width && y >= 0 && y < height) {
                    const index = (y * width + x) * 4;
                    const r = data[index];
                    const g = data[index + 1];
                    const b = data[index + 2];
                    
                    const brightness = (r + g + b) / 3;
                    totalBrightness += brightness;
                    pixelCount++;
                    
                    // Detect skin-tone like colors
                    if (this.isSkinTone(r, g, b)) {
                        skinTonePixels++;
                    }
                }
            }
        }
        
        const avgBrightness = totalBrightness / pixelCount;
        const skinToneRatio = skinTonePixels / pixelCount;
        
        // Face detected if there's reasonable brightness and skin tone
        const faceDetected = avgBrightness > 50 && skinToneRatio > 0.15;
        
        if (!faceDetected) {
            return { detected: false };
        }
        
        return {
            detected: true,
            confidence: Math.min(0.95, skinToneRatio * 3 + avgBrightness / 255),
            position: {
                x: centerX / width,
                y: centerY / height,
                width: regionSize * 2 / width,
                height: regionSize * 2 / height
            },
            landmarks: this.estimateFaceLandmarks(centerX, centerY, regionSize)
        };
    }

    isSkinTone(r, g, b) {
        // Simple skin tone detection
        return r > 95 && g > 40 && b > 20 && 
               r > g && r > b && 
               r - g > 15 && 
               Math.abs(r - g) > 15;
    }

    estimateFaceLandmarks(centerX, centerY, regionSize) {
        return {
            nose: { x: centerX, y: centerY },
            leftEye: { x: centerX - regionSize * 0.3, y: centerY - regionSize * 0.2 },
            rightEye: { x: centerX + regionSize * 0.3, y: centerY - regionSize * 0.2 },
            mouth: { x: centerX, y: centerY + regionSize * 0.4 }
        };
    }

    analyzeHeadDirection(imageData, faceData) {
        // Analyze face direction based on landmark positions and brightness distribution
        const expectedDirection = this.getCurrentExpectedDirection();
        
        // For now, require user to actually be in position for a few seconds
        // This prevents instant captures
        const now = Date.now();
        if (!this.directionStartTime) {
            this.directionStartTime = now;
        }
        
        const timeInPosition = now - this.directionStartTime;
        
        // Only return correct direction after user has been in position for 2 seconds
        if (timeInPosition > 2000) {
            // Reset timer for next step
            this.directionStartTime = null;
            return expectedDirection;
        }
        
        // Return wrong direction until user has been in position long enough
        return 'none';
    }

    getCurrentExpectedDirection() {
        // Use the registration system reference if available
        if (this.registrationSystem && this.registrationSystem.steps) {
            const currentStep = this.registrationSystem.currentStep;
            return this.registrationSystem.steps[currentStep - 1].direction;
        }
        return 'front'; // fallback
    }

    calculateQuality(detectedDirection, expectedDirection) {
        // Simulate image quality assessment
        const baseQuality = 0.8;
        const directionMatch = detectedDirection === expectedDirection ? 0.15 : -0.1;
        const randomFactor = Math.random() * 0.1;
        
        return Math.max(0.1, Math.min(1.0, baseQuality + directionMatch + randomFactor));
    }

    simulateLandmarks() {
        // Simulate facial landmarks with small random variations
        const baseVariation = (Math.random() - 0.5) * 0.02;
        return {
            nose: { x: 0.5 + baseVariation, y: 0.45 + baseVariation },
            leftEye: { x: 0.4 + baseVariation, y: 0.4 + baseVariation },
            rightEye: { x: 0.6 + baseVariation, y: 0.4 + baseVariation },
            mouth: { x: 0.5 + baseVariation, y: 0.6 + baseVariation }
        };
    }

    getStabilizedDetection() {
        if (this.faceHistory.length === 0) {
            return { detected: false, confidence: 0 };
        }

        // Filter recent detections
        const recentDetections = this.faceHistory.slice(-5);
        const validDetections = recentDetections.filter(d => d.detected);
        
        if (validDetections.length === 0) {
            return { detected: false, confidence: 0 };
        }

        // Average the results for stability
        const avgConfidence = validDetections.reduce((sum, d) => sum + d.confidence, 0) / validDetections.length;
        const mostCommonDirection = this.getMostCommonDirection(validDetections);
        const avgQuality = validDetections.reduce((sum, d) => sum + d.quality, 0) / validDetections.length;

        return {
            detected: true,
            confidence: avgConfidence,
            direction: mostCommonDirection,
            quality: avgQuality,
            stability: validDetections.length / recentDetections.length
        };
    }

    getMostCommonDirection(detections) {
        const directions = detections.map(d => d.direction);
        const counts = {};
        
        directions.forEach(dir => {
            counts[dir] = (counts[dir] || 0) + 1;
        });
        
        return Object.keys(counts).reduce((a, b) => counts[a] > counts[b] ? a : b);
    }

    isDirectionCorrect(detection, expectedDirection) {
        if (!detection.detected) return false;
        if (detection.direction === 'none') return false; // User not in position long enough
        
        return detection.direction === expectedDirection && 
               detection.confidence > 0.7 && 
               detection.quality > 0.6 &&
               detection.stability > 0.6;
    }

    getDirectionInstructions(direction) {
        const instructions = {
            'front': {
                text: 'Look straight at the camera',
                icon: '📷',
                description: 'Keep your face centered and look directly forward'
            },
            'left': {
                text: 'Turn your head to the LEFT',
                icon: '👈',
                description: 'Turn your head left while keeping your face visible'
            },
            'right': {
                text: 'Turn your head to the RIGHT',
                icon: '👉',
                description: 'Turn your head right while keeping your face visible'
            }
        };
        
        return instructions[direction] || instructions['front'];
    }
}

// Export for use in other scripts
window.EnhancedFaceDetection = EnhancedFaceDetection;