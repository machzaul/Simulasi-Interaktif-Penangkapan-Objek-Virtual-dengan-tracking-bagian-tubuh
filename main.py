import cv2
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)

keranjang_img = cv2.imread('keranjang.png', cv2.IMREAD_UNCHANGED)
keranjang_img = cv2.resize(keranjang_img, (150, 150))

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
            nose_tip = face_landmarks.landmark[1]
            nose_x = int(nose_tip.x * iw)
            nose_y = int(nose_tip.y * ih)

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
        else:
            frame[top_left_y:top_left_y+150, top_left_x:top_left_x+150] = keranjang_img

    cv2.imshow("
