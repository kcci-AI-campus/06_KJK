# DriverSense V9 Evaluation — Tester A/B/C 통합 분석 (ver.2)

> 데이터셋: `performance_test_ABC_ver.2.zip`  
> 총 CSV: **78개**  
> 분석 기준: Evaluation Logger V2 기록  
> Normal Test: **A/B/C 각 3 Session, 총 9 Session**

---

# 1. 이번 ver.2에서 바뀐 점

- Tester B의 `EYE_WARNING` **5 Session 재측정**
- Tester B의 `EYE_DROWSY` **5 Session 재측정**
- NORMAL을 A/B/C 각각 3 Session으로 보강하여 **총 9 Session** 확보
- 이전 1차 분석과 동일한 방식으로 전체 ZIP을 처음부터 다시 계산

Tester B 재시험 결과는 다음과 같다.

| 재시험 | Session | 목표 Reason 검출 |
|---|---:|---:|
| EYE_WARNING | 5 | **5/5** |
| EYE_DROWSY | 5 | **5/5** |

즉 이전 데이터에서 B가 목표 시간만큼 눈을 감지 못했던 문제는 이번 데이터에서 보완되었다.

---

# 2. 데이터 품질 확인

ZIP 안 파일명/폴더를 Tester·Scenario·Run의 기준으로 사용했다.
CSV 내부 metadata에는 **6개 파일에서 라벨 불일치**가 확인되었다.

- `A_EYE_WARNING_01`: CSV 내부 Scenario가 `EYE_WARNIN`으로 기록
- `A_REST_PROTOCOL_04`: CSV 내부 Run이 3으로 기록
- `B_NORMAL_02`, `B_NORMAL_03`: CSV 내부 Tester가 C로 기록
- `C_NORMAL_02`, `C_NORMAL_03`: CSV 내부 Tester가 A로 기록

파일이 실제 Tester 폴더와 명확한 파일명 규칙으로 분류되어 있으므로, 이번 분석에서는 **폴더/파일명을 Ground Truth label로 적용**했다.

이 metadata 문제는 성능 알고리즘 문제가 아니라 실행 시 환경변수 Label 입력 문제이다.

---

# 3. 핵심 결과 요약

| 항목 | 설계 기준 | 실측 평균 | 결과 |
|---|---:|---:|---|
| Eye CAUTION | 0.60 s | **0.624 s** | 기준 근접 |
| Eye WARNING | 1.00 s | **1.039 s** | 기준 근접 |
| Eye DROWSY | 2.00 s | **2.027 s** | 기준 근접 |
| Attention CAUTION | 1.00 s | **1.037 s** | 기준 근접 |
| DISTRACTED | 2.00 s | **2.037 s** | 기준 근접 |
| SEARCHING | 1.00 s | **1.038 s** | 기준 근접 |
| NO DRIVER | 2.00 s | **2.035 s** | 기준 근접 |
| PERCLOS CAUTION | 20 % | **20.11 %** | 정상 |
| PERCLOS WARNING | 30 % | **30.14 %** | 정상 |
| FPS | 실시간 처리 | **12.88 FPS** | 실시간 동작 |

핵심적으로 **시간 기반 Threshold는 설정값보다 약 0.02~0.04초 늦은 수준**에서 동작했다. 이는 약 13 FPS 수준의 Frame 단위 처리에서 자연스럽게 발생할 수 있는 차이다.

---

# 4. Eye Threshold 평가

## 4-1. Trigger 발생시간

Logger에서 실제 `LONG BLINK`, `EYE CLOSED 1s`, `EYE CLOSED 2s` Reason이 발생한 시점의 `eye_closed_duration_s`를 집계했다.

| 단계 | Trigger 기록 수 | 평균 | 최소 | 최대 |
|---|---:|---:|---:|---:|
| CAUTION / Long Blink | 148 | **0.624s** | 0.605s | 0.714s |
| WARNING / Eye Closed 1s | 116 | **1.039s** | 1.001s | 1.361s |
| DROWSY / Eye Closed 2s | 45 | **2.027s** | 2.001s | 2.077s |

### Tester별 평균

| Tester | CAUTION | WARNING | DROWSY |
|---|---:|---:|---:|
| A | 0.629s | 1.026s | 2.041s |
| B | 0.642s | 1.060s | 2.020s |
| C | 0.618s | 1.036s | 2.026s |

세 Tester 사이에서도 Trigger 시간은 큰 차이가 없다.

## 4-2. Session 단위 검출

- EYE_WARNING: **15/15 Session에서 목표 Reason 확인**
- EYE_DROWSY: 전체 15 Session 중 13 Session에서 `EYE CLOSED 2s` Reason 확인
- 다만 A DROWSY Run 2는 실제 최대 눈 감김이 2초에 도달하지 않아 유효 Trial로 보기 어렵다.
- 실제 2초 이상 CLOSED가 기록된 DROWSY Session만 보면 **13/14 = 92.9%**
- A DROWSY Run 4는 2.052초로 임계값 바로 근처에서 종료되어 `EYE CLOSED 2s`가 기록되지 않은 Boundary Case였다.

따라서 Eye Drowsy 결과는 `정확도 92.9%`라고 단정하기보다, **2초 Threshold 근처에서 Frame Sampling에 의한 Boundary Case 1건이 관찰되었다**고 설명하는 것이 더 정확하다.

---

# 5. NORMAL Test — 9 Session

총 Monitoring 시간:

- **654.3초 = 10.91분**
- NORMAL State 유지율: **93.0%**
- 비-NORMAL State 시간: **7.0%**

## Tester별 NORMAL 유지율

| Tester | 총 Monitoring | NORMAL 유지율 | 비-NORMAL 전환 수 |
|---|---:|---:|---:|
| A | 207.6s | **97.4%** | 4 |
| B | 187.2s | **78.9%** | 20 |
| C | 259.6s | **99.6%** | 2 |

전체 평균만 보면 93.0%이지만 Tester별 편차가 매우 크다.

특히 B는 NORMAL 상태에서도 다음 Reason이 반복 발생했다.

- `ATTENTION AWAY`
- `BLINK RATE`
- `LONG BLINK`
- `EYE CLOSED 1s`
- `PERCLOS`

NORMAL Session에서 발생한 비-NORMAL 전환의 주요 Reason 횟수:

| Reason | 횟수 |
|---|---:|
| ATTENTION AWAY | 11 |
| BLINK RATE | 5 |
| LONG BLINK | 5 |
| EYE CLOSED 1s | 3 |
| PERCLOS | 3 |

### 해석

이 결과는 **개인별 Blink/Gaze 특성 차이에 대한 Threshold 개인화가 아직 충분하지 않다**는 것을 보여준다.

따라서 PPT에서는:

> `NORMAL 유지율 93.0%`만 크게 강조하기보다 `A 97.4% / B 78.9% / C 99.6%`를 함께 보여주고, **개인차가 주요 개선과제**라고 설명하는 것이 좋다.

---

# 6. Head / Gaze

## 방향 Coverage

| Tester | Head | Gaze |
|---|---:|---:|
| A | **4/4** | **4/4** |
| B | **4/4** | **1/4** |
| C | **4/4** | **2/4** |

Head는 세 Tester 모두 LEFT / RIGHT / UP / DOWN이 확인되었다.

반면 Gaze는:

- A: LEFT / RIGHT / UP / DOWN 모두 확인
- B: DOWN만 확인
- C: RIGHT / UP 확인

즉 **Gaze는 개인별 눈 구조·홍채 위치·Calibration에 매우 민감**한 것으로 나타났다.

이 값은 각 방향 Trial별 정확도가 아니라, 테스트한 네 방향 중 Logger에서 실제 검출된 방향의 **Coverage**이다.

## Attention Timer

| 상태 | 설계 | 실측 평균 | 범위 |
|---|---:|---:|---:|
| CAUTION | 1.0s | **1.037s** | 1.000~1.082s |
| DISTRACTED | 2.0s | **2.037s** | 2.000~2.080s |

즉 방향 자체가 정상적으로 검출되면 **Attention Timer는 설계값대로 안정적으로 동작**했다.

---

# 7. Face Missing

| 상태 | 설계 | 실측 평균 | 범위 | 기록 수 |
|---|---:|---:|---:|---:|
| SEARCHING | 1.0s | **1.038s** | 1.002~1.064s | 12 |
| NO DRIVER | 2.0s | **2.035s** | 2.007~2.062s | 8 |

Face Missing State 전이는 가장 안정적인 항목 중 하나였다.

---

# 8. PERCLOS

Tester A 전용 PERCLOS Session에서:

```text
설정 20% → 실제 CAUTION 최초 확인 20.11%
설정 30% → 실제 HIGH PERCLOS 최초 확인 30.14%
```

따라서 PERCLOS 20% / 30% Threshold 역시 정상적으로 동작했다.

---

# 9. Yawn

Yawn Count 로직 자체는 확인되었다.

- A: Yawn Count 3~4까지 누적되며 2회 CAUTION / 3회 WARNING 확인
- C: 3회 누적 및 CAUTION/WARNING 확인
- B: 해당 Session에서는 Yawn Count가 1회까지만 기록

B/C 일부 Session에서는 하품 자세 중 눈이 CLOSED로 같이 인식되어:

```text
YAWN + CLOSED EYE → DROWSY
```

가 발생했다.

이는 복합 위험 조건으로서는 설계된 동작이지만, **순수 Yawn 검출만 평가할 때는 Head/Eye 움직임이 간섭할 수 있음**을 보여준다.

---

# 10. Safety State Machine

완료된 Safety Protocol Test만 기준으로 집계하면:

| Scenario | 완료 Trial | PASS |
|---|---:|---:|
| Repeated Drowsy | 3 | **3/3** |
| Recovery Success | 3 | **3/3** |
| Recovery Fail → Rest Required | 3 | **3/3** |
| STOP Mode | 4 | **4/4** |
| Rest Protocol | 3 | **3/3** |
| **합계** | **16** | **16/16** |

`REST_PROTOCOL_03`은 재시작 후 30초 Rest 완료까지 기다리기 전에 Session이 종료되어 **미완료 Trial**로 분류했고 실패로 계산하지 않았다.

### 검증된 흐름

```text
DROWSY Event × 3
→ Recovery Required
→ Recovery 중 New DROWSY
→ Rest Required
→ S : Rest Start
→ D too early : Not Enough Rest
→ S : Rest Restart
→ Rest Complete
→ D : Normal Driving
```

또한 STOP Mode 4개 Trial에서는 STOP 이후:

- 새 DROWSY Event 발생 없음
- Drowsy Count = 0 유지
- DISTRACTED / SEARCHING / NO DRIVER 전환 차단

이 확인되었다.

---

# 11. FPS

A의 전용 FPS Session 기준:

| 항목 | 결과 |
|---|---:|
| Sample 수 | 117 |
| 평균 | **12.88 FPS** |
| 중앙값 | 12.95 FPS |
| 5 percentile | 12.77 FPS |
| 95 percentile | 13.09 FPS |
| 최소 | 7.85 FPS |
| 최대 | 13.83 FPS |

대부분 약 12.8~13.1 FPS에 밀집되어 있다. 최소 7.85 FPS는 일시적인 처리 지연 Sample이다.

---

# 12. PPT 프로젝트 결과 슬라이드 추천

## 슬라이드 제목

**DriverSense V9 Performance Evaluation**

### 상단 작은 설명

```text
Tester A/B/C · 78 CSV · Raspberry Pi Real-time Test
```

---

## 왼쪽 — Response Time Validation

설정값과 실측값을 나란히 보여준다.

| Function | Target | Measured |
|---|---:|---:|
| Eye CAUTION | 0.60s | **0.624s** |
| Eye WARNING | 1.00s | **1.039s** |
| Eye DROWSY | 2.00s | **2.027s** |
| SEARCHING | 1.00s | **1.038s** |
| NO DRIVER | 2.00s | **2.035s** |

메인 메시지:

> **설정 Threshold 대비 약 0.02~0.04초 이내 차이**

---

## 오른쪽 상단 — Safety Logic

크게:

```text
16 / 16 PASS
```

작게:

```text
Repeated Drowsy · Recovery · Rest · STOP
완료된 Safety Protocol Trial 기준
```

---

## 오른쪽 중단 — Real-time

```text
12.88 FPS
```

```text
Raspberry Pi + MediaPipe Face Landmarker
```

---

## 하단 — Generalization / Limitation

### NORMAL State 유지율

```text
A 97.4%   B 78.9%   C 99.6%
Overall 93.0%
```

### Direction Coverage

```text
HEAD : A 4/4 · B 4/4 · C 4/4
GAZE : A 4/4 · B 1/4 · C 2/4
```

강조 문구:

> **Head Detection은 안정적 / Gaze와 Blink는 개인차에 민감 → 개인별 Calibration 고도화 필요**

---

# 13. 발표 멘트 예시 — 약 50초

> “Tester A, B, C의 총 78개 Evaluation CSV를 분석했습니다. 먼저 시간 기반 Threshold는 Eye Caution 0.624초, Warning 1.039초, Drowsy 2.027초로 설정값과 약 0.02에서 0.04초 정도의 차이만 보였습니다. Face Missing 역시 Searching 1.038초, No Driver 2.035초로 목표 시간에 근접했습니다. 반복 졸음, Recovery, Rest, Stop과 관련된 완료된 Safety Protocol 16개 Trial은 모두 정상 동작했고, Raspberry Pi에서는 평균 12.88 FPS로 처리되었습니다. 다만 Normal Test에서는 Tester별 유지율이 A 97.4%, B 78.9%, C 99.6%로 차이가 있었고, 특히 Gaze는 A는 네 방향 모두 검출했지만 B와 C에서는 일부 방향만 검출되어 개인차에 대한 Calibration 개선이 필요하다는 한계도 확인했습니다.”

---

# 14. 최종 해석

이번 데이터로 가장 강하게 주장할 수 있는 부분은 다음이다.

1. **시간 기반 Threshold Logic이 설정값에 근접하게 동작함**
2. **Face Missing State 전환이 안정적임**
3. **Repeated Drowsy / Recovery / Rest / STOP State Machine이 완료 Trial에서 모두 정상 동작함**
4. **약 13 FPS로 Raspberry Pi에서 실시간 구동 가능함**
5. **Head Detection은 Tester간 안정적임**

반대로 한계는 명확하다.

1. Gaze 검출은 Tester별 차이가 큼
2. NORMAL Session에서 B의 False State가 많음
3. Blink Rate / PERCLOS / Gaze Threshold의 개인화가 더 필요함
4. 2초와 같이 임계값에 매우 가까운 행동은 Frame Sampling Boundary의 영향을 받을 수 있음

따라서 프로젝트 결과를 단일 `AI Accuracy XX%`로 표현하는 것보다:

```text
Response Time
+ State Transition Success
+ NORMAL Stability
+ Direction Coverage
+ FPS
```

의 다축 평가로 제시하는 것이 데이터에 가장 충실하고 발표 설득력도 높다.
