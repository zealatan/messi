# FPGA Firmware Verification: A Common Approach for Simulation and Hardware Tests — 논문 정리

## 1. 논문 정보

- **제목**: *FPGA Firmware Verification: a common approach for simulation and hardware tests*
- **저자**: Stefano Pavinato, Emmanuel D’Costa, Stephane Gabourin
- **소속**: European Spallation Source (ESS), Lund, Sweden
- **주제**: FPGA firmware verification에서 **simulation test**와 **real hardware test**를 하나의 Python 기반 framework로 통합하는 방법
- **핵심 도구**:
  - **Cocotb**: RTL simulation verification
  - **Pytest**: 실제 FPGA hardware validation / Factory Acceptance Testing (FAT)
  - **JSON/YAML**: test scenario 및 requirement traceability 표현
  - **JUnit XML**: 통합 test report format

---

## 2. 한 줄 요약

이 논문은 FPGA firmware 검증에서 **Cocotb 기반 simulation test**와 **Pytest 기반 hardware test**를 같은 Python 구조로 작성하고, test scenario, scoreboard, requirement coverage, report를 재사용하는 **통합 verification framework**를 제안한다.

---

## 3. 문제 정의

기존 FPGA 개발 flow는 보통 다음과 같이 나뉜다.

```text
RTL design
→ unit test / integration test / system test in simulation
→ synthesis / implementation
→ FPGA bitstream generation
→ board-level hardware test
→ Factory Acceptance Testing (FAT)
```

문제는 simulation test와 hardware test가 서로 다른 tool, script, methodology로 작성되는 경우가 많다는 것이다.

그 결과:

- simulation에서 만든 testbench를 hardware test에 재사용하기 어렵다.
- 같은 기능을 simulation과 board에서 중복 검증해야 한다.
- test scenario와 requirement coverage를 일관되게 관리하기 어렵다.
- FAT 단계에서 manual script와 proprietary tool에 의존하게 된다.
- test report와 audit trail을 통합하기 어렵다.

논문의 목표는 이 gap을 줄이는 것이다.

---

## 4. 논문의 핵심 접근법

논문은 다음 세 가지 verification 철학을 결합한다.

### 4.1 UVM-style modular verification

UVM의 핵심 개념인 다음 구조를 Python으로 단순화한다.

```text
Test
 └── Environment
      ├── Driver
      ├── Monitor
      └── Scoreboard
```

각 역할은 다음과 같다.

| Component | 역할 |
|---|---|
| Driver | DUT에 stimulus를 인가 |
| Monitor | DUT output 또는 hardware response 관찰 |
| Scoreboard | expected result와 actual result 비교 |
| Environment | driver, monitor, scoreboard를 묶어서 test 실행 |

중요한 점은 **simulation과 hardware test 모두에서 같은 구조를 사용한다는 것**이다.

---

### 4.2 Cocotb + Pytest 통합

논문은 simulation에는 Cocotb, hardware test에는 Pytest를 사용한다.

```text
Simulation environment:
    Cocotb + RTL simulator

Hardware environment:
    Pytest + FPGA board + EPICS/hardware interface
```

두 framework 모두 Python 기반이기 때문에 다음 장점이 있다.

- test structure를 비슷하게 유지 가능
- parameterized test 작성 가능
- 같은 JSON scenario를 읽어서 test 가능
- JUnit XML report 생성 가능
- GitLab CI/CD에 쉽게 통합 가능

---

### 4.3 PSS-like JSON scenario

PSS(Portable Test and Stimulus Standard)의 철학은 하나의 test scenario description을 여러 verification stage에서 재사용하는 것이다.

이 논문은 완전한 PSS DSL을 사용하지 않고, 간단한 JSON format으로 test scenario를 표현한다.

예시 구조는 다음과 같다.

```json
{
  "component": {
    "name": "redundancy_check",
    "test_name": "DDS_21_5_rflps",
    "data": {
      "input": [
        {"name": "slot", "type": "int", "domain": [0, 1, 2, 3]},
        {"name": "port", "type": "int", "domain": [0, 1]},
        {"name": "signal", "type": "string", "domain": ["Beam Permit", "Redundant Beam Permit"]},
        {"name": "signal_value", "type": "string", "domain": ["OK", "NOK"]}
      ]
    },
    "action": {
      "name": "run_check_phase",
      "inputs": ["slot", "port", "signal", "signal_value"],
      "activity": [
        {"do": {"action": "driver"}},
        {"do": {"action": "get_expectation"}},
        {"do": {"action": "monitor"}},
        {"do": {"action": "check_phase"}}
      ]
    }
  }
}
```

이 JSON은 다음 목적으로 사용된다.

- test input domain 정의
- expected output 계산에 필요한 parameter 정의
- simulation test와 hardware test에서 같은 scenario 재사용
- requirement coverage와 연결

---

## 5. Framework 구조

논문에서 제안하는 구조는 다음과 같이 정리할 수 있다.

```text
                Shared Test Scenario
                    JSON / Excel
                         |
        -------------------------------------
        |                                   |
 Simulation Test                      Hardware Test
 Cocotb                               Pytest
        |                                   |
 Driver_sim                           Driver_hw
 Monitor_sim                          Monitor_hw
        |                                   |
        ---------- Shared Scoreboard --------
                         |
                  JUnit XML Report
                         |
          Requirement Traceability Matrix
```

핵심은 **Driver와 Monitor는 환경별로 다르지만, Scoreboard와 test parameter는 최대한 공유한다는 것**이다.

---

## 6. Verification Metrics

논문은 verification completion을 위해 세 가지 metric을 사용한다.

### 6.1 Requirement Traceability Matrix (RTM)

각 test를 다음과 연결한다.

```text
System Requirement Specification (SRS)
→ Detailed Design Specification (DDS)
→ Test case
→ Simulation result
→ Hardware test result
```

검증 완료 조건은 다음과 같다.

```text
모든 requirement가 적어도 하나 이상의 successful simulation test와 hardware test로 cover되어야 한다.
```

---

### 6.2 Scenario Coverage

V&V engineer가 정의한 test scenario가 실제로 모두 실행되었는지 확인한다.

논문에서는 Excel 또는 JSON 형태의 scenario table을 사용하고, 이를 Cocotb/Pytest parameterized test로 변환한다.

---

### 6.3 Code Coverage

HDL simulator에서 code coverage를 수집한다.

coverage가 100%에 도달하지 못하면:

- 추가 scenario가 필요한지 확인
- uncovered code가 실제로 release에 필요한 기능인지 확인
- unused code인지 분석

단, 논문에서는 randomized functional coverage보다는 deterministic scenario coverage를 더 중요하게 본다.

---

## 7. Case Study: RISC-V Input Monitoring

논문의 case study는 ESS Fast Beam Interlock System(FBIS)의 RISC-V input monitoring 기능이다.

### 7.1 배경

FBIS는 여러 sensor system으로부터 redundant input을 받고, 이 input들이 서로 일관적인지 확인해야 한다.

이를 위해 FPGA 내부에 lightweight RISC-V CPU를 넣고, sensor configuration에 따라 input monitoring logic을 수행한다.

### 7.2 검증 대상

논문은 RISC-V CPU 전체의 micro-architectural corner case를 검증하는 것이 아니라, simulation과 hardware 양쪽에서 공유 가능한 **functional correctness test**에 집중한다.

즉 검증 대상은 다음에 가깝다.

```text
주어진 input condition에서
redundancy check logic이
올바른 output을 생성하는가?
```

### 7.3 Test 흐름

공통 test 흐름은 다음과 같다.

```text
1. JSON scenario에서 parameter load
2. Driver가 DUT 또는 hardware에 input stimulus 적용
3. Scoreboard가 expected output 계산
4. Monitor가 actual output 관찰
5. Scoreboard가 actual과 expected 비교
6. JUnit XML report 생성
```

---

## 8. 논문의 주요 기여

이 논문의 contribution은 새로운 hardware algorithm이 아니라, **verification workflow engineering**이다.

주요 기여는 다음과 같다.

### 8.1 Simulation과 hardware test의 구조 통일

Cocotb와 Pytest를 모두 Python 기반으로 사용하여 simulation과 hardware test의 구조를 맞춘다.

---

### 8.2 UVM 개념의 lightweight Python 구현

전통적인 UVM의 복잡한 class hierarchy 대신, Python class로 단순화된 environment/driver/monitor/scoreboard 구조를 만든다.

---

### 8.3 PSS-like scenario reuse

PSS의 “portable test scenario” 개념을 JSON 기반으로 단순화하여 simulation과 hardware test 모두에서 재사용한다.

---

### 8.4 Requirement coverage와 report 통합

JUnit XML report와 RTM을 이용해 test result와 requirement coverage를 일관되게 관리한다.

---

### 8.5 FAT 자동화 효율 향상

실제 ESS FBIS 환경에서 Factory Acceptance Testing(FAT)의 test automation, reviewability, maintainability가 개선되었다고 주장한다.

---

## 9. 한계점

논문은 실무적으로 유용하지만, 연구 논문 관점에서는 몇 가지 한계가 있다.

### 9.1 새로운 알고리즘은 아님

Cocotb, Pytest, JSON, UVM-style 구조를 조합한 engineering framework에 가깝다.

---

### 9.2 Quantitative metric이 약함

논문은 efficiency와 coverage 향상을 주장하지만, 다음과 같은 정량 지표는 충분히 강하지 않다.

- test development time reduction
- debug time reduction
- bug detection rate
- number of reused test components
- before/after FAT execution time
- coverage increase percentage

---

### 9.3 AI/LLM 기반 자동화는 없음

논문은 test scenario를 재사용하지만, 실패 원인 분석이나 다음 test generation은 여전히 사람이 한다.

없는 기능:

- LLM-based failure diagnosis
- automatic debug hypothesis generation
- ILA trigger generation
- synthesis/implementation log analysis
- board measurement log reasoning
- adaptive next-test selection

---

### 9.4 Hardware observability 문제는 여전히 존재

논문도 simulation과 hardware의 timing scale과 observability가 다르기 때문에 Driver/Monitor 구현이 달라질 수밖에 없다고 인정한다.

---

## 10. 네 아이디어와의 연결

이 논문은 네가 생각하는 **Simulation-to-FPGA Feedback-Driven Multi-Agent Verification Framework**의 좋은 baseline이 될 수 있다.

논문의 framework는 다음 단계까지 제공한다.

```text
Shared scenario
→ Cocotb simulation
→ Pytest hardware test
→ unified report
```

네 아이디어는 여기에 다음 loop를 추가할 수 있다.

```text
Simulation failure / hardware failure
→ log collection
→ LLM-based analysis
→ debug hypothesis generation
→ next testbench generation
→ board test script generation
→ ILA trigger proposal
→ rerun simulation or hardware test
```

즉 네 논문의 차별점은 다음과 같이 잡을 수 있다.

```text
기존 연구:
    Simulation과 hardware test 사이의 code/scenario reuse

네 아이디어:
    Simulation, implementation, FPGA board test 결과를 이용한 closed-loop AI verification agent
```

---

## 11. 네 논문/특허 관점의 Contribution 후보

이 논문을 related work로 두고, 네가 주장할 수 있는 contribution은 다음과 같다.

### Contribution 1. Closed-loop simulation-to-hardware verification

기존 framework는 test를 재사용하지만, 실패 결과를 바탕으로 다음 action을 자동 결정하지 않는다.

네 구조는 다음을 자동화한다.

```text
failure observation
→ root-cause hypothesis
→ next verification action
```

---

### Contribution 2. Multi-agent role separation

각 agent가 서로 다른 역할을 맡는다.

```text
Spec Agent          : requirement와 test objective 분석
Simulation Agent    : Cocotb testbench 생성/수정
Synthesis Agent     : synthesis/implementation log 분석
Board Agent         : Pytest/board script 실행 계획 생성
ILA Agent           : trigger condition과 probe 추천
Debug Agent         : failure hypothesis 생성
Report Agent        : RTM과 coverage report 업데이트
```

---

### Contribution 3. Hardware-in-the-loop evidence database

simulation result, timing report, bitstream version, board log, UART output, DMA memory dump, ILA waveform을 하나의 evidence database로 관리한다.

---

### Contribution 4. Adaptive verification planning

고정된 scenario를 실행하는 것이 아니라, 이전 실패 결과에 따라 다음 test를 선택한다.

```text
If simulation passes but hardware fails:
    suspect timing, CDC, reset, AXI protocol, board interface, clocking, or IO issue

If simulation fails:
    suspect RTL logic, testbench assumption, reference model mismatch

If timing fails:
    propose pipeline insertion, constraint review, or critical path localization
```

---

### Contribution 5. FPGA-specific debug automation

일반 software LLM agent와 달리 FPGA verification에 특화된 action을 생성한다.

예:

```text
- ILA probe selection
- AXI transaction test generation
- DMA memory consistency check
- RFSoC register readback test
- reset sequence variation
- clock domain crossing stress test
- timing report interpretation
```

---

## 12. 논문에서 가져올 수 있는 Related Work 문장

아래 문장은 네 논문에 사용할 수 있는 형태다.

```text
Recent work has proposed a unified FPGA firmware verification methodology that combines Cocotb-based simulation with Pytest-based hardware validation. By adopting UVM-like modular components such as drivers, monitors, and scoreboards, and by describing test scenarios using JSON templates, the framework improves code reuse and traceability between simulation and Factory Acceptance Testing. However, the approach still relies on engineers to interpret simulation failures, hardware logs, and board-level measurements, and does not provide an adaptive mechanism for generating the next verification action.
```

---

## 13. 네 논문 제목 후보

### 후보 1

```text
A Simulation-to-FPGA Feedback-Driven Multi-Agent Framework for Automated RTL Verification and Hardware Debugging
```

### 후보 2

```text
Closing the Loop Between RTL Simulation and FPGA Board Testing with LLM-Based Verification Agents
```

### 후보 3

```text
Hardware-in-the-Loop Multi-Agent Verification for FPGA Firmware: From Simulation Failures to Board-Level Debug Actions
```

### 후보 4

```text
An LLM-Orchestrated Verification Framework for RTL Simulation, Timing Analysis, and FPGA Hardware Testing
```

---

## 14. 최종 평가

이 논문은 아이디어 자체가 매우 복잡하거나 강한 algorithmic novelty를 가진 논문은 아니다. 하지만 FPGA verification 분야에서는 실무적인 workflow 개선도 충분히 논문 가치가 있다.

특히 이 논문은 다음 메시지를 준다.

```text
Simulation과 hardware test를 통합하는 것만으로도 DVCon급 논문이 될 수 있다.
```

따라서 네가 여기에 LLM/multi-agent/closed-loop feedback/ILA automation/board-log reasoning을 추가하면, 충분히 더 강한 논문 주제로 발전시킬 수 있다.

---

## 15. 핵심 정리

```text
이 논문 = Cocotb + Pytest + JSON + RTM 기반 unified FPGA verification framework

장점:
- simulation/hardware test 재사용
- UVM-style 구조 단순화
- requirement traceability 강화
- FAT 자동화에 유용

한계:
- AI 없음
- adaptive debug 없음
- quantitative performance 약함
- hardware failure reasoning 없음

네가 확장할 방향:
- LLM multi-agent
- simulation-to-board feedback loop
- ILA/UART/AXI/DMA log reasoning
- next-test automatic generation
- OFDM/DMA/RFSoC case study
```
