import cv2
import mediapipe as mp
import random
import time

# Inisialisasi MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)

# Muat gambar keranjang
keranjang_img = cv2.imread('keranjang.png', cv2.IMREAD_UNCHANGED)
keranjang_img = cv2.resize(keranjang_img, (150, 150))

# Muat gambar bola berdasarkan warna
ball_images = {
    (255, 0, 0): cv2.imread('bolabiru.png', cv2.IMREAD_UNCHANGED),
    (0, 255, 255): cv2.imread('bolakuning.png', cv2.IMREAD_UNCHANGED),
    (0, 255, 0): cv2.imread('bolahijau.png', cv2.IMREAD_UNCHANGED),
    (0, 0, 255): cv2.imread('bolamerah.png', cv2.IMREAD_UNCHANGED)
}

# Ubah ukuran gambar bola
for color in ball_images:
    ball_images[color] = cv2.resize(ball_images[color], (60, 60))

ball_radius = 30
colors = list(ball_images.keys())  # Pakai kunci dari dict

score = 0
game_over = False
game_started = False
balls = []

def create_ball():
    x = random.randint(ball_radius, 640 - ball_radius)
    y = -ball_radius
    color = random.choice(colors)
    speed = random.randint(5, 10)
    delay = random.uniform(0, 3)
    spawn_time = time.time() + delay
    return {"x": x, "y": y, "color": color, "speed": speed, "spawn_time": spawn_time, "active": False}

# Buat 4 bola awal
for _ in range(4):
    balls.append(create_ball())

# Waktu bermain
total_game_time = 60

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    ih, iw, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    nose_tip_x, nose_tip_y = None, None

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            nose_tip = face_landmarks.landmark[1]
            nose_tip_x = int(nose_tip.x * iw)
            nose_tip_y = int(nose_tip.y * ih)

    # Layar pembuka
    if not game_started:
        cv2.putText(frame, "TEKAN ENTER UNTUK MULAI", (iw // 2 - 250, ih // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        cv2.imshow("Catch the Blue Ball", frame)
        key = cv2.waitKey(1)
        if key == 13:  # Enter
            game_started = True
            start_time = time.time()
        elif key == 27:
            break
        continue

    # Hitung waktu
    if game_started and not game_over:
        elapsed_time = time.time() - start_time
        remaining_time = int(total_game_time - elapsed_time)
    else:
        remaining_time = 0

    if remaining_time <= 0 and not game_over:
        game_over = True
        win = True

    # Tampilkan keranjang mengikuti wajah
    if nose_tip_x is not None and nose_tip_y is not None:
        top_left_x = nose_tip_x - keranjang_img.shape[1] // 2
        top_left_y = nose_tip_y - keranjang_img.shape[0] // 2
        top_left_x = max(0, min(top_left_x, iw - keranjang_img.shape[1]))
        top_left_y = max(0, min(top_left_y, ih - keranjang_img.shape[0]))

        if keranjang_img.shape[2] == 4:
            keranjang_rgb = keranjang_img[:, :, :3]
            keranjang_alpha = keranjang_img[:, :, 3] / 255.0
            roi = frame[top_left_y:top_left_y + keranjang_img.shape[0], top_left_x:top_left_x + keranjang_img.shape[1]]
            for c in range(3):
                roi[:, :, c] = (keranjang_alpha * keranjang_rgb[:, :, c] +
                                (1 - keranjang_alpha) * roi[:, :, c])
        else:
            frame[top_left_y:top_left_y + keranjang_img.shape[0], top_left_x:top_left_x + keranjang_img.shape[1]] = keranjang_img

    if not game_over:
        for ball in balls[:]:
            if not ball["active"]:
                if time.time() >= ball["spawn_time"]:
                    ball["active"] = True
                else:
                    continue

            ball["y"] += ball["speed"]

            if ball["y"] > ih:
                balls.remove(ball)
                balls.append(create_ball())
                continue

            # Cek tabrakan
            if nose_tip_x is not None and nose_tip_y is not None:
                dx = ball["x"] - nose_tip_x
                dy = ball["y"] - nose_tip_y
                if dx * dx + dy * dy < ball_radius ** 2:
                    if ball["color"] == (255, 0, 0):  # Bola biru
                        score += 1
                        balls.remove(ball)
                        balls.append(create_ball())
                        continue
                    else:
                        game_over = True
                        win = False
                        break

            # Gambar bola (pakai gambar)
            ball_img = ball_images[ball["color"]]
            bh, bw = ball_img.shape[:2]
            bx = ball["x"] - bw // 2
            by = ball["y"] - bh // 2

            if 0 <= bx < iw - bw and 0 <= by < ih - bh:
                roi = frame[by:by+bh, bx:bx+bw]
                alpha_s = ball_img[:, :, 3] / 255.0
                alpha_l = 1.0 - alpha_s
                for c in range(3):
                    roi[:, :, c] = (alpha_s * ball_img[:, :, c] +
                                    alpha_l * roi[:, :, c])

    # Skor dan waktu
    cv2.putText(frame, f"Skor: {score}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, f"Waktu: {remaining_time}s", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    if game_over:
        if win:
            cv2.putText(frame, f"ANDA MENANG!", (iw // 2 - 200, ih // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 5)
        else:
            cv2.putText(frame, "GAME OVER", (iw // 2 - 150, ih // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 5)

    cv2.imshow("Catch the Blue Ball", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
