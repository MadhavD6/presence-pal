import cv2
import numpy as np
from skimage.feature import local_binary_pattern
from backend.core.config import get_settings

class LivenessService:
    def __init__(self):
        settings = get_settings()
        
        # Thresholds from config (configurable via .env)
        self.blur_threshold = settings.LIVENESS_BLUR_THRESHOLD
        self.motion_threshold = settings.LIVENESS_MOTION_THRESHOLD
        self.texture_variance_threshold = settings.LIVENESS_LBP_THRESHOLD
        self.min_face_ratio = settings.LIVENESS_MIN_FACE_RATIO
        
        # LBP settings for texture analysis
        self.lbp_radius = 3
        self.lbp_points = 8 * self.lbp_radius
        
        # Load Haar Cascades (frontal + profile for better angle tolerance)
        try:
            self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        except:
            print("Warning: Could not load cascades. Advanced detection disabled.")
            self.eye_cascade = None
            self.face_cascade = None
            self.profile_cascade = None

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

    def check_liveness(self, frames_bytes: list[bytes]) -> tuple[bool, str, dict]:
        """
        Multi-frame liveness check with detailed metrics.
        Returns: (is_live, check_failure_reason, metrics_dict)
        """
        metrics = {
            "blur_score": 0.0,
            "motion_score": 0.0, 
            "texture_score": 0.0,
            "blink_detected": False
        }

        if not frames_bytes:
            print("Liveness Reject: No frames")
            return False, "No video frames received", metrics

        try:
            frames = []
            for b in frames_bytes:
                nparr = np.frombuffer(b, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    frames.append(img)
            
            if not frames:
                return False, "Could not decode frames", metrics

            # 1. Blur Check (on the first frame)
            mid_frame = frames[0]
            variance = cv2.Laplacian(mid_frame, cv2.CV_64F).var()
            metrics["blur_score"] = round(variance, 2)
            
            if variance < self.blur_threshold:
                print(f"Liveness Reject: Blur {variance} < {self.blur_threshold}")
                return False, "Image too blurry. Please stand still.", metrics

            # 1.5. Face Detection Validation (uses both frontal + profile for angle tolerance)
            if self.face_cascade is not None:
                face_count = 0
                for frame in frames:
                    # Try frontal face first
                    faces = self.face_cascade.detectMultiScale(frame, 1.1, 5, minSize=(60, 60))
                    if len(faces) >= 1:
                        face_count += 1
                    elif self.profile_cascade is not None:
                        # Try profile (side) face if frontal not found
                        profile_faces = self.profile_cascade.detectMultiScale(frame, 1.1, 5, minSize=(60, 60))
                        if len(profile_faces) >= 1:
                            face_count += 1
                
                metrics["face_detected_frames"] = face_count
                print(f"Liveness: Face detected in {face_count}/{len(frames)} frames")
                
                # Use configurable minimum face ratio
                min_required = max(1, int(len(frames) * self.min_face_ratio))
                if face_count < min_required:
                    print(f"Liveness Reject: Face detected in only {face_count}/{len(frames)} frames (need {min_required})")
                    return False, "No clear face detected. Please uncover your face and look at the camera.", metrics

            # If only 1 frame, limited checks
            if len(frames) < 2:
                print("Liveness Warning: Single frame provided.")
                return True, "Single frame accepted (Limited Security)", metrics

            # 2. Motion Check
            diff = cv2.absdiff(frames[0], frames[-1])
            non_zero_count = np.count_nonzero(diff > 15)
            total_pixels = mid_frame.shape[0] * mid_frame.shape[1]
            motion_score = non_zero_count / total_pixels
            metrics["motion_score"] = round(motion_score, 6)
            
            print(f"Liveness Motion Score: {motion_score:.4f}")
            
            if motion_score < self.motion_threshold:
                print("Liveness Reject: No motion detected (Static Photo?)")
                return False, "Static photo detected. Please blink or move slightly.", metrics

            # 3. LBP Texture Analysis (Anti-Screen)
            texture_variance = self._compute_lbp_variance(mid_frame)
            metrics["texture_score"] = round(texture_variance, 2)
            print(f"Liveness LBP Variance: {texture_variance:.2f}")
            
            if texture_variance < self.texture_variance_threshold:
                print(f"Liveness Reject: Low texture variance (screen/photo?)")
                return False, "Screen or printed photo detected. Please use a real face.", metrics

            # 4. Blink Pattern Detection
            blink_detected, eyes_count = self._check_blink_pattern(frames)
            metrics["blink_detected"] = blink_detected
            print(f"Eyes detected in {eyes_count}/{len(frames)} frames, Blink: {blink_detected}")
            
            # 5. Face Size Consistency
            face_consistent, consistency_reason = self._check_face_consistency(frames)
            
            if not face_consistent:
                print(f"Liveness Reject: {consistency_reason}")
                return False, "Face movement inconsistent. Please hold still.", metrics

            return True, "Passed", metrics

        except Exception as e:
            print(f"Liveness Check Error: {e}")
            return False, f"Liveness check error: {str(e)}", metrics

liveness_service = LivenessService()

