# DriverSense V9 코드 설명서
## 기준 소스: `combi_final_ui_integrated_v9.py`

> 이 문서는 현재 대화에서 생성된 **V9 원본 2293줄**을 기준으로 작성했다.  
> 목적은 코드를 줄 단위로 외우는 것이 아니라, **어떤 구간이 어떤 기능을 담당하고 서로 어떻게 연결되는지 이해하는 것**이다.
>
> **주의:** 현재 이 V9 파일의 PERCLOS 상수는 `20% / 30%`이다.  
> 사용자가 Raspberry Pi의 로컬 파일에서 직접 `50% / 60%`으로 수정했다면 **70~71줄의 값만 이 문서와 달라질 수 있다.**

---

# 0. 프로그램을 먼저 한 문장으로 이해하기

이 프로그램은 다음 순서로 동작한다.

```text
Webcam
  ↓
MediaPipe Face Landmarker
  ↓
얼굴 Landmark 추출
  ↓
EAR / MAR / Head / Gaze / Blink / PERCLOS / Nod 계산
  ↓
위험 이유(reason) 생성
  ↓
raw_state 결정
  ↓
DROWSY latch / 반복 DROWSY / Recovery / Rest 같은 안전 로직 적용
  ↓
final_state 결정
  ↓
LED / Buzzer / UI / CSV Log 출력
```

즉 **영상 처리 → 특징값 계산 → 상태 판단 → 안전 프로토콜 → 출력**의 5단 구조이다.

---

# 1. 전체 코드 Line Map

| 줄 | Part | 핵심 역할 |
|---:|---|---|
| 1~12 | 파일 설명 | UI와 Detection/State 로직의 분리를 명시 |
| 14~40 | Import / GPIO 초기화 | OpenCV, MediaPipe, GPIO 및 Virtual Hardware 설정 |
| 41~57 | Landmark Index | 눈·홍채·입·코·얼굴 기준 Landmark 번호 |
| 58~123 | Threshold / 시간 상수 | Blink, DROWSY, PERCLOS, Yawn, Head, Gaze, Recovery, Rest 기준 |
| 124~132 | 전역 Runtime 변수 | Virtual LED/Buzzer, ACK, 현재 State |
| 133~172 | DROWSY Log 함수 | CSV 경로, 기존 Log 읽기, 새 Event 저장 |
| 174~178 | 공통 수학 함수 | 거리 계산, 값 제한 |
| 180~187 | EAR 계산 | 눈 감김 정도 계산 |
| 189~202 | MAR 계산 | 입 벌어짐/하품 정도 계산 |
| 204~229 | Head 계산 | 얼굴 기준 Nose 상대위치 → LEFT/RIGHT/UP/DOWN |
| 231~265 | Gaze 계산 | Iris 상대위치 → LEFT/RIGHT/UP/DOWN |
| 267~290 | LED 제어 | State별 Green/Yellow/Red LED |
| 291~361 | BuzzerController | 경고음 패턴과 연속 부저 제어 |
| 364~386 | Alert / ACK | 경고 Cooldown 및 R/물리버튼 ACK |
| 388~395 | Virtual HW 보조 | 예전 방식의 가상 LED/Buzzer 표시 함수 |
| 396~540 | UI 기본 구성 | UI 색상, 둥근 박스, 텍스트, 기본 Dashboard |
| 543~1314 | `draw_ui()` | 현재 Runtime 상태를 Dashboard에 표시 |
| 1317~1360 | MediaPipe / Webcam 초기화 | 모델 설정, 640×480 MJPG, 30 FPS, UI Window |
| 1361~1494 | Calibration | 5초간 개인 EAR/Head/Gaze 기준값 계산 |
| 1495~1543 | Monitoring 상태변수 초기화 | Blink/Yawn/PERCLOS/DROWSY/Rest용 Timer·Deque 생성 |
| 1544~1617 | Main Loop + ACK 후 처리 | 최근 DROWSY Count에 따라 1회/2회/3회 ACK 분기 |
| 1619~1649 | FPS / Inference 준비 | Rest 중 Buzzer OFF, FPS 계산, 320×240 추론 |
| 1650~1839 | 얼굴 검출 시 Feature/State 계산 | EAR, PERCLOS, Blink, Yawn, Head, Gaze, Nod, Risk State |
| 1841~1970 | DROWSY Event 관리 | 독립 Event 검출, Re-arm, 3회 반복졸음 진입 |
| 1972~2084 | DROWSY Latch / Recovery / 최종 State | Recovery, Rest Override, STOP Override, LED/Buzzer |
| 2085~2121 | 얼굴 미검출 | NORMAL→SEARCHING→NO DRIVER, STOP 예외 |
| 2122~2147 | Event Log / UI 출력 | Event Log 추가 후 `draw_ui()` 호출 |
| 2148~2261 | Keyboard Control | Q/D/S/R/C 키 처리 |
| 2262~2279 | C Recalibration Reset | 안전 프로토콜 외 상태에서 Calibration 재시작 |
| 2280~2293 | 종료 처리 | Buzzer/GPIO/Webcam/Window 정리 |

---

# 2. 1~40줄 — 파일 설명, Import, GPIO

## 1~12줄: 파일의 설계 원칙

```python
# UI rendering is separated from the detection/state algorithm.
```

이 주석이 V9의 중요한 설계 원칙이다.

Detection/State 로직은 실제 운전자 상태를 판단하고, UI는 그 결과값을 **읽어서 표시만** 한다.

즉 이상적으로는:

```text
Algorithm → Runtime Variable → draw_ui()
```

방향이며,

```text
draw_ui() → Algorithm 변경
```

은 하지 않는다.

이 구조 덕분에 UI를 수정하면서 핵심 알고리즘을 건드리지 않을 수 있었다.

---

## 14~19줄: 필수 Library

```python
import cv2
import time
import math
from collections import deque
import mediapipe as mp
import numpy as np
```

### `cv2`
- Webcam 영상 획득
- 영상 Flip/Resize/Color conversion
- UI Window
- 도형·글자 출력

### `time`
- 눈 감은 시간
- Head/Gaze 이탈 시간
- Recovery
- Rest Timer
- FPS
- Timestamp

등 거의 모든 **시간 기반 알고리즘**의 핵심이다.

### `math`
- Landmark 사이 Euclidean distance 계산 등에 사용.

### `deque`
일정 시간 Window만 유지하는 데이터에 사용한다.

대표적으로:

```text
blink_times
long_close_times
yawn_times
nod_times
perclos_data
drowsy_event_times
```

오래된 데이터는 `popleft()`로 제거한다.

### `mediapipe`
Face Landmarker를 통해 얼굴 Landmark를 얻는다.

### `numpy`
Dashboard Canvas 생성에 사용한다.

---

## 20~40줄: Hardware Mode

```python
HARDWARE_ENABLED = False
```

### False
실제 GPIO를 사용하지 않는다.

### True
다음 GPIO가 활성화된다.

| 장치 | BCM |
|---|---:|
| Green LED | 17 |
| Yellow LED | 27 |
| Red LED | 22 |
| Active Buzzer | 18 |
| ACK Button | 23 |

실물 Raspberry Pi에서 사용할 때만 `gpiozero`를 Import한다.

```python
if HARDWARE_ENABLED:
    ...
else:
    green_led = None
```

이 방식의 장점은 PC나 GPIO가 없는 환경에서도 프로그램을 테스트할 수 있다는 것이다.

---

# 3. 41~57줄 — MediaPipe Landmark Index

Face Landmarker는 얼굴의 각 위치에 번호를 부여한다.

V9는 필요한 Landmark만 선택해서 사용한다.

## Eye

```python
LEFT_EYE  = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
```

각 눈의 6개 점을 사용해 EAR을 계산한다.

## Iris

```python
LEFT_IRIS  = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]
```

홍채 중심 좌표를 얻어 Gaze를 계산한다.

## Mouth

```python
MOUTH_LEFT   = 78
MOUTH_RIGHT  = 308
MOUTH_TOP    = 13
MOUTH_BOTTOM = 14
```

MAR 계산에 사용한다.

## Head

```python
NOSE       = 1
LEFT_FACE  = 234
RIGHT_FACE = 454
FOREHEAD   = 10
CHIN       = 152
```

얼굴 전체에서 코가 어느 방향에 위치하는지 계산하여 Head Pose를 판단한다.

---

# 4. 58~123줄 — Threshold와 시간 상수

이 구간은 V9 알고리즘의 **설정값 모음**이다.

알고리즘 자체를 수정하지 않고 민감도를 조절할 때 대부분 이 부분을 수정한다.

---

## 58~60줄: Calibration

```python
CALIBRATION_TIME = 5.0
CALIBRATION_DELAY = 5.0
DEFAULT_EAR_THRESHOLD = 0.2
```

### `CALIBRATION_TIME`
실제로 정면 기준값을 수집하는 시간 = 5초.

### `CALIBRATION_DELAY`
V9에서는 상수는 남아 있지만 **현재 Main Flow에서는 실제로 사용되지 않는다.**

첫 실행은 SPACE를 누르면 바로 Calibration으로 들어간다.

### `DEFAULT_EAR_THRESHOLD`
Calibration 데이터를 얻지 못했을 때 사용하는 기본 EAR Threshold.

---

## 61~65줄: Eye Closure

```python
BLINK_MIN_TIME = 0.08
BLINK_MAX_TIME = 0.6
LONG_BLINK_TIME = 0.6
EYE_WARNING_TIME = 1.0
DROWSY_TIME = 2.0
```

V9에서 눈 감김 지속시간은 다음처럼 해석된다.

```text
0.08 ~ 0.6 s → 일반 Blink
0.6 s 이상   → Long Blink 후보
1.0 s 이상   → WARNING reason
2.0 s 이상   → DROWSY reason
```

중요:

`DROWSY_TIME = 2.0`은 **State 판단 기준**이다.

뒤의 `DROWSY_EVENT_EYE_TIME = 1.5`는 **반복횟수 Event Count 기준**으로 별개이다.

---

## 66~71줄: Long Close / PERCLOS

```python
LONG_CLOSE_WINDOW = 30.0
LONG_CLOSE_LIMIT = 3

PERCLOS_WINDOW = 30.0
PERCLOS_ENABLE_TIME = 10.0
PERCLOS_CAUTION = 20.0
PERCLOS_WARNING = 30.0
```

### Long Close
최근 30초 동안 1초 이상 눈 감은 Event가 3회 이상이면 DROWSY Reason이 된다.

### PERCLOS

최근 30초 동안:

```text
눈을 감고 있었던 시간
──────────────────── × 100
전체 측정 시간
```

으로 계산한다.

초기 10초 동안은 PERCLOS State 판정에 사용하지 않는다.

> **현재 이 V9 원본은 20/30이다.**  
> 로컬 코드에서 50/60으로 수정했다면 이 두 줄만 다르다.

---

## 72~80줄: Yawn

```python
MAR_THRESHOLD = 0.35
YAWN_TIME = 0.8
YAWN_RESET_THRESHOLD = 0.20
YAWN_RESET_TIME = 0.25
YAWN_WINDOW = 60.0
YAWN_CAUTION_COUNT = 2
YAWN_WARNING_COUNT = 3
YAWN_WATCH_TIME = 10.0
YAWN_WATCH_EYE_TIME = 1.0
```

### 기본 원리

입이 충분히 벌어진 상태:

```text
MAR > 0.35
```

가 0.8초 이상 지속되면 Yawn 1회.

동일한 하품이 프레임마다 여러 번 Count되지 않도록:

```text
MAR < 0.20
```

상태가 0.25초 지속되어야 다시 새로운 하품을 받을 수 있다.

### 반복 하품

최근 60초:

```text
2회 → CAUTION
3회 → WARNING
```

### Yawn 후 졸음 집중 감시

하품 후 10초 동안 눈을 1초 이상 감으면:

```text
YAWN + CLOSED EYE
→ DROWSY reason
```

으로 처리한다.

---

## 81~95줄: Head / Gaze / Attention / Nod / Face Missing

### Head Margin

```python
HEAD_X_MARGIN = 0.12
HEAD_Y_UP_MARGIN = 0.12
HEAD_Y_DOWN_MARGIN = 0.09
```

Calibration에서 얻은 Center 기준으로 Margin을 넘으면:

```text
LEFT / RIGHT / UP / DOWN
```

으로 판단한다.

### Gaze Margin

```python
GAZE_X_MARGIN = 0.14
GAZE_Y_MARGIN = 0.04
```

Iris의 Calibration Center에서 이 범위를 벗어나면 Gaze 이탈이다.

### Attention

```python
ATTENTION_CAUTION_TIME = 1.0
DISTRACTED_TIME = 2.0
```

DRIVE Mode에서 Head 또는 Gaze가 CENTER가 아니면 `attention_away=True`.

```text
1초 이상 → CAUTION reason
2초 이상 → DISTRACTED State
```

`ATTENTION AWAY`는 **State 이름이 아니다.**

내부 `caution_reasons`에 들어가는 Reason 문자열이다.

### Head Down

```text
1초 이상 → CAUTION
2초 이상 → WARNING
```

### Down + Closed

```text
0.8초 이상 → DROWSY
```

### Nod

최근 10초:

```text
2회 → CAUTION
3회 → DROWSY
```

### Face Missing

```text
1초 이상 → SEARCHING
2초 이상 → NO DRIVER
```

2초는 SEARCHING에 진입한 뒤 추가 2초가 아니라 **얼굴이 처음 사라진 시점부터 총 2초**이다.

---

## 96~103줄: Blink Baseline / Alert / 일반 DROWSY Recovery

```python
BLINK_BASELINE_TIME = 30.0
BLINK_WINDOW = 30.0
BLINK_CAUTION_RATIO = 1.5
BLINK_WARNING_RATIO = 2.0
```

초기 30초 Blink 수를 개인 Baseline으로 잡는다.

이후 현재 30초 Blink 횟수가:

```text
Baseline × 1.5 이상 → CAUTION
Baseline × 2.0 이상 → WARNING
```

### Alert

```python
ALERT_COOLDOWN = 4.0
```

같은 경고음이 매 프레임 반복되지 않게 최소 4초 간격을 둔다.

### DROWSY Hold

```python
DROWSY_MIN_HOLD = 2.0
RECOVERY_TIME = 1.0
```

한번 DROWSY가 발생하면 최소 2초 유지한다.

그 뒤:

```text
눈 OPEN
Head CENTER
Gaze CENTER
```

가 1초 유지되면 일반 DROWSY latch를 해제한다.

---

## 105~119줄: 반복 DROWSY / Recovery / Rest

```python
DROWSY_EVENT_WINDOW = 60.0
DROWSY_REARM_TIME = 0.7
POST_DROWSY_WARNING_TIME = 3.0
REPEATED_DROWSY_COUNT = 3
```

최근 60초 내 독립 DROWSY Event 3회가 핵심이다.

### Event Count용 Eye 기준

```python
DROWSY_EVENT_EYE_TIME = 1.5
RECOVERY_DROWSY_EYE_TIME = 1.5
```

즉:

```text
State DROWSY : 눈 감김 2.0초
Event Count  : 눈 감김 1.5초
```

이 둘은 의도적으로 분리되어 있다.

### Recovery

```python
REPEATED_RECOVERY_TIME = 30.0
REPEATED_WARNING_START = 15.0
```

3번째 Event 이후:

```text
0~15초  → 화면상 DROWSY
15~30초 → WARNING
30초 완료 → NORMAL
```

### Mandatory Rest

```python
MANDATORY_REST_TIME = 30.0
```

현재 Prototype 시연값은 30초이다.

---

# 5. 124~132줄 — Global Runtime 변수

```python
virtual_green
virtual_yellow
virtual_red
virtual_buzzer
```

실제 GPIO를 사용하지 않을 때도 현재 LED/Buzzer 상태를 저장한다.

UI가 이 값을 읽어 R/Y/G 및 BUZZ 상태를 표시한다.

```python
buzzer_mute_until
```

일반 경고 ACK 후 몇 초 동안 Buzzer를 음소거할지 저장.

```python
drowsy_acknowledged
```

현재 DROWSY 경고를 사용자가 ACK했는지 표시.

```python
current_final_state
```

최종적으로 UI/Hardware가 사용 중인 State.

```python
ack_drowsy_requested
```

물리 버튼 Callback과 Main Loop를 직접 충돌시키지 않고, Main Loop에게 ACK 처리를 요청하는 Flag.

---

# 6. 133~172줄 — CSV DROWSY Event Log

## 133~135줄 `get_drowsy_log_path()`

실행 중인 Python 파일과 같은 폴더에:

```text
drowsy_events.csv
```

경로를 만든다.

---

## 137~155줄 `load_recent_drowsy_logs()`

프로그램 시작 시 기존 CSV를 읽는다.

```python
recent = deque(maxlen=3)
```

이므로 UI에 필요한 **최근 3개**만 메모리에 남긴다.

파일이 없으면:

```text
timestamp
```

Header를 가진 새 CSV를 생성한다.

---

## 157~172줄 `save_drowsy_event()`

새 독립 DROWSY Event가 발생할 때:

```text
YYYY-MM-DD HH:MM:SS
```

형식으로 파일에 추가한다.

이 함수는 **State가 DROWSY인 모든 Frame에서 호출되지 않는다.**

뒤의 `new_drowsy_event`가 실제로 발생한 경우만 호출된다.

---

# 7. 174~265줄 — Landmark → Feature 계산 함수

## 174~175줄 `distance()`

두 점 사이 Euclidean distance:

```text
sqrt((x1-x2)^2 + (y1-y2)^2)
```

EAR, MAR 계산의 기본 함수.

---

## 177~178줄 `clamp()`

```python
max(min_value, min(value, max_value))
```

값이 범위를 벗어나지 못하게 제한한다.

Calibration EAR Threshold를:

```text
0.16 ~ 0.22
```

안에 제한할 때 사용한다.

---

## 180~187줄 `calculate_ear()`

EAR:

```text
        vertical1 + vertical2
EAR = ─────────────────────────
           2 × horizontal
```

눈을 뜨면 수직거리가 커져 EAR이 크고, 눈을 감으면 수직거리가 작아져 EAR이 낮아진다.

V9는 좌우 눈 EAR을 각각 구한 뒤 평균한다.

---

## 189~202줄 `calculate_mar()`

입의:

```text
세로 거리
────────
가로 거리
```

를 계산한다.

입이 크게 벌어질수록 MAR이 증가한다.

하품 검출에 사용한다.

---

## 204~218줄 `calculate_head_metrics()`

얼굴 전체의 Center를 구한 뒤 Nose 위치를 정규화한다.

```python
head_x = (nose.x - face_center_x) / face_width
head_y = (nose.y - face_center_y) / face_height
```

절대 Pixel 좌표가 아니라 **얼굴 크기에 대한 상대좌표**를 쓰기 때문에 카메라와의 거리가 조금 달라져도 영향을 줄인다.

---

## 220~229줄 `classify_head()`

Calibration Center를 기준으로:

```text
X + Margin → RIGHT
X - Margin → LEFT
Y - Margin → UP
Y + Margin → DOWN
그 외       → CENTER
```

를 반환한다.

---

## 231~254줄 Iris/Gaze 계산

### `calculate_iris_center()`
홍채 Landmark들의 평균 좌표.

### `calculate_single_eye_gaze()`

홍채가 눈의 좌우 끝점 사이에서 어느 위치에 있는지 계산한다.

```python
gaze_x = (iris_x - eye_min_x) / eye_width
```

Y값도 눈 너비로 정규화한다.

### `calculate_gaze_metrics()`

양쪽 눈 결과를 평균한다.

---

## 256~265줄 `classify_gaze()`

Calibration의 정면 시선값을 기준으로:

```text
LEFT / RIGHT / UP / DOWN / CENTER
```

로 분류한다.

---

# 8. 267~386줄 — LED / Buzzer / ACK

## 267~290줄 `set_led()`

State를 LED에 대응시킨다.

```text
NORMAL                       → Green
CAUTION / WARNING / SEARCHING → Yellow
DROWSY / DISTRACTED / NO DRIVER → Red
```

먼저 Virtual LED 변수를 갱신하고,

```python
if HARDWARE_ENABLED:
```

일 때만 실제 GPIO도 변경한다.

---

# 9. 291~361줄 — `BuzzerController`

Buzzer는 단순 `sleep()`으로 울리지 않는다.

왜냐하면 `sleep()`을 쓰면 Webcam Frame 처리가 멈추기 때문이다.

대신:

```text
현재 Pattern
현재 Index
다음 상태 변경 시간
```

을 기억하면서 Main Loop마다 `update()`를 호출하는 **비동기형 State 방식**을 사용한다.

---

## `stop()` 300~308줄

모든 Pattern을 종료하고 Buzzer OFF.

---

## `output()` 310~317줄

Virtual Buzzer와 실제 GPIO Buzzer를 동시에 제어.

---

## `continuous_on()` 319~324줄

DROWSY의 지속 경고음.

일반 Pattern과 달리 스스로 끝나지 않는다.

ACK나 State 해제가 필요하다.

---

## `play()` 326~345줄

Pattern별 ON/OFF Sequence 정의.

| Pattern | 의미 |
|---|---|
| SHORT | 짧은 1회 경고 |
| DOUBLE | 두 번 경고 |
| STRONG | 강한 두 번 경고 |
| DISTRACTED | 주의이탈 패턴 |
| LONG | 긴 1회 경고 |

---

## `update()` 347~360줄

현재 시간이 `next_change`를 넘으면 Sequence 다음 단계로 넘어간다.

따라서 Camera Loop를 멈추지 않고 소리를 낼 수 있다.

---

# 10. 364~386줄 — Alert Cooldown / ACK

## `alert_once()`

같은 경고가 Frame마다 반복되지 않도록:

```python
now - previous >= ALERT_COOLDOWN
```

인 경우만 Buzzer Pattern 실행.

---

## `acknowledge_alert()`

현재 State가 DROWSY이면:

```python
drowsy_acknowledged = True
ack_drowsy_requested = True
```

Main Loop에서 DROWSY 횟수에 따른 상태복귀를 처리한다.

DROWSY가 아니면:

```python
buzzer_mute_until = now + BUTTON_MUTE_TIME
```

일반 경고를 잠깐 음소거한다.

### 왜 Main Loop에서 다시 처리하는가?

GPIO Callback 내부에서 수많은 상태변수를 직접 변경하지 않기 위해서다.

Callback:

```text
ACK 요청 Flag 설정
```

Main Loop:

```text
실제 State / Count Reset
```

으로 역할을 분리한다.

---

# 11. 388~395줄 — `draw_virtual_hardware()`

Virtual LED와 Buzzer를 직접 Frame 위에 그리는 예전 방식의 함수다.

현재 V9의 Dashboard에서는 별도의 `draw_ui()`가 Virtual Hardware를 표시하므로 **현재 Main Flow에서 이 함수는 호출되지 않는다.**

즉 남아 있는 보조/Legacy 함수로 보면 된다.

---

# 12. 396~540줄 — UI 기반 구조

## 397줄

```python
UI_W, UI_H = 1200, 800
```

Dashboard 기본 해상도.

---

## 401~418줄

UI에서 쓰는 색상 정의.

OpenCV는 RGB가 아니라 **BGR 순서**라는 점에 주의한다.

---

## 421~429줄 `rr()`

Rounded Rectangle을 직접 구현한다.

OpenCV 기본 `rectangle()`에는 둥근 모서리가 없기 때문에:

```text
중앙 직사각형 2개
+
네 모서리 원 4개
```

를 결합한다.

---

## 432~436줄 `put_text()`

UI 글자 출력 Wrapper.

```python
FONT_HERSHEY_DUPLEX
FONT_HERSHEY_SIMPLEX
```

중 하나를 사용하고 `size`를 OpenCV `fontScale`로 변환한다.

---

## 439~522줄 `build_ui_base()`

매 Frame마다 고정 UI를 처음부터 다시 그리지 않도록 **변하지 않는 Dashboard 배경을 미리 생성**한다.

고정 항목:

- Header
- LIVE CAMERA
- DRIVER STATUS
- CURRENT STATUS
- SWITCH / ACK
- ABNORMAL EVENT LOG
- LIVE METRICS
- KEY BUTTONS

마지막에:

```python
UI_BASE = build_ui_base()
```

로 한 번 만들어두고 `draw_ui()`에서는 `.copy()`한다.

---

## 528~540줄 `state_info()`

State 이름을 UI 문구와 색상으로 변환한다.

예:

```python
'NORMAL'
→ 'NORMAL DRIVING'
→ 'Drive safely.'
→ UI_GREEN
```

알고리즘 State와 사용자에게 보여주는 문구를 분리한 Mapping 함수이다.

---

# 13. 543~1314줄 — `draw_ui()`

V9 UI의 핵심 함수다.

중요한 점:

> **이 함수는 State를 판단하지 않는다.**

이미 계산된 State/Count/Head/Gaze 등을 받아 **표시만** 한다.

---

## 543~554줄: 입력 Parameter

```python
draw_ui(
    frame,
    state,
    eye_state,
    drowsy_count,
    yawn_count,
    blink_count,
    perclos_value,
    head_status,
    gaze_status,
    fps,
    event_log,
    ...
)
```

알고리즘의 결과값을 UI에 전달한다.

---

## 555~595줄: Header / Camera

`UI_BASE.copy()` 후 현재 시간과 Camera Frame을 삽입한다.

Calibration 중에는 Camera 화면을 어둡게 Overlay한다.

FPS도 Camera 왼쪽 아래에 표시한다.

---

## 596~632줄: Runtime Flag 읽기

UI는 다음 전역변수를 **읽기만** 한다.

```text
rest_required_latched
rest_active
rest_start_time
insufficient_rest_warning
repeated_drowsiness_latched
repeated_recovery_elapsed
DRIVE_MODE
```

`globals().get()`을 이용해 가져온다.

---

## 634~895줄: DRIVER STATUS 특수 화면

UI Priority:

```text
REST REQUIRED
>
NOT ENOUGH REST
>
REST TIMER
>
REPEATED RECOVERY
>
CALIBRATION
>
일반 Status Cards
```

### 641~688
`TAKE A REST`

Recovery 중 새 DROWSY Event가 발생한 상태.

### 690~728
`NOT ENOUGH REST`

Mandatory Rest가 끝나기 전에 D를 누른 상태.

### 730~802
Rest Timer.

남은 시간을:

```text
MM:SS
```

형식으로 보여준다.

Timer가 끝나면:

```text
REST COMPLETE
Press D to resume driving.
```

### 804~895
Repeated Drowsiness Recovery.

```text
RECOVERY REQUIRED
RECOVERY: XXs
HEAD
GAZE
```

를 표시한다.

여기서 **Gaze는 UI 정보로 표시될 뿐, 실제 반복졸음 Recovery 조건에는 사용되지 않는다.**

실제 Recovery 조건은 뒤의 1992~2006줄에 있는:

```text
Head CENTER
+
현재 acute DROWSY event signal 없음
```

이다.

> 코드 876~878줄의 주석에는 과거 표현인 `raw_state != DROWSY`가 남아 있지만, 실제 V9 알고리즘은 1992~1996줄이 기준이다.

---

## 897~1021줄: READY / CALIBRATION UI

`calibration_x = 735`를 공통 X좌표로 사용해서 전부 좌측 정렬한다.

### READY
SPACE 입력 안내.

### COUNTDOWN
Countdown 표시 기능은 UI에 존재한다.

하지만 **현재 V9 Main Loop에서는 COUNTDOWN Phase를 실제로 호출하지 않는다.**

### CALIBRATING
남은 5초와 정면/눈 OPEN 안내.

---

## 1023~1121줄: 일반 DRIVER STATUS Cards

4개 정보:

```text
Eye State
Drowsy Count
Head Pose
Gaze
```

STOP Mode에서는:

```python
0 if not drive_mode_ui else drowsy_count
```

이므로 UI Drowsy Count가 반드시 0으로 표시된다.

---

## 1123~1191줄: SWITCH / ACK

표시:

```text
BUZZ ON/OFF
MODE DRIVE/STOP
R / Y / G LED
```

실제 GPIO 또는 Virtual Hardware 상태를 그대로 보여준다.

---

## 1193~1248줄: CURRENT STATUS

중요한 UI Override:

```python
if not drive_mode_ui:
    title = 'STOPPED'
```

즉 알고리즘 내부 Final State가 NORMAL로 강제되어 있더라도 사용자 UI에는:

```text
STOPPED
```

라고 표시한다.

이것이 State Diagram에서 일반 STOP mode를 별도로 표현한 이유다.

---

## 1250~1278줄: Event Log

최근 DROWSY Event 3개를 화면에 표시한다.

---

## 1280~1312줄: LIVE METRICS

```text
Yawn60
Blink30
PERCLOS
```

표시.

이 값들은 새 알고리즘이 아니라 기존 Runtime Deque/PERCLOS 계산값을 읽는다.

---

# 14. 1317~1360줄 — MediaPipe / Webcam 초기화

## MediaPipe

```python
model_path = 'models/face_landmarker.task'
```

Face Landmarker를 VIDEO Mode로 설정하고 얼굴 1명만 검출한다.

Confidence는 모두 0.5.

---

## Webcam

```python
cap = cv2.VideoCapture(0)
```

설정:

```text
Codec      MJPG
Resolution 640×480
FPS        30
Buffer     1
```

### Buffer 1

오래된 Frame이 Queue에 쌓여 영상이 지연되는 것을 줄인다.

---

## 1348~1349줄

```python
cv2.namedWindow('DriverSense', cv2.WINDOW_NORMAL)
cv2.resizeWindow('DriverSense', UI_W, UI_H)
```

사용자가 Window 크기를 변경할 수 있다.

따라서 체크리스트에서 확인했듯 Window 크기를 줄이면 전체 UI Window도 줄어든다.

---

## 1351~1358줄

기존 CSV에서 최근 DROWSY Event를 읽어 UI Event Log 초기값으로 넣는다.

---

# 15. 1361~1494줄 — Calibration

이 구간은 발표에서 반드시 이해해야 하는 핵심이다.

---

## 1361~1379줄: Calibration Buffer 초기화

수집값:

```text
EAR
Head X
Head Y
Gaze X
Gaze Y
```

을 List에 저장한다.

---

## 1381~1410줄: 최초 SPACE 대기

프로그램 첫 실행 때만:

```python
if first_start:
```

SPACE를 누를 때까지 READY 화면 유지.

`Q`는 즉시 종료.

C로 Recalibration하는 경우에는 `first_start=False`이므로 다시 SPACE를 요구하지 않고 바로 Calibration으로 간다.

---

## 1412~1476줄: 5초 Calibration

매 Frame:

1. Camera Read
2. 좌우반전
3. BGR→RGB
4. MediaPipe 실행
5. EAR 계산
6. Head 좌표 계산
7. Gaze 계산
8. 각 값을 Calibration List에 저장
9. 실제 얼굴이 검출된 시간만 `calibration_elapsed`에 추가

즉 단순 Clock 5초가 아니라 **얼굴 Landmark가 정상적으로 검출된 누적시간**을 기준으로 한다.

---

## 1477~1489줄: 개인 Baseline 계산

EAR:

```python
EAR_BASELINE = 평균
EAR_THRESHOLD = clamp(EAR_BASELINE * 0.55, 0.16, 0.22)
```

예를 들어 정면에서 평균 EAR=0.32라면:

```text
0.32 × 0.55 = 0.176
```

이 값이 눈 감김 Threshold가 된다.

Head와 Gaze는 Calibration 평균을 CENTER로 저장한다.

Calibration 실패 시 Default 값 사용.

---

# 16. 1495~1543줄 — Monitoring용 변수 초기화

Calibration이 끝나면 Monitoring Session에 필요한 모든 변수를 Reset한다.

---

## Eye

```text
eye_closed_start
was_eye_closed
```

눈 감기 시작시간과 이전 Frame의 눈 상태.

---

## Yawn

```text
yawn_open_start
yawn_active
yawn_reset_start
yawn_watch_until
```

한 번의 하품을 Event 단위로 관리하고 하품 후 집중 감시를 한다.

---

## Attention / Head

```text
attention_away_start
head_down_start
down_closed_start
face_missing_start
```

각 행동의 지속시간 측정.

---

## Sliding Window Deque

```python
blink_times
long_close_times
yawn_times
nod_times
perclos_data
```

최근 N초 Event만 관리.

---

## General DROWSY latch

```text
drowsy_latched
drowsy_hold_until
recovery_start
```

일반 DROWSY State가 순간적으로 바로 풀리지 않도록 유지.

---

## Repeated DROWSY

```text
drowsy_event_times
drowsy_event_armed
drowsy_rearm_start
repeated_drowsiness_latched
```

최근 60초 독립 DROWSY 횟수 관리.

---

## Edge Tracking

```text
previous_repeated_long_close
previous_nodding_drowsy
```

`REPEATED LONG CLOSE` 같은 지속 조건을 Frame마다 Event로 중복 Count하지 않기 위한 이전 상태 기억.

---

## Recovery / Rest

```text
repeated_recovery_start
repeated_recovery_elapsed

rest_required_latched
rest_active
rest_start_time
insufficient_rest_warning
```

State Diagram 오른쪽 Recovery/Rest 영역과 직접 대응한다.

---

# 17. 1544~1617줄 — Main Loop 시작과 ACK 처리

---

## 1554~1555줄: 60초 Window 유지

```python
while drowsy_event_times and now - drowsy_event_times[0] > 60:
    popleft()
```

따라서 `len(drowsy_event_times)`는 **최근 60초 DROWSY Event 수**이다.

---

## 1557~1617줄: DROWSY ACK

R 버튼이 눌리면 `ack_drowsy_requested=True`.

Main Loop에서 현재 60초 Count를 확인한다.

### Rest Required 상태

ACK해도:

```text
DROWSY 유지
Buzzer만 OFF
```

강제 휴식을 ACK로 우회할 수 없다.

### 3회 이상

```text
Repeated Drowsiness 유지
Buzzer OFF
```

### 1회

```text
ACK → NORMAL
```

### 2회

```text
ACK → WARNING 3초
```

이 부분이 State Diagram의:

```text
DROWSY #1 → R → NORMAL
DROWSY #2 → R → WARNING
```

에 해당한다.

ACK 후에는 Blink/Yawn/PERCLOS 등의 누적 위험 데이터를 일부 Reset하여 바로 위험 State로 재진입하는 것을 줄인다.

하지만 `drowsy_event_times` 자체는 유지하므로 60초 반복 DROWSY Count는 보존된다.

---

# 18. 1619~1649줄 — Rest Buzzer / FPS / MediaPipe 추론 준비

## Rest 중

```python
if rest_active:
    buzzer_controller.stop()
```

Rest 중에는 Buzzer를 계속 끈다.

---

## FPS

1초 동안 처리된 Frame 수를 이용해 FPS 계산.

---

## Inference 최적화

원본 Camera는 640×480이지만 MediaPipe에 넣을 때는:

```python
small_frame = cv2.resize(frame, (320, 240))
```

으로 축소한다.

목적:

```text
UI 영상 품질은 640×480 유지
추론 연산량은 320×240으로 감소
```

---

# 19. 1650~1716줄 — EAR / PERCLOS / Blink

얼굴이 검출되면 실행되는 첫 번째 Feature 부분.

---

## 1650~1667줄: 눈 감김

좌우 EAR:

```python
left_closed = left_ear < EAR_THRESHOLD
right_closed = right_ear < EAR_THRESHOLD
eye_closed = left_closed and right_closed
```

중요:

**양쪽 눈이 모두 감긴 경우만 `eye_closed=True`.**

---

## 1668~1684줄: 시간 기반 PERCLOS

각 Frame 사이 실제 시간 `dt`를 계산한다.

눈이 감겼다면:

```python
closed_dt = dt
```

눈이 열렸다면:

```python
closed_dt = 0
```

최근 30초 Data만 남기고:

```python
perclos = closed_window / total_time * 100
```

계산.

따라서 Frame Rate가 조금 변해도 단순 Frame Count 방식보다 안정적이다.

---

## 1685~1706줄: Eye Duration / Blink / Long Close

눈을 뜨는 순간 직전 눈 감김 시간을 계산한다.

```text
0.08~0.6초 → blink_times
1초 이상   → long_close_times
```

그리고 각 Deque에서 Window를 초과한 오래된 Event를 삭제한다.

---

## 1712~1716줄: Blink 개인 Baseline

Monitoring 시작 후 30초가 지나면:

```python
blink_baseline_30s = max(3, len(blink_times))
```

Baseline이 너무 작은 값이 되는 것을 막기 위해 최소 3으로 설정.

이후 현재 Blink 횟수 ÷ Baseline으로 `blink_ratio` 계산.

---

# 20. 1717~1739줄 — Yawn Detection

MAR > Threshold 상태가 0.8초 지속되면:

```python
yawn_times.append(now)
```

하품 1회.

동시에:

```python
yawn_watch_until = now + 10초
```

로 하품 후 졸음 집중감시 Window를 연다.

### 중복 하품 방지

한번 `yawn_active=True`가 되면 바로 다음 하품으로 인정하지 않는다.

입이 충분히 닫힌:

```text
MAR < 0.20
```

상태가 0.25초 유지되어야 `yawn_active=False`가 된다.

이게 **Hysteresis / Re-arm** 역할이다.

---

# 21. 1740~1784줄 — Head / Gaze / Nod / Attention

## Head

Calibration Center와 Margin으로:

```text
CENTER / LEFT / RIGHT / UP / DOWN
```

판정.

---

## Gaze

눈이 열려 있을 때만 계산.

눈이 감겼으면:

```python
gaze_status = 'CLOSED'
```

---

## Head Down Timer

DOWN 지속시간 계산.

---

## Down + Closed

Head=DOWN과 Eye Closed가 동시에 지속된 시간 계산.

---

## Nod

State 전이:

```text
이전: CENTER 등
현재: DOWN
→ nod_down_start 기록

이전: DOWN
현재: CENTER
→ 3초 이내 복귀했다면 Nod 1회
```

즉 단순 DOWN 상태가 아니라:

```text
정면 → 아래 → 정면
```

패턴을 한 번의 Nod로 본다.

---

## Attention Away

```python
if DRIVE_MODE:
    if head_status != 'CENTER' or
       (not eye_closed and gaze_status != 'CENTER'):
        attention_away = True
```

STOP Mode에서는 Attention Away 자체를 State 판단에 사용하지 않는다.

### 1초

```text
CAUTION reason = ATTENTION AWAY
```

### 2초

```text
DISTRACTED
```

---

# 22. 1785~1839줄 — Reason 생성과 `raw_state`

V9 State Decision의 핵심이다.

---

## 세 가지 Reason List

```python
drowsy_reasons = []
warning_reasons = []
caution_reasons = []
```

각 Feature가 해당 위험도를 이 List에 추가한다.

---

## Eye

```text
≥ 2.0초 → DROWSY
≥ 1.0초 → WARNING
≥ 0.6초 → CAUTION
```

---

## Repeated Long Close

최근 30초 3회 이상:

```text
DROWSY
```

---

## PERCLOS

초기 10초가 지난 후:

```text
≥ Warning Threshold → WARNING
≥ Caution Threshold → CAUTION
```

---

## Yawn

```text
60초 3회 → WARNING
60초 2회 → CAUTION
하품 후 10초 내 눈 1초 감김 → DROWSY
```

---

## Head

```text
Head DOWN 2초 → WARNING
Head DOWN 1초 → CAUTION
Down + Closed 0.8초 → DROWSY
```

---

## Nod

```text
10초 3회 → DROWSY
10초 2회 → CAUTION
```

---

## Blink Rate

개인 Baseline 대비:

```text
×2.0 → WARNING
×1.5 → CAUTION
```

---

## Attention

```text
≥ 2초 → DISTRACTED
≥ 1초 → CAUTION reason
```

---

## 1828줄: Risk Score

```python
risk_score =
    caution reason × 1
  + warning reason × 2
  + drowsy reason × 3
```

---

## 1829~1838줄: `raw_state`

Priority:

```text
1. DROWSY reason 존재 → DROWSY
2. distracted         → DISTRACTED
3. WARNING reason 또는 risk_score ≥ 3 → WARNING
4. CAUTION reason     → CAUTION
5. 아무 조건 없음      → NORMAL
```

### `raw_state`란?

현재 Frame에서 Sensor/Feature 조건만 보고 내린 **1차 판단**이다.

아직 DROWSY Hold, 반복졸음 Recovery, Rest, STOP Mode 같은 상위 안전정책은 적용하지 않았다.

---

# 23. 꼭 구분해야 할 4가지 State 관련 변수

이 부분을 이해하면 V9 전체가 훨씬 쉬워진다.

## `raw_state`

Feature만 이용한 즉시 상태.

```text
NORMAL
CAUTION
WARNING
DROWSY
DISTRACTED
```

---

## `drowsy_event_signal`

“현재 새로운 DROWSY Event로 Count할 만한 급성 신호가 있는가?”

State와 별도이다.

---

## `final_state`

Latch / Recovery / Rest / STOP 같은 상위 정책까지 적용한 최종 알고리즘 State.

---

## `current_final_state`

`final_state`를 전역에서 ACK/UI 등이 참조할 수 있도록 보관한 변수.

---

# 24. 1841~1893줄 — DROWSY Event Signal

V9에서 가장 중요한 개선 중 하나다.

## 왜 `raw_state == DROWSY`를 Event Count에 쓰지 않는가?

예를 들어:

```text
최근 30초 Long Close 3회
```

가 발생하면 `REPEATED LONG CLOSE` reason은 일정 시간 계속 유지될 수 있다.

그때 매 Frame:

```text
raw_state = DROWSY
```

이므로 이것을 Event Trigger로 쓰면:

```text
3번째 졸음
→ 다음 Frame
→ 4번째 졸음으로 오인
→ TAKE A REST
```

문제가 발생한다.

그래서 **State와 Event를 분리**했다.

---

## Event Signal 구성

### 1. 지속 눈감김

```python
eye_closed_duration >= event_eye_threshold
```

일반/Recovery 모두 현재 1.5초.

### 2. Yawn + Closed Eye

```python
yawn_after_eye_drowsy
```

### 3. Head Down + Closed

```python
down_closed_duration >= 0.8
```

### 4. Repeated Long Close가 처음 Threshold를 넘는 순간

```python
new_repeated_long_close
```

### 5. Nodding이 처음 Threshold를 넘는 순간

```python
new_nodding_drowsy
```

---

## Edge Detection

```python
current = 조건
new = current and not previous
previous = current
```

즉 계속 True인 상태를 Event 한 번으로만 본다.

---

# 25. 1895~1915줄 — Event Re-arm

DROWSY Event 하나를 Count한 직후:

```python
drowsy_event_armed = False
```

다시 Event를 받을 수 있으려면:

```text
Head CENTER
+
현재 DROWSY Event Signal 없음
+
0.7초 유지
```

가 필요하다.

Gaze는 의도적으로 제외되어 있다.

---

# 26. 1917~1970줄 — 독립 DROWSY Count / 3회 Recovery

Event Count 조건:

```python
drowsy_event_signal
and drowsy_event_armed
and not rest_active
and DRIVE_MODE
```

여기서 V8 이후 중요한 조건:

```python
and DRIVE_MODE
```

STOP Mode에서는 **새 DROWSY Event가 절대 Count되지 않는다.**

---

## Event 발생 시

```python
drowsy_event_times.append(now)
drowsy_event_armed = False
new_drowsy_event = True
```

CSV에도 저장한다.

---

## 3번째 Event

Event 직전에 이미 repeated 상태였는지 저장:

```python
was_repeated_before_event
```

### 아직 repeated가 아니고 Count가 3이 됨

```python
repeated_drowsiness_latched = True
```

→ `RECOVERY REQUIRED`

### 이미 repeated였는데 새 Event가 또 발생

```python
rest_required_latched = True
```

→ `REST REQUIRED / TAKE A REST`

이 구조 덕분에 **3번째 Event 자체가 4번째로 중복 계산되는 문제를 해결**했다.

---

# 27. 1972~2040줄 — 일반 DROWSY Latch

## DROWSY 발생

```python
if raw_state == 'DROWSY'
   and not rest_active
   and DRIVE_MODE:
```

STOP에서는 DROWSY latch를 새로 만들지 않는다.

DROWSY가 발생하면 최소:

```text
2초
```

간 유지한다.

---

## 일반 DROWSY Recovery

최소 Hold가 지난 뒤:

```python
safe_now =
    eye OPEN
    and head CENTER
    and gaze CENTER
```

가 1초 유지되면 DROWSY latch 해제.

이것은 **일반 DROWSY의 복귀 조건**이다.

뒤의 반복 DROWSY Recovery와 다르다.

---

# 28. 1992~2022줄 — Repeated DROWSY Recovery

3번째 DROWSY Event 이후 실행.

Recovery 조건:

```python
head_status == 'CENTER'
and not drowsy_event_signal
```

즉:

```text
Head CENTER
+
현재 급성 DROWSY Event 없음
```

Gaze는 조건이 아니다.

---

## Recovery 중 조건을 깨면

```python
repeated_recovery_start = None
repeated_recovery_elapsed = 0
```

즉 다시 0부터 시작.

---

## 30초 완료

다음 데이터를 Reset:

```text
repeated_drowsiness_latched
drowsy_event_times
event arm
drowsy latch
ACK
Edge tracking
```

→ NORMAL 복귀 가능.

이 부분이 State Diagram의:

```text
RECOVERY REQUIRED
→ Head CENTER + no new Drowsy for 30 s
→ NORMAL
```

이다.

---

# 29. 2042~2061줄 — Safety State Override

`raw_state` 위에 상위 안전정책을 덮어쓴다.

## Rest Required

### Rest 중
내부 `final_state = NORMAL`.

### Rest 부족 상태
Raw가 DROWSY면 DROWSY, 아니면 WARNING.

### 아직 STOP 하지 않음
DROWSY 유지.

---

## Repeated Recovery

```text
Recovery < 15 s → DROWSY
Recovery ≥ 15 s → WARNING
```

30초가 완료되면 앞 단계에서 repeated latch가 해제된다.

---

## 2번째 DROWSY ACK 후

`post_drowsy_warning_until` 동안 WARNING 유지.

---

# 30. 2063~2084줄 — STOP Override / LED / Buzzer

V7~V9에서 매우 중요한 수정.

```python
if not DRIVE_MODE:
    final_state = 'NORMAL'
```

즉 STOP Mode에서는 검출 알고리즘이 값 자체는 계산해도 **경고 State로 전환하지 않는다.**

UI에서는 이 내부 NORMAL을 그대로 `NORMAL DRIVING`으로 보여주지 않고:

```text
STOPPED
```

로 별도 표시한다.

---

## Buzzer

### DROWSY
ACK 전까지 Continuous ON.

### 그 외
Continuous Buzzer OFF.

WARNING / DISTRACTED는 `alert_once()`를 통해 패턴 경고.

---

# 31. 2085~2121줄 — 얼굴 미검출 State

`result.face_landmarks`가 없을 때 실행한다.

---

## STOP Mode

가장 먼저:

```python
if not DRIVE_MODE:
    final_state = 'NORMAL'
```

따라서 STOP에서는:

```text
SEARCHING
NO DRIVER
```

로 변하지 않는다.

---

## DRIVE Mode

처음 얼굴이 사라진 시각:

```python
face_missing_start = now
```

### 총 1초 이상

```text
SEARCHING
```

### 총 2초 이상

```text
NO DRIVER
+
LONG Buzzer
```

### 얼굴이 복귀

Face detected Branch로 다시 들어가며 `face_missing_start=None`.

State Diagram의:

```text
NORMAL → SEARCHING → NO DRIVER
SEARCHING → NORMAL
NO DRIVER → NORMAL
```

흐름과 대응한다.

---

# 32. 2122~2147줄 — UI Event Log / 화면 출력

새 독립 DROWSY Event가 발생했다면:

```python
event_log.append(...)
```

UI 하단에 표시.

그 뒤 모든 현재값을 `draw_ui()`에 전달한다.

```text
Frame
State
Eye
Drowsy Count
Yawn
Blink
PERCLOS
Head
Gaze
FPS
Event Log
```

---

# 33. 2148~2261줄 — Keyboard Control

발표에서 Key 기능을 설명할 때 이 부분이 기준이다.

---

## Q — 2149~2151줄

프로그램 종료 Flag.

---

## D — 2152~2223줄

DRIVE Mode 진입.

### Rest Required가 아닌 일반 STOP

```python
DRIVE_MODE = True
```

→ 일반 Monitoring 복귀.

### Mandatory Rest 중이고 Rest 완료

대규모 Reset 후:

```text
DRIVE
NORMAL
Drowsy Count = 0
```

으로 복귀.

Reset 대상:

- Rest Flags
- Repeated Drowsy
- Event Times
- Drowsy latch
- Eye/Yawn/Attention/Head
- Blink/Long Close/Yawn/Nod
- PERCLOS
- Alert Cooldown

즉 **새 Driving Session처럼 초기화**한다.

### Rest 완료 전 D

```text
DRIVE_MODE = True
rest_active = False
insufficient_rest_warning = True
```

→ `NOT ENOUGH REST / WARNING`

---

## S — 2224~2251줄

STOP Mode.

가장 먼저:

```python
DRIVE_MODE = False
```

그리고:

```python
drowsy_event_times.clear()
```

즉 STOP 진입 순간 Drowsy Count=0.

새 Event Count도 앞의 1926줄 `and DRIVE_MODE` 때문에 차단된다.

DROWSY latch도 제거한다.

---

### Rest Required 상태에서 S

아직 Rest Timer가 없으면:

```python
rest_active = True
rest_start_time = now
```

Rest 시작.

이미 Rest가 진행 중이면:

```text
rest_start_time을 변경하지 않는다.
```

따라서 S를 반복해서 눌러도 Timer가 초기화되지 않는다.

Rest가 이미 0초에 도달한 상태에서도 S 재입력으로 Timer를 다시 시작하지 않는다.

---

## R — 2253~2254줄

`acknowledge_alert()` 호출.

---

## C — 2256~2261줄

다음 Safety Protocol 중 하나라도 활성화되어 있으면 차단:

```text
repeated_drowsiness_latched
rest_required_latched
rest_active
insufficient_rest_warning
```

그 외에는:

```python
reset_requested = True
```

로 Calibration으로 돌아간다.

따라서 V9에서 C는:

```text
NORMAL
CAUTION
WARNING
일반 DROWSY
일반 STOP
```

에서는 가능하고,

```text
RECOVERY REQUIRED
REST REQUIRED
REST IN PROGRESS
NOT ENOUGH REST
```

에서는 차단된다.

---

# 34. 2262~2279줄 — C 버튼 Recalibration

`reset_requested=True`이면 Monitoring Loop를 빠져나온 뒤:

- Buzzer OFF
- LED NORMAL
- Alert 기록 Clear
- Repeated/Rest 관련 Flag Reset

후:

```python
continue
```

로 가장 바깥 Calibration Loop 처음으로 돌아간다.

`first_start=False`이므로 SPACE 대기로 가지 않고 **바로 Calibration을 시작**한다.

이것이 State Diagram의:

```text
General Monitoring States
      │ C
      ▼
Calibration
```

이다.

---

# 35. 2280~2293줄 — 프로그램 종료

종료할 때:

```text
Buzzer OFF
LED OFF
GPIO close
Button close
Webcam release
OpenCV Window destroy
```

를 수행한다.

실물 GPIO를 사용하면 자원 해제가 중요하다.

---

# 36. V9 핵심 변수 사전

| 변수 | 의미 |
|---|---|
| `EAR_THRESHOLD` | 개인화된 눈 감김 기준 |
| `HEAD_X_CENTER`, `HEAD_Y_CENTER` | 개인 정면 Head 기준 |
| `GAZE_X_CENTER`, `GAZE_Y_CENTER` | 개인 정면 Gaze 기준 |
| `eye_closed_duration` | 현재 연속 눈 감김 시간 |
| `blink_times` | 최근 30초 일반 Blink 발생 시각 |
| `long_close_times` | 최근 30초 긴 눈 감김 발생 시각 |
| `yawn_times` | 최근 60초 Yawn 발생 시각 |
| `nod_times` | 최근 10초 Nod 발생 시각 |
| `perclos_data` | 최근 30초 Frame 시간/눈 감김 시간 |
| `attention_away_duration` | Head/Gaze 이탈 지속시간 |
| `raw_state` | Sensor 조건 기반 1차 State |
| `drowsy_latched` | 일반 DROWSY 유지 Flag |
| `drowsy_event_signal` | 독립 DROWSY Event 후보 |
| `drowsy_event_times` | 최근 60초 독립 DROWSY Event |
| `drowsy_event_armed` | 새 Event Count 가능 여부 |
| `repeated_drowsiness_latched` | 3회 반복졸음 Recovery 상태 |
| `repeated_recovery_elapsed` | Recovery 정상 유지 시간 |
| `rest_required_latched` | 강제휴식 필요 Flag |
| `rest_active` | Mandatory Rest Timer 동작 여부 |
| `rest_start_time` | Rest 시작 시각 |
| `insufficient_rest_warning` | Rest 부족 Warning |
| `DRIVE_MODE` | DRIVE/STOP mode |
| `final_state` | Safety Override 적용 후 최종 State |
| `current_final_state` | 전역에서 참조할 최종 State |

---

# 37. `deque`를 이해하면 코드가 쉬워진다

V9에서 여러 번 나오는 구조:

```python
times.append(now)

while times and now - times[0] > WINDOW:
    times.popleft()
```

의 의미는:

```text
새 Event 시간 추가
↓
Window보다 오래된 Event 삭제
↓
len(times) = 최근 Window 내 Event 횟수
```

이다.

예:

```python
yawn_times
WINDOW = 60초
```

라면:

```text
len(yawn_times)
= 최근 60초 하품 횟수
```

이다.

---

# 38. `Latch`란 무엇인가?

`latched=True`는 한 Frame의 조건이 사라져도 **상태를 계속 기억한다**는 의미다.

예:

```python
drowsy_latched = True
```

한 Frame에서 눈이 2초 감겨 DROWSY가 됐다가 바로 눈을 떠도 즉시 NORMAL로 바꾸지 않는다.

정해진 Recovery 조건을 통과해야 Latch를 해제한다.

V9 주요 Latch:

```text
drowsy_latched
repeated_drowsiness_latched
rest_required_latched
```

각각:

```text
일반 DROWSY 기억
반복졸음 Recovery 기억
강제휴식 필요 기억
```

이다.

---

# 39. V9의 State Diagram과 코드 위치 연결

| State Diagram | 코드 위치 |
|---|---:|
| READY → SPACE → CALIBRATION | 1381~1476 |
| Calibration → NORMAL | 1477~1494 |
| NORMAL / CAUTION / WARNING / DROWSY | 1785~1838 |
| NORMAL → DISTRACTED | 1771~1781, 1822~1838 |
| DISTRACTED → NORMAL | Attention 조건 해제 후 1828~1838 |
| NORMAL → SEARCHING | 2090~2117 |
| SEARCHING → NO DRIVER | 2108~2114 |
| SEARCHING/NO DRIVER → NORMAL | 얼굴 재검출 후 1650~, State 재평가 |
| DROWSY #1 + R → NORMAL | 1557~1610 |
| DROWSY #2 + R → WARNING | 1557~1615 |
| 3rd DROWSY / 60s → RECOVERY | 1922~1970 |
| Recovery → NORMAL | 1992~2022 |
| Recovery 중 New DROWSY → REST REQUIRED | 1945~1953 |
| REST REQUIRED + S → REST IN PROGRESS | 2224~2251 |
| Rest 미완료 + D → NOT ENOUGH REST | 2208~2219 |
| NOT ENOUGH REST + S → Rest 재시작 | 2224~2251 |
| Rest 완료 + D → NORMAL | 2152~2206 |
| General Monitoring + S → STOPPED | 2224~2236 |
| STOPPED + D → DRIVE | 2221~2223 |
| General Monitoring + C → CALIBRATION | 2256~2279 |

---

# 40. 발표에서 꼭 설명할 만한 코드 5개

수천 줄을 보여줄 필요가 없다.

다음 5개만 이해하면 전체 코드의 핵심을 설명할 수 있다.

---

## ① EAR

```python
return (vertical1 + vertical2) / (2.0 * horizontal)
```

말로 설명:

> 눈 Landmark의 세로 거리와 가로 거리의 비율인 EAR을 계산해 눈 감김을 검출했습니다.

---

## ② Reason 기반 State Decision

```python
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
```

말로 설명:

> 각각의 센서값을 바로 상태로 쓰는 것이 아니라 Caution, Warning, Drowsy Reason으로 분류한 뒤 우선순위와 Risk Score를 통해 State를 결정했습니다.

---

## ③ State와 Event 분리

```python
drowsy_event_signal = (
    eye_closed_duration >= event_eye_threshold
    or yawn_after_eye_drowsy
    or down_closed_duration >= DOWN_CLOSED_DROWSY_TIME
    or new_repeated_long_close
    or new_nodding_drowsy
)
```

말로 설명:

> DROWSY 상태가 여러 Frame 유지된다고 반복 졸음으로 여러 번 세지 않도록, State와 독립 Event를 분리했습니다.

---

## ④ 3회 반복졸음 / 추가졸음 분기

```python
if was_repeated_before_event:
    rest_required_latched = True
elif len(drowsy_event_times) >= REPEATED_DROWSY_COUNT:
    repeated_drowsiness_latched = True
```

말로 설명:

> 최근 60초 내 세 번째 Drowsy Event에서는 Recovery로 진입하고, Recovery 이후 새로운 졸음이 다시 발생했을 때만 강제 휴식으로 전환했습니다.

---

## ⑤ STOP Mode

```python
if not DRIVE_MODE:
    final_state = 'NORMAL'
```

그리고 Event Count 조건:

```python
and DRIVE_MODE
```

말로 설명:

> 정차 중에는 운전자 이탈이나 눈 감김을 주행 위험으로 판단하지 않도록 경고 State와 Drowsy Event Count를 모두 억제했습니다. UI에는 내부 NORMAL 대신 STOPPED로 표시했습니다.

---

# 41. V9를 공부할 때 추천 순서

2293줄을 1줄부터 읽지 않는 것이 좋다.

다음 순서로 읽으면 훨씬 빠르다.

### 1단계
`58~119줄`

Threshold가 무엇인지 익힌다.

### 2단계
`180~265줄`

EAR / MAR / Head / Gaze 계산법을 이해한다.

### 3단계
`1650~1839줄`

각 Feature가 어떻게 Reason과 `raw_state`가 되는지 본다.

### 4단계
`1841~2084줄`

State와 Event의 차이, 반복 DROWSY, Recovery를 이해한다.

### 5단계
`2148~2279줄`

S/D/R/C 버튼에 따른 상태 전이를 이해한다.

### 6단계
마지막으로 `543~1314줄`

알고리즘 값이 UI에 어떻게 표현되는지 확인한다.

---

# 42. 코드에서 혼동하기 쉬운 부분

## 1. DROWSY 2초와 Event 1.5초는 다르다

```text
DROWSY State 기준 = 2.0초
DROWSY Event Count 기준 = 1.5초
```

따라서 1.5~2.0초 눈 감김은:

```text
Event Count는 증가할 수 있지만
State가 DROWSY까지 가지 않을 수 있다.
```

현재 V9의 의도된 구조이다.

---

## 2. Attention Away는 State가 아니다

```text
ATTENTION AWAY
```

는 CAUTION Reason.

2초 이상 지속되면:

```text
DISTRACTED
```

가 실제 State이다.

---

## 3. STOP 내부 State와 UI 이름이 다르다

Algorithm:

```text
final_state = NORMAL
```

UI:

```text
STOPPED
```

STOP에서는 안전 경고를 억제하기 위해 내부 State를 NORMAL로 만들지만 사용자가 “운전 중”으로 오해하지 않게 화면은 STOPPED로 표시한다.

---

## 4. 일반 DROWSY Recovery와 Repeated DROWSY Recovery는 다르다

### 일반 DROWSY
```text
Eye OPEN + Head CENTER + Gaze CENTER
1초
```

### Repeated DROWSY
```text
Head CENTER + no acute Drowsy Event
30초
```

---

## 5. CSV Event와 UI State는 1:1이 아니다

CSV는 **독립 DROWSY Event**를 저장한다.

매 Frame의 DROWSY State를 저장하는 것이 아니다.

---

# 43. 현재 V9에서 확인되는 Legacy / 주석상 주의점

이 항목들은 동작상 치명적인 문제라는 뜻이 아니라, 코드를 읽다가 혼동할 수 있어 기록한다.

### `CALIBRATION_DELAY = 5.0`
상수는 선언되어 있지만 현재 Main Flow에서 사용되지 않는다.

### `COUNTDOWN` UI
`draw_ui()`에 존재하지만 현재 Main Flow에서는 호출되지 않는다.

### `draw_virtual_hardware()`
정의되어 있지만 현재 Dashboard Flow에서는 호출되지 않는다.

### Recovery UI 주석
876~878줄 주석에는 과거 `raw_state != DROWSY` 설명이 남아 있지만 실제 V9 Recovery 로직은 1992~1996줄:

```text
Head CENTER
+
not drowsy_event_signal
```

이다.

### 2206줄 출력 문자열
```python
'[REST] 10 min complete ...'
```

라고 Print하지만 실제 `MANDATORY_REST_TIME`은 현재 30초이다.

즉 Console 문구만 과거 표현이 남은 것이며 Timer 알고리즘은 상수 30초를 사용한다.

---

# 44. 내가 이 코드를 설명해야 할 때 쓸 수 있는 1분 요약

> V9 프로그램은 MediaPipe Face Landmarker에서 얻은 얼굴 Landmark를 기반으로 EAR, MAR, Head Pose, Gaze를 계산합니다. 이후 Blink, PERCLOS, Yawn, Nod 같은 시간 기반 데이터를 누적해 Caution, Warning, Drowsy Reason을 만들고 이를 이용해 기본 State를 결정합니다. 단순 State 판정에서 끝나지 않고 Drowsy Event를 별도로 정의하여 최근 60초 내 반복 횟수를 관리하며, 3회 발생 시 Recovery, Recovery 중 추가 졸음 발생 시 Mandatory Rest로 전환됩니다. 또한 STOP Mode에서는 주행 중이 아니므로 Drowsy Count와 Driver Missing, Distracted 경고를 억제하도록 구성했습니다. 최종 State는 LED와 Buzzer에 연결되고 Dashboard UI와 CSV Event Log에도 표시됩니다.

---

# 45. 발표 질문 대비 핵심 Q&A

## Q. 왜 Calibration을 하나?

사람마다 눈 크기, 얼굴 형태, 정면 Head/Gaze 값이 달라 고정 Threshold만 쓰면 오차가 커질 수 있기 때문이다.

EAR/Head/Gaze의 개인 기준값을 5초간 측정한다.

---

## Q. 왜 양쪽 눈이 모두 감겨야 Closed인가?

한쪽 눈만 일시적으로 감거나 Landmark가 흔들리는 상황을 DROWSY로 오인할 가능성을 줄이기 위해:

```python
eye_closed = left_closed and right_closed
```

를 사용한다.

---

## Q. 왜 Event와 State를 분리했나?

DROWSY State가 여러 Frame 지속되어도 실제 졸음 행동은 한 번이기 때문이다.

Frame마다 Count하면 반복졸음 횟수가 잘못 증가한다.

---

## Q. 왜 deque를 사용했나?

60초, 30초, 10초 같은 Sliding Window 안의 Event만 효율적으로 유지하기 위해서다.

오래된 값은 왼쪽에서 즉시 제거할 수 있다.

---

## Q. STOP Mode에서 왜 내부 State를 NORMAL로 하나?

정차 상태에서는 운전자 얼굴 이탈, 시선 이탈, 눈 감김을 주행 안전 경고로 볼 필요가 없기 때문이다.

대신 UI 문구는 `STOPPED`로 보여준다.

---

## Q. 왜 Recovery에서 Gaze는 조건에 넣지 않았나?

현재 V9 반복졸음 Recovery 조건은 코드상:

```text
Head CENTER
+
no acute drowsy event
```

이다.

Gaze는 UI에서 참고 정보로 표시하지만 Recovery Timer 조건에는 포함되지 않는다.

---

# 46. 최종적으로 V9를 이해할 때 기억해야 할 핵심

```text
1. Landmark를 얻는다.
2. EAR / MAR / Head / Gaze를 계산한다.
3. 시간 Window로 Blink/Yawn/PERCLOS/Nod를 누적한다.
4. Reason을 만든다.
5. raw_state를 결정한다.
6. DROWSY Event를 State와 별도로 Count한다.
7. 3회면 Recovery로 간다.
8. Recovery 중 새 DROWSY면 Rest Required가 된다.
9. S/D/R/C 입력으로 Mode와 안전 프로토콜을 제어한다.
10. final_state를 LED/Buzzer/UI에 출력한다.
```

이 10단계를 이해하면 2293줄을 모두 암기하지 않아도 V9 프로그램의 전체 구조와 핵심 원리를 설명할 수 있다.
