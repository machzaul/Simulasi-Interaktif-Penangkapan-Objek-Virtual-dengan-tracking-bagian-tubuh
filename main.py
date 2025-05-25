import cv2
import mediapipe as mp
import random
import time

# Setup Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)

# Load keranjang
keranjang_img = cv2.imread('keranjang.png', cv2.IMREAD_UNCHANGED)
keranjang_img = cv2.resize(keranjang_img, (150, 150))

ball_radius = 30
colors = [(0, 0, 255), (0, 255, 255), (0, 255, 0), (255, 0, 0)]

score = 0
balls = []

def create_ball():
    return {
        "x": random.randint(ball_radius, 640 - ball_radius),
        "y": -ball_radius,
        "color": random.choice(colors),
        "speed": random.randint(5, 10)
    }

for _ in range(4):
    balls.append(create_ball())

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    ih, iw, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    nose_x, nose_y = None, None

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            nose = face_landmarks.landmark[1]
            nose_x = int(nose.x * iw)
            nose_y = int(nose.y * ih)

    if nose_x and nose_y:
        top_left_x = nose_x - keranjang_img.shape[1] // 2
        top_left_y = nose_y - keranjang_img.shape[0] // 2

        top_left_x = max(0, min(top_left_x, iw - keranjang_img.shape[1]))
        top_left_y = max(0, min(top_left_y, ih - keranjang_img.shape[0]))

        if keranjang_img.shape[2] == 4:
            alpha = keranjang_img[:, :, 3] / 255.0
            for c in range(3):
                frame[top_left_y:top_left_y+150, top_left_x:top_left_x+150, c] = (
                    alpha * keranjang_img[:, :, c] +
                    (1 - alpha) * frame[top_left_y:top_left_y+150, top_left_x:top_left_x+150, c]
                )

    for ball in balls[:]:
        ball["y"] += ball["speed"]
        if ball["y"] > ih:
            balls.remove(ball)
            balls.append(create_ball())
            continue

        if nose_x and nose_y:
            dx = ball["x"] - nose_x
            dy = ball["y"] - nose_y
            if dx * dx + dy * dy < ball_radius ** 2:
                if ball["color"] == (255, 0, 0):
                    score += 1
                    balls.remove(ball)
                    balls.append(create_ball())
                else:
                    cv2.putText(frame, "GAME OVER", (iw // 2 - 100, ih // 2),
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                    cv2.imshow("Catch the Blue Ball", frame)
                    cv2.waitKey(2000)
                    cap.release()
                    cv2.destroyAllWindows()
                    exit()

        cv2.circle(frame, (ball["x"], ball["y"]), ball_radius, ball["color"], -1)

    cv2.putText(frame, f"Score: {score}", (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    cv2.imshow("Catch the Blue Ball", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()