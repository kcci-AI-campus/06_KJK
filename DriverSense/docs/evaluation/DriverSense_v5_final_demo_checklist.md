# DriverSense 최종 통합 시연 체크리스트  
## 기준 파일: `combi_final_ui_integrated_v5.py`

> 목적: 최종 UI 통합 버전의 **알고리즘 / 상태 전이 / Recovery / Rest / GPIO / CSV / UI 표시 / 키 입력**을 전체 시연하면서 재검증하기 위한 체크리스트  
> 체크 방법: 각 항목 테스트 후 `☐ → ☑` 변경 또는 비고란에 이상 현상 기록

---

## 0. 현재 시연용 주요 설정

| 항목 | 현재 설정 |
|---|---:|
| Calibration | `5.0 s` |
| 일반 DROWSY State | `2.0 s` |
| DROWSY Event Count 기준 | `1.5 s` |
| Recovery 중 DROWSY Event 기준 | `1.5 s` |
| DROWSY Event Re-arm | `0.7 s` |
| DROWSY Count Window | `60.0 s` |
| Repeated Drowsiness 진입 | `3회` |
| Recovery 총 시간 | `30.0 s` |
| Recovery 중 WARNING 전환 | `15.0 s` |
| Mandatory Rest | `30.0 s` |

---

# 1. 프로그램 실행 / 초기 UI

| No. | 체크 항목 | 테스트 방법 | 정상 동작 기준 | 결과 / 비고 |
|---:|---|---|---|---|
| 1 | 프로그램 실행 | 프로그램 실행 | 오류 없이 DriverSense UI 실행 | ☑ |
| 2 | Webcam 연결 | 시작 화면 확인 | LIVE CAMERA 영역에 영상 정상 출력 | ☑ |
| 3 | UI 전체 배치 | 전체 화면 확인 | Header / Live Camera / Driver Status / Current Status / Switch·ACK / Event Log 표시 | ☑ |
| 4 | Header 시간 | 상단 우측 확인 | 현재 날짜·시간이 실시간 갱신 | ☑ |
| 5 | FPS 표시 | 카메라 좌하단 확인 | FPS 값 정상 표시 | ☑ |
| 6 | Key Buttons | 오른쪽 하단 확인 | `SPACE / R / C / D / S / Q` 목록 정상 표시 | ☑ |
| 7 | UI 잘림 여부 | 전체 창 확인 | 글자·패널·키 가
이드가 창 밖으로 잘리지 않음 | ☑ |

---

# 2. Calibration

| No. | 체크 항목 | 테스트 방법 | 정상 동작 기준 | 결과 / 비고 |
|---:|---|---|---|---|
| 8 | 초기 대기 | 실행 후 아무 키도 누르지 않음 | Calibration 자동 시작되지 않음 | ☑ |
| 9 | Space 시작 | `SPACE` 입력 | Calibration 시작 | ☑ |
| 10 | Calibration 안내 | Calibration 화면 확인 | 정면 응시 / 눈 뜨기 안내 정상 표시 | ☑ |
| 11 | Calibration 시간 | 정면 유지 | 약 `5.0초` 진행 | ☑ |
| 12 | Calibration 완료 | 완료 후 확인 | 정상 감시 화면으로 진입 | ☑ |
| 13 | 재Calibration | 일반 상태에서 `C` | 즉시 Calibration 재시작 | ☑ |
| 14 | Calibration 중 종료 | `Q` 입력 | 정상 종료 | ☑ |

---

# 3. NORMAL / Driver Status UI

| No. | 체크 항목 | 테스트 방법 | 정상 동작 기준 | 결과 / 비고 |
|---:|---|---|---|---|
| 15 | NORMAL 상태 | 정면 + 눈 OPEN | `NORMAL DRIVING`, Green LED, BUZZ OFF | ☑ |
| 16 | Eye State | 눈 뜨기/감기 | `OPEN / CLOSED` 정상 표시 | ☑ |
| 17 | Drowsy Count | 졸음 이벤트 발생 | 최근 60초 졸음 이벤트 수 정상 표시 | ☑ |
| 18 | Head Pose | 좌/우/상/하 움직임 | `LEFT / RIGHT / UP / DOWN / CENTER` 정상 표시 | ☑ |
| 19 | Gaze | 눈동자 좌/우/상/하 이동 | Gaze 상태 정상 표시 | ☑ |
| 20 | 카드 정렬 | Driver Status 확인 | Label / Value가 일정한 왼쪽 기준으로 정렬 | ☑ |
| 21 | 하품 UI 제거 | Driver Status 확인 | `Yawning Count`는 표시되지 않음 | ☑ |
| 22 | 내부 하품 기능 유지 | 실제 하품 | UI에 Count는 없어도 내부 Yawn 알고리즘 정상 작동 | ☑ |

---

# 4. Blink / Eye Closure / DROWSY Event

| No. | 체크 항목 | 테스트 방법 | 정상 동작 기준 | 결과 / 비고 |
|---:|---|---|---|---|
| 23 | 일반 Blink | 빠르게 눈 깜빡임 | DROWSY Event 증가 없음 | ☑ |
| 24 | Long Blink | 약 0.6~1.0초 눈 감음 | CAUTION 계열 반응, Event Count 오증가 없음 | ☑ |
| 25 | DROWSY Event | 약 `1.5초` 이상 눈 감음 | Drowsy Count +1 | ☑ |
| 26 | 실제 DROWSY State | 약 `2.0초` 이상 눈 감음 | `DROWSINESS DETECTED`, Red LED, BUZZ ON | ☑ |
| 27 | Event 중복 방지 | 눈 계속 감은 채 유지 | 같은 Episode가 여러 번 Count되지 않음 | ☑ |
| 28 | Event Re-arm | 눈 뜨고 Head CENTER 유지 | 약 `0.7초` 후 다음 Event 수신 가능 | ☑ |
| 29 | CSV 기록 | DROWSY Event 발생 | `drowsy_events.csv`에 Timestamp 저장 | ☑ |
| 30 | Event Log UI | DROWSY 발생 | 최근 Event가 하단 로그에 표시 | ☑ |
| 31 | 최근 3개 표시 | DROWSY 4회 이상 발생 | UI에는 최신 3개만 표시 | ☑ |

---

# 5. ACK 동작

| No. | 체크 항목 | 테스트 방법 | 정상 동작 기준 | 결과 / 비고 |
|---:|---|---|---|---|
| 32 | 1회 DROWSY ACK | 첫 DROWSY 후 `R` | BUZZ OFF → NORMAL 복귀 | ☑ |
| 33 | 물리 ACK | GPIO23 버튼 사용 | 키보드 `R`과 동일하게 동작 | ☑ |
| 34 | 2회 DROWSY | 두 번째 독립 DROWSY 발생 | Drowsy Count = 2 | ☑ |
| 35 | 2회 ACK | 두 번째 DROWSY에서 ACK | WARNING 약 3초 유지 후 정상 평가 복귀 | ☑ |
| 36 | ACK 중복 입력 | 여러 번 `R` | 비정상 State 전이/오류 없음 | ☑ |

---

# 6. Repeated Drowsiness 핵심 검증

> **이번 버전에서 가장 중요한 구간**

| No. | 체크 항목 | 테스트 방법 | 정상 동작 기준 | 결과 / 비고 |
|---:|---|---|---|---|
| 37 | 3번째 DROWSY | 독립 DROWSY 3회 발생 | Drowsy Count = 3 | ☑ |
| 38 | Repeated 진입 | 3번째 Event 직후 | `RECOVERY REQUIRED` 화면 진입 | ☑ |
| 39 | 즉시 Rest 방지 | 3번째 Event 직후 확인 | **`TAKE A REST`가 바로 뜨지 않음** | ☑ |
| 40 | 중복 4번째 방지 | 3번째 눈감김을 계속 유지 | 동일 Episode가 4번째 Event로 재Count되지 않음 | ☑ |
| 41 | Recovery 시작 | 눈 뜨고 Head CENTER | Recovery Timer 시작 | ☑ |
| 42 | Recovery UI 정렬 | Recovery 화면 확인 | 모든 텍스트가 왼쪽 기준으로 정렬 | ☑ |
| 43 | Recovery 안내 | 화면 확인 | `RECOVERY REQUIRED`, 남은 시간, HEAD, GAZE 안내 정상 표시 | ☑ |

---

# 7. Recovery 정상 복귀 경로

| No. | 체크 항목 | 테스트 방법 | 정상 동작 기준 | 결과 / 비고 |
|---:|---|---|---|---|
| 44 | Head CENTER 유지 | Recovery 동안 정면 유지 | Recovery Timer 계속 진행 | ☑ |
| 45 | 일반 Blink | Recovery 중 짧게 깜빡임 | Recovery Timer 불필요하게 초기화되지 않음 | ☑ |
| 46 | Gaze 이동 | Head CENTER 유지 + 시선 이동 | Gaze 때문에 Recovery Timer 초기화되지 않음 | ☑ |
| 47 | Head 이탈 | Head LEFT/RIGHT/UP/DOWN | Recovery 진행 중단 또는 초기화 | ☑ |
| 48 | Head 복귀 | 다시 CENTER | Recovery Timer 다시 시작 | ☑ |
| 49 | Recovery 초반 | 0~15초 | State = DROWSY / Red LED | ☑ |
| 50 | WARNING 전환 | 약 `15.0초` 경과 | DROWSY → WARNING / Yellow LED | ☑ |
| 51 | Recovery 완료 | 총 `30.0초` 유지 | WARNING → NORMAL / Green LED | ☑ |
| 52 | Count Reset | Recovery 완료 직후 | Drowsy Count 초기화 | ☑ |
| 53 | 새 Session | 복귀 후 다시 졸음 | 다시 첫 Event부터 Count | ☑ |

---

# 8. Recovery 중 추가 DROWSY → 강제 휴식

| No. | 체크 항목 | 테스트 방법 | 정상 동작 기준 | 결과 / 비고 |
|---:|---|---|---|---|
| 54 | Recovery 재진입 | 다시 DROWSY 3회 | `RECOVERY REQUIRED` 정상 진입 | ☑ |
| 55 | 새 DROWSY Event | Recovery 중 약 `1.5초` 이상 눈 감음 | 새로운 Event 1회 추가 | ☐ |
| 56 | Rest Required | 위 Event 발생 직후 | `TAKE A REST / STOP THE DRIVING` 표시 | ☑ |
| 57 | Event 중복 방지 | 계속 눈 감기 | 동일 Episode가 추가 Count되지 않음 | ☑ |
| 58 | ACK | Rest Required 중 `R` | 부저는 OFF 가능하나 Rest Required는 해제되지 않음 | ☑ |
| 59 | Reset 차단 | Rest Required 중 `C` | Calibration Reset으로 우회되지 않음 | ☑ |

---

# 9. STOP / Mandatory Rest

| No. | 체크 항목 | 테스트 방법 | 정상 동작 기준 | 결과 / 비고 |
|---:|---|---|---|---|
| 60 | STOP 진입 | Rest Required에서 `S` | STOP Mode + Rest Timer 시작 | ☑ |
| 61 | Mode 표시 | Switch / ACK 패널 확인 | `MODE: STOP` | ☑ |
| 62 | Rest 화면 | STOP 직후 확인 | `TAKE A REST` + 남은 Rest Time 표시 | ☑ |
| 63 | Rest Countdown | 대기 | `30.0초` 기준 감소 | ☑ |
| 64 | Rest 중 Buzzer | Rest 진행 | BUZZ OFF | ☑ |
| 65 | Rest 중 LED | Rest 진행 | 기존 설계에 맞게 상태 표시 정상 | ☑ |
| 66 | Rest 완료 | Timer 0 | `REST COMPLETE` 표시 | ☑ |
| 67 | 완료 안내 | Rest 완료 화면 | `Press D to resume driving` 표시 | ☑ |

---

# 10. 휴식 부족 / DRIVE 복귀

| No. | 체크 항목 | 테스트 방법 | 정상 동작 기준 | 결과 / 비고 |
|---:|---|---|---|---|
| 68 | 조기 DRIVE | Rest 완료 전 `D` | `NOT ENOUGH REST` + WARNING | ☑ |
| 69 | 조기 DRIVE Mode | 화면 확인 | `MODE: DRIVE`, 그러나 정상 Session으로 완전 복귀하지 않음 | ☑ |
| 70 | 다시 STOP | `S` | STOP Mode 재진입 | ☑ |
| 71 | Rest 재시작 | 다시 STOP 후 | Rest Timer 다시 시작 | ☑ |
| 72 | 정상 DRIVE 복귀 | Rest 완료 후 `D` | DRIVE + NORMAL + Green LED | ☑ |
| 73 | 전체 Count 초기화 | 정상 DRIVE 복귀 직후 | Drowsy/Long Close/Yawn/Nod/PERCLOS 관련 누적값 초기화 | ☑ |

---

# 11. Attention / Head / Gaze / Nod / Yawn / PERCLOS

| No. | 체크 항목 | 테스트 방법 | 정상 동작 기준 | 결과 / 비고 |
|---:|---|---|---|---|
| 74 | Head 이탈 | DRIVE에서 고개 좌/우 | CAUTION → DISTRACTED 정상 전이 | ☑ |
| 75 | Gaze 이탈 | DRIVE에서 시선만 장시간 이탈 | Attention Away 정상 동작 | ☑ |
| 76 | STOP 중 Attention | STOP에서 Head/Gaze 이탈 | DRIVE 전용 경고가 불필요하게 발생하지 않음 | non pass |
| 77 | Head Down | 고개 숙임 | CAUTION → WARNING 정상 동작 | ☑ |
| 78 | Down + Closed | 고개 숙인 채 눈 감음 | DROWSY 복합 조건 정상 검출 | ☑ |
| 79 | Yawn | 하품 | 내부 Yawn Event 정상 인식 | 확인불가 |
| 80 | Repeated Yawn | 여러 차례 하품 | 기존 CAUTION/WARNING 정상 동작 | 확인불가 |
| 81 | Nod | DOWN→CENTER 반복 | Nod 관련 CAUTION/DROWSY 정상 동작 | ☑ |
| 82 | PERCLOS | 장시간 눈 감김 비율 증가 | PERCLOS CAUTION/WARNING 정상 동작 | 확인불가 |

---

# 12. Face Missing

| No. | 체크 항목 | 테스트 방법 | 정상 동작 기준 | 결과 / 비고 |
|---:|---|---|---|---|
| 83 | 순간 얼굴 이탈 | 약 1초 미만 | 과도한 경고 없음 | ☑ |
| 84 | SEARCHING | 얼굴 약 1~2초 미검출 | SEARCHING | ☑ |
| 85 | NO DRIVER | 얼굴 2초 이상 미검출 | NO DRIVER + Red / 경고 | ☑ |
| 86 | 얼굴 복귀 | 다시 카메라 안으로 이동 | 정상 감시 재개 | ☑ |

---

# 13. GPIO / Virtual Hardware

| No. | 체크 항목 | 테스트 방법 | 정상 동작 기준 | 결과 / 비고 |
|---:|---|---|---|---|
| 87 | NORMAL LED | NORMAL | Green ON | ☑ |
| 88 | WARNING LED | WARNING | Yellow ON | ☑ |
| 89 | DROWSY LED | DROWSY | Red ON | ☑ |
| 90 | DROWSY Buzzer | DROWSY | Continuous Buzzer ON | 확인불가 |
| 91 | ACK Buzzer | DROWSY에서 ACK | 즉시 Buzzer OFF | ☑ |
| 92 | UI LED 연동 | 각 상태 확인 | Switch / ACK 패널 R/Y/G 표시와 실제 상태 일치 | ☑ |
| 93 | BUZZ UI 연동 | Buzzer ON/OFF | UI의 `BUZZ: ON/OFF`와 실제 출력 일치 | ☑ |

---

# 14. Key Button 전체 확인

| Key | 기능 | 정상 동작 기준 | 결과 / 비고 |
|---|---|---|---|
| `SPACE` | 최초 Calibration 시작 | READY에서 정상 시작 | ☑ |
| `R` | ACK | 경고 확인 / Buzzer 제어 | ☑ |
| `C` | Reset / Recalibration | 허용 상태에서 재Calibration | ☑ |
| `D` | DRIVE Mode | DRIVE 전환 | ☑ |
| `S` | STOP Mode | STOP 전환 / 필요 시 Rest 시작 | ☑ |
| `Q` | Quit | 프로그램 정상 종료 | ☑ |

---

# 15. UI 최종 품질 체크

| No. | 체크 항목 | 정상 기준 | 결과 / 비고 |
|---:|---|---|---|
| 94 | Driver Status 정렬 | 모든 항목 정렬 통일 | ☑ |
| 95 | Recovery 정렬 | 모든 문구 왼쪽 정렬 | ☑ |
| 96 | Rest 화면 정렬 | 특수 상태 UI 배치 통일 | ☑ |
| 97 | Drowsy Count | Yawn 대신 졸음 횟수 표시 | ☑ |
| 98 | Event Log | 최신 3개 가독성 확보 | ☑ |
| 99 | Key Buttons | 오른쪽 하단에 6개 키 정상 표시 | ☑ |
| 100 | 글자 겹침 | 어떤 State에서도 텍스트 겹침 없음 | ☑ |
| 101 | 화면 갱신 | 상태 전환 시 이전 문구 잔상 없음 | ☑ |
| 102 | 창 Resize | 창 크기 변경 후 심각한 UI 깨짐 없음 | ☑ |

---

# 16. 최종 시연 시나리오

전체 기능을 빠르게 한 번에 검증할 때는 아래 순서대로 진행한다.

```text
프로그램 실행
    ↓
SPACE
    ↓
Calibration
    ↓
NORMAL
    ↓
DROWSY #1 → ACK → NORMAL
    ↓
DROWSY #2 → ACK → WARNING → NORMAL
    ↓
DROWSY #3
    ↓
RECOVERY REQUIRED
    ↓
Head CENTER 유지
    ↓
DROWSY → WARNING → NORMAL
```

두 번째 시나리오:

```text
DROWSY #1
    ↓
DROWSY #2
    ↓
DROWSY #3
    ↓
RECOVERY REQUIRED
    ↓
Recovery 중 NEW DROWSY
    ↓
TAKE A REST / STOP THE DRIVING
    ↓
S
    ↓
STOP + REST TIMER
    ↓
[Case A] 완료 전 D
    → NOT ENOUGH REST
    → S
    → Rest 다시 진행

[Case B] Rest 완료
    → D
    → NORMAL / DRIVE
    → Count Reset
```

---

# 17. 이번 버전에서 가장 중요한 필수 PASS 항목

최종 시연 전에 아래 항목은 반드시 모두 통과하는 것을 권장한다.

- [o ] **3번째 DROWSY 직후 `RECOVERY REQUIRED`가 표시된다.**
- [o ] **3번째 DROWSY 자체가 즉시 4번째 Event로 재Count되지 않는다.**
- [o ] **Recovery 중 Head CENTER이면 Timer가 정상 진행된다.**
- [ o] **일반 Blink / Gaze 변화만으로 Recovery Timer가 초기화되지 않는다.**
- [o ] **Recovery 중 새로운 DROWSY가 발생해야만 `TAKE A REST`로 전환된다.**
- [o ] **Rest 완료 전 DRIVE 복귀 시 `NOT ENOUGH REST`가 표시된다.**
- [o ] **Rest 완료 후 DRIVE 복귀 시 Count가 초기화된다.**
- [o ] **UI의 `Drowsy Count`가 실제 Event Count와 일치한다.**
- [o ] **CSV와 화면 Event Log 기록이 정상이다.**
- [o ] **물리 ACK 버튼과 키보드 R이 동일하게 동작한다.**
- [o ] **R/Y/G LED와 UI 표시가 실제 State와 일치한다.**
- [o ] **오른쪽 하단 Key Buttons가 정상 표시된다.**

---

## 테스트 결과 요약

| 구분 | PASS | FAIL | 비고 |
|---|---:|---:|---|
| 초기 실행 / Calibration |  |  |  |
| 기본 Detection |  |  |  |
| ACK |  |  |  |
| Repeated Drowsiness |  |  |  |
| Recovery |  |  |  |
| Mandatory Rest |  |  |  |
| Attention / Head / Gaze |  |  |  |
| GPIO / Buzzer |  |  |  |
| CSV / Event Log |  |  |  |
| UI / Key Buttons |  |  |  |

### 최종 판정

- [ ] 전체 기능 PASS
- [ ] 일부 수정 필요
- [ ] 재시험 필요
