import cv2
import numpy as np
import math

class DrawIOActorDetector:
    def __init__(self, image_path, debug=False):
        self.debug = debug

        # Load image
        img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Handle transparency
        if len(img.shape) == 3 and img.shape[2] == 4:
            white_bg = np.ones((img.shape[0], img.shape[1], 3), dtype=np.uint8) * 255
            alpha = img[:, :, 3] / 255.0
            for c in range(3):
                white_bg[:, :, c] = (1 - alpha) * white_bg[:, :, c] + alpha * img[:, :, c]
            self.image = white_bg
        else:
            self.image = img

        self.height, self.width = self.image.shape[:2]
        print(f"Image loaded: {self.width}x{self.height}")

    # ------------------------------------------------------------
    # Preprocess
    # ------------------------------------------------------------
    def preprocess(self):
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        if np.mean(gray) > 127:
            gray = 255 - gray
        _, binary = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
        return binary

    # ------------------------------------------------------------
    # HEAD DETECTION (correct ROI, robust)
    # ------------------------------------------------------------
    def verify_head_circle(self, binary, actor_pos, actor_id=None,
                           search_height=35, search_width=50):

        x, y = actor_pos
        
        # ROI only above actor
        y1 = max(0, y - search_height)
        y2 = y
        x1 = max(0, x - search_width // 2)
        x2 = min(self.width, x + search_width // 2)

        roi = binary[y1:y2, x1:x2]
        if roi.size == 0:
            return False, None, (x1, y1, x2, y2)

        if self.debug:
            cv2.imwrite(f"debug_roi_actor{actor_id}.png", roi)
            print(f"[DEBUG] ROI actor {actor_id}: debug_roi_actor{actor_id}.png")

        roi_blur = cv2.GaussianBlur(roi, (5,5), 0)

        circles = cv2.HoughCircles(
            roi_blur,
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=20,
            param1=80,
            param2=18,
            minRadius=4,
            maxRadius=12
        )

        if circles is None:
            if self.debug:
                print(f"[DEBUG] Actor {actor_id}: ❌ No head")
            return False, None, (x1, y1, x2, y2)

        circles = np.uint16(np.around(circles[0]))
        circles_abs = []
        for (cx, cy, r) in circles:
            global_x = x1 + cx
            global_y = y1 + cy
            circles_abs.append((global_x, global_y, r))

        # Filter by geometric correctness (head above actor)
        circles_abs = [
            (cx, cy, r)
            for (cx, cy, r) in circles_abs
            if cy < y and abs(cx - x) < 25
        ]

        if self.debug:
            out = cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR)
            if len(circles_abs) > 0:
                for (cx, cy, r) in circles:
                    cv2.circle(out, (cx, cy), r, (0,255,0), 2)
            cv2.imwrite(f"debug_roi_actor{actor_id}_circles.png", out)
            print(f"[DEBUG] Circles actor {actor_id}: debug_roi_actor{actor_id}_circles.png")

        if len(circles_abs) == 0:
            return False, None, (x1, y1, x2, y2)

        best_circle = min(circles_abs, key=lambda c: abs(c[0]-x))
        return True, best_circle, (x1, y1, x2, y2)

    # ------------------------------------------------------------
    # TEXT RECOGNITION BELOW ACTOR (EasyOCR)
    # ------------------------------------------------------------
    def extract_text_below(self, actor_pos, actor_id=None):
        x, y = actor_pos

        roi_h = 80
        roi_w = 160

        x1 = max(0, x - roi_w // 2)
        x2 = min(self.width, x + roi_w // 2)
        y1 = y + 10
        y2 = min(self.height, y + roi_h)

        roi = self.image[y1:y2, x1:x2]

        if roi.size == 0:
            return "", None

        if self.debug:
            cv2.imwrite(f"debug_text_roi_actor{actor_id}.png", roi)
            print(f"[DEBUG] Texto ROI actor {actor_id}: debug_text_roi_actor{actor_id}.png")

        import easyocr
        reader = easyocr.Reader(['en', 'es'], gpu=False)
        result = reader.readtext(roi)
        text = " ".join([txt[1] for txt in result])
        return text.strip(), (x1, y1, x2, y2)

    # ------------------------------------------------------------
    # Template detection
    # ------------------------------------------------------------
    def find_actors_by_template(self, binary):
        actors = []
        template_sizes = [40, 50, 60, 70, 80]

        for size in template_sizes:
            template = np.zeros((size, size), dtype=np.uint8)
            cx = size // 2

            # head
            head_r = size // 6
            cv2.circle(template, (cx, head_r), head_r, 255, 1)
            # body
            cv2.line(template, (cx, head_r*2), (cx, size*2//3), 255, 1)
            # arms
            arm_len = size // 3
            cv2.line(template, (cx-arm_len, head_r*2+size//10),
                               (cx+arm_len, head_r*2+size//10), 255, 1)

            res = cv2.matchTemplate(binary, template, cv2.TM_CCOEFF_NORMED)
            locs = np.where(res >= 0.41)

            for pt in zip(*locs[::-1]):
                center = (pt[0]+size//2, pt[1]+size//2)
                if all(math.dist(center, a) > 15 for a in actors):
                    actors.append(center)

        return actors

    # ------------------------------------------------------------
    # MAIN DETECTION PIPELINE
    # ------------------------------------------------------------
    def detect_actors(self):
        binary = self.preprocess()

        print("Processing...")
        actors = self.find_actors_by_template(binary)
        print(f"Template detection: {len(actors)}")

        verified = []
        debug_info = []
        text_results = []

        for idx, actor_pos in enumerate(actors):
            ok, circle, roi_box = self.verify_head_circle(binary, actor_pos, idx+1)
            
            if ok:
                text, text_roi = self.extract_text_below(actor_pos, idx+1)
                text_results.append((idx+1, text))
                verified.append(actor_pos)
            else:
                text_results.append((idx+1, ""))
                text_roi = None

            debug_info.append((actor_pos, roi_box, circle, text_results[-1], text_roi))

        # Remove near duplicates
        final_actors = []
        for a in verified:
            if all(math.dist(a, b) > 25 for b in final_actors):
                final_actors.append(a)

        print(f"FINAL count: {len(final_actors)}")

        print("\n=== RESULTADOS ===")
        for actor_id, text in text_results:
            print(f"Actor {actor_id} – {text}")

        self.draw_results(binary, final_actors, debug_info)
        return len(final_actors), final_actors, text_results

    # ------------------------------------------------------------
    # FINAL OUTPUT DRAWING
    # ------------------------------------------------------------
    def draw_results(self, binary, actors, debug_info):
        out = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)

        for idx, (actor_pos, roi_box, head_circle, (_, text), text_roi) in enumerate(debug_info):
            x, y = actor_pos
            x1, y1, x2, y2 = roi_box

            # draw actor
            cv2.circle(out, (x,y), 20, (0,255,0), 2)
            cv2.putText(out, f"A{idx+1}", (x-15,y-25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,(0,255,0),2)

            # draw roi box (head)
            cv2.rectangle(out, (x1,y1), (x2,y2), (255,0,0), 1)

            # draw head circle if exists
            if head_circle is not None:
                cx,cy,r = head_circle
                cv2.circle(out, (cx,cy), r, (0,255,255), 2)
                cv2.putText(out, "HEAD", (cx-10,cy-r-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4,(0,255,255),1)
            else:
                cv2.putText(out, "NO HEAD", (x1,y1-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4,(0,0,255),1)

            # draw text ROI and text
            if text_roi is not None and text != "":
                tx1, ty1, tx2, ty2 = text_roi
                cv2.rectangle(out, (tx1, ty1), (tx2, ty2), (0,128,255), 1)
                cv2.putText(out, text, (tx1, ty2 + 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,128,255), 1)

        cv2.imwrite("actors_debug_output.png", out)
        print("Saved: actors_debug_output.png")


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python script.py <image> [debug]")
        return

    image_path = sys.argv[1]
    debug = len(sys.argv) > 2 and sys.argv[2].lower()=="debug"

    detector = DrawIOActorDetector(image_path, debug)
    detector.detect_actors()


if __name__ == "__main__":
    main()
