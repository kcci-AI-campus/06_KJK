# =========================================================
# DriverSense UI Integrated Version
#
# Detection / state-transition / GPIO / buzzer / recovery logic:
#     combi_final_maybe_3
#
# UI layout:
#     combi_final_ui_original_logic_v2 + provided UI reference
#
# IMPORTANT:
# UI rendering is separated from the detection/state algorithm.
# =========================================================

import cv2
import time
import math
from collections import deque
import mediapipe as mp
import numpy as np
HARDWARE_ENABLED = False
GPIO_GREEN_LED = 17
GPIO_YELLOW_LED = 27
GPIO_RED_LED = 22
GPIO_BUZZER = 18
GPIO_BUTTON = 23
if HARDWARE_ENABLED:
    from gpiozero import LED
    from gpiozero import Buzzer
    from gpiozero import Button
    green_led = LED(GPIO_GREEN_LED)
    yellow_led = LED(GPIO_YELLOW_LED)
    red_led = LED(GPIO_RED_LED)
    buzzer_hw = Buzzer(GPIO_BUZZER)
    acknowledge_button = Button(GPIO_BUTTON, pull_up=True, bounce_time=0.05)
else:
    green_led = None
    yellow_led = None
    red_led = None
    buzzer_hw = None
    acknowledge_button = None
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]
LEFT_EYE_LEFT = 33
LEFT_EYE_RIGHT = 133
RIGHT_EYE_LEFT = 362
RIGHT_EYE_RIGHT = 263
MOUTH_LEFT = 78
MOUTH_RIGHT = 308
MOUTH_TOP = 13
MOUTH_BOTTOM = 14
NOSE = 1
LEFT_FACE = 234
RIGHT_FACE = 454
FOREHEAD = 10
CHIN = 152
CALIBRATION_TIME = 5.0
CALIBRATION_DELAY = 5.0
DEFAULT_EAR_THRESHOLD = 0.2
BLINK_MIN_TIME = 0.08
BLINK_MAX_TIME = 0.6
LONG_BLINK_TIME = 0.6
EYE_WARNING_TIME = 1.0
DROWSY_TIME = 2.0
LONG_CLOSE_WINDOW = 30.0
LONG_CLOSE_LIMIT = 3
PERCLOS_WINDOW = 30.0
PERCLOS_ENABLE_TIME = 10.0
PERCLOS_CAUTION = 20.0
PERCLOS_WARNING = 30.0
MAR_THRESHOLD = 0.35
YAWN_TIME = 0.8
YAWN_RESET_THRESHOLD = 0.20
YAWN_RESET_TIME = 0.25
YAWN_WINDOW = 60.0
YAWN_CAUTION_COUNT = 2
YAWN_WARNING_COUNT = 3
YAWN_WATCH_TIME = 10.0
YAWN_WATCH_EYE_TIME = 1.0
HEAD_X_MARGIN = 0.12
HEAD_Y_UP_MARGIN = 0.12
HEAD_Y_DOWN_MARGIN = 0.09
GAZE_X_MARGIN = 0.14
GAZE_Y_MARGIN = 0.04
ATTENTION_CAUTION_TIME = 1.0
DISTRACTED_TIME = 2.0
HEAD_DOWN_CAUTION_TIME = 1.0
HEAD_DOWN_WARNING_TIME = 2.0
DOWN_CLOSED_DROWSY_TIME = 0.8
NOD_WINDOW = 10.0
NOD_CAUTION_COUNT = 2
NOD_DROWSY_COUNT = 3
FACE_SEARCH_TIME = 1.0
NO_DRIVER_TIME = 2.0
BLINK_BASELINE_TIME = 30.0
BLINK_WINDOW = 30.0
BLINK_CAUTION_RATIO = 1.5
BLINK_WARNING_RATIO = 2.0
ALERT_COOLDOWN = 4.0
DROWSY_MIN_HOLD = 2.0
RECOVERY_TIME = 1.0
BUTTON_MUTE_TIME = 3.0

# Repeated DROWSY event management
DROWSY_EVENT_WINDOW = 60.0
DROWSY_REARM_TIME = 0.7
POST_DROWSY_WARNING_TIME = 3.0
REPEATED_DROWSY_COUNT = 3

# Slightly relaxed criteria used only for DROWSY-event counting.
# Main DROWSY state still uses DROWSY_TIME = 2.0.
DROWSY_EVENT_EYE_TIME = 1.5
RECOVERY_DROWSY_EYE_TIME = 1.5

# Repeated DROWSY recovery / mandatory rest management
REPEATED_RECOVERY_TIME = 30.0
REPEATED_WARNING_START = 15.0
MANDATORY_REST_TIME = 30.0

# Persistent DROWSY event log (saved next to this Python file)
DROWSY_LOG_FILE = 'drowsy_events.csv'

virtual_green = False
virtual_yellow = False
virtual_red = False
virtual_buzzer = False
buzzer_mute_until = 0.0
drowsy_acknowledged = False
current_final_state = 'NORMAL'
ack_drowsy_requested = False

def get_drowsy_log_path():
    import os
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DROWSY_LOG_FILE)

def load_recent_drowsy_logs():
    recent = deque(maxlen=3)
    path = get_drowsy_log_path()
    try:
        if not __import__('os').path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                f.write('timestamp\n')
            return recent

        with open(path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        for line in lines:
            if line.lower() == 'timestamp':
                continue
            recent.append(line)
    except OSError as e:
        print('[LOG] load failed:', e)
    return recent

def save_drowsy_event(recent_logs):
    timestamp_text = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    path = get_drowsy_log_path()

    try:
        import os
        new_file = not os.path.exists(path)
        with open(path, 'a', encoding='utf-8') as f:
            if new_file:
                f.write('timestamp\n')
            f.write(timestamp_text + '\n')
    except OSError as e:
        print('[LOG] save failed:', e)

    recent_logs.append(timestamp_text)
    return timestamp_text

def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def calculate_ear(points):
    p1, p2, p3, p4, p5, p6 = points
    vertical1 = distance(p2, p6)
    vertical2 = distance(p3, p5)
    horizontal = distance(p1, p4)
    if horizontal == 0:
        return 0.0
    return (vertical1 + vertical2) / (2.0 * horizontal)

def calculate_mar(landmarks, width, height):
    left = landmarks[MOUTH_LEFT]
    right = landmarks[MOUTH_RIGHT]
    top = landmarks[MOUTH_TOP]
    bottom = landmarks[MOUTH_BOTTOM]
    left_point = (int(left.x * width), int(left.y * height))
    right_point = (int(right.x * width), int(right.y * height))
    top_point = (int(top.x * width), int(top.y * height))
    bottom_point = (int(bottom.x * width), int(bottom.y * height))
    vertical = distance(top_point, bottom_point)
    horizontal = distance(left_point, right_point)
    if horizontal == 0:
        return 0.0
    return vertical / horizontal

def calculate_head_metrics(landmarks):
    nose = landmarks[NOSE]
    left_face = landmarks[LEFT_FACE]
    right_face = landmarks[RIGHT_FACE]
    forehead = landmarks[FOREHEAD]
    chin = landmarks[CHIN]
    face_center_x = (left_face.x + right_face.x) / 2
    face_width = abs(right_face.x - left_face.x)
    face_center_y = (forehead.y + chin.y) / 2
    face_height = abs(chin.y - forehead.y)
    if face_width == 0 or face_height == 0:
        return (0.0, 0.0)
    head_x = (nose.x - face_center_x) / face_width
    head_y = (nose.y - face_center_y) / face_height
    return (head_x, head_y)

def classify_head(head_x, head_y, center_x, center_y):
    if head_x > center_x + HEAD_X_MARGIN:
        return 'RIGHT'
    if head_x < center_x - HEAD_X_MARGIN:
        return 'LEFT'
    if head_y < center_y - HEAD_Y_UP_MARGIN:
        return 'UP'
    if head_y > center_y + HEAD_Y_DOWN_MARGIN:
        return 'DOWN'
    return 'CENTER'

def calculate_iris_center(landmarks, iris_indices):
    x = sum((landmarks[i].x for i in iris_indices)) / len(iris_indices)
    y = sum((landmarks[i].y for i in iris_indices)) / len(iris_indices)
    return (x, y)

def calculate_single_eye_gaze(landmarks, iris_indices, eye_left_idx, eye_right_idx):
    iris_x, iris_y = calculate_iris_center(landmarks, iris_indices)
    left = landmarks[eye_left_idx]
    right = landmarks[eye_right_idx]
    eye_width = abs(right.x - left.x)
    if eye_width == 0:
        return (0.5, 0.0)
    eye_min_x = min(left.x, right.x)
    gaze_x = (iris_x - eye_min_x) / eye_width
    eye_center_y = (left.y + right.y) / 2
    gaze_y = (iris_y - eye_center_y) / eye_width
    return (gaze_x, gaze_y)

def calculate_gaze_metrics(landmarks):
    lx, ly = calculate_single_eye_gaze(landmarks, LEFT_IRIS, LEFT_EYE_LEFT, LEFT_EYE_RIGHT)
    rx, ry = calculate_single_eye_gaze(landmarks, RIGHT_IRIS, RIGHT_EYE_LEFT, RIGHT_EYE_RIGHT)
    gaze_x = (lx + rx) / 2
    gaze_y = (ly + ry) / 2
    return (gaze_x, gaze_y)

def classify_gaze(gaze_x, gaze_y, center_x, center_y):
    if gaze_x < center_x - GAZE_X_MARGIN:
        return 'LEFT'
    if gaze_x > center_x + GAZE_X_MARGIN:
        return 'RIGHT'
    if gaze_y < center_y - GAZE_Y_MARGIN:
        return 'UP'
    if gaze_y > center_y + GAZE_Y_MARGIN:
        return 'DOWN'
    return 'CENTER'

def set_led(state):
    global virtual_green
    global virtual_yellow
    global virtual_red
    virtual_green = False
    virtual_yellow = False
    virtual_red = False
    if state == 'NORMAL':
        virtual_green = True
    elif state in ['CAUTION', 'WARNING', 'SEARCHING']:
        virtual_yellow = True
    elif state in ['DROWSY', 'DISTRACTED', 'NO DRIVER']:
        virtual_red = True
    if HARDWARE_ENABLED:
        green_led.off()
        yellow_led.off()
        red_led.off()
        if virtual_green:
            green_led.on()
        if virtual_yellow:
            yellow_led.on()
        if virtual_red:
            red_led.on()

class BuzzerController:

    def __init__(self):
        self.sequence = []
        self.index = 0
        self.next_change = 0.0
        self.active = False
        self.continuous = False

    def stop(self):
        global virtual_buzzer
        self.sequence = []
        self.index = 0
        self.active = False
        self.continuous = False
        virtual_buzzer = False
        if HARDWARE_ENABLED and buzzer_hw is not None:
            buzzer_hw.off()

    def output(self, on):
        global virtual_buzzer
        virtual_buzzer = on
        if HARDWARE_ENABLED and buzzer_hw is not None:
            if on:
                buzzer_hw.on()
            else:
                buzzer_hw.off()

    def continuous_on(self):
        self.sequence = []
        self.index = 0
        self.active = False
        self.continuous = True
        self.output(True)

    def play(self, pattern, now):
        self.continuous = False
        if pattern == 'SHORT':
            sequence = [(True, 0.15), (False, 0.1)]
        elif pattern == 'DOUBLE':
            sequence = [(True, 0.15), (False, 0.15), (True, 0.15), (False, 0.1)]
        elif pattern == 'STRONG':
            sequence = [(True, 0.5), (False, 0.15), (True, 0.5), (False, 0.1)]
        elif pattern == 'DISTRACTED':
            sequence = [(True, 0.2), (False, 0.4), (True, 0.2), (False, 0.1)]
        elif pattern == 'LONG':
            sequence = [(True, 1.0), (False, 0.1)]
        else:
            return
        self.sequence = sequence
        self.index = 0
        self.active = True
        state, duration = self.sequence[0]
        self.output(state)
        self.next_change = now + duration

    def update(self, now):
        if self.continuous:
            return
        if not self.active:
            return
        if now < self.next_change:
            return
        self.index += 1
        if self.index >= len(self.sequence):
            self.stop()
            return
        state, duration = self.sequence[self.index]
        self.output(state)
        self.next_change = now + duration
buzzer_controller = BuzzerController()
last_alert_time = {}

def alert_once(key, pattern, now):
    global buzzer_mute_until
    if now < buzzer_mute_until:
        return
    previous = last_alert_time.get(key, 0)
    if now - previous >= ALERT_COOLDOWN:
        buzzer_controller.play(pattern, now)
        last_alert_time[key] = now

def acknowledge_alert():
    global buzzer_mute_until, drowsy_acknowledged, ack_drowsy_requested
    now = time.time()
    if current_final_state == 'DROWSY':
        drowsy_acknowledged = True
        ack_drowsy_requested = True
        buzzer_controller.stop()
        print('[ACK] DROWSY button pressed')
    else:
        buzzer_mute_until = now + BUTTON_MUTE_TIME
        buzzer_controller.stop()
        print('[ACK] Alert muted')
if HARDWARE_ENABLED:
    acknowledge_button.when_pressed = acknowledge_alert

def draw_virtual_hardware(frame):
    cv2.circle(frame, (470, 400), 12, (0, 255, 0) if virtual_green else (50, 50, 50), -1)
    cv2.putText(frame, 'G', (465, 405), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    cv2.circle(frame, (510, 400), 12, (0, 255, 255) if virtual_yellow else (50, 50, 50), -1)
    cv2.putText(frame, 'Y', (505, 405), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    cv2.circle(frame, (550, 400), 12, (0, 0, 255) if virtual_red else (50, 50, 50), -1)
    cv2.putText(frame, 'R', (545, 405), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    cv2.putText(frame, 'BUZZ: ON' if virtual_buzzer else 'BUZZ: OFF', (470, 435), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255) if virtual_buzzer else (200, 200, 200), 2)
# ---------------- Blue top / white bottom UI ----------------
UI_W, UI_H = 1200, 800

# Top outer/background area: same white as the lower UI.
# Keep the blue camera/status panels unchanged.
UI_BG = (128, 76, 38)
UI_HEADER = (255, 255, 255)
UI_PANEL = (135, 82, 42)
UI_PANEL2 = (160, 93, 52)

# Bottom area: white / light gray
UI_BOTTOM_BG = (248, 250, 252)
UI_BOTTOM_PANEL = (255, 255, 255)
UI_BOTTOM_BORDER = (220, 226, 232)
UI_DARK = (35, 45, 55)
UI_MUTED = (105, 118, 132)

# Status colors
UI_GREEN = (48, 220, 139)
UI_YELLOW = (0, 215, 255)
UI_RED = (74, 74, 255)
UI_BLUE = (255, 171, 86)
UI_WHITE = (245, 248, 252)


def rr(img, p1, p2, color, r=18):
    x1, y1 = p1
    x2, y2 = p2
    r = min(r, max(1, (x2 - x1) // 2), max(1, (y2 - y1) // 2))
    cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, -1)
    cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, -1)
    for x, y in ((x1 + r, y1 + r), (x2 - r, y1 + r),
                 (x1 + r, y2 - r), (x2 - r, y2 - r)):
        cv2.circle(img, (x, y), r, color, -1)


def put_text(img, text, xy, size=24, color=UI_WHITE, bold=False):
    font = cv2.FONT_HERSHEY_DUPLEX if bold else cv2.FONT_HERSHEY_SIMPLEX
    scale = size / 42.0
    thickness = 2 if size >= 18 else 1
    cv2.putText(img, str(text), xy, font, scale, color, thickness, cv2.LINE_AA)


def build_ui_base():
    # Start with the white lower background.
    base = np.full((UI_H, UI_W, 3), UI_BOTTOM_BG, dtype=np.uint8)

    # The upper dashboard is blue.
    cv2.rectangle(base, (0, 0), (UI_W - 1, 536), UI_BG, -1)

    # Header
    rr(base, (18, 14), (1182, 88), UI_HEADER)
    put_text(base, 'Drowsiness Detection System', (38, 49), 31, UI_DARK, True)
    put_text(base, 'Driver Sense  |  Raspberry Pi', (40, 73), 17, UI_DARK)

    # Camera panel
    rr(base, (18, 106), (660, 536), UI_PANEL)
    put_text(base, 'LIVE CAMERA', (34, 139), 20, UI_WHITE, True)

    # Driver status panel
    rr(base, (676, 106), (1182, 536), UI_PANEL)
    put_text(base, 'DRIVER STATUS', (700, 139), 28, UI_WHITE, True)

    # Current status panel - white
    rr(base, (18, 550), (832, 662), UI_BOTTOM_PANEL, 20)
    put_text(base, 'CURRENT STATUS', (55, 580), 28, UI_DARK, True)

    # ACK / hardware status panel - white
    rr(base, (850, 550), (1182, 662), UI_BOTTOM_PANEL, 20)
    put_text(base, 'SWITCH / ACK', (914, 578), 21, UI_DARK, True)

    # BUZZ status + R/Y/G LED indicators are rendered dynamically in draw_ui().
    # GPIO pin numbers are intentionally hidden from the UI.

    # Event log panel - white
    rr(base, (18, 678), (1182, 790), UI_BOTTOM_PANEL, 18)
    put_text(base, 'ABNORMAL EVENT LOG', (38, 710), 28, UI_DARK, True)

    # LIVE METRICS - bottom center
    # Display only. Detection/counting algorithms are unchanged.
    cv2.line(base, (505, 704), (505, 772), UI_BOTTOM_BORDER, 1, cv2.LINE_AA)
    put_text(base, 'LIVE METRICS', (530, 710), 20, UI_DARK, True)

    # KEY BUTTON GUIDE - bottom right
    # UI-only addition. Existing keyboard behavior is unchanged.
    put_text(base, 'KEY BUTTONS', (820, 710), 20, UI_DARK, True)
    cv2.line(base, (790, 704), (790, 772), UI_BOTTOM_BORDER, 1, cv2.LINE_AA)

    key_items = [
        ('SPACE', 'Start', 820, 735),
        ('R', 'ACK', 945, 735),
        ('C', 'Reset', 1040, 735),
        ('D', 'Drive', 820, 762),
        ('S', 'Stop', 945, 762),
        ('Q', 'Quit', 1040, 762),
    ]

    for key_name, action, x, y in key_items:
        key_w = 58 if key_name == 'SPACE' else 30

        rr(
            base,
            (x, y - 16),
            (x + key_w, y + 5),
            UI_BOTTOM_BORDER,
            6
        )

        put_text(
            base,
            key_name,
            (x + 5, y),
            14 if key_name == 'SPACE' else 15,
            UI_DARK,
            True
        )

        put_text(
            base,
            action,
            (x + key_w + 6, y),
            14,
            UI_MUTED,
            True
        )

    return base


UI_BASE = build_ui_base()


def state_info(state):
    return {
        'NORMAL': ('NORMAL DRIVING', 'Drive safely.', UI_GREEN),
        'CAUTION': ('CAUTION', 'Please check your condition.', UI_YELLOW),
        'WARNING': ('WARNING', 'Driver attention is required.', UI_YELLOW),
        'DROWSY': ('DROWSINESS DETECTED', 'Please stay alert.', UI_RED),
        'DISTRACTED': ('DISTRACTION DETECTED', 'Keep your eyes on the road.', UI_RED),
        'NO DRIVER': ('NO DRIVER', 'Driver could not be detected.', UI_RED),
        'SEARCHING': ('SEARCHING FOR DRIVER', 'Looking for the driver...', UI_YELLOW),
        'CALIBRATING': ('CALIBRATION IN PROGRESS', 'Look straight ahead and keep your eyes open.', UI_YELLOW),
        'COUNTDOWN': ('STARTING CHECK', 'Get ready for calibration.', UI_BLUE),
        'READY': ('START CHECKING', 'Press SPACE to start calibration.', UI_BLUE),
    }.get(state, (state, '', UI_DARK))


def draw_ui(frame, state, eye_state, drowsy_count,
            yawn_count, blink_count, perclos_value,
            head_status, gaze_status, fps,
            event_log, camera_connected=True,
            calibration_remaining=None, calibration_phase=None):
    """
    Presentation layer only.

    This function reads existing runtime state and draws the dashboard.
    It does NOT change detection thresholds, state transitions, GPIO,
    buzzer behavior, ACK behavior, recovery logic, or rest logic.
    """
    ui = UI_BASE.copy()

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------
    put_text(
        ui,
        time.strftime('%Y.%m.%d  %H:%M:%S'),
        (914, 61),
        17,
        UI_DARK
    )

    # ---------------------------------------------------------
    # LIVE CAMERA
    # ---------------------------------------------------------
    camera = cv2.resize(
        frame,
        (610, 385),
        interpolation=cv2.INTER_AREA
    )

    if state in ('CALIBRATING', 'READY', 'COUNTDOWN'):
        overlay = np.zeros_like(camera)
        camera = cv2.addWeighted(
            camera, 0.60,
            overlay, 0.40,
            0
        )

    ui[145:530, 34:644] = camera

    put_text(
        ui,
        f'FPS: {fps:.0f}',
        (35, 523),
        16,
        UI_WHITE,
        True
    )

    # ---------------------------------------------------------
    # Read existing state flags for DISPLAY ONLY.
    # ---------------------------------------------------------
    rest_required_ui = globals().get(
        'rest_required_latched',
        False
    )

    rest_active_ui = globals().get(
        'rest_active',
        False
    )

    rest_start_ui = globals().get(
        'rest_start_time',
        None
    )

    insufficient_rest_ui = globals().get(
        'insufficient_rest_warning',
        False
    )

    repeated_drowsiness_ui = globals().get(
        'repeated_drowsiness_latched',
        False
    )

    repeated_recovery_elapsed_ui = globals().get(
        'repeated_recovery_elapsed',
        0.0
    )

    drive_mode_ui = globals().get(
        'DRIVE_MODE',
        True
    )

    # ---------------------------------------------------------
    # DRIVER STATUS panel
    #
    # Priority is UI-only:
    # REST REQUIRED > NOT ENOUGH REST > REST TIMER
    # > REPEATED RECOVERY > CALIBRATION > normal cards
    # ---------------------------------------------------------
    if (
        rest_required_ui
        and not rest_active_ui
        and not insufficient_rest_ui
    ):
        rr(
            ui,
            (694, 160),
            (1165, 506),
            UI_PANEL2,
            18
        )

        put_text(
            ui,
            'TAKE A REST',
            (735, 245),
            40,
            UI_RED,
            True
        )

        put_text(
            ui,
            'STOP THE DRIVING',
            (735, 300),
            31,
            UI_RED,
            True
        )

        put_text(
            ui,
            'Additional drowsiness detected',
            (735, 365),
            19,
            UI_WHITE,
            True
        )

        put_text(
            ui,
            'Press S to enter STOP mode',
            (735, 415),
            18,
            UI_BLUE,
            True
        )

    elif (
        rest_required_ui
        and insufficient_rest_ui
        and not rest_active_ui
    ):
        rr(
            ui,
            (694, 160),
            (1165, 506),
            UI_PANEL2,
            18
        )

        put_text(
            ui,
            'NOT ENOUGH REST',
            (735, 260),
            34,
            UI_YELLOW,
            True
        )

        put_text(
            ui,
            'Rest time has not been completed.',
            (735, 320),
            18,
            UI_WHITE,
            True
        )

        put_text(
            ui,
            'Press S and continue resting.',
            (735, 380),
            18,
            UI_BLUE,
            True
        )

    elif rest_active_ui:
        rr(
            ui,
            (694, 160),
            (1165, 506),
            UI_PANEL2,
            18
        )

        put_text(
            ui,
            'TAKE A REST',
            (790, 245),
            40,
            UI_RED,
            True
        )

        if rest_start_ui is not None:
            elapsed = max(
                0.0,
                time.time() - rest_start_ui
            )

            remaining = max(
                0,
                int(
                    math.ceil(
                        MANDATORY_REST_TIME - elapsed
                    )
                )
            )

            minutes = remaining // 60
            seconds = remaining % 60

            if remaining > 0:
                put_text(
                    ui,
                    f'REST TIME: {minutes:02d}:{seconds:02d}',
                    (735, 325),
                    28,
                    UI_WHITE,
                    True
                )

                put_text(
                    ui,
                    'Keep STOP mode until the timer ends.',
                    (735, 390),
                    17,
                    UI_BLUE,
                    True
                )

            else:
                put_text(
                    ui,
                    'REST COMPLETE',
                    (735, 325),
                    30,
                    UI_GREEN,
                    True
                )

                put_text(
                    ui,
                    'Press D to resume driving.',
                    (735, 390),
                    21,
                    UI_GREEN,
                    True
                )

    elif (
        repeated_drowsiness_ui
        and not rest_required_ui
    ):
        rr(
            ui,
            (694, 160),
            (1165, 506),
            UI_PANEL2,
            18
        )

        recovery_x = 735

        put_text(
            ui,
            'RECOVERY REQUIRED',
            (recovery_x, 245),
            30,
            UI_RED,
            True
        )

        recovery_remaining = max(
            0,
            int(
                math.ceil(
                    REPEATED_RECOVERY_TIME
                    - repeated_recovery_elapsed_ui
                )
            )
        )

        put_text(
            ui,
            f'RECOVERY: {recovery_remaining}s',
            (recovery_x, 300),
            26,
            UI_RED,
            True
        )

        head_accent = (
            UI_GREEN
            if head_status == 'CENTER'
            else UI_RED
        )

        gaze_accent = (
            UI_GREEN
            if gaze_status == 'CENTER'
            else UI_RED
        )

        put_text(
            ui,
            f'HEAD: {head_status}',
            (recovery_x, 355),
            22,
            head_accent,
            True
        )

        put_text(
            ui,
            f'GAZE: {gaze_status}',
            (recovery_x, 390),
            22,
            gaze_accent,
            True
        )

        # Gaze is displayed as driver information.
        # The recovery algorithm itself remains the original:
        # HEAD CENTER and raw_state != DROWSY.
        put_text(
            ui,
            'Keep your head centered and stay awake',
            (recovery_x, 440),
            18,
            UI_BLUE,
            True
        )

        put_text(
            ui,
            f'for {int(REPEATED_RECOVERY_TIME)} seconds.',
            (recovery_x, 472),
            18,
            UI_BLUE,
            True
        )

    elif state in (
        'READY',
        'COUNTDOWN',
        'CALIBRATING'
    ):
        rr(
            ui,
            (694, 160),
            (1165, 506),
            UI_PANEL2,
            18
        )

        phase = calibration_phase or state
        calibration_x = 735

        if phase == 'READY':
            put_text(
                ui,
                'START CHECKING',
                (calibration_x, 240),
                32,
                UI_BLUE,
                True
            )

            put_text(
                ui,
                'Look straight ahead',
                (calibration_x, 310),
                20,
                UI_WHITE,
                True
            )

            put_text(
                ui,
                'Keep your eyes open',
                (calibration_x, 350),
                18,
                (210, 225, 240)
            )

            put_text(
                ui,
                'Press SPACE to start calibration',
                (calibration_x, 415),
                18,
                UI_BLUE,
                True
            )

        elif phase == 'COUNTDOWN':
            count = int(
                calibration_remaining or 0
            )

            put_text(
                ui,
                'START CHECKING',
                (calibration_x, 220),
                28,
                UI_BLUE,
                True
            )

            put_text(
                ui,
                str(count),
                (calibration_x, 315),
                74,
                UI_BLUE,
                True
            )

            put_text(
                ui,
                'Get ready...',
                (calibration_x, 400),
                19,
                UI_WHITE,
                True
            )

        else:
            put_text(
                ui,
                'CALIBRATION IN PROGRESS',
                (calibration_x, 215),
                25,
                UI_YELLOW,
                True
            )

            remaining = (
                calibration_remaining
                if calibration_remaining is not None
                else 0
            )

            put_text(
                ui,
                f'{remaining:.1f}s',
                (calibration_x, 315),
                50,
                UI_YELLOW,
                True
            )

            put_text(
                ui,
                'Look straight ahead',
                (calibration_x, 400),
                20,
                UI_WHITE,
                True
            )

            put_text(
                ui,
                'Keep your eyes open',
                (calibration_x, 430),
                19,
                (210, 225, 240)
            )

    else:
        # Normal status cards
        eye_accent = (
            UI_GREEN
            if eye_state == 'OPEN'
            else UI_RED
        )

        head_accent = (
            UI_GREEN
            if head_status == 'CENTER'
            else UI_RED
        )

        gaze_accent = (
            UI_GREEN
            if gaze_status == 'CENTER'
            else UI_RED
        )

        cards = [
            (
                'Eye State',
                eye_state,
                eye_accent
            ),
            (
                'Drowsy Count',
                f'{0 if not drive_mode_ui else drowsy_count}',
                UI_WHITE
            ),
            (
                'Head Pose',
                head_status,
                head_accent
            ),
            (
                'Gaze',
                gaze_status,
                gaze_accent
            )
        ]

        cy = 166

        # Two fixed left-aligned columns:
        # label column x=724 / value column x=965.
        # Values are deliberately NOT right-aligned.
        label_x = 724
        value_x = 965

        for label, value, accent in cards:
            rr(
                ui,
                (694, cy),
                (1165, cy + 78),
                UI_PANEL2,
                16
            )

            put_text(
                ui,
                label,
                (label_x, cy + 50),
                28,
                UI_WHITE,
                True
            )

            put_text(
                ui,
                str(value),
                (value_x, cy + 50),
                27,
                accent,
                True
            )

            cy += 86

        cv2.circle(
            ui,
            (720, 518),
            8,
            UI_GREEN
            if camera_connected
            else UI_RED,
            -1
        )

        put_text(
            ui,
            'CAMERA CONNECTED'
            if camera_connected
            else 'CAMERA ERROR',
            (738, 524),
            17,
            UI_WHITE
        )

    # ---------------------------------------------------------
    # SWITCH / ACK panel
    # ---------------------------------------------------------
    buzz_color = (
        UI_RED
        if virtual_buzzer
        else UI_MUTED
    )

    put_text(
        ui,
        f'BUZZ: {"ON" if virtual_buzzer else "OFF"}',
        (883, 621),
        17,
        buzz_color,
        True
    )

    put_text(
        ui,
        f'MODE: {"DRIVE" if drive_mode_ui else "STOP"}',
        (883, 645),
        15,
        UI_DARK,
        True
    )

    led_items = [
        (
            'R',
            virtual_red,
            UI_RED,
            1005
        ),
        (
            'Y',
            virtual_yellow,
            UI_YELLOW,
            1060
        ),
        (
            'G',
            virtual_green,
            UI_GREEN,
            1115
        ),
    ]

    for label, active, color, x in led_items:
        cv2.circle(
            ui,
            (x, 637),
            7,
            color
            if active
            else (180, 180, 180),
            -1
        )

        put_text(
            ui,
            label,
            (x + 12, 642),
            13,
            UI_DARK
            if active
            else UI_MUTED,
            True
        )

    # ---------------------------------------------------------
    # CURRENT STATUS panel
    # ---------------------------------------------------------
    if not drive_mode_ui:
        title = 'STOPPED'
        subtitle = 'STOP mode active.'
        accent = UI_GREEN

    elif (
        rest_required_ui
        and insufficient_rest_ui
        and not rest_active_ui
    ):
        title = 'NOT ENOUGH REST'
        subtitle = 'Return to STOP mode and complete the required rest.'
        accent = UI_YELLOW

    elif rest_active_ui:
        title = 'REST IN PROGRESS'
        subtitle = 'Remain in STOP mode until the rest timer is complete.'
        accent = UI_BLUE

    elif rest_required_ui:
        title = 'STOP DRIVING'
        subtitle = 'Additional drowsiness detected. Take a rest.'
        accent = UI_RED

    else:
        title, subtitle, accent = state_info(
            state
        )

    cv2.rectangle(
        ui,
        (18, 550),
        (24, 662),
        accent,
        -1
    )

    put_text(
        ui,
        title,
        (55, 616),
        27,
        accent,
        True
    )

    put_text(
        ui,
        subtitle,
        (55, 646),
        16,
        UI_DARK
    )

    # ---------------------------------------------------------
    # ABNORMAL EVENT LOG
    #
    # Existing persistent DROWSY timestamps are used.
    # Only the most recent three rows are displayed.
    # ---------------------------------------------------------
    if not event_log:
        put_text(
            ui,
            'No drowsiness events recorded.',
            (38, 748),
            16,
            UI_MUTED
        )

    else:
        y = 738

        for timestamp_text, message in list(event_log)[-3:][::-1]:
            put_text(
                ui,
                f'{timestamp_text}  |  {message}',
                (40, y),
                16,
                UI_RED,
                True
            )

            y += 20

    # ---------------------------------------------------------
    # LIVE METRICS
    # Left-aligned values for test/demo visibility.
    # These values are read from the existing algorithm only.
    # ---------------------------------------------------------
    metric_x = 530

    put_text(
        ui,
        f'Yawn60   : {yawn_count}',
        (metric_x, 737),
        17,
        UI_DARK,
        True
    )

    put_text(
        ui,
        f'Blink30  : {blink_count}',
        (metric_x, 757),
        17,
        UI_DARK,
        True
    )

    put_text(
        ui,
        f'PERCLOS  : {perclos_value:.1f}%',
        (metric_x, 777),
        17,
        UI_DARK,
        True
    )

    return ui


BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode
model_path = 'models/face_landmarker.task'
options = FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=model_path), running_mode=RunningMode.VIDEO, num_faces=1, min_face_detection_confidence=0.5, min_face_presence_confidence=0.5, min_tracking_confidence=0.5)
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

print("WIDTH :", cap.get(cv2.CAP_PROP_FRAME_WIDTH))
print("HEIGHT:", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print("FPS   :", cap.get(cv2.CAP_PROP_FPS))

fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
codec = "".join([
    chr(fourcc & 0xFF),
    chr((fourcc >> 8) & 0xFF),
    chr((fourcc >> 16) & 0xFF),
    chr((fourcc >> 24) & 0xFF)
])
print("FOURCC:", codec)

if not cap.isOpened():
    print('Webcam open failed')
    exit()

cv2.namedWindow('DriverSense', cv2.WINDOW_NORMAL)
cv2.resizeWindow('DriverSense', UI_W, UI_H)

recent_drowsy_logs = load_recent_drowsy_logs()

# UI-only view of the existing persistent DROWSY log.
# CSV storage remains controlled by save_drowsy_event().
event_log = deque(maxlen=20)
for saved_stamp in recent_drowsy_logs:
    display_stamp = saved_stamp[-8:] if len(saved_stamp) >= 8 else saved_stamp
    event_log.append((display_stamp, 'DROWSINESS DETECTED'))

DRIVE_MODE = True
calibration_ear = []
calibration_head_x = []
calibration_head_y = []
calibration_gaze_x = []
calibration_gaze_y = []
calibration_elapsed = 0.0
previous_calibration_time = time.time()
with FaceLandmarker.create_from_options(options) as landmarker:
    first_start = True
    while True:
        calibration_ear = []
        calibration_head_x = []
        calibration_head_y = []
        calibration_gaze_x = []
        calibration_gaze_y = []
        calibration_elapsed = 0.0
        previous_calibration_time = time.time()
        reset_requested = False
        quit_requested = False

        if first_start:
            while True:
                ret, frame = cap.read()
                if not ret:
                    continue
                frame = cv2.flip(frame, 1)
                ready_ui = draw_ui(
                    frame,
                    'READY',
                    'UNKNOWN',
                    0,
                    0,
                    0,
                    0.0,
                    'UNKNOWN',
                    'UNKNOWN',
                    0.0,
                    event_log,
                    cap.isOpened(),
                    None,
                    'READY'
                )
                cv2.imshow('DriverSense', ready_ui)
                key = cv2.waitKey(1) & 255
                if key == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    exit()
                elif key == ord(' '):
                    break

        previous_calibration_time = time.time()
        while calibration_elapsed < CALIBRATION_TIME:
            read_start = time.perf_counter()
            ret, frame = cap.read()
            read_ms = (time.perf_counter() - read_start) * 1000
            if not ret:
                continue
            now = time.time()
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int(time.monotonic() * 1000)
            infer_start = time.perf_counter()
            result = landmarker.detect_for_video(mp_image, timestamp_ms)
            infer_ms = (time.perf_counter() - infer_start) * 1000
            if result.face_landmarks:
                landmarks = result.face_landmarks[0]
                h, w, _ = frame.shape
                left_points = []
                right_points = []
                for idx in LEFT_EYE:
                    lm = landmarks[idx]
                    left_points.append((int(lm.x * w), int(lm.y * h)))
                for idx in RIGHT_EYE:
                    lm = landmarks[idx]
                    right_points.append((int(lm.x * w), int(lm.y * h)))
                left_ear = calculate_ear(left_points)
                right_ear = calculate_ear(right_points)
                ear = (left_ear + right_ear) / 2
                head_x, head_y = calculate_head_metrics(landmarks)
                if len(landmarks) > 477:
                    gaze_x, gaze_y = calculate_gaze_metrics(landmarks)
                else:
                    gaze_x = 0.5
                    gaze_y = -0.087
                calibration_ear.append(ear)
                calibration_head_x.append(head_x)
                calibration_head_y.append(head_y)
                calibration_gaze_x.append(gaze_x)
                calibration_gaze_y.append(gaze_y)
                dt = now - previous_calibration_time
                calibration_elapsed += dt
            previous_calibration_time = now
            remaining = max(0, CALIBRATION_TIME - calibration_elapsed)
            calib_ui = draw_ui(
                frame,
                'CALIBRATING',
                'UNKNOWN',
                0,
                0,
                0,
                0.0,
                'UNKNOWN',
                'UNKNOWN',
                0.0,
                event_log,
                cap.isOpened(),
                remaining,
                'CALIBRATING'
            )
            cv2.imshow('DriverSense', calib_ui)
            if cv2.waitKey(1) & 255 == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                exit()
        if calibration_ear:
            EAR_BASELINE = sum(calibration_ear) / len(calibration_ear)
            EAR_THRESHOLD = clamp(EAR_BASELINE * 0.55, 0.16, 0.22)
            HEAD_X_CENTER = sum(calibration_head_x) / len(calibration_head_x)
            HEAD_Y_CENTER = sum(calibration_head_y) / len(calibration_head_y)
            GAZE_X_CENTER = sum(calibration_gaze_x) / len(calibration_gaze_x)
            GAZE_Y_CENTER = sum(calibration_gaze_y) / len(calibration_gaze_y)
        else:
            EAR_THRESHOLD = DEFAULT_EAR_THRESHOLD
            HEAD_X_CENTER = 0.0
            HEAD_Y_CENTER = 0.07
            GAZE_X_CENTER = 0.5
            GAZE_Y_CENTER = -0.087
        print('Calibration complete')
        print('EAR threshold:', EAR_THRESHOLD)
        print('Head center:', HEAD_X_CENTER, HEAD_Y_CENTER)
        print('Gaze center:', GAZE_X_CENTER, GAZE_Y_CENTER)
        first_start = False
        eye_closed_start = None
        was_eye_closed = False
        yawn_open_start = None
        yawn_active = False
        yawn_reset_start = None
        yawn_watch_until = 0.0
        attention_away_start = None
        head_down_start = None
        down_closed_start = None
        face_missing_start = None
        blink_times = deque()
        long_close_times = deque()
        yawn_times = deque()
        nod_times = deque()
        previous_head_status = 'CENTER'
        nod_down_start = None
        perclos_data = deque()
        previous_perclos_time = None
        valid_runtime = 0.0
        blink_baseline_start = time.time()
        blink_baseline_30s = None
        drowsy_latched = False
        drowsy_hold_until = 0.0
        recovery_start = None

        drowsy_event_times = deque()
        drowsy_event_armed = True
        drowsy_rearm_start = None
        post_drowsy_warning_until = 0.0
        repeated_drowsiness_latched = False

        # DROWSY-event edge tracking.
        # Persistent aggregate reasons are counted only when they
        # newly cross the threshold, not on every frame.
        previous_repeated_long_close = False
        previous_nodding_drowsy = False

        repeated_recovery_start = None
        repeated_recovery_elapsed = 0.0

        rest_required_latched = False
        rest_active = False
        rest_start_time = None
        insufficient_rest_warning = False

        frame_count = 0
        fps = 0.0
        fps_frame_count = 0
        fps_start = time.time()
        while True:
            read_start = time.perf_counter()
            ret, frame = cap.read()
            read_ms = (time.perf_counter() - read_start) * 1000

            if not ret:
                print('Frame read failed')
                break
            now = time.time()

            while drowsy_event_times and now - drowsy_event_times[0] > DROWSY_EVENT_WINDOW:
                drowsy_event_times.popleft()

            if ack_drowsy_requested:
                buzzer_controller.stop()

                drowsy_count = len(drowsy_event_times)

                if rest_required_latched:
                    drowsy_latched = True
                    drowsy_acknowledged = True
                    current_final_state = 'DROWSY'
                    set_led('DROWSY')
                    print('[ACK] REST REQUIRED -> BUZZ OFF / DROWSY maintained')

                elif repeated_drowsiness_latched or drowsy_count >= REPEATED_DROWSY_COUNT:
                    repeated_drowsiness_latched = True
                    drowsy_latched = True
                    drowsy_acknowledged = True
                    post_drowsy_warning_until = 0.0
                    current_final_state = 'DROWSY'
                    set_led('DROWSY')
                    print(f'[ACK] DROWSY60={drowsy_count} -> REPEATED DROWSINESS / BUZZ OFF')

                else:
                    drowsy_latched = False
                    drowsy_hold_until = 0.0
                    recovery_start = None
                    drowsy_acknowledged = False

                    eye_closed_start = None
                    was_eye_closed = False
                    yawn_open_start = None
                    yawn_active = False
                    yawn_reset_start = None
                    yawn_watch_until = 0.0
                    attention_away_start = None
                    head_down_start = None
                    down_closed_start = None
                    face_missing_start = None
                    previous_head_status = 'CENTER'
                    nod_down_start = None

                    blink_times.clear()
                    long_close_times.clear()
                    yawn_times.clear()
                    nod_times.clear()
                    perclos_data.clear()
                    previous_perclos_time = None
                    valid_runtime = 0.0

                    if drowsy_count <= 1:
                        post_drowsy_warning_until = 0.0
                        current_final_state = 'NORMAL'
                        set_led('NORMAL')
                        print(f'[ACK] DROWSY60={drowsy_count} -> NORMAL')

                    else:
                        post_drowsy_warning_until = now + POST_DROWSY_WARNING_TIME
                        current_final_state = 'WARNING'
                        set_led('WARNING')
                        print(f'[ACK] DROWSY60={drowsy_count} -> WARNING {POST_DROWSY_WARNING_TIME:.0f}s')

                ack_drowsy_requested = False

            if rest_active:
                buzzer_mute_until = now + 1.0
                buzzer_controller.stop()

            frame_count += 1
            fps_frame_count += 1
            fps_elapsed = now - fps_start
            if fps_elapsed >= 1.0:
                fps = fps_frame_count / fps_elapsed
                fps_frame_count = 0
                fps_start = now
            buzzer_controller.update(now)
            frame = cv2.flip(frame, 1)
            small_frame = cv2.resize(frame, (320, 240))
            rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int(time.monotonic() * 1000)
            infer_start = time.perf_counter()
            result = landmarker.detect_for_video(mp_image, timestamp_ms)
            infer_ms = (time.perf_counter() - infer_start) * 1000

            # UI-only defaults for the current frame.
            new_drowsy_event = False
            eye_state_ui = 'UNKNOWN'
            head_status_ui = 'UNKNOWN'
            gaze_status_ui = 'UNKNOWN'
            drowsy_count_ui = len(drowsy_event_times)
            yawn_count_ui = len(yawn_times)
            blink_count_ui = len(blink_times)
            perclos_ui = 0.0

            if result.face_landmarks:
                face_missing_start = None
                landmarks = result.face_landmarks[0]
                h, w, _ = frame.shape
                left_points = []
                right_points = []
                for idx in LEFT_EYE:
                    lm = landmarks[idx]
                    left_points.append((int(lm.x * w), int(lm.y * h)))
                for idx in RIGHT_EYE:
                    lm = landmarks[idx]
                    right_points.append((int(lm.x * w), int(lm.y * h)))
                left_ear = calculate_ear(left_points)
                right_ear = calculate_ear(right_points)
                left_closed = left_ear < EAR_THRESHOLD
                right_closed = right_ear < EAR_THRESHOLD
                eye_closed = left_closed and right_closed
                eye_state_ui = 'CLOSED' if eye_closed else 'OPEN'
                if previous_perclos_time is None:
                    previous_perclos_time = now
                else:
                    dt = now - previous_perclos_time
                    previous_perclos_time = now
                    valid_runtime += dt
                    closed_dt = dt if eye_closed else 0.0
                    perclos_data.append((now, dt, closed_dt))
                while perclos_data and now - perclos_data[0][0] > PERCLOS_WINDOW:
                    perclos_data.popleft()
                total_time = sum((x[1] for x in perclos_data))
                closed_window = sum((x[2] for x in perclos_data))
                if total_time > 0:
                    perclos = closed_window / total_time * 100
                else:
                    perclos = 0.0
                perclos_ui = perclos
                if eye_closed:
                    if eye_closed_start is None:
                        eye_closed_start = now
                    eye_closed_duration = now - eye_closed_start
                else:
                    eye_closed_duration = 0.0
                    if was_eye_closed and eye_closed_start is not None:
                        duration = now - eye_closed_start
                        if BLINK_MIN_TIME <= duration <= BLINK_MAX_TIME:
                            blink_times.append(now)
                        if duration >= EYE_WARNING_TIME:
                            long_close_times.append(now)
                    eye_closed_start = None
                was_eye_closed = eye_closed
                while blink_times and now - blink_times[0] > BLINK_WINDOW:
                    blink_times.popleft()
                while long_close_times and now - long_close_times[0] > LONG_CLOSE_WINDOW:
                    long_close_times.popleft()
                while yawn_times and now - yawn_times[0] > YAWN_WINDOW:
                    yawn_times.popleft()
                while nod_times and now - nod_times[0] > NOD_WINDOW:
                    nod_times.popleft()

                # UI-only live metric values from the existing deques.
                yawn_count_ui = len(yawn_times)
                blink_count_ui = len(blink_times)

                if blink_baseline_30s is None and now - blink_baseline_start >= BLINK_BASELINE_TIME:
                    blink_baseline_30s = max(3, len(blink_times))
                blink_ratio = 1.0
                if blink_baseline_30s is not None:
                    blink_ratio = len(blink_times) / blink_baseline_30s
                mar = calculate_mar(landmarks, w, h)
                if not yawn_active:
                    if mar > MAR_THRESHOLD:
                        if yawn_open_start is None:
                            yawn_open_start = now
                        if now - yawn_open_start >= YAWN_TIME:
                            yawn_active = True
                            yawn_reset_start = None
                            yawn_times.append(now)
                            yawn_watch_until = now + YAWN_WATCH_TIME
                            alert_once('YAWN', 'SHORT', now)
                    else:
                        yawn_open_start = None
                else:
                    if mar < YAWN_RESET_THRESHOLD:
                        if yawn_reset_start is None:
                            yawn_reset_start = now
                        elif now - yawn_reset_start >= YAWN_RESET_TIME:
                            yawn_active = False
                            yawn_open_start = None
                            yawn_reset_start = None
                    else:
                        yawn_reset_start = None
                head_x, head_y = calculate_head_metrics(landmarks)
                head_status = classify_head(head_x, head_y, HEAD_X_CENTER, HEAD_Y_CENTER)
                head_status_ui = head_status
                if not eye_closed and len(landmarks) > 477:
                    gaze_x, gaze_y = calculate_gaze_metrics(landmarks)
                    gaze_status = classify_gaze(gaze_x, gaze_y, GAZE_X_CENTER, GAZE_Y_CENTER)
                    gaze_status_ui = gaze_status
                else:
                    gaze_status = 'CLOSED'
                    gaze_status_ui = gaze_status
                if head_status == 'DOWN':
                    if head_down_start is None:
                        head_down_start = now
                    head_down_duration = now - head_down_start
                else:
                    head_down_start = None
                    head_down_duration = 0.0
                if head_status == 'DOWN' and eye_closed:
                    if down_closed_start is None:
                        down_closed_start = now
                    down_closed_duration = now - down_closed_start
                else:
                    down_closed_start = None
                    down_closed_duration = 0.0
                if previous_head_status != 'DOWN' and head_status == 'DOWN':
                    nod_down_start = now
                if previous_head_status == 'DOWN' and head_status == 'CENTER' and (nod_down_start is not None):
                    if now - nod_down_start <= 3.0:
                        nod_times.append(now)
                    nod_down_start = None
                previous_head_status = head_status
                attention_away = False
                if DRIVE_MODE:
                    if head_status != 'CENTER' or (not eye_closed and gaze_status != 'CENTER'):
                        attention_away = True
                if attention_away:
                    if attention_away_start is None:
                        attention_away_start = now
                    attention_away_duration = now - attention_away_start
                else:
                    attention_away_start = None
                    attention_away_duration = 0.0
                yawn_watch_active = now < yawn_watch_until
                drowsy_count_ui = len(drowsy_event_times)
                yawn_after_eye_drowsy = yawn_watch_active and eye_closed_duration >= YAWN_WATCH_EYE_TIME
                drowsy_reasons = []
                warning_reasons = []
                caution_reasons = []
                if eye_closed_duration >= DROWSY_TIME:
                    drowsy_reasons.append('EYE CLOSED 2s')
                elif eye_closed_duration >= EYE_WARNING_TIME:
                    warning_reasons.append('EYE CLOSED 1s')
                elif eye_closed_duration >= LONG_BLINK_TIME:
                    caution_reasons.append('LONG BLINK')
                if len(long_close_times) >= LONG_CLOSE_LIMIT:
                    drowsy_reasons.append('REPEATED LONG CLOSE')
                if valid_runtime >= PERCLOS_ENABLE_TIME:
                    if perclos >= PERCLOS_WARNING:
                        warning_reasons.append('HIGH PERCLOS')
                    elif perclos >= PERCLOS_CAUTION:
                        caution_reasons.append('PERCLOS')
                if len(yawn_times) >= YAWN_WARNING_COUNT:
                    warning_reasons.append('REPEATED YAWN')
                elif len(yawn_times) >= YAWN_CAUTION_COUNT:
                    caution_reasons.append('YAWN COUNT')
                if yawn_after_eye_drowsy:
                    drowsy_reasons.append('YAWN + CLOSED EYE')
                if head_down_duration >= HEAD_DOWN_WARNING_TIME:
                    warning_reasons.append('HEAD DOWN')
                elif head_down_duration >= HEAD_DOWN_CAUTION_TIME:
                    caution_reasons.append('HEAD DOWN')
                if down_closed_duration >= DOWN_CLOSED_DROWSY_TIME:
                    drowsy_reasons.append('DOWN + CLOSED')
                if len(nod_times) >= NOD_DROWSY_COUNT:
                    drowsy_reasons.append('NODDING')
                elif len(nod_times) >= NOD_CAUTION_COUNT:
                    caution_reasons.append('NOD')
                if blink_baseline_30s is not None:
                    if blink_ratio >= BLINK_WARNING_RATIO:
                        warning_reasons.append('BLINK RATE')
                    elif blink_ratio >= BLINK_CAUTION_RATIO:
                        caution_reasons.append('BLINK RATE')
                distracted = False
                if DRIVE_MODE:
                    if attention_away_duration >= DISTRACTED_TIME:
                        distracted = True
                    elif attention_away_duration >= ATTENTION_CAUTION_TIME:
                        caution_reasons.append('ATTENTION AWAY')
                risk_score = len(caution_reasons) + len(warning_reasons) * 2 + len(drowsy_reasons) * 3
                if drowsy_reasons:
                    raw_state = 'DROWSY'
                elif distracted:
                    raw_state = 'DISTRACTED'
                elif warning_reasons or risk_score >= 3:
                    raw_state = 'WARNING'
                elif caution_reasons:
                    raw_state = 'CAUTION'
                else:
                    raw_state = 'NORMAL'
                safe_now = not eye_closed and head_status == 'CENTER' and (gaze_status == 'CENTER')

                while drowsy_event_times and now - drowsy_event_times[0] > DROWSY_EVENT_WINDOW:
                    drowsy_event_times.popleft()

                # ---------------------------------------------------------
                # DROWSY EVENT SIGNAL
                # ---------------------------------------------------------
                # raw_state can stay DROWSY for many seconds because some
                # reasons use sliding windows (e.g. REPEATED LONG CLOSE,
                # NODDING). Therefore raw_state itself must NOT be used as
                # the event counter trigger.
                #
                # Instead, count one event from:
                #   1) a sustained eye closure,
                #   2) yawn + closed eye,
                #   3) head down + closed eye,
                #   4) a NEW threshold crossing of repeated long close,
                #   5) a NEW threshold crossing of nodding.
                #
                # This prevents the 3rd event from being re-counted as an
                # immediate 4th event.

                repeated_long_close_now = (
                    len(long_close_times) >= LONG_CLOSE_LIMIT
                )
                nodding_drowsy_now = (
                    len(nod_times) >= NOD_DROWSY_COUNT
                )

                new_repeated_long_close = (
                    repeated_long_close_now
                    and not previous_repeated_long_close
                )
                new_nodding_drowsy = (
                    nodding_drowsy_now
                    and not previous_nodding_drowsy
                )

                previous_repeated_long_close = repeated_long_close_now
                previous_nodding_drowsy = nodding_drowsy_now

                event_eye_threshold = (
                    RECOVERY_DROWSY_EYE_TIME
                    if repeated_drowsiness_latched
                    else DROWSY_EVENT_EYE_TIME
                )

                drowsy_event_signal = (
                    eye_closed_duration >= event_eye_threshold
                    or yawn_after_eye_drowsy
                    or down_closed_duration >= DOWN_CLOSED_DROWSY_TIME
                    or new_repeated_long_close
                    or new_nodding_drowsy
                )

                # ---------------------------------------------------------
                # EVENT RE-ARM
                # ---------------------------------------------------------
                # A counted episode must end before a new one can be counted.
                # Gaze is intentionally excluded from the re-arm condition.
                # Head CENTER + no active drowsy-event signal for 0.7 s is
                # enough to allow the next independent event.
                if not drowsy_event_armed and not rest_active:
                    drowsy_rearm_condition = (
                        head_status == 'CENTER'
                        and not drowsy_event_signal
                    )

                    if drowsy_rearm_condition:
                        if drowsy_rearm_start is None:
                            drowsy_rearm_start = now
                        elif now - drowsy_rearm_start >= DROWSY_REARM_TIME:
                            drowsy_event_armed = True
                            drowsy_rearm_start = None
                    else:
                        drowsy_rearm_start = None

                new_drowsy_event = False

                # ---------------------------------------------------------
                # COUNT ONE INDEPENDENT DROWSY EVENT
                # ---------------------------------------------------------
                if (
                    drowsy_event_signal
                    and drowsy_event_armed
                    and not rest_active
                    and DRIVE_MODE
                ):
                    was_repeated_before_event = repeated_drowsiness_latched

                    drowsy_event_times.append(now)
                    drowsy_event_armed = False
                    drowsy_rearm_start = None
                    new_drowsy_event = True

                    log_time = save_drowsy_event(recent_drowsy_logs)
                    print(
                        f'[DROWSY] {log_time} / event count in '
                        f'{DROWSY_EVENT_WINDOW:.0f}s: {len(drowsy_event_times)}'
                    )

                    # IMPORTANT:
                    # 3rd event only enters REPEATED DROWSINESS.
                    # REST REQUIRED is allowed only if REPEATED DROWSINESS
                    # was already active BEFORE this new event.
                    if was_repeated_before_event:
                        rest_required_latched = True
                        repeated_recovery_start = None
                        repeated_recovery_elapsed = 0.0
                        insufficient_rest_warning = False
                        print(
                            '[REST] NEW DROWSY during recovery '
                            '-> REST REQUIRED'
                        )

                        if not DRIVE_MODE and not rest_active:
                            rest_active = True
                            rest_start_time = now
                            print(
                                '[REST] STOP mode already active '
                                '-> rest timer started'
                            )

                    elif len(drowsy_event_times) >= REPEATED_DROWSY_COUNT:
                        repeated_drowsiness_latched = True
                        repeated_recovery_start = None
                        repeated_recovery_elapsed = 0.0
                        print(
                            '[RECOVERY] REPEATED DROWSINESS entered '
                            '-> recovery phase started'
                        )

                # Keep the original DROWSY state/latch algorithm.
                # The relaxed event counter above does not replace raw_state.
                if raw_state == 'DROWSY' and not rest_active and DRIVE_MODE:
                    drowsy_latched = True
                    drowsy_hold_until = now + DROWSY_MIN_HOLD
                    recovery_start = None

                # ---------------------------------------------------------
                # REPEATED DROWSINESS RECOVERY
                # ---------------------------------------------------------
                # Recovery no longer depends on raw_state != DROWSY because
                # old sliding-window reasons can keep raw_state DROWSY even
                # after the actual episode has ended.
                #
                # Recovery condition:
                #   HEAD CENTER + no current acute DROWSY-event signal.
                #
                # Therefore:
                #   3rd event -> recovery can begin normally.
                #   A genuinely new event during recovery -> REST REQUIRED.
                if repeated_drowsiness_latched and not rest_required_latched:
                    repeated_normal_condition = (
                        head_status == 'CENTER'
                        and not drowsy_event_signal
                    )

                    if repeated_normal_condition:
                        if repeated_recovery_start is None:
                            repeated_recovery_start = now
                        repeated_recovery_elapsed = (
                            now - repeated_recovery_start
                        )
                    else:
                        repeated_recovery_start = None
                        repeated_recovery_elapsed = 0.0

                    if repeated_recovery_elapsed >= REPEATED_RECOVERY_TIME:
                        repeated_drowsiness_latched = False
                        repeated_recovery_start = None
                        repeated_recovery_elapsed = 0.0
                        drowsy_event_times.clear()
                        drowsy_event_armed = True
                        drowsy_rearm_start = None
                        drowsy_latched = False
                        drowsy_acknowledged = False
                        post_drowsy_warning_until = 0.0
                        previous_repeated_long_close = False
                        previous_nodding_drowsy = False
                        print(
                            '[RECOVERY] REPEATED DROWSINESS -> NORMAL'
                        )

                if drowsy_latched:
                    if now < drowsy_hold_until:
                        final_state = 'DROWSY'
                    elif safe_now:
                        if recovery_start is None:
                            recovery_start = now
                        if now - recovery_start >= RECOVERY_TIME:
                            drowsy_latched = False
                            recovery_start = None
                            final_state = raw_state
                        else:
                            final_state = 'DROWSY'
                    else:
                        recovery_start = None
                        final_state = 'DROWSY'
                else:
                    final_state = raw_state

                # Safety-state overrides.
                if rest_required_latched:
                    if rest_active:
                        final_state = 'NORMAL'
                    elif insufficient_rest_warning:
                        if raw_state == 'DROWSY':
                            final_state = 'DROWSY'
                        else:
                            final_state = 'WARNING'
                    else:
                        final_state = 'DROWSY'

                elif repeated_drowsiness_latched:
                    if repeated_recovery_elapsed < REPEATED_WARNING_START:
                        final_state = 'DROWSY'
                    else:
                        final_state = 'WARNING'

                elif final_state != 'DROWSY' and now < post_drowsy_warning_until:
                    final_state = 'WARNING'

                # STOP MODE override:
                # regardless of eye/head/gaze/PERCLOS/yawn detection results,
                # STOP mode always stays NORMAL and produces no warning state.
                if not DRIVE_MODE:
                    final_state = 'NORMAL'

                current_final_state = final_state
                set_led(final_state)
                if final_state == 'DROWSY':
                    if not drowsy_acknowledged:
                        if not buzzer_controller.continuous:
                            buzzer_controller.continuous_on()
                    elif buzzer_controller.continuous:
                        buzzer_controller.stop()
                else:
                    if buzzer_controller.continuous:
                        buzzer_controller.stop()
                    drowsy_acknowledged = False
                    if final_state == 'WARNING':
                        alert_once('WARNING', 'DOUBLE', now)
                    elif final_state == 'DISTRACTED':
                        alert_once('DISTRACTED', 'DISTRACTED', now)
            else:
                previous_perclos_time = None
                attention_away_start = None
                head_down_start = None
                down_closed_start = None
                if face_missing_start is None:
                    face_missing_start = now
                missing_time = now - face_missing_start

                # STOP MODE override:
                # face loss must not cause SEARCHING / NO DRIVER or warnings.
                if not DRIVE_MODE:
                    final_state = 'NORMAL'
                    set_led(final_state)
                elif rest_required_latched and rest_active:
                    final_state = 'NORMAL'
                    set_led(final_state)
                elif rest_required_latched and insufficient_rest_warning:
                    final_state = 'WARNING'
                    set_led(final_state)
                elif rest_required_latched:
                    final_state = 'DROWSY'
                    set_led(final_state)
                elif missing_time >= NO_DRIVER_TIME:
                    final_state = 'NO DRIVER'
                    set_led(final_state)
                    alert_once('NO DRIVER', 'LONG', now)
                elif missing_time >= FACE_SEARCH_TIME:
                    final_state = 'SEARCHING'
                    set_led(final_state)
                else:
                    final_state = 'NORMAL'
                    set_led(final_state)
                current_final_state = final_state
                if buzzer_controller.continuous:
                    buzzer_controller.stop()
                drowsy_acknowledged = False
            # UI-only event display. The actual timestamp is already saved
            # by the original save_drowsy_event() logic.
            if new_drowsy_event:
                event_log.append(
                    (
                        time.strftime('%H:%M:%S'),
                        'DROWSINESS DETECTED'
                    )
                )

            # UI rendering only.
            ui = draw_ui(
                frame,
                current_final_state,
                eye_state_ui,
                drowsy_count_ui,
                yawn_count_ui,
                blink_count_ui,
                perclos_ui,
                head_status_ui,
                gaze_status_ui,
                fps,
                event_log,
                cap.isOpened()
            )
            cv2.imshow('DriverSense', ui)
            key = cv2.waitKey(1) & 255
            if key == ord('q'):
                quit_requested = True
                break
            elif key == ord('d'):
                if rest_required_latched:
                    if rest_active and rest_start_time is not None:
                        rest_elapsed = now - rest_start_time

                        if rest_elapsed >= MANDATORY_REST_TIME:
                            DRIVE_MODE = True

                            rest_required_latched = False
                            rest_active = False
                            rest_start_time = None
                            insufficient_rest_warning = False

                            repeated_drowsiness_latched = False
                            repeated_recovery_start = None
                            repeated_recovery_elapsed = 0.0

                            drowsy_event_times.clear()
                            drowsy_event_armed = True
                            drowsy_rearm_start = None
                            previous_repeated_long_close = False
                            previous_nodding_drowsy = False

                            drowsy_latched = False
                            drowsy_hold_until = 0.0
                            recovery_start = None
                            drowsy_acknowledged = False
                            post_drowsy_warning_until = 0.0

                            eye_closed_start = None
                            was_eye_closed = False
                            yawn_open_start = None
                            yawn_active = False
                            yawn_reset_start = None
                            yawn_watch_until = 0.0
                            attention_away_start = None
                            head_down_start = None
                            down_closed_start = None
                            face_missing_start = None
                            previous_head_status = 'CENTER'
                            nod_down_start = None

                            blink_times.clear()
                            long_close_times.clear()
                            yawn_times.clear()
                            nod_times.clear()
                            perclos_data.clear()
                            previous_perclos_time = None
                            valid_runtime = 0.0
                            last_alert_time.clear()

                            buzzer_controller.stop()
                            current_final_state = 'NORMAL'
                            set_led('NORMAL')
                            print('[REST] 10 min complete -> DRIVE / NORMAL / counts reset')

                        else:
                            DRIVE_MODE = True
                            rest_active = False
                            rest_start_time = None
                            insufficient_rest_warning = True
                            buzzer_controller.stop()
                            print('[REST] Not enough rest -> WARNING')

                    else:
                        DRIVE_MODE = True
                        insufficient_rest_warning = True
                        print('[REST] Rest required -> WARNING')

                else:
                    DRIVE_MODE = True

            elif key == ord('s'):
                DRIVE_MODE = False

                # STOP mode starts with a fresh DROWSY event counter.
                # Existing REST / RECOVERY safety flags are not changed.
                drowsy_event_times.clear()
                drowsy_event_armed = True
                drowsy_rearm_start = None

                # Do not carry an active DROWSY latch into STOP mode.
                drowsy_latched = False
                drowsy_hold_until = 0.0
                recovery_start = None

                if rest_required_latched:
                    if rest_active:
                        # Rest timer is already running (or has completed).
                        # Repeated S input must not reset rest_start_time.
                        buzzer_controller.stop()
                        drowsy_acknowledged = True
                        print('[REST] STOP already active -> rest timer unchanged')
                    else:
                        rest_active = True
                        rest_start_time = now
                        insufficient_rest_warning = False
                        buzzer_controller.stop()
                        drowsy_acknowledged = True
                        print('[REST] STOP mode -> rest timer started')

            elif key == ord('r'):
                acknowledge_alert()

            elif key == ord('c'):
                if repeated_drowsiness_latched or rest_required_latched or rest_active or insufficient_rest_warning:
                    print('[RESET] Blocked during repeated-drowsiness/rest protocol')
                else:
                    reset_requested = True
                    break
        if reset_requested:
            buzzer_controller.stop()
            set_led('NORMAL')
            last_alert_time.clear()
            drowsy_acknowledged = False
            ack_drowsy_requested = False
            repeated_drowsiness_latched = False
            previous_repeated_long_close = False
            previous_nodding_drowsy = False
            repeated_recovery_start = None
            repeated_recovery_elapsed = 0.0
            rest_required_latched = False
            rest_active = False
            rest_start_time = None
            insufficient_rest_warning = False
            current_final_state = 'NORMAL'
            print('[RESET] Restarting calibration immediately')
            continue
        if quit_requested:
            break
buzzer_controller.stop()
if HARDWARE_ENABLED:
    green_led.off()
    yellow_led.off()
    red_led.off()
    green_led.close()
    yellow_led.close()
    red_led.close()
    buzzer_hw.close()
    acknowledge_button.close()
cap.release()
cv2.destroyAllWindows()
