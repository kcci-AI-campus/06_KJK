# project development history_v9_2026.09.28

## 웹캠 기반 졸음/집중도 감지기 프로젝트 개발 이력
### 기준 최종 파일: `combi_final_ui_integrated_v9.py`

> 작성 기준일: **2026.09.28**  
> 기준 자료: 업로드된 `project file_~v9.zip` 내부 소스 + 이전 개발 History에서 확인된 초기 개발 흐름  
> 목적: 프로젝트 최초 단계부터 V9까지 **무엇이 문제였고, 왜 다음 버전이 만들어졌으며, 코드가 어떤 원리로 발전했는지**를 한 문서에서 추적하기 위함.
>

---

# 1. 프로젝트 한 줄 요약

초기에는:

```text
Webcam에서 얼굴 Landmark를 검출하고
눈 감김(EAR)을 확인하는 Prototype
```

으로 시작했다.

최종 V9에서는:

```text
Webcam
→ MediaPipe Face Landmark
→ EAR / MAR / Head / Gaze / Blink / PERCLOS / Nod
→ NORMAL / CAUTION / WARNING / DROWSY / DISTRACTED / SEARCHING / NO DRIVER
→ 반복 DROWSY Event Count
→ Recovery / Mandatory Rest
→ DRIVE / STOP Mode
→ LED / Buzzer / ACK Button
→ Dashboard UI / CSV Event Log
```

까지 통합된 **Driver Monitoring Prototype**으로 발전했다.

---

# 2. 전체 개발 계보

```text
[사전 검증]
test_face.py
    ↓
face_webcam.py
    ↓
eye_test.py
    ↓
drowsiness_full.py
    ↓
drowsiness_full_2.py
    ↓
drowsiness_full_3.py
    ↓
drowsiness_full_4.py
    ↓
drowsiness_full_5.py
    ↓
Iris.py
    ↓
Iris_2.py
    ↓
Iris_3.py
    ↓
combi.py
    ↓
combi_2.py
    ↓
combi_3_compact.py
    ↓
combi_4_frame.py
    ↓
combi_5_fps.py
    ↓
combi_6_yawn_drowsy_buzz.py
    ↓
combi_7_calibration_delay.py
    ↓
combi_8_reset_calibration.py
    ↓
combi_9_space_start_calibration.py
    ↓
combi_10_button_normal_reset.py
    ↓
combi_final_maybe.py
    ↓
combi_final_maybe_2.py
    ↓
combi_final_maybe_3.py
    ↓
combi_final_maybe_4.py
    ↓
combi_final_ui_integrated.py
    ↓
combi_final_ui_integrated_v2.py
    ↓
combi_final_ui_integrated_v3.py
    ↓
combi_final_ui_integrated_v4.py
    ↓
combi_final_ui_integrated_v5.py
    ↓
combi_final_ui_integrated_v6.py
    ↓
combi_final_ui_integrated_v7.py
    ↓
combi_final_ui_integrated_v8.py
    ↓
combi_final_ui_integrated_v9.py
```

---

# 3. 업로드 압축파일 소스 목록

| 파일 | 줄 수 |
|---|---:|
| `test_face.py` | 18 |
| `face_webcam.py` | 97 |
| `eye_test.py` | 301 |
| `drowsiness_full.py` | 888 |
| `drowsiness_full_2.py` | 796 |
| `drowsiness_full_3.py` | 772 |
| `drowsiness_full_4.py` | 1095 |
| `drowsiness_full_5.py` | 1081 |
| `Iris.py` | 1468 |
| `Iris_2.py` | 1340 |
| `Iris_3.py` | 1372 |
| `combi.py` | 2516 |
| `combi_2.py` | 3687 |
| `combi_3_compact.py` | 684 |
| `combi_4_frame.py` | 697 |
| `combi_5_fps.py` | 743 |
| `combi_6_yawn_drowsy_buzz.py` | 783 |
| `combi_7_calibration_delay.py` | 803 |
| `combi_8_reset_calibration.py` | 827 |
| `combi_9_space_start_calibration.py` | 830 |
| `combi_10_button_normal_reset.py` | 859 |
| `combi_final_maybe.py` | 867 |
| `combi_final_maybe_2.py` | 939 |
| `combi_final_maybe_3.py` | 1220 |
| `combi_final_maybe_4.py` | 1338 |
| `combi_final_ui_integrated.py` | 2032 |
| `combi_final_ui_integrated_v2.py` | 2051 |
| `combi_final_ui_integrated_v3.py` | 2152 |
| `combi_final_ui_integrated_v4.py` | 2153 |
| `combi_final_ui_integrated_v5.py` | 2197 |
| `combi_final_ui_integrated_v6.py` | 2256 |
| `combi_final_ui_integrated_v7.py` | 2275 |
| `combi_final_ui_integrated_v8.py` | 2292 |
| `combi_final_ui_integrated_v9.py` | 2293 |

---

# 4. 개발 이력 상세

| 날짜 | 파일 / 단계 | 문제점 또는 개발 필요사항 | 개선 방향 | 코드 원리 / 핵심 변화 | 후속 파일 |
|---|---|---|---|---|---|
| 9/21 이전 | `test_face.py` | Raspberry Pi에서 MediaPipe Tasks API와 `face_landmarker.task` 모델이 정상적으로 로딩되는지 우선 확인 필요 | Webcam 처리 전에 Face Landmarker 생성만 단독 검증 | `RunningMode.IMAGE`, `num_faces=1`로 `FaceLandmarkerOptions`를 설정하고 `FaceLandmarker.create_from_options()`가 성공하면 `Face Landmarker loaded successfully!`를 출력. 영상 입력 없이 **모델 경로·MediaPipe 설치·Landmarker 객체 생성** 문제를 먼저 분리 확인 | `face_webcam.py` |
| 9/21 초기 | `face_webcam.py` | 모델 로딩만으로는 실제 Webcam 영상에서 Face Landmark가 검출되는지 알 수 없음 | OpenCV Webcam과 MediaPipe 통합 | `VideoCapture(0)` → 좌우반전 → RGB 변환 → `mp.Image` → `detect_for_video()` | `eye_test.py` |
| 9/21 초기 | `eye_test.py` | 얼굴 Landmark만으로는 졸음 상태 판단 불가 | EAR 기반 눈 감김 검출 추가 | 양쪽 눈 6개 Landmark의 수직/수평 거리 비율로 EAR 계산 | `drowsiness_full.py` |
| 9/21 | `drowsiness_full.py` | 눈 감김만으로는 하품이나 고개 움직임을 반영할 수 없음 | MAR / Head Pose 추가 | 입 세로/가로 비율 MAR, 얼굴 Landmark 기반 Head 상태 계산 | `drowsiness_full_2.py` |
| 9/21 | `drowsiness_full_2.py` | Head Pose 계산이 실제 Webcam 환경에서 불안정할 가능성 | 상대좌표 기반 Head 방향으로 단순화 | 얼굴 폭/높이에 대한 Nose 상대좌표를 이용해 LEFT/RIGHT/UP/DOWN/CENTER 판단 | `drowsiness_full_3.py` |
| 9/21 | `drowsiness_full_3.py` | 순간 Head 움직임도 바로 위험으로 판단될 수 있음 | 지속시간 기반 Attention 판단 | CENTER 이탈 시작시간을 기록하고 일정 시간 이상 지속될 때 상태 변화 | `drowsiness_full_4.py` |
| 9/21 | `drowsiness_full_4.py` | 눈 감김 외의 반복 행동과 장시간 위험도를 반영할 필요 | Blink / PERCLOS / Face Missing 구조 추가 | Blink Count, Sliding Window PERCLOS, 얼굴 미검출 시간 측정 | `drowsiness_full_5.py` |
| 9/21 | `drowsiness_full_5.py` | Frame Count 기반 PERCLOS는 FPS 변화에 따라 실제 시간 비율 오차 발생 | 시간 기반 PERCLOS로 변경 | 각 Frame의 `dt`, `closed_dt`를 저장하여 `closed_time / total_time × 100` 계산 | `Iris.py` |
| 9/21 | `Iris.py` | Head가 정면이어도 눈만 다른 방향을 보는 경우 검출 불가 | Iris 기반 Gaze 추적 추가 | Iris Landmark 중심을 눈 영역에 대해 정규화 | `Iris_2.py` |
| 9/21 | `Iris_2.py` | 특히 Gaze UP/DOWN 오판 발생 | 수직 Gaze 계산 보정 | 눈꼬리 평균 Y와 Iris Y의 signed offset을 계산하고 눈 폭으로 정규화 | `Iris_3.py` |
| 9/21 | `Iris_3.py` | 개인별 정면 시선값이 달라 고정 기준의 오차 발생 | Calibration Center + Margin 방식 | 개인 CENTER를 저장한 뒤 ± Margin 바깥에서만 방향 이탈 판정 | `combi.py` |
| 9/21 | `combi.py` | EAR/MAR/Head/Gaze/PERCLOS 기능이 분리되어 있고 하나의 State Decision이 없음 | 통합 State Decision 구성 | `caution_reasons`, `warning_reasons`, `drowsy_reasons`와 Risk Score를 이용해 State 결정 | `combi_2.py` |
| 9/21 | `combi_2.py` | 알고리즘은 통합됐지만 실물 LED/Buzzer/Button과 연결되지 않음 | GPIO Hardware 계층 추가 | BCM17/27/22 LED, BCM18 Buzzer, BCM23 ACK Button 및 `HARDWARE_ENABLED` 분리 | `combi_3_compact.py` |
| 9/21 | `combi_3_compact.py` | 통합 코드가 매우 길어 유지보수와 확인이 불편 | Compact 버전 구성 | 핵심 기능은 유지하면서 코드 구조를 압축·정리 | `combi_4_frame.py` |
| 9/21 | `combi_4_frame.py` | Raspberry Pi에서 실제 처리 성능 확인이 어려움 | Frame/FPS 표시 | Frame Count와 시간차를 이용하여 실시간 FPS 확인 | `combi_5_fps.py` |
| 9/21~22 | `combi_5_fps.py` | Camera Read와 MediaPipe Inference 중 병목 위치 확인 필요 | Webcam/MJPG/Resize/FPS 최적화 | Webcam 640×480 MJPG 30FPS, Buffer 1, Inference 320×240 적용 | `combi_6_yawn_drowsy_buzz.py` |
| 9/22 | `combi_6_yawn_drowsy_buzz.py` | 하나의 하품이 여러 번 Count될 수 있고 DROWSY 부저가 충분히 유지되지 않음 | Yawn Hysteresis + Continuous Buzzer | MAR Reset Threshold를 통과해야 다음 Yawn을 허용하고 DROWSY는 `continuous_on()` | `combi_7_calibration_delay.py` |
| 9/22 | `combi_7_calibration_delay.py` | 실행 직후 Calibration이 시작되어 사용자가 자세를 준비하기 어려움 | Calibration 준비 구간 추가 | Calibration 전에 정면/눈 OPEN 안내 화면 제공 | `combi_8_reset_calibration.py` |
| 9/22 | `combi_8_reset_calibration.py` | Calibration을 다시 하려면 프로그램 전체 재실행 필요 | `C` Recalibration 추가 | `reset_requested` Flag로 Monitoring Loop에서 Calibration Loop로 복귀 | `combi_9_space_start_calibration.py` |
| 9/22 | `combi_9_space_start_calibration.py` | 자동 시작보다 사용자가 직접 준비 후 시작하는 UX 필요 | 최초 SPACE 시작 | 최초 실행은 SPACE 대기, 이후 `C`는 즉시 Recalibration | `combi_10_button_normal_reset.py` |
| 9/22 | `combi_10_button_normal_reset.py` | ACK 후 Buzzer만 꺼지고 DROWSY State/Red LED가 남을 수 있음 | ACK 기반 State 복귀 | GPIO Callback은 Flag만 설정하고 실제 State Reset은 Main Loop에서 수행 | `combi_final_maybe.py` |
| 9/22 | `combi_final_maybe.py` | ACK 후 과거 Blink/PERCLOS/Yawn/Nod 데이터 때문에 위험 State 재진입 가능 | ACK Reset 범위 확대 | Calibration 기준은 유지하되 Sliding Window/Timer/위험 데이터 초기화 | `combi_final_maybe_2.py` |
| 9/23 | `combi_final_maybe_2.py` | 반복 DROWSY를 모두 동일한 단일 Event처럼 취급 | 최근 60초 독립 DROWSY Event Count 도입 | `drowsy_event_times`, `drowsy_event_armed` 사용. 1회→NORMAL, 2회→WARNING, 3회→Repeated | `combi_final_maybe_3.py` |
| 9/23 | `combi_final_maybe_3.py` | 3회 반복 DROWSY 이후 복귀/휴식 정책 부족 | Recovery + Mandatory Rest + CSV Log 추가 | 3회 후 Recovery Timer, Recovery 중 추가 DROWSY 시 `rest_required_latched`, Rest Timer/NOT ENOUGH REST 구성 | `combi_final_maybe_4.py` |
| 9/23 | `combi_final_maybe_3` 문제수정 | 동일한 지속 DROWSY 원인이 새 Event처럼 다시 Count되어 3회 직후 TAKE A REST가 발생할 수 있음 | State와 Event 분리 | `raw_state`와 별도로 `drowsy_event_signal`, Edge Detection, Re-arm을 구현 | `combi_final_maybe_4.py` |
| 9/23 | `combi_final_maybe_4.py` | 시연에서 반복 DROWSY Event 재현이 너무 엄격 | Event Count 기준 완화 | DROWSY State 2.0초는 유지, Event Eye 1.5초 / Re-arm 0.7초로 분리 | UI 통합 계열 |
| 9/23 | `combi_final_ui_integrated.py` | Debug 중심 화면은 발표/시연 가독성이 낮음 | 1200×800 Dashboard UI 통합 | Algorithm과 UI를 분리하고 `draw_ui()`가 Runtime 값만 읽도록 구성 | `..._v2.py` |
| 9/23 | `combi_final_ui_integrated_v2.py` | 3번째 DROWSY 후 Recovery 대신 Rest가 너무 빨리 발생할 수 있음 | 3번째 Event와 Recovery 중 새 Event 구분 강화 | Re-arm 조건을 이용해 기존 Episode가 끝난 뒤의 새 Event만 인정 | `..._v3.py` |
| 9/23 | `combi_final_ui_integrated_v3.py` | Sliding Window DROWSY reason이 계속 유지되면 단순 Re-arm만으로 중복 Event 가능 | `combi_final_maybe_4`의 Event Signal 구조 적용 | acute Event + Edge Detection으로 3회→Recovery, 이후 새 Event→Rest | `..._v4.py` |
| 9/23 | `combi_final_ui_integrated_v4.py` | Yawning Count보다 Drowsy Count가 시연에 중요. Driver Status/Recovery 정렬 불규칙 | Drowsy Count + 좌측 정렬 | `len(drowsy_event_times)`를 UI 표시. Driver/Recovery/Rest 텍스트 X 기준 통일 | `..._v5.py` |
| 9/23 | `combi_final_ui_integrated_v5.py` | 발표 중 조작키를 기억하기 어렵고 관객에게 키 설명이 보이지 않음 | KEY BUTTONS Guide 추가 | Event Log 오른쪽 공간에 `SPACE/R/C/D/S/Q` Key Cap 표시 | `..._v6.py` |
| 9/23 | `combi_final_ui_integrated_v6.py` | 테스트 중 Yawn/Blink/PERCLOS 내부 값 확인이 어렵고 일부 글씨가 작음 | LIVE METRICS + 가독성 개선 | `Yawn60`, `Blink30`, `PERCLOS`를 기존 Deque/계산값에서 읽어 UI에 표시. Calibration/Rest/Mode 관련 일부 Font 확대 | `..._v7.py` |
| 9/23 | `combi_final_ui_integrated_v7.py` | STOP Mode인데 얼굴이 사라지면 SEARCHING/NO DRIVER로 전이되고 경고 발생. Rest 중 S 재입력 시 Timer Reset | STOP State Override + Rest S 재입력 방지 | `DRIVE_MODE=False`이면 최종 State를 NORMAL로 억제. 이미 `rest_active=True`이면 `rest_start_time`을 다시 쓰지 않음 | `..._v8.py` |
| 9/23 | `combi_final_ui_integrated_v8.py` | STOP Mode에서 눈을 오래 감으면 Drowsy Event Count가 계속 증가하고 TAKE A REST까지 진입 가능. UI가 NORMAL DRIVING으로 표시됨 | STOP Mode Event Count 차단 + STOPPED UI | Event Count와 DROWSY latch 조건에 `DRIVE_MODE` 추가. S 진입 시 Event Count Clear. STOP UI `Drowsy Count=0`, Current Status=`STOPPED` | `..._v9.py` |
| 9/23 | `combi_final_ui_integrated_v9.py` | Calibration/재Calibration 화면의 텍스트 위치가 제각각 | Calibration UI 좌측 정렬 통일 | `calibration_x = 735` 공통 기준으로 READY/COUNTDOWN/CALIBRATING 문구 X좌표 통일 | **최종 기준 버전** |

---

# 5. 단계 1 — Face Landmarker / Webcam 기본 검증

```text
test_face
→ face_webcam
→ eye_test
```

## `test_face.py` — 최초 MediaPipe 모델 로딩 검증

실제 제공된 최초 파일은 **18줄의 최소 검증 코드**로, Webcam이나 OpenCV를 연결하기 전에 MediaPipe Face Landmarker 자체가 정상적으로 생성되는지만 확인한다.

### 실제 코드 구조

```python
import mediapipe as mp

BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode
```

MediaPipe Tasks API에서 Face Landmarker 생성에 필요한 Class를 별칭으로 가져온다.

다음으로 옵션을 설정한다.

```python
options = FaceLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path="models/face_landmarker.task"
    ),
    running_mode=RunningMode.IMAGE,
    num_faces=1
)
```

핵심 설정은 다음과 같다.

| 설정 | 의미 |
|---|---|
| `model_asset_path="models/face_landmarker.task"` | 사용할 Face Landmarker 모델 파일 경로 |
| `RunningMode.IMAGE` | 아직 실시간 Webcam 단계가 아니므로 단일 이미지 처리 Mode로 객체를 생성 |
| `num_faces=1` | 한 명의 얼굴만 검출하도록 설정 |

마지막으로:

```python
with FaceLandmarker.create_from_options(options) as landmarker:
    print("Face Landmarker loaded successfully!")
```

를 실행한다.

### 이 단계의 코드 원리

이 파일은 얼굴을 실제로 검출하는 프로그램이 아니다.

목적은 복잡한 요소를 모두 제거하고:

```text
MediaPipe 설치 정상?
        ↓
Tasks API 사용 가능?
        ↓
face_landmarker.task 경로 정상?
        ↓
FaceLandmarker 객체 생성 가능?
```

만 확인하는 것이다.

따라서 오류가 발생하면 Webcam/OpenCV/EAR 로직을 의심할 필요 없이 **MediaPipe 환경 또는 모델 파일 문제**로 범위를 좁힐 수 있다.

### 다음 파일로 발전한 이유

`test_face.py`에서 모델 객체 생성이 정상임을 확인한 뒤에는 다음 질문이 남는다.

> “그렇다면 실제 Webcam Frame을 넣었을 때 얼굴 Landmark가 정상 검출되는가?”

이 검증을 위해 다음 단계인 `face_webcam.py`에서:

```text
OpenCV Webcam
+
MediaPipe Face Landmarker
```

를 통합하였다.

---

초기 목표는 복잡한 졸음 판단이 아니라 다음 순서의 **기초 검증**이었다.

```text
MediaPipe 모델 로딩
        ↓
Webcam Frame 획득
        ↓
Face Landmark 검출
        ↓
Eye Landmark 추출
        ↓
EAR 계산
```

이 단계에서 시스템의 가장 기본적인 입력 파이프라인이 만들어졌다.

---

# 6. 단계 2 — EAR에서 복합 졸음 Feature로 확장

```text
drowsiness_full
→ drowsiness_full_2
→ drowsiness_full_3
→ drowsiness_full_4
→ drowsiness_full_5
```

주요 Feature가 순차적으로 추가되었다.

```text
EAR
→ MAR / Yawn
→ Head Direction
→ Attention Duration
→ Blink
→ PERCLOS
→ Face Missing
```

## EAR

양쪽 눈 Landmark의:

```text
수직거리 합
───────────
2 × 수평거리
```

를 계산한다.

눈을 감으면 수직거리가 줄어 EAR이 낮아진다.

---

## MAR

입 Landmark의:

```text
입 세로거리
─────────
입 가로거리
```

를 이용한다.

MAR가 일정 Threshold 이상 지속되면 Yawn으로 판단한다.

---

## PERCLOS 개선

초기 Frame 중심 접근보다 실제 시간 기반 계산이 더 안정적이다.

```text
최근 30초 동안 눈을 감고 있었던 실제 시간
───────────────────────────────────── × 100
최근 30초 전체 측정시간
```

Frame Rate가 변해도 시간 비율을 유지할 수 있다.

---

# 7. 단계 3 — Iris / Gaze Tracking

```text
Iris.py
→ Iris_2.py
→ Iris_3.py
```

### 목적

Head가 CENTER여도 실제 운전자는 눈만 다른 방향을 보고 있을 수 있다.

따라서:

```text
Head Pose
+
Eye Gaze
```

를 별도로 판단하도록 확장했다.

### 최종 접근

```text
Iris Center
↓
Eye 영역 내 상대 X/Y
↓
Calibration Center
↓
CENTER ± Margin
↓
LEFT / RIGHT / UP / DOWN
```

특히 UP/DOWN 오판을 줄이기 위해 수직 offset 계산과 Calibration Center 방식을 보완했다.

---

# 8. 단계 4 — DriverSense 통합 State Decision

```text
combi.py
→ combi_2.py
```

개별 Feature를 하나의 State Decision으로 결합했다.

### 입력

```text
EAR
Blink
Long Close
PERCLOS
Yawn
Head
Gaze
Nod
Face Missing
```

### Reason

```text
caution_reasons
warning_reasons
drowsy_reasons
```

### Risk Score

```text
CAUTION reason × 1
WARNING reason × 2
DROWSY reason × 3
```

### State Priority

```text
DROWSY reason 존재
    ↓
DROWSY

그 외 DISTRACTED
    ↓
DISTRACTED

그 외 WARNING reason 또는 높은 Risk Score
    ↓
WARNING

그 외 CAUTION reason
    ↓
CAUTION

없음
    ↓
NORMAL
```

---

# 9. 단계 5 — GPIO Hardware 통합

실물 장치:

```text
Green LED  : BCM17
Yellow LED : BCM27
Red LED    : BCM22
Buzzer     : BCM18
ACK Button : BCM23
```

`HARDWARE_ENABLED`를 이용하여:

```text
Virtual Test
↔
Physical GPIO Test
```

를 동일한 코드에서 전환할 수 있도록 했다.

---

# 10. 단계 6 — 코드 Compact / Raspberry Pi 성능 최적화

```text
combi_3_compact
→ combi_4_frame
→ combi_5_fps
```

### Camera

```text
640 × 480
MJPG
30 FPS
Buffer = 1
```

### Inference

```text
Camera 640×480
      ↓
320×240 Resize
      ↓
MediaPipe
```

UI는 비교적 큰 화면을 유지하면서 추론 입력은 줄여 연산량을 감소시켰다.

---

# 11. 단계 7 — Yawn 중복 방지 / Buzzer / Calibration UX

```text
combi_6_yawn_drowsy_buzz
→ combi_7_calibration_delay
→ combi_8_reset_calibration
→ combi_9_space_start_calibration
```

## Yawn Hysteresis

한 번 Yawn으로 Count된 뒤 입이 잠깐만 움직였다고 바로 다음 Yawn으로 계산하지 않는다.

```text
MAR > Threshold
→ Yawn Event

입이 충분히 닫힘
+
Reset 시간 유지
→ 다음 Yawn 허용
```

---

## Calibration UX

발전:

```text
프로그램 실행 즉시 Calibration
        ↓
Calibration 준비 Delay
        ↓
C 버튼 Recalibration
        ↓
최초 SPACE 입력 후 시작
```

V9에서도 최초 실행은 SPACE를 누른 뒤 Calibration을 시작하며, 일반 Monitoring 중 `C`를 누르면 SPACE 재입력 없이 바로 Calibration으로 돌아간다.

---

# 12. 단계 8 — ACK 기반 DROWSY 복구

```text
combi_10_button_normal_reset
→ combi_final_maybe
```

초기 문제:

```text
DROWSY
→ ACK
→ Buzzer OFF
→ DROWSY State와 Red LED가 남을 수 있음
```

개선:

```text
ACK
→ Main Loop에 처리 요청
→ 위험 누적 데이터 Reset
→ State 복귀
```

GPIO Callback 자체에서 모든 변수를 변경하지 않고:

```text
Callback → Flag
Main Loop → 실제 상태 처리
```

구조를 사용했다.

---

# 13. 단계 9 — 최근 60초 DROWSY Event Count

## `combi_final_maybe_2.py`

```text
DROWSY #1 + ACK
→ NORMAL

DROWSY #2 + ACK
→ WARNING

DROWSY #3 within 60s
→ REPEATED DROWSINESS
```

`drowsy_event_times = deque()`에 Event Timestamp를 보관하고 60초보다 오래된 Event는 삭제한다.

---

# 14. 단계 10 — Recovery / Rest Protocol

## `combi_final_maybe_3.py`

3회 반복졸음 이후 두 경로를 만든다.

### Recovery 성공

```text
3rd DROWSY
→ RECOVERY REQUIRED
→ 정상 조건 유지
→ DROWSY
→ WARNING
→ NORMAL
```

### Recovery 중 새 졸음

```text
RECOVERY REQUIRED
→ NEW DROWSY
→ REST REQUIRED
→ S
→ STOP / REST
```

### Rest 미완료

```text
Rest 도중 D
→ NOT ENOUGH REST
```

### Rest 완료

```text
Rest Timer 완료
→ D
→ NORMAL / DRIVE
```

---

# 15. 단계 11 — State와 Event 분리

## `combi_final_maybe_4.py`

프로젝트에서 가장 중요한 로직 보완 중 하나이다.

### 문제

Sliding Window Reason이 남아 있으면:

```text
raw_state = DROWSY
```

가 여러 Frame 지속될 수 있다.

이를 그대로 Event로 세면:

```text
하나의 졸음 Episode
→ 여러 Event로 중복 Count
```

된다.

### 해결

```text
State ≠ Event
```

로 분리.

### DROWSY Event Signal

대표 조건:

```text
Eye Closed ≥ Event Threshold
Yawn + Closed Eye
Head Down + Closed Eye
Repeated Long Close의 Threshold 신규 진입
Nodding Threshold 신규 진입
```

### Edge Detection

```text
False → True
```

로 바뀌는 순간만 Event로 인정한다.

### Re-arm

Event 후:

```text
Head CENTER
+
Drowsy Event Signal 없음
+
0.7초
```

가 되어야 다음 Event를 받을 수 있다.

---

# 16. 단계 12 — UI Dashboard 통합

## `combi_final_ui_integrated.py`

Presentation Layer를 분리했다.

```text
Detection / State / Safety Logic
            ↓
        Runtime 변수
            ↓
         draw_ui()
            ↓
      Dashboard 표시
```

### UI

```text
LIVE CAMERA
DRIVER STATUS
CURRENT STATUS
SWITCH / ACK
ABNORMAL EVENT LOG
```

목표는 Debug Text 중심 화면을 시연 가능한 Dashboard로 바꾸는 것이었다.

---

# 17. UI V2 — Recovery 전환 오류 보완

## `combi_final_ui_integrated_v2.py`

3번째 DROWSY 직후 동일 Episode 때문에 바로 Rest Required로 넘어가는 문제를 완화했다.

```text
3rd Event
→ Recovery

기존 Episode 종료
→ Re-arm

그 다음 실제 새로운 Event
→ Rest Required
```

---

# 18. UI V3 — Event Signal 구조 완전 적용

## `combi_final_ui_integrated_v3.py`

단순 Re-arm만으로 부족했던 문제를 해결하기 위해 `combi_final_maybe_4`의 State/Event 분리 로직을 UI 통합본에도 반영했다.

결과:

```text
3rd DROWSY
→ RECOVERY REQUIRED

같은 눈 감김 유지
→ Event 추가 X

Recovery 중 새 DROWSY
→ REST REQUIRED
```

이 버전 이후 반복졸음 흐름이 의도대로 동작하는 것을 테스트로 확인했다.

---

# 19. UI V4 — Drowsy Count / 정렬 개선

## `combi_final_ui_integrated_v4.py`

### Driver Status

기존:

```text
Eye State
Yawning Count
Head Pose
Gaze
```

변경:

```text
Eye State
Drowsy Count
Head Pose
Gaze
```

`Drowsy Count`는 최근 60초 `drowsy_event_times` 길이를 표시한다.

Yawn Detection 자체는 그대로 유지했다.

### Alignment

Driver Status와 Recovery/Rest 문구를 공통 X 기준으로 왼쪽 정렬했다.

---

# 20. UI V5 — Key Button Guide

## `combi_final_ui_integrated_v5.py`

우측 하단에:

```text
SPACE  Start
R      ACK
C      Reset
D      Drive
S      Stop
Q      Quit
```

을 추가했다.

목적:

- 시연 중 조작 실수 감소
- 관객이 키 기능을 즉시 이해
- 발표자가 별도 키 설명을 하지 않아도 됨

이 변경은 UI 전용으로 기존 Key 동작은 변경하지 않았다.

---

# 21. UI V6 — LIVE METRICS / 가독성 개선

## `combi_final_ui_integrated_v6.py`

2인 기능 테스트에서:

```text
Yawn/PERCLOS/Blink 확인이 어려움
일부 안내문 Font가 작음
```

문제가 확인되었다.

### 추가

```text
LIVE METRICS
Yawn60
Blink30
PERCLOS
```

기존 알고리즘이 이미 계산 중이던 값을 읽어 표시한다.

따라서 Detection Threshold나 Count Algorithm을 바꾸지 않고 **관찰 가능성(Observability)**만 향상했다.

### 가독성

다음 Font를 확대:

- Key Buttons
- Rest Complete 안내
- Calibration 안내
- Camera 상태
- BUZZ / MODE
- Event Log

---

# 22. V7 — STOP Mode State 고정 / Rest Timer 보호

## `combi_final_ui_integrated_v7.py`

테스트에서 두 가지 명확한 Logic Bug가 발견되었다.

---

## 문제 1 — STOP인데 Driver Missing 경고

기존:

```text
S → STOP
운전자가 Webcam 밖으로 나감
→ SEARCHING
→ NO DRIVER
→ 경고
```

하지만 STOP은 운전 중이 아니므로 잘못된 동작이다.

### 수정

Face가 보이는 Branch와 보이지 않는 Branch 모두:

```python
if not DRIVE_MODE:
    final_state = 'NORMAL'
```

로 Override.

알고리즘 내부 안전 State는 NORMAL로 억제한다.

---

## 문제 2 — Rest 중 S 재입력

기존:

```text
Rest Timer 진행
→ S 다시 입력
→ rest_start_time = now
→ Timer 초기화
```

Rest 완료 후 S를 누른 경우에도 Timer가 다시 시작될 수 있었다.

### 수정

```text
rest_active == True
→ S 입력
→ rest_start_time 변경 X
```

이미 진행/완료 중인 Rest Timer를 재시작하지 않는다.

---

# 23. V8 — STOP Mode Drowsy Event 완전 차단

## `combi_final_ui_integrated_v8.py`

V7 테스트에서 추가 문제를 발견했다.

### 문제

STOP에서 State는 NORMAL로 보이지만 Detection/Event 계산은 계속 진행되므로:

```text
STOP
→ 눈 오래 감음
→ Drowsy Event Count 증가
→ 3회
→ Recovery/TAKE A REST 가능
```

즉 표시 State만 막고 Event Count는 막지 않은 상태였다.

### 수정 1 — Event Count 차단

Event 조건에:

```python
and DRIVE_MODE
```

추가.

STOP에서는 새로운 Drowsy Event를 Count하지 않는다.

---

### 수정 2 — DROWSY Latch 차단

```python
if raw_state == 'DROWSY' and not rest_active and DRIVE_MODE:
```

로 변경.

STOP에서 숨겨진 DROWSY latch가 쌓이는 것을 막는다.

---

### 수정 3 — S 진입 시 Count 초기화

```python
drowsy_event_times.clear()
drowsy_event_armed = True
drowsy_rearm_start = None
```

STOP을 누르는 즉시 Drowsy Count를 0으로 만든다.

---

### 수정 4 — STOPPED UI

기존:

```text
NORMAL DRIVING
```

변경:

```text
STOPPED
STOP mode active.
```

알고리즘 내부에서는 NORMAL로 안전 억제하지만 UI는 운전 중으로 오해하지 않게 STOPPED로 표시한다.

---

### 수정 5 — Drowsy Count 표시

```text
DRIVE → 실제 Count
STOP  → 0
```

로 고정.

---

## 압축파일 기준 V8의 추가 변경사항

이번 업로드 ZIP의 V8 소스에는 다음 변경도 확인된다.

```python
HARDWARE_ENABLED = True
PERCLOS_CAUTION = 45.0
PERCLOS_WARNING = 55.0
```

즉 이 특정 V8 파일은 **실물 Hardware Test 설정과 완화된 PERCLOS 기준**을 포함한다.

이는 STOP Mode 로직 수정과 별개로, 테스트 과정에서 로컬로 적용된 설정 변경으로 볼 수 있다.

---

# 24. V9 — Calibration UI 최종 정렬

## `combi_final_ui_integrated_v9.py`

V8 기능 검증 후 남은 UI 문제:

```text
초기 Calibration
C Recalibration
Countdown/안내문
```

의 텍스트 시작 위치가 서로 달랐다.

### 수정

```python
calibration_x = 735
```

공통 기준을 만들고:

```text
START CHECKING
Look straight ahead
Keep your eyes open
Press SPACE to start calibration
Countdown
CALIBRATION IN PROGRESS
남은 시간
```

모두 같은 X 기준으로 정렬했다.

### 결과

초기 SPACE Calibration과 `C` Recalibration 모두 동일한 정렬을 사용한다.

---

## 압축파일 기준 V9 설정 주의

이번 ZIP에 포함된 V9 파일은 V8과 비교할 때:

```python
HARDWARE_ENABLED = False
PERCLOS_CAUTION = 20.0
PERCLOS_WARNING = 30.0
```

으로 되어 있다.

따라서 압축파일의 버전 차이만 보면:

```text
V8 : Hardware=True, PERCLOS=45/55
V9 : Hardware=False, PERCLOS=20/30
```

이다.

이는 Calibration UI 변경과 직접 관련된 로직 변경은 아니다.

사용자가 Raspberry Pi에서 별도로 수정한 **실제 시연용 로컬 V9**가 있다면 PERCLOS/HARDWARE 값은 그 로컬 파일을 최종 기준으로 확인해야 한다.

---

# 25. V9 현재 전체 Architecture

```text
┌──────────────────────┐
│       Webcam         │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ MediaPipe Landmarker │
└──────────┬───────────┘
           ↓
┌──────────────────────────────────────┐
│ Feature Extraction                   │
│ EAR / MAR / Head / Gaze              │
│ Blink / Long Close / PERCLOS / Nod   │
└──────────┬───────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│ Reason / Risk Decision               │
│ Caution / Warning / Drowsy Reasons   │
└──────────┬───────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│ raw_state                            │
│ NORMAL / CAUTION / WARNING / DROWSY  │
│ DISTRACTED                           │
└──────────┬───────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│ Safety State Layer                   │
│ DROWSY Latch                         │
│ DROWSY Event Count                   │
│ Repeated Drowsiness                  │
│ Recovery / Rest                      │
│ DRIVE / STOP Override                │
└──────────┬───────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│ Output                               │
│ LED / Buzzer / UI / CSV Log          │
└──────────────────────────────────────┘
```

---

# 26. V9 핵심 State Flow

## 시작

```text
READY
  │ SPACE
  ▼
CALIBRATION
  │ 5s complete
  ▼
NORMAL
```

---

## 일반 Driving

```text
NORMAL
  ⇄
CAUTION
  ⇄
WARNING
  ↓
DROWSY
```

---

## Attention / Face Missing

```text
NORMAL
 ├─ Head/Gaze away ≥ 2s → DISTRACTED
 │                          │
 │                          └─ Recover → NORMAL
 │
 └─ Face missing ≥ 1s → SEARCHING
                           ├─ Face returns → NORMAL
                           └─ Total missing ≥ 2s → NO DRIVER
                                                   │
                                                   └─ Face returns → NORMAL
```

---

## 반복 DROWSY

```text
1st DROWSY + R
→ NORMAL

2nd DROWSY + R
→ WARNING

3rd DROWSY within 60s
→ RECOVERY REQUIRED
```

---

## Recovery

```text
RECOVERY REQUIRED
        │
        ├─ Head CENTER + no new Drowsy 30s
        │
        └────────────→ NORMAL

        └─ NEW DROWSY
                 ↓
          REST REQUIRED
```

---

## Rest

```text
REST REQUIRED
      │ S
      ▼
STOPPED / REST IN PROGRESS
      │
      ├─ Rest complete
      │       ↓
      │   REST COMPLETE
      │       │ D
      │       ▼
      │     NORMAL
      │
      └─ D before complete
              ↓
       NOT ENOUGH REST
              │ S
              └────→ REST IN PROGRESS
```

---

# 27. 일반 STOP Mode

V8 이후 일반 STOP은 강제 Rest와 별개로 정리되었다.

```text
General Monitoring
      │ S
      ▼
   STOPPED
      │ D
      ▼
General Monitoring
```

STOP Mode의 원칙:

```text
1. UI State = STOPPED
2. Drowsy Count = 0
3. 새 Drowsy Event Count 금지
4. DROWSY latch 신규 생성 금지
5. DISTRACTED 금지
6. SEARCHING 금지
7. NO DRIVER 금지
```

즉 정차 중 행동을 주행 위험으로 해석하지 않는다.

---

# 28. Recalibration Flow

일반 Monitoring 상태에서는:

```text
NORMAL
CAUTION
WARNING
General DROWSY
General STOP
      │
      │ C
      ▼
CALIBRATION
```

하지만 다음 Safety Protocol 중에는 `C`를 차단한다.

```text
RECOVERY REQUIRED
REST REQUIRED
REST IN PROGRESS
NOT ENOUGH REST
```

목적은 사용자가 Calibration Reset으로 Safety Protocol을 우회하지 못하게 하는 것이다.

---

# 29. DROWSY State와 DROWSY Event의 차이

V9를 이해할 때 가장 중요한 개념이다.

## State

```text
현재 Frame과 Sliding Window 정보를 이용한 현재 위험상태
```

예:

```text
raw_state = DROWSY
```

는 여러 Frame 유지될 수 있다.

---

## Event

```text
새롭게 발생한 독립적인 졸음 Episode
```

하나의 눈 감김이 2초 동안 30 Frame 유지되더라도:

```text
DROWSY State = 여러 Frame
DROWSY Event = 1회
```

여야 한다.

이 구분 덕분에 반복졸음 Count가 정확해졌다.

---

# 30. DROWSY Event Signal

독립 Event 후보:

```text
Eye Closed ≥ 1.5s
Yawn + Closed Eye
Down + Closed
Repeated Long Close Threshold 신규 진입
Nodding Threshold 신규 진입
```

지속 조건은 Edge Detection을 사용한다.

```text
False → True
```

인 순간만 Event로 인정한다.

---

# 31. Re-arm

Event Count 직후:

```text
drowsy_event_armed = False
```

새 Event를 받기 위해서는:

```text
Head CENTER
+
현재 acute Drowsy Signal 없음
+
0.7s
```

가 필요하다.

이는 같은 행동을 두 번 Count하는 것을 방지한다.

---

# 32. 현재 핵심 Prototype 설정

압축파일 V9 기준:

```text
Calibration                  5.0 s

Blink                         0.08 ~ 0.6 s
Long Blink                    ≥ 0.6 s
Eye Warning                   ≥ 1.0 s
DROWSY State                  ≥ 2.0 s

DROWSY Event Eye              ≥ 1.5 s
Event Re-arm                  0.7 s
Event Window                  60 s
Repeated DROWSY               3 Events

PERCLOS Window                30 s
PERCLOS Enable                after 10 s
PERCLOS CAUTION               20 %
PERCLOS WARNING               30 %

Yawn Window                   60 s
Yawn CAUTION                  2
Yawn WARNING                  3

Attention CAUTION             1 s
DISTRACTED                    2 s

Face Missing SEARCHING        1 s
Face Missing NO DRIVER        2 s

Recovery Warning Start        15 s
Recovery Complete             30 s
Mandatory Rest                30 s
```

> 실제 Raspberry Pi 시연본에서 PERCLOS 값을 별도 수정했다면 해당 로컬 파일이 우선이다.

---

# 33. UI 최종 구조

```text
┌────────────────────────────────────────────────────────────┐
│                 DRIVER DROWSINESS SYSTEM                   │
├───────────────────────────┬────────────────────────────────┤
│                           │ DRIVER STATUS                  │
│      LIVE CAMERA          │ Eye State                      │
│                           │ Drowsy Count                   │
│                           │ Head Pose                      │
│                           │ Gaze                           │
├───────────────────────────┴────────────────────────────────┤
│ CURRENT STATUS                    │ SWITCH / ACK           │
├────────────────────────────────────────────────────────────┤
│ ABNORMAL EVENT LOG | LIVE METRICS | KEY BUTTONS            │
└────────────────────────────────────────────────────────────┘
```

### LIVE METRICS

```text
Yawn60
Blink30
PERCLOS
```

### KEY BUTTONS

```text
SPACE Start
R ACK
C Reset
D Drive
S Stop
Q Quit
```

---

# 34. CSV Event Logging

파일:

```text
drowsy_events.csv
```

Event 발생 시:

```text
YYYY-MM-DD HH:MM:SS
```

형태로 저장한다.

### 역할 분리

```text
CSV
→ 전체 Event History 보존

UI
→ 최근 3개 Event 표시
```

---

# 35. 테스트를 통해 수정된 대표 Bug

## Bug 1 — 같은 DROWSY가 4번째 Event로 재Count

해결:

```text
raw_state
≠
drowsy_event_signal
```

---

## Bug 2 — 3번째 DROWSY 직후 TAKE A REST

해결:

```text
3rd Event
→ Recovery Required

Repeated가 이미 활성화된 이후의 NEW Event
→ Rest Required
```

---

## Bug 3 — STOP인데 NO DRIVER 발생

해결:

```python
if not DRIVE_MODE:
    final_state = 'NORMAL'
```

---

## Bug 4 — Rest 중 S를 누르면 Timer Reset

해결:

```text
rest_active=True
→ S 입력
→ rest_start_time 유지
```

---

## Bug 5 — STOP 중 Drowsy Count 증가

해결:

```text
Event Count 조건에 DRIVE_MODE 추가
+
STOP 진입 시 drowsy_event_times.clear()
```

---

## Bug 6 — STOP 화면이 NORMAL DRIVING

해결:

```text
내부 final_state = NORMAL
UI title = STOPPED
```

---

# 36. 버전별 핵심 변화 압축표

| 버전 | 핵심 변화 |
|---|---|
| `face_webcam` | Webcam + Face Landmark |
| `eye_test` | EAR |
| `drowsiness_full` | MAR / Head |
| `drowsiness_full_2~5` | Head 개선, Attention, Blink, PERCLOS, Face Missing |
| `Iris~Iris_3` | Gaze Tracking / Calibration Margin |
| `combi` | Feature 통합 State Decision |
| `combi_2` | GPIO |
| `combi_3_compact` | 코드 Compact |
| `combi_4_frame` | Frame 표시 |
| `combi_5_fps` | FPS / 추론 최적화 |
| `combi_6` | Yawn 중복방지 / DROWSY Buzzer |
| `combi_7` | Calibration Delay |
| `combi_8` | C Recalibration |
| `combi_9` | SPACE Start |
| `combi_10` | ACK State Reset |
| `final_maybe` | ACK 후 Risk Data Reset 확대 |
| `final_maybe_2` | 60초 Drowsy Event Count |
| `final_maybe_3` | Recovery / Rest / CSV |
| `final_maybe_4` | State/Event 분리 |
| `UI integrated` | Dashboard UI |
| `UI v2` | Recovery→Rest 조기전환 개선 |
| `UI v3` | Event Signal 완전 적용 |
| `UI v4` | Drowsy Count + 좌측정렬 |
| `UI v5` | Key Buttons |
| `UI v6` | Yawn/Blink/PERCLOS Live Metrics + Font |
| `UI v7` | STOP State 고정 + Rest S Timer 보호 |
| `UI v8` | STOP Count=0 / Event 차단 / STOPPED |
| `UI v9` | Calibration UI 좌측정렬 |

---

# 37. 프로젝트 개발 흐름을 기능 관점에서 요약

```text
1. Webcam이 정상적으로 들어오는가?
        ↓
2. Face Landmark를 얻을 수 있는가?
        ↓
3. 눈 감김을 계산할 수 있는가?
        ↓
4. 하품과 고개도 볼 수 있는가?
        ↓
5. 시선까지 볼 수 있는가?
        ↓
6. 여러 Feature를 State로 합칠 수 있는가?
        ↓
7. LED/Buzzer/Button과 연결할 수 있는가?
        ↓
8. Raspberry Pi에서 실시간으로 돌릴 수 있는가?
        ↓
9. ACK 후 상태를 안전하게 복구할 수 있는가?
        ↓
10. 반복졸음을 단일 DROWSY와 구분할 수 있는가?
        ↓
11. 반복졸음 후 Recovery/Rest Protocol을 만들 수 있는가?
        ↓
12. 같은 Episode를 중복 Event로 세지 않을 수 있는가?
        ↓
13. 발표 가능한 UI로 표시할 수 있는가?
        ↓
14. STOP / REST / Event Count의 예외조건까지 안전하게 처리할 수 있는가?
        ↓
15. Calibration 및 UI 가독성을 최종 정리할 수 있는가?
```

---

# 38. 최종 V9의 의미

최초 개발 단계의 핵심 질문은:

> **“Webcam에서 눈을 감았는지 알 수 있는가?”**

였다.

V9에서의 핵심 질문은:

> **“여러 운전자 행동을 실시간으로 통합하고, 반복 졸음과 정차/휴식 상황까지 구분하여 적절한 State와 경고 흐름을 만들 수 있는가?”**

로 발전했다.

즉 최종 프로그램은 단일 검출 프로그램이 아니라:

```text
Detect
→ Measure
→ Evaluate
→ Decide State
→ Warn
→ Acknowledge
→ Count Events
→ Recover
→ Rest
→ Resume
→ Record
```

의 전체 안전 흐름을 구현한 Prototype이다.

---

# 39. 최종 정리

프로젝트의 발전은 크게 다음 네 축으로 정리할 수 있다.

### 1. Detection 정확도

```text
Face
→ Eye
→ Mouth
→ Head
→ Iris
→ Blink/PERCLOS/Nod
```

### 2. State Logic

```text
Feature
→ Reason
→ Risk Score
→ raw_state
→ final_state
```

### 3. Safety Protocol

```text
DROWSY
→ ACK
→ Event Count
→ Repeated Drowsiness
→ Recovery
→ Mandatory Rest
```

### 4. User / Hardware Interface

```text
Calibration
GPIO
LED
Buzzer
ACK
DRIVE / STOP
Dashboard UI
Event Log
```

최종 `combi_final_ui_integrated_v9.py`는 이 네 축을 하나의 프로그램에 통합한 현재 프로젝트의 기준 버전이다.
