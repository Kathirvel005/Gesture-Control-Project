import cv2
import mediapipe as mp
import pyautogui
import subprocess

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

screen_width, screen_height = pyautogui.size()

prev_x, prev_y = 0, 0
smoothening = 5

thumb_x, thumb_y = 0, 0

def fingers_up(hand_landmarks):
    tips = [4, 8, 12, 16, 20]
    fingers = []

    if hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x:
        fingers.append(1)
    else:
        fingers.append(0)

    for tip in tips[1:]:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:

            for id, lm in enumerate(hand_landmarks.landmark):
                x = int(lm.x * screen_width)
                y = int(lm.y * screen_height)

                if id == 4:
                    thumb_x, thumb_y = x, y

                if id == 8:
                    index_x, index_y = x, y

                    curr_x = prev_x + (index_x - prev_x) / smoothening
                    curr_y = prev_y + (index_y - prev_y) / smoothening

                    pyautogui.moveTo(curr_x, curr_y)

                    prev_x, prev_y = curr_x, curr_y

                    distance = abs(index_x - thumb_x) + abs(index_y - thumb_y)
                    if distance < 40:
                        pyautogui.click()

            fingers = fingers_up(hand_landmarks)

            if fingers == [1, 1, 1, 1, 1]:
                print("Opening UI 🔥")
                subprocess.Popen(["python", "ui.py"])

            if index_x - prev_x > 100:
                print("Swipe Right 👉")

            if prev_x - index_x > 100:
                print("Swipe Left 👈")

            distance = abs(index_x - thumb_x) + abs(index_y - thumb_y)
            if distance > 200:
                print("Zoom Out 🔍")
            elif distance < 50:
                print("Zoom In 🔎")

            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    cv2.putText(img, "IRON MAN MODE", (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)

    cv2.imshow("Gesture Control", img)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows() 