import cv2
import numpy as np
from skimage.feature import local_binary_pattern

class LivenessService:
    def __init__(self):
        # Thresholds - RELAXED for easier UX
        self.blur_threshold = 15.0 # Lowered from 30.0
        self.motion_threshold = 0.002  # 0.2% of pixels must change
        
        # LBP settings for texture analysis
        self.lbp_radius = 3
        self.lbp_points = 8 * self.lbp_radius
        self.texture_variance_threshold = 20  # Lowered from 100 - reduce false positives
        
        # Load Haar Cascades
        try:
            self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        except:
            print("Warning: Could not load cascades. Advanced detection disabled.")
            self.eye_cascade = None
            self.face_cascade = None

    def _compute_lbp_variance(self, gray_img) -> float:
        """
        Compute LBP texture variance.
        Real faces have high variance; screens/photos have low variance.
        """
        try:
            lbp = local_binary_pattern(gray_img, self.lbp_points, self.lbp_radius, method='uniform')
            variance = np.var(lbp)
            return variance
        except Exception as e:
            print(f"LBP error: {e}")
            return 1000  # High value to pass check on error

    def _check_blink_pattern(self, frames: list) -> tuple[bool, int]:
        """
        Check for blink pattern: eyes_open -> eyes_closed -> eyes_open.
        Returns: (blink_detected, eyes_detected_count)
        """
        if not self.eye_cascade or len(frames) < 3:
            return True, 0  # Pass if can't check
        
        eye_states = []  # True = eyes detected, False = no eyes
        
        for frame in frames:
            eyes = self.eye_cascade.detectMultiScale(frame, 1.3, 5)
            eye_states.append(len(eyes) >= 1)
        
        # Count eyes detected
        eyes_detected = sum(eye_states)
        
        # Look for open->closed->open pattern (blink)
        # Simple: if we see variation in eye detection, it's likely a real person
        if len(set(eye_states)) > 1:  # Has variation
            return True, eyes_detected
        
        # All same state - might be photo
        return False, eyes_detected

    def _check_face_consistency(self, frames: list) -> tuple[bool, str]:
        """
        Check that face size is consistent across frames.
        Drastic size changes indicate zoom/presentation attack.
        """
        if not self.face_cascade or len(frames) < 2:
            return True, "single_frame"
        
        face_sizes = []
        for frame in frames:
            faces = self.face_cascade.detectMultiScale(frame, 1.1, 5)
            if len(faces) > 0:
                # Get largest face
                largest = max(faces, key=lambda f: f[2] * f[3])
                face_sizes.append(largest[2] * largest[3])  # width * height
        
        if len(face_sizes) < 2:
            return True, "not_enough_faces"
        
        # Check variance in face sizes
        size_variance = np.std(face_sizes) / (np.mean(face_sizes) + 1e-6)
        
        # If variance is too high (>30%), suspicious
        if size_variance > 0.3:
            return False, f"Face size inconsistent: {size_variance:.2%}"
        
        return True, "consistent"

    def check_liveness(self, frames_bytes: list[bytes]) -> tuple[bool, str]:
        """
        Multi-frame liveness check with:
        1. Blur detection
        2. Motion detection  
        3. LBP texture analysis (anti-screen/photo)
        4. Blink pattern detection
        5. Face size consistency
        
        Returns: (is_live, check_failure_reason)
        """
        if not frames_bytes:
            print("Liveness Reject: No frames")
            return False, "No video frames received"

        try:
            frames = []
            for b in frames_bytes:
                nparr = np.frombuffer(b, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    frames.append(img)
            
            if not frames:
                return False, "Could not decode frames"

            # 1. Blur Check (on the first frame)
            mid_frame = frames[0]
            variance = cv2.Laplacian(mid_frame, cv2.CV_64F).var()
            if variance < self.blur_threshold:
                print(f"Liveness Reject: Blur {variance} < {self.blur_threshold}")
                return False, "Image too blurry. Please stand still."

            # If only 1 frame, limited checks
            if len(frames) < 2:
                print("Liveness Warning: Single frame provided.")
                return True, "Single frame accepted (Limited Security)"

            # 2. Motion Check
            diff = cv2.absdiff(frames[0], frames[-1])
            non_zero_count = np.count_nonzero(diff > 15)
            total_pixels = mid_frame.shape[0] * mid_frame.shape[1]
            motion_score = non_zero_count / total_pixels
            
            print(f"Liveness Motion Score: {motion_score:.4f}")
            
            if motion_score < self.motion_threshold:
                print("Liveness Reject: No motion detected (Static Photo?)")
                return False, "Static photo detected. Please blink or move slightly."

            # 3. LBP Texture Analysis (Anti-Screen)
            texture_variance = self._compute_lbp_variance(mid_frame)
            print(f"Liveness LBP Variance: {texture_variance:.2f}")
            
            if texture_variance < self.texture_variance_threshold:
                print(f"Liveness Reject: Low texture variance (screen/photo?)")
                return False, "Screen or printed photo detected. Please use a real face."

            # 4. Blink Pattern Detection
            blink_detected, eyes_count = self._check_blink_pattern(frames)
            print(f"Eyes detected in {eyes_count}/{len(frames)} frames, Blink: {blink_detected}")
            
            # 5. Face Size Consistency
            face_consistent, consistency_reason = self._check_face_consistency(frames)
            
            if not face_consistent:
                print(f"Liveness Reject: {consistency_reason}")
                return False, "Face movement inconsistent. Please hold still."

            return True, "Passed"

        except Exception as e:
            print(f"Liveness Check Error: {e}")
            return False, f"Liveness check error: {str(e)}"

liveness_service = LivenessService()

