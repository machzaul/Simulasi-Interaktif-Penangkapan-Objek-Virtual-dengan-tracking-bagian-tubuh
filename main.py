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
show_lobby = False
show_menu = False
selected_ball_color = None
balls = []
total_game_time = 60
start_time = 0
lobby_selection_time = 0
selection_duration = 2.0  # 2 detik untuk memilih

# Konfigurasi untuk spacing bola
MIN_BALL_DISTANCE = 120  # Jarak minimum antar bola
MAX_SPAWN_ATTEMPTS = 50  # Maksimum percobaan spawn untuk menghindari infinite loop

# Konfigurasi kecepatan
BASE_SPEED_MIN = 3
BASE_SPEED_MAX = 6
SPEED_INCREASE_RATE = 0.5  # Peningkatan kecepatan per 10 detik
MAX_SPEED_TIME = 40  # Waktu maksimum untuk peningkatan kecepatan (detik)

# Mapping warna untuk tampilan
color_names = {
    (255, 0, 0): "BIRU",
    (0, 255, 255): "KUNING", 
    (0, 255, 0): "HIJAU",
    (0, 0, 255): "MERAH"
}

def reset_game():
    global score, game_over, game_started, show_menu, show_lobby, selected_ball_color, balls, start_time
    score = 0
    game_over = False
    game_started = False
    show_menu = False
    show_lobby = False
    selected_ball_color = None
    balls = []

def get_current_speed_range():
    """Menghitung range kecepatan berdasarkan waktu yang telah berlalu"""
    if not game_started:
        return BASE_SPEED_MIN, BASE_SPEED_MAX
    
    elapsed_time = time.time() - start_time
    
    # Batasi peningkatan kecepatan sampai 40 detik
    capped_time = min(elapsed_time, MAX_SPEED_TIME)
    
    # Hitung multiplier berdasarkan waktu (setiap 10 detik kecepatan naik)
    speed_multiplier = 1 + (capped_time // 10) * SPEED_INCREASE_RATE
    
    min_speed = int(BASE_SPEED_MIN * speed_multiplier)
    max_speed = int(BASE_SPEED_MAX * speed_multiplier)
    
    return min_speed, max_speed

def check_ball_collision(new_x, new_y, existing_balls):
    """Cek apakah posisi bola baru bertabrakan dengan bola yang sudah ada"""
    for ball in existing_balls:
        if ball["active"]:
            distance = ((new_x - ball["x"])**2 + (new_y - ball["y"])**2)**0.5
            if distance < MIN_BALL_DISTANCE:
                return True
    return False

def create_ball():
    """Membuat bola baru dengan posisi yang tidak bertabrakan"""
    min_speed, max_speed = get_current_speed_range()
    
    # Coba beberapa kali untuk mendapatkan posisi yang tidak bertabrakan
    for attempt in range(MAX_SPAWN_ATTEMPTS):
        x = random.randint(ball_radius + 50, 640 - ball_radius - 50)  # Tambah margin
        y = -ball_radius
        
        # Cek collision dengan bola yang sudah ada
        if not check_ball_collision(x, y, balls):
            color = random.choice(colors)
            speed = random.randint(min_speed, max_speed)
            delay = random.uniform(0.5, 2.5)  # Delay lebih konsisten
            spawn_time = time.time() + delay
            return {"x": x, "y": y, "color": color, "speed": speed, "spawn_time": spawn_time, "active": False}
    
    # Jika tidak bisa menemukan posisi yang bagus, buat dengan posisi random
    # (fallback untuk menghindari infinite loop)
    x = random.randint(ball_radius, 640 - ball_radius)
    y = -ball_radius
    color = random.choice(colors)
    speed = random.randint(min_speed, max_speed)
    delay = random.uniform(0.5, 2.5)
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

def draw_lobby_screen(frame, iw, ih, nose_tip_x, nose_tip_y):
    global lobby_selection_time, selected_ball_color
    
    # Judul
    draw_text_with_shadow(frame, "PILIH BOLA YANG INGIN DITANGKAP", 
                         (iw//2 - 250, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    draw_text_with_shadow(frame, "Arahkan kepala ke bola untuk memilih", 
                         (iw//2 - 200, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
    
    # Posisi bola untuk dipilih
    ball_positions = [
        {"pos": (iw//4, ih//2), "color": (255, 0, 0), "name": "BIRU"},
        {"pos": (iw//2, ih//2), "color": (0, 255, 255), "name": "KUNING"},
        {"pos": (3*iw//4, ih//2), "color": (0, 255, 0), "name": "HIJAU"},
        {"pos": (iw//2, ih//2 + 120), "color": (0, 0, 255), "name": "MERAH"}
    ]
    
    current_selection = None
    
    # Cek posisi kepala untuk menentukan pilihan
    if nose_tip_x is not None and nose_tip_y is not None:
        for ball_option in ball_positions:
            distance = ((nose_tip_x - ball_option["pos"][0])**2 + (nose_tip_y - ball_option["pos"][1])**2)**0.5
            if distance < 80:  # Radius deteksi
                current_selection = ball_option["color"]
                
                # Jika bola yang sama dipilih terus menerus
                if selected_ball_color == current_selection:
                    elapsed = time.time() - lobby_selection_time
                    if elapsed >= selection_duration:
                        return True  # Pilihan selesai
                else:
                    selected_ball_color = current_selection
                    lobby_selection_time = time.time()
                break
        
        if current_selection is None:
            selected_ball_color = None
    
    # Gambar bola pilihan
    for ball_option in ball_positions:
        pos = ball_option["pos"]
        color = ball_option["color"]
        name = ball_option["name"]
        
        # Gambar bola
        ball_img = ball_images[color]
        bh, bw = ball_img.shape[:2]
        bx = pos[0] - bw // 2
        by = pos[1] - bh // 2
        
        # Highlight jika sedang dipilih
        if selected_ball_color == color:
            elapsed = time.time() - lobby_selection_time
            progress = elapsed / selection_duration
            
            # Ring progress
            angle = int(360 * progress)
            cv2.ellipse(frame, pos, (50, 50), 0, 0, angle, (0, 255, 0), 5)
            
            # Background highlight
            cv2.circle(frame, pos, 55, (255, 255, 255), 3)
            
        if 0 <= bx < iw - bw and 0 <= by < ih - bh:
            roi = frame[by:by+bh, bx:bx+bw]
            if ball_img.shape[2] == 4:
                alpha_s = ball_img[:, :, 3] / 255.0
                alpha_l = 1.0 - alpha_s
                for c in range(3):
                    roi[:, :, c] = (alpha_s * ball_img[:, :, c] + alpha_l * roi[:, :, c])
        
        # Label nama bola
        text_pos = (pos[0] - 30, pos[1] + 80)
        draw_text_with_shadow(frame, name, text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Instruksi
    if selected_ball_color:
        elapsed = time.time() - lobby_selection_time
        remaining = selection_duration - elapsed
        draw_text_with_shadow(frame, f"Memilih {color_names[selected_ball_color]}... {remaining:.1f}s", 
                             (iw//2 - 120, ih - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    else:
        draw_text_with_shadow(frame, "Arahkan kepala ke bola yang diinginkan", 
                             (iw//2 - 180, ih - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return False

def draw_game_ui(frame, iw, remaining_time):
    # Background untuk UI - made smaller since we removed speed and level
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
    
    # Removed speed indicator
    # Removed level indicator
    
    # Instruksi game dengan warna yang dipilih
    draw_text_with_shadow(frame, "Ayo! Tangkap bola warna", 
                         (iw//2 - 150, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    if selected_ball_color:
        color_name = color_names[selected_ball_color]
        draw_text_with_shadow(frame, color_name, 
                             (iw//2 - len(color_name)*15, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 3)

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

def cleanup_balls():
    """Membersihkan bola yang sudah keluar dari layar dan menambah bola baru"""
    global balls
    balls_to_remove = []
    
    for i, ball in enumerate(balls):
        if ball["y"] > 480:  # Asumsi tinggi layar 480
            balls_to_remove.append(i)
    
    # Hapus bola dari belakang untuk menghindari index shifting
    for i in reversed(balls_to_remove):
        del balls[i]
    
    # Tambah bola baru untuk mengganti yang dihapus
    for _ in range(len(balls_to_remove)):
        balls.append(create_ball())

# Inisialisasi game
reset_game()

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Gagal membaca dari kamera")
        break

    # Hilangkan efek mirror dengan flip horizontal
    frame = cv2.flip(frame, 1)
    
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
    if not game_started and not show_lobby and not show_menu:
        draw_start_screen(frame, iw, ih)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 13:  # Enter
            show_lobby = True
        elif key == 27:  # ESC
            break
    
    # Layar lobby untuk memilih bola
    elif show_lobby:
        selection_complete = draw_lobby_screen(frame, iw, ih, nose_tip_x, nose_tip_y)
        
        if selection_complete:
            game_started = True
            show_lobby = False
            start_time = time.time()
            # Buat 3 bola awal dengan jarak yang aman
            balls = []
            for _ in range(3):
                new_ball = create_ball()
                balls.append(new_ball)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC untuk kembali ke menu utama
            show_lobby = False
    
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

            # Cleanup bola yang keluar layar
            if ball["y"] > ih + 50:  # Tambah margin
                balls.remove(ball)
                balls.append(create_ball())
                continue

            # Cek tabrakan
            if nose_tip_x is not None and nose_tip_y is not None:
                dx = ball["x"] - nose_tip_x
                dy = ball["y"] - nose_tip_y
                if dx * dx + dy * dy < ball_radius ** 2:
                    if ball["color"] == selected_ball_color:  # Bola yang dipilih
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

        # Pastikan selalu ada minimal 3 bola aktif
        active_balls = [ball for ball in balls if ball["active"]]
        if len(balls) < 4:  # Jaga agar ada 4 bola (beberapa mungkin belum aktif)
            balls.append(create_ball())

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