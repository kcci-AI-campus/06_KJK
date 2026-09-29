# DriverSense V9 성능평가 테스트 체크리스트
## 대상 파일: `combi_final_ui_integrated_v9_evaluation_v2.py`

> 목적: 조원들이 **같은 조건과 같은 절차**로 테스트하여 결과를 합칠 수 있도록 하는 공통 Test Protocol이다.  
> Logger V2는 V9 알고리즘을 변경하지 않고, 기존 Runtime 값을 읽어 성능평가 CSV만 추가 저장한다.

---

# 0. 가장 중요한 원칙

- [ ] **모든 조원이 동일한 Evaluation V2 파일 사용**
- [ ] Test 중 V9 Threshold 수정 금지
- [ ] Tester마다 Calibration 새로 수행
- [ ] 가능하면 동일 Webcam / 거리 / 조명 사용
- [ ] 한 Scenario가 끝난 뒤 결과가 안정화된 것을 확인하고 다음 항목 진행
- [ ] 눈 감김 시간은 사람이 Stopwatch로 재지 않음
- [ ] State 전환시간은 Logger의 `eye_closed_duration_s`, `eye_elapsed_s`, Reason Change를 사용
- [ ] 실패한 Trial도 삭제하지 말 것
- [ ] CSV 원본은 수정하지 말고 그대로 보관

---

# 1. 실행 전 준비

## 1-1. 파일

Raspberry Pi 작업 폴더에 다음 파일을 둔다.

```text
combi_final_ui_integrated_v9_evaluation_v2.py
models/face_landmarker.task
```

---

## 1-2. Tester / Scenario 이름 지정

Logger V2는 실행할 때 Tester와 Scenario 이름을 CSV 안에 자동으로 저장할 수 있다.

예:

```bash
DRIVERSENSE_TESTER=A DRIVERSENSE_SCENARIO=NORMAL DRIVERSENSE_RUN=01 python combi_final_ui_integrated_v9_evaluation_v2.py
```

생성 예:

```text
v9_evaluation_A_NORMAL_01_20260928_120000.csv
```

### Tester 이름 통일

```text
A
B
C
```

처럼 미리 정한다.

### Scenario 이름도 아래 표기 그대로 사용하는 것을 권장

```text
NORMAL
EYE_CAUTION
EYE_WARNING
EYE_DROWSY
HEAD
GAZE
FACE_MISSING
YAWN
REPEATED_DROWSY
RECOVERY_SUCCESS
RECOVERY_FAIL
STOP_MODE
REST_PROTOCOL
FPS
```

---

# 2. Calibration 공통 조건

각 Scenario 시작 전:

- [ ] 카메라 정면 위치
- [ ] 얼굴 전체가 화면 안에 들어옴
- [ ] 눈을 자연스럽게 OPEN
- [ ] 고개 CENTER
- [ ] 시선 CENTER
- [ ] SPACE 입력
- [ ] 5초 Calibration 완료
- [ ] Calibration 완료 후 NORMAL 확인

가능하면 Tester와 Camera 간 거리를 Test 중 크게 바꾸지 않는다.

---

# 3. Logger V2에서 추가 확인할 수 있는 값

기존 Logger보다 다음 정보가 추가되었다.

```text
left_ear / right_ear / avg_ear
EAR threshold
eye_closed_duration
MAR
Head X / Y
Gaze X / Y
Head Down duration
Down + Closed duration
Risk Score
CAUTION reasons
WARNING reasons
DROWSY reasons
Drowsy Event Signal
Drowsy Event Armed
Long Close Count
Nod Count
Blink Ratio
```

따라서 최종 State가 다른 Feature 때문에 먼저 바뀌더라도:

```text
LONG BLINK
EYE CLOSED 1s
EYE CLOSED 2s
HIGH PERCLOS
HEAD DOWN
ATTENTION AWAY
...
```

중 **실제 원인이 무엇이었는지 CSV에서 확인 가능**하다.

---

# 4. 모든 Tester가 수행할 Core Test

권장:

```text
Tester A
Tester B
Tester C
```

모두 동일한 Core Test를 수행한다.

이 데이터는 **사람별 Detection 차이**를 확인하는 데 사용한다.

---

## TEST 1 — NORMAL

### 목적
정상 상태에서 False Alarm이 얼마나 발생하는지 확인.

### 방법

- [ ] Scenario = `NORMAL`
- [ ] Calibration 완료
- [ ] 60초 동안 정면 유지
- [ ] 자연스럽게 Blink
- [ ] 일부러 하품/고개이탈/시선이탈하지 않음
- [ ] 종료 후 CSV 보관

### 기대

```text
대부분 NORMAL
DROWSY / DISTRACTED / NO DRIVER 발생 X
```

### 평가

```text
False Alarm Rate
Average FPS
Minimum FPS
```

---

# 5. TEST 2 — Eye / State Threshold

눈을 감은 상태에서는 사람이 시간을 볼 수 없으므로 **대략적인 시간만 의도적으로 유지**하고 정확한 시간은 Logger가 측정한다.

---

## 2-A. EYE_CAUTION

### 행동

약 `0.7 ~ 0.9초` 정도 눈을 감았다가 뜬다.

- [ ] Scenario = `EYE_CAUTION`
- [ ] 5회 반복
- [ ] 각 Trial 사이 최소 2초 NORMAL 유지

### 기대 Trigger

```text
CAUTION_REASONS_CHANGE
→ LONG BLINK
```

Logger의:

```text
eye_closed_duration_s
```

가 약 `0.6초 이상`에서 Reason이 나타나는지 확인한다.

> PERCLOS 등 다른 조건으로 Final State가 먼저 변할 수 있으므로 **Eye Threshold 평가는 Final State만 보지 않고 Reason을 함께 본다.**

---

## 2-B. EYE_WARNING

### 행동

약 `1.1 ~ 1.3초` 눈을 감는다.

- [ ] Scenario = `EYE_WARNING`
- [ ] 5회 반복
- [ ] Trial 사이 최소 2초 OPEN/CENTER

### 기대 Trigger

```text
WARNING_REASONS_CHANGE
→ EYE CLOSED 1s
```

예상:

```text
eye_closed_duration_s ≈ 1.0 s
```

---

## 2-C. EYE_DROWSY

### 행동

`2초 이상` 충분히 눈을 감는다.

- [ ] Scenario = `EYE_DROWSY`
- [ ] DROWSY 발생 확인
- [ ] `DROWSY_REASONS_CHANGE`에 `EYE CLOSED 2s` 확인
- [ ] `NEW_DROWSY_EVENT` 확인

### 중요

DROWSY Event는 최근 60초에 누적된다.

따라서 **순수 Eye DROWSY Test를 반복할 때 3번째 Trial은 Recovery Protocol에 들어갈 수 있다.**

권장 방법:

```text
한 Session에서 1~2회만 DROWSY Test
→ 프로그램 종료
→ 새 Session / 새 Calibration
```

또는 3번째 Trial은 별도의 `REPEATED_DROWSY` Test로 사용한다.

---

# 6. TEST 3 — HEAD

### Scenario

```text
HEAD
```

### 각 방향

- [ ] LEFT 유지
- [ ] RIGHT 유지
- [ ] UP 유지
- [ ] DOWN 유지

각각 2~3회.

### LEFT / RIGHT / UP

2초 이상 이탈.

기대:

```text
HEAD_STATUS_CHANGE
CENTER → 해당 방향

약 1 s
→ ATTENTION AWAY / CAUTION

약 2 s
→ DISTRACTED
```

### DOWN

기대 Reason:

```text
약 1 s → HEAD DOWN / CAUTION
약 2 s → HEAD DOWN / WARNING
```

단, Attention Logic도 동시에 작동할 수 있으므로 Reason Column을 함께 확인한다.

---

# 7. TEST 4 — GAZE

### Scenario

```text
GAZE
```

고개는 최대한 CENTER로 유지하고 **눈동자만** 움직인다.

- [ ] LEFT 2~3회
- [ ] RIGHT 2~3회
- [ ] UP 2~3회
- [ ] DOWN 2~3회

각 방향에서 약 2초 이상 유지.

### 기대

```text
GAZE_STATUS_CHANGE
CENTER → 해당 방향

약 1 s → ATTENTION AWAY
약 2 s → DISTRACTED
```

### 주의

Gaze는 사람별 눈 구조와 Calibration 차이의 영향을 많이 받을 수 있다.

**오검출도 그대로 기록**한다.

예:

```text
실제 LEFT
→ CSV Gaze = CENTER
```

이면 실패 Trial로 남긴다.

---

# 8. TEST 5 — FACE MISSING

### Scenario

```text
FACE_MISSING
```

### 방법

Calibration 후 얼굴 전체를 Camera 밖으로 이동.

- [ ] 3~5회 반복
- [ ] 얼굴 이탈 후 3초 이상 유지
- [ ] 다시 화면 중앙으로 복귀

### 기대

```text
FACE_DETECTION_CHANGE
1 → 0

약 1 s → SEARCHING
약 2 s → NO DRIVER

Face Return
→ NORMAL
```

### 평가

```text
SEARCHING Response Time
NO DRIVER Response Time
복귀 성공 여부
```

---

# 9. TEST 6 — YAWN

### Scenario

```text
YAWN
```

### 방법

입을 충분히 크게 벌리고 약 1초 이상 유지.

- [ ] Yawn 1회
- [ ] 입을 완전히 닫고 Reset
- [ ] 다시 Yawn
- [ ] 총 3회 수행

### 확인

```text
YAWN_COUNT_CHANGE
MAR
MAR Threshold
```

Expected:

```text
1회 → Yawn Count 1
2회 → YAWN COUNT / CAUTION
3회 → REPEATED YAWN / WARNING
```

### 주의

동일하게 입을 계속 벌린 상태가 여러 Yawn으로 Count되지 않아야 한다.

---

# 10. Optional — PERCLOS

PERCLOS는 단발 동작보다 **Window 기반 Metric**이므로 단순 1회 Trial로 평가하기 어렵다.

본 발표에서는:

```text
PERCLOS 수치가 정상적으로 누적되는가
+
Threshold Reason이 발생하는가
```

정도로 확인해도 충분하다.

### 방법

- [ ] Calibration 후 최소 10초 이상 정상 Monitoring
- [ ] 이후 의도적으로 눈 감김 비율 증가
- [ ] `perclos_pct` 상승 확인
- [ ] `PERCLOS` 또는 `HIGH PERCLOS` Reason 확인

정확도 비교가 필요하면 별도의 Video Ground Truth가 필요하므로 **Core Detection Rate와 분리하여 분석**한다.

---

# 11. Safety / State Machine Test
## 한 명의 Tester가 대표로 수행해도 됨

이 부분은 개인 얼굴 특성보다 State Logic 자체 검증 목적이 크므로, 모든 Tester가 반복할 필요는 없다.

권장 담당 Tester 1명:

```text
각 Scenario 3회
```

---

## TEST 7 — REPEATED DROWSY

### Scenario

```text
REPEATED_DROWSY
```

### 방법

60초 내 독립적인 DROWSY를 3회 만든다.

각 DROWSY 사이:

```text
눈 OPEN
Head CENTER
0.7초 이상
```

유지하여 Event가 Re-arm되도록 한다.

- [ ] Event #1
- [ ] Event #2
- [ ] Event #3

### 기대

```text
DROWSY Count
1 → 2 → 3

3rd Event
→ REPEATED_DROWSINESS_CHANGE 0→1
→ RECOVERY REQUIRED
```

### 핵심 검증

3번째 DROWSY가 같은 Episode로 즉시 4번째 Event가 되어서는 안 된다.

---

# 12. TEST 8 — RECOVERY SUCCESS

### Scenario

```text
RECOVERY_SUCCESS
```

Repeated Drowsiness 진입 후:

```text
Head CENTER
+
새 Drowsy Event 없음
```

을 30초 유지한다.

### 체크

- [ ] Recovery 시작
- [ ] 0~15초 DROWSY 표시
- [ ] 15~30초 WARNING 표시
- [ ] 30초 후 NORMAL 복귀
- [ ] `recovery_elapsed_s` 증가 확인
- [ ] `repeated_drowsiness` 1→0 확인

---

# 13. TEST 9 — RECOVERY FAIL

### Scenario

```text
RECOVERY_FAIL
```

Repeated Recovery 중 새로운 독립 DROWSY Event 발생.

### 기대

```text
NEW_DROWSY_EVENT
↓
REST_REQUIRED_CHANGE
0 → 1
↓
TAKE A REST
```

- [ ] Rest Required 진입 확인

---

# 14. TEST 10 — STOP MODE

### Scenario

```text
STOP_MODE
```

일반 Monitoring에서 `S`.

### 확인 1 — 기본

- [ ] UI = STOPPED
- [ ] Drowsy Count = 0

### 확인 2 — 눈 감기

STOP 상태에서 2초 이상 눈 감기.

- [ ] STOPPED 유지
- [ ] Drowsy Count = 0 유지
- [ ] NEW_DROWSY_EVENT 없음

### 확인 3 — 얼굴 이탈

STOP 상태에서 Camera 밖으로 3초 이상 이동.

- [ ] SEARCHING으로 전환 X
- [ ] NO DRIVER로 전환 X
- [ ] STOPPED 유지

### 확인 4 — Head/Gaze 이탈

- [ ] DISTRACTED 전환 X

### 복귀

- [ ] `D` 입력
- [ ] DRIVE Mode 복귀

---

# 15. TEST 11 — REST PROTOCOL

### Scenario

```text
REST_PROTOCOL
```

Recovery 중 새 DROWSY로 REST REQUIRED를 만든 뒤:

### Rest 시작

- [ ] `S`
- [ ] STOPPED / REST IN PROGRESS
- [ ] Rest Timer 시작

### S 반복 입력

Rest 진행 중 S를 다시 누른다.

- [ ] Timer가 처음부터 Reset되지 않음

### Rest 미완료 상태에서 D

- [ ] `D`
- [ ] NOT ENOUGH REST 표시

### 다시 S

- [ ] `S`
- [ ] Rest Timer 다시 진행

### Rest 완료

- [ ] 30초 완료
- [ ] REST COMPLETE

### 완료 후 D

- [ ] `D`
- [ ] NORMAL
- [ ] DRIVE Mode
- [ ] Drowsy Count Reset

---

# 16. FPS Test

### Scenario

```text
FPS
```

두 조건을 권장.

## NORMAL 60초

- [ ] 정상 정면 상태 60초

## Active 60초

Head/Gaze/Eye 등의 상태를 여러 번 변화시킨다.

- [ ] 동적 상태 60초

CSV의:

```text
event = PERF_SAMPLE
```

행에서:

```text
Average FPS
Minimum FPS
Maximum FPS
```

를 계산한다.

### 주의

Logger 자체의 CSV Write가 아주 작은 Overhead를 추가할 수 있으므로, 이 FPS는 **Evaluation Logger가 활성화된 실측 성능**으로 표기한다.

---

# 17. 각 Tester가 끝난 뒤 확인할 것

- [ ] CSV 파일 생성 확인
- [ ] Tester 이름 확인
- [ ] Scenario 이름 확인
- [ ] `SESSION_START` 확인
- [ ] 필요한 Event들이 기록됐는지 확인
- [ ] Test 실패 데이터도 삭제하지 않음
- [ ] CSV 원본 그대로 전달
- [ ] 가능하면 같은 Scenario의 화면녹화 1개 보관

---

# 18. CSV를 전달할 때

가능하면 폴더를 다음처럼 정리한다.

```text
performance_test/
├─ Tester_A/
│  ├─ NORMAL/
│  ├─ EYE_CAUTION/
│  ├─ EYE_WARNING/
│  ├─ EYE_DROWSY/
│  ├─ HEAD/
│  ├─ GAZE/
│  ├─ FACE_MISSING/
│  └─ YAWN/
│
├─ Tester_B/
│  └─ ...
│
├─ Tester_C/
│  └─ ...
│
└─ State_Logic/
   ├─ REPEATED_DROWSY/
   ├─ RECOVERY_SUCCESS/
   ├─ RECOVERY_FAIL/
   ├─ STOP_MODE/
   └─ REST_PROTOCOL/
```

ZIP으로 묶어 전달하면 이후 통합 분석하기 쉽다.

---

# 19. 결과 분석 시 사용할 핵심 Event

| 평가 항목 | CSV에서 볼 Event / Column |
|---|---|
| Eye 0.6 s | `CAUTION_REASONS_CHANGE`, `LONG BLINK`, `eye_closed_duration_s` |
| Eye 1.0 s | `WARNING_REASONS_CHANGE`, `EYE CLOSED 1s` |
| Eye 2.0 s | `DROWSY_REASONS_CHANGE`, `EYE CLOSED 2s` |
| Drowsy Event | `NEW_DROWSY_EVENT` |
| Head | `HEAD_STATUS_CHANGE` |
| Gaze | `GAZE_STATUS_CHANGE` |
| Attention 1 s | `ATTENTION AWAY` Reason |
| Distracted 2 s | `RAW_STATE_CHANGE` / `FINAL_STATE_CHANGE` |
| Face Loss | `FACE_DETECTION_CHANGE` |
| Searching / No Driver | `FINAL_STATE_CHANGE` |
| Yawn | `YAWN_COUNT_CHANGE`, `mar` |
| PERCLOS | `perclos_pct`, Reason Column |
| Repeated Drowsy | `REPEATED_DROWSINESS_CHANGE` |
| Rest Required | `REST_REQUIRED_CHANGE` |
| Rest Active | `REST_ACTIVE_CHANGE` |
| Insufficient Rest | `INSUFFICIENT_REST_CHANGE` |
| FPS | `PERF_SAMPLE`, `fps` |

---

# 20. 꼭 알아둘 주의사항

## ① Final State가 Threshold 시간보다 빨리 변해도 곧바로 실패가 아니다

V9은 여러 Feature를 동시에 사용한다.

예:

```text
눈 감김 0.8초
+
높은 PERCLOS
→ WARNING
```

이 가능하다.

따라서 Eye Threshold Test에서는:

```text
final_state만 보지 말고
Reason + eye_closed_duration_s
```

를 같이 봐야 한다.

---

## ② DROWSY Trial은 서로 독립적이지 않을 수 있다

최근 60초 DROWSY Count가 유지된다.

3번째 Event부터 Recovery Protocol에 들어간다.

따라서 개별 Eye DROWSY 정확도를 평가할 때는 Session을 분리하거나 1~2회만 수행한다.

---

## ③ Calibration 조건이 달라지면 Tester 비교가 어려워진다

가능하면:

```text
같은 조명
같은 Camera
같은 거리
같은 정면 자세
```

를 유지한다.

---

## ④ Gaze 실패를 숨기지 않는다

개인차가 있으면 그 자체가 성능평가 결과다.

```text
Tester A LEFT 성공
Tester B LEFT 실패
```

같은 결과를 그대로 남긴다.

이는 프로젝트의 Limitations/Future Work에 사용할 수 있다.

---

## ⑤ 화면 녹화는 필수 데이터는 아니지만 권장

Logger는 알고리즘 내부 시점을 정확히 기록한다.

화면 녹화는:

```text
사람의 실제 행동
vs
알고리즘 인식
```

을 나중에 눈으로 검증할 수 있게 해준다.

대표 Scenario 몇 개만 녹화해도 충분하다.

---

# 21. 최종적으로 계산할 성능지표

CSV를 모두 모은 뒤 다음을 계산한다.

```text
1. Scenario별 Detection Rate
2. Tester별 Detection Rate
3. False Alarm Rate
4. Eye Threshold 실제 전환시간
5. Head/Gaze 방향 인식 성공률
6. Face Missing State 전환시간
7. State Transition Success Rate
8. STOP Mode 차단 성공률
9. Recovery / Rest Protocol 성공률
10. Average / Minimum / Maximum FPS
11. 실패 Case 공통 패턴
```

이 결과 중 핵심 값만 PPT `프로젝트 결과` 슬라이드에 넣는다.
