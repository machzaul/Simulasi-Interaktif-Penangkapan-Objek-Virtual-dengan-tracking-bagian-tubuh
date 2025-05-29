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
colors = list(ball_images.keys())

# Game variables
score = 0
game_over = False
game_started = False
show_menu = False
balls = []
total_game_time = 60
start_time = 0

def reset_game():
    global score, game_over, game_started, show_menu, balls, start_time
    score = 0
    game_over = False
    game_started = False
    show_menu = False
    balls = []
    # Buat 4 bola awal
    for _ in range(4):
        balls.append(create_ball())

def create_ball():
    x = random.randint(ball_radius, 640 - ball_radius)
    y = -ball_radius
    color = random.choice(colors)
    speed = random.randint(5, 10)
    delay = random.uniform(0, 3)
    spawn_time = time.time() + delay
    return {"x": x, "y": y, "color": color, "speed": speed, "spawn_time": spawn_time, "active": False}

def draw_text_with_shadow(frame, text, pos, font, scale, color, thickness, shadow_color=(0, 0, 0)):
    # Gambar shadow
    cv2.putText(frame, text, (pos[0]+2, pos[1]+2), font, scale, shadow_color, thickness+1)
    # Gambar text utama
    cv2.putText(frame, text, pos, font, scale, color, thickness)

def draw_start_screen(frame, iw, ih):
    # Gambar berbagai warna bola di layar awal
    ball_positions = [
        (150, 150), (450, 180), (350, 120), (200, 280), 
        (400, 260), (280, 200), (500, 300), (100, 220)
    ]
    
    for i, pos in enumerate(ball_positions):
        color = colors[i % len(colors)]
        ball_img = ball_images[color]
        bh, bw = ball_img.shape[:2]
        bx = pos[0] - bw // 2
        by = pos[1] - bh // 2
        
        if 0 <= bx < iw - bw and 0 <= by < ih - bh:
            roi = frame[by:by+bh, bx:bx+bw]
            if ball_img.shape[2] == 4:
                alpha_s = ball_img[:, :, 3] / 255.0
                alpha_l = 1.0 - alpha_s
                for c in range(3):
                    roi[:, :, c] = (alpha_s * ball_img[:, :, c] + alpha_l * roi[:, :, c])
    
    # Text judul
    draw_text_with_shadow(frame, "Apakah anda siap menangkap bola?", 
                         (iw//2 - 280, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Instruksi
    draw_text_with_shadow(frame, "Klik enter untuk mulai", 
                         (iw//2 - 150, ih - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Button Enter
    cv2.rectangle(frame, (iw//2 - 60, ih - 50), (iw//2 + 60, ih - 20), (0, 100, 255), -1)
    cv2.rectangle(frame, (iw//2 - 60, ih - 50), (iw//2 + 60, ih - 20), (255, 255, 255), 2)
    draw_text_with_shadow(frame, "Enter", (iw//2 - 30, ih - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

def draw_game_ui(frame, iw, remaining_time):
    # Background untuk UI
    cv2.rectangle(frame, (10, 10), (250, 80), (0, 0, 0), -1)
    cv2.rectangle(frame, (10, 10), (250, 80), (255, 255, 255), 2)
    
    # Clock icon (simple circle dengan garis)
    cv2.circle(frame, (30, 35), 15, (255, 255, 255), 2)
    cv2.line(frame, (30, 35), (30, 25), (255, 255, 255), 2)
    cv2.line(frame, (30, 35), (35, 35), (255, 255, 255), 2)
    
    # Time text
    draw_text_with_shadow(frame, f": {remaining_time}", (45, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Ball icon (red circle)
    cv2.circle(frame, (140, 35), 12, (0, 0, 255), -1)
    cv2.circle(frame, (140, 35), 12, (255, 255, 255), 2)
    
    # Score text
    draw_text_with_shadow(frame, f": {score}", (155, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Instruksi game
    draw_text_with_shadow(frame, "Ayo! Tangkap bola warna", 
                         (iw//2 - 150, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    draw_text_with_shadow(frame, "BIRU", 
                         (iw//2 - 30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 3)

def draw_end_screen(frame, iw, ih, win):
    # Semi-transparent overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (iw, ih), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    if win:
        draw_text_with_shadow(frame, "ANDA MENANG!", 
                             (iw//2 - 150, ih//2 - 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
    else:
        draw_text_with_shadow(frame, "GAME OVER", 
                             (iw//2 - 120, ih//2 - 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
    
    draw_text_with_shadow(frame, f"Skor Akhir: {score}", 
                         (iw//2 - 100, ih//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Menu pilihan
    draw_text_with_shadow(frame, "Tekan 'R' untuk bermain lagi", 
                         (iw//2 - 180, ih//2 + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    draw_text_with_shadow(frame, "Tekan 'ESC' untuk keluar", 
                         (iw//2 - 150, ih//2 + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

# Inisialisasi game
reset_game()

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Gagal membaca dari kamera")
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
    if not game_started and not show_menu:
        draw_start_screen(frame, iw, ih)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 13:  # Enter
            game_started = True
            start_time = time.time()
        elif key == 27:  # ESC
            break
    
    # Game sedang berjalan
    elif game_started and not game_over:
        # Hitung waktu
        elapsed_time = time.time() - start_time
        remaining_time = int(total_game_time - elapsed_time)
        
        if remaining_time <= 0:
            game_over = True
            show_menu = True
            win = True
        
        # Tampilkan UI game
        draw_game_ui(frame, iw, remaining_time)
        
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

        # Update dan gambar bola
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
                        show_menu = True
                        win = False
                        break

            # Gambar bola
            ball_img = ball_images[ball["color"]]
            bh, bw = ball_img.shape[:2]
            bx = ball["x"] - bw // 2
            by = ball["y"] - bh // 2

            if 0 <= bx < iw - bw and 0 <= by < ih - bh:
                roi = frame[by:by+bh, bx:bx+bw]
                if ball_img.shape[2] == 4:
                    alpha_s = ball_img[:, :, 3] / 255.0
                    alpha_l = 1.0 - alpha_s
                    for c in range(3):
                        roi[:, :, c] = (alpha_s * ball_img[:, :, c] + alpha_l * roi[:, :, c])

    # Layar akhir game
    elif show_menu:
        draw_end_screen(frame, iw, ih, win)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('r') or key == ord('R'):  # Restart
            reset_game()
        elif key == 27:  # ESC
            break

    cv2.imshow("Catch the Blue Ball", frame)
    
    # Cek jika window ditutup
    if cv2.getWindowProperty("Catch the Blue Ball", cv2.WND_PROP_VISIBLE) < 1:
        break
    
    # ESC untuk keluar
    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()
print("Game selesai. Terima kasih telah bermain!")