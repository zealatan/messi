# AutoBench 논문 분석 및 확장 아이디어 정리

## 1. 논문 개요

업로드한 논문은 **AutoBench: Automatic Testbench Generation and Evaluation Using LLMs for HDL Design**이다.

이 논문의 핵심은 다음과 같다.

> LLM을 이용해 Verilog testbench를 자동 생성하고, 생성된 testbench의 품질을 자동 평가하는 프레임워크를 제안한다.

기존 LLM 기반 RTL/HDL 연구가 주로 **RTL 코드 생성**에 집중했다면, AutoBench는 **testbench 생성과 평가**에 초점을 둔다.

논문에서 제안하는 전체 구조는 크게 두 가지다.

```text
1. AutoBench
   - DUT description과 module header만으로 testbench 자동 생성

2. AutoEval
   - 생성된 testbench의 syntax, correctness, coverage를 자동 평가
```

---

## 2. AutoBench의 핵심 아이디어

AutoBench는 DUT의 RTL code를 직접 보지 않고, 다음 두 가지 정보만 입력으로 사용한다.

```text
1. RTL description
2. Module header
```

DUT 코드를 직접 보지 않는 이유는, DUT 코드에 오류가 있을 경우 LLM이 그 오류에 영향을 받아 잘못된 testbench를 만들 수 있기 때문이다.

AutoBench의 기본 흐름은 다음과 같다.

```text
DUT description + module header
        ↓
Circuit type discrimination
        ↓
Testbench specification generation
        ↓
Scenario list generation
        ↓
Verilog driver generation
        ↓
Python checker generation
        ↓
Hybrid testbench execution
        ↓
Self-enhancement / auto-debug / reboot
```

---

## 3. Hybrid Testbench Architecture

AutoBench의 가장 중요한 구조적 특징은 **hybrid testbench**이다.

즉, testbench를 전부 Verilog로 작성하지 않고 다음처럼 나눈다.

```text
Verilog Driver
    - DUT에 stimulus 입력
    - DUT output을 파일로 export

Python Checker
    - export된 output 파일을 읽음
    - expected output 계산
    - actual output과 비교
```

구조적으로는 다음과 같다.

```text
              ┌──────────────┐
              │ Verilog DUT  │
              └──────┬───────┘
                     │
        stimulus     │ output
                     ↓
              ┌──────────────┐
              │ Verilog TB   │
              │ Driver       │
              └──────┬───────┘
                     │ TBout.txt
                     ↓
              ┌──────────────┐
              │ Python       │
              │ Checker      │
              └──────────────┘
```

이 구조의 장점은 다음과 같다.

```text
1. Python checker는 Verilog보다 LLM이 더 잘 생성할 가능성이 높다.
2. Python은 abstraction level이 높아서 reference model 작성에 유리하다.
3. Verilog DUT를 Verilog reference로 검증할 때 생길 수 있는 동일 오류 반복 가능성을 줄인다.
4. 사람이 checker를 수정하기 쉽다.
```

---

## 4. AutoBench Generation Pipeline

AutoBench는 testbench 생성을 여러 단계로 나눈다.

### Stage 0: Circuit Type Discriminator

LLM이 먼저 간단한 RTL code sample을 생성하고, 그 코드의 구조를 분석하여 DUT가 다음 중 어떤 타입인지 구분한다.

```text
1. Combinational circuit
2. Sequential circuit
```

Sequential circuit의 경우 clock, reset, time dependency가 중요하므로, testbench 생성 방식이 combinational circuit보다 훨씬 복잡하다.

---

### Stage 1: Testbench Specification Generation

LLM은 DUT description과 module header를 바탕으로 testbench specification을 생성한다.

예를 들면 다음과 같은 정보를 정리한다.

```text
- DUT input/output port
- bit-width
- expected behavior
- important corner cases
- testing strategy
```

---

### Stage 2: Scenario List Generation

LLM은 testbench가 커버해야 할 scenario list를 생성한다.

예를 들면 combinational circuit의 경우 다음과 같은 scenario가 가능하다.

```text
scenario 1: all zero input
scenario 2: all one input
scenario 3: alternating bit pattern
scenario 4: random input pattern
scenario 5: boundary condition
```

이 단계의 목적은 LLM이 testbench를 직접 만들 때 발생하는 **laziness**를 줄이는 것이다.

즉, 바로 Verilog testbench를 만들게 하면 몇 개의 간단한 case만 만들고 끝낼 수 있기 때문에, 먼저 scenario를 명시적으로 만들게 한다.

---

### Stage 3: Python Core Rule Generation

LLM은 DUT의 expected behavior를 Python function 형태로 작성한다.

예를 들어 100-input AND/OR/XOR 회로라면 다음과 같은 checker rule을 만든다.

```python
def calculate_out_and(input_vector):
    return all(input_vector)

def calculate_out_or(input_vector):
    return any(input_vector)

def calculate_out_xor(input_vector):
    return sum(input_vector) % 2 == 1
```

---

### Stage 4: Verilog Driver Generation

LLM은 scenario list를 기반으로 Verilog driver를 생성한다.

Driver의 역할은 다음과 같다.

```text
1. DUT에 input stimulus를 넣는다.
2. DUT output을 일정 시간 후 읽는다.
3. input/output signal을 TBout.txt로 저장한다.
```

예시 구조는 다음과 같다.

```verilog
initial begin
    file = $fopen("TBout.txt", "w");

    // Scenario 1
    in = 100'b0;
    #10;
    $fdisplay(file, "scenario: %d, in = %d, out_and = %d, out_or = %d, out_xor = %d",
              1, in, out_and, out_or, out_xor);

    // Scenario 2
    in = ~100'b0;
    #10;
    $fdisplay(file, "scenario: %d, in = %d, out_and = %d, out_or = %d, out_xor = %d",
              2, in, out_and, out_or, out_xor);

    $fclose(file);
end
```

---

### Stage 5: Complete Python Checker Generation

마지막으로 LLM은 TBout.txt를 읽고, 각 scenario에 대해 expected output과 actual output을 비교하는 Python checker를 만든다.

개념적으로는 다음과 같다.

```python
def check_dut(test_vectors):
    failed_scenarios = []

    for scenario in test_vectors:
        expected = reference_model(scenario["input"])
        actual = scenario["output"]

        if expected != actual:
            failed_scenarios.append(scenario["scenario_id"])

    return failed_scenarios
```

---

## 5. Self-Enhancement 구조

AutoBench는 LLM이 한 번 생성한 testbench를 그대로 쓰지 않는다.

다음과 같은 self-enhancement 단계를 추가한다.

```text
1. Code completion
2. Code standardization
3. Scenario checking
4. Auto-debugging
5. Rebooting
```

---

### 5.1 Code Completion and Standardization

Python checker에는 고정된 signal interface function을 붙여서 TBout.txt를 읽을 수 있게 한다.

Sequential circuit의 경우 Verilog driver가 복잡하므로, 다음과 같은 standardization이 필요하다.

```text
- long delay를 여러 개의 #10 delay로 분할
- 필요한 시점마다 $fdisplay 삽입
- clock cycle별 input/output export 보장
```

---

### 5.2 Scenario Checking

LLM이 scenario list를 만들었더라도, Verilog driver 생성 과정에서 일부 scenario를 빼먹을 수 있다.

이를 방지하기 위해 Python script가 다음을 검사한다.

```text
- Stage 2에서 만든 scenario들이
- Stage 4의 Verilog driver에 모두 포함되어 있는가?
```

누락된 scenario가 있으면 LLM에게 다시 driver를 보완하게 한다.

---

### 5.3 Auto-Debugging and Rebooting

생성된 Verilog driver와 Python checker는 각각 simulator와 Python interpreter로 실행된다.

문제가 발생하면 다음처럼 처리한다.

```text
1. Syntax error 발생
2. Error message와 line marker를 LLM에게 전달
3. LLM이 코드 수정
4. 일정 횟수 실패하면 해당 stage부터 regenerate
```

즉, 단순히 한 번 생성하고 끝나는 구조가 아니라, debug loop를 포함한다.

---

## 6. AutoEval: Testbench 평가 프레임워크

이 논문의 또 다른 핵심은 AutoEval이다.

AutoEval은 생성된 testbench의 품질을 세 단계로 평가한다.

```text
Eval0: Syntax correctness
Eval1: Golden RTL에 대한 preliminary correctness
Eval2: Mutant RTL 기반 coverage-oriented correctness
```

---

### Eval0

Eval0는 testbench가 syntax error 없이 compile/run 되는지를 확인한다.

```text
Eval0 pass = testbench code has no syntax error
```

---

### Eval1

Eval1은 golden RTL을 DUT로 넣었을 때 testbench가 pass를 출력하는지 확인한다.

```text
Eval1 pass = golden RTL에 대해 testbench가 pass 출력
```

하지만 Eval1만으로는 충분하지 않다.

왜냐하면 아무것도 검사하지 않고 항상 pass를 출력하는 testbench도 Eval1을 통과할 수 있기 때문이다.

---

### Eval2

Eval2는 이 논문에서 가장 중요한 평가 기준이다.

핵심 아이디어는 **mutant coverage**이다.

```text
1. Golden RTL을 준비한다.
2. LLM이 golden RTL을 조금씩 수정하여 mutant RTL들을 만든다.
3. Generated TB와 Golden TB를 각각 mutant RTL에 대해 실행한다.
4. 두 testbench의 pass/fail 결과가 일치하는지 비교한다.
5. 일치율이 threshold 이상이면 Eval2 pass로 판단한다.
```

구조는 다음과 같다.

```text
Golden RTL
    ↓
LLM-generated Mutant RTLs
    ↓
Generated TB 실행
Golden TB 실행
    ↓
pass/fail 결과 비교
    ↓
Eval2 ratio 계산
```

논문에서는 Eval2 threshold를 80%로 설정했다.

---

## 7. 실험 결과 요약

논문은 VerilogEval-Human / HDLBits 기반 156개 task를 사용했다.

중요한 결과는 다음과 같다.

| Group | Metric | AutoBench Pass@1 | Baseline Pass@1 |
|---|---:|---:|---:|
| Total | Eval2 | 44.81% | 28.46% |
| Total | Eval1 | 51.47% | 41.73% |
| Total | Eval0 | 95.71% | 70.06% |
| CMB | Eval2 | 62.22% | 47.65% |
| SEQ | Eval2 | 26.00% | 7.73% |
| SEQ | Eval0 | 97.33% | 55.47% |

핵심 해석은 다음과 같다.

```text
1. AutoBench는 baseline 대비 Total Eval2 pass@1에서 57% 개선.
2. Sequential circuit에서는 Eval2 pass@1이 baseline 대비 3.36배 향상.
3. Sequential circuit의 Eval0 pass@1은 97.33%로, baseline 55.47% 대비 매우 크게 개선.
```

즉, AutoBench의 장점은 특히 **sequential circuit testbench generation**에서 두드러진다.

---

## 8. AutoBench의 한계

AutoBench는 매우 좋은 출발점이지만, 한계도 명확하다.

가장 중요한 한계는 다음과 같다.

```text
AutoBench는 simulation-based verification에 머문다.
```

즉, AutoBench의 loop는 다음과 같다.

```text
LLM
 → testbench generation
 → simulator
 → syntax / golden RTL / mutant RTL evaluation
```

하지만 실제 FPGA 개발에서는 simulation을 통과해도 다음 단계에서 문제가 발생할 수 있다.

```text
- synthesis warning
- timing violation
- implementation failure
- AXI protocol issue
- reset sequencing issue
- CDC issue
- DMA buffer alignment issue
- FPGA board programming issue
- ILA trigger issue
- UART/AXI/DMA log mismatch
- clocking / PLL / RFDC setup issue
```

따라서 AutoBench는 실제 FPGA bring-up과 hardware-in-the-loop debug까지는 다루지 않는다.

---

## 9. 내 아이디어와의 연결

내가 생각하는 아이디어는 AutoBench를 simulation 밖으로 확장하는 것이다.

기존 AutoBench는 다음 문제를 다룬다.

```text
Can LLM generate a good simulation testbench?
```

내가 확장할 수 있는 문제는 다음과 같다.

```text
Can an LLM-based multi-agent system close the loop between simulation and real FPGA behavior?
```

즉, 목표는 다음과 같은 구조다.

```text
RTL description
    ↓
LLM-generated testbench
    ↓
RTL simulation
    ↓
synthesis / implementation
    ↓
bitstream generation
    ↓
FPGA board programming
    ↓
board-level test
    ↓
ILA / UART / AXI / DMA / measurement logs
    ↓
LLM-based failure analysis
    ↓
next verification action generation
```

이 구조는 AutoBench보다 한 단계 더 나아간다.

---

## 10. 제안 논문 주제 1: AutoBench-HIL

### 제목 후보

> AutoBench-HIL: Hardware-in-the-Loop Testbench Generation and Debugging Using Multi-Agent LLMs

### 핵심 아이디어

AutoBench를 hardware-in-the-loop 환경으로 확장한다.

```text
Simulation result만 보는 것이 아니라,
실제 FPGA board test result까지 feedback으로 사용하는 LLM verification framework
```

### 주요 기여

```text
1. LLM 기반 simulation testbench 생성
2. FPGA board test script 자동 생성
3. ILA trigger/probe configuration 자동 추천
4. AXI/UART/DMA log 자동 분석
5. Simulation-pass but FPGA-fail case에 대한 debug hypothesis 생성
6. 다음 testbench 또는 board-level test action 자동 생성
```

### 시스템 구조

```text
Spec Agent
    ↓
TB Generation Agent
    ↓
Simulation Agent
    ↓
Synthesis / Implementation Agent
    ↓
Board Test Agent
    ↓
ILA / Log Analysis Agent
    ↓
Debug Manager Agent
    ↓
Next Action Generator
```

### 실험 대상

```text
1. AXI-Lite register IP
2. AXI DMA IP
3. AXI-Stream FIFO IP
4. OFDM synchronization IP
5. Correlator IP
6. CORDIC-based phase estimator
```

### 평가 지표

```text
1. Simulation pass rate
2. FPGA board test pass rate
3. Bug localization accuracy
4. Number of human interventions
5. Time-to-root-cause
6. Generated next-action usefulness
7. Coverage improvement
```

---

## 11. 제안 논문 주제 2: Sim-to-FPGA Mismatch Benchmark

### 제목 후보

> A Benchmark for Simulation-to-FPGA Mismatch Debugging in LLM-Assisted Hardware Verification

### 핵심 아이디어

AutoBench에는 HDLBits 기반 simulation benchmark가 있다.

하지만 실제 FPGA 개발에서 중요한 문제는 다음이다.

```text
Simulation에서는 pass하지만 FPGA에서는 fail하는 경우
```

따라서 이런 mismatch case를 benchmark로 만들 수 있다.

### Benchmark 예시

```text
1. AXI handshake timing issue
2. Reset sequencing issue
3. Clock domain crossing issue
4. DMA buffer alignment issue
5. FIFO underflow / overflow issue
6. ILA trigger misconfiguration
7. Timing closure failure
8. Clock/PLL setup mismatch
9. Register map mismatch
10. Board script configuration error
```

### 주요 기여

```text
1. Simulation-pass / FPGA-fail benchmark 정의
2. Failure taxonomy 제안
3. LLM agent의 failure classification 성능 평가
4. Next debug action recommendation 평가
5. Human engineer 대비 debug step 감소량 측정
```

### 평가 방식

```text
Input:
    simulation log
    synthesis report
    timing report
    board test log
    ILA capture
    AXI transaction log

Output:
    failure category
    root-cause hypothesis
    next debug action
    modified testbench or board script
```

---

## 12. 제안 논문 주제 3: Multi-Agent FPGA Debug Orchestrator

### 제목 후보

> Multi-Agent LLM Orchestration for FPGA Verification: From RTL Simulation to Board-Level Debug

### 핵심 아이디어

단일 LLM이 모든 일을 하는 것이 아니라, 역할별 agent를 나눈다.

```text
Spec Agent:
    요구사항 분석

TB Agent:
    Verilog/SystemVerilog testbench 생성

Simulation Agent:
    compile/simulation log 분석

Synthesis Agent:
    synthesis/implementation/timing report 분석

Board Agent:
    FPGA programming 및 board test script 생성

ILA Agent:
    ILA probe/trigger 설정 및 waveform 해석

Debug Manager Agent:
    failure hypothesis ranking 및 next action 결정
```

### 장점

```text
1. 복잡한 FPGA verification flow를 agent 단위로 분해 가능
2. 각 agent의 역할과 책임이 명확함
3. 실패 원인 추적이 쉬움
4. 기존 EDA flow와 통합 가능
5. human engineer의 debug workflow를 모방 가능
```

---

## 13. 특허 아이디어로의 확장

AutoBench-HIL 구조는 특허 아이디어로도 확장 가능하다.

### 특허 제목 후보

> Hardware-in-the-Loop Feedback-Driven Verification System Using Multi-Agent Large Language Models

### 청구항 방향

```text
1. RTL simulation result와 FPGA board execution result를 함께 수집하는 시스템
2. LLM agent가 simulation result와 hardware result의 mismatch를 분석하는 방법
3. ILA trigger/probe setting을 자동 생성하는 방법
4. AXI/UART/DMA log를 기반으로 root-cause hypothesis를 생성하는 방법
5. 다음 verification action을 자동 선택하는 multi-agent orchestration 방법
6. Simulation-pass but FPGA-fail case를 자동 분류하는 방법
```

### 차별화 포인트

기존 AutoBench:

```text
LLM-based testbench generation + simulation-based evaluation
```

확장 아이디어:

```text
LLM-based verification orchestration + real FPGA feedback + next action generation
```

---

## 14. 논문 포지셔닝 문장

논문 introduction에 사용할 수 있는 포지셔닝 문장은 다음과 같다.

```text
Recent works such as AutoBench have demonstrated that large language models can generate and evaluate simulation testbenches for RTL designs. However, modern FPGA development failures often occur after simulation, during synthesis, implementation, board bring-up, and hardware measurement. These failures include timing violations, interface protocol mismatches, reset sequencing issues, and board-level configuration errors, which cannot be fully captured by simulation-only testbench generation frameworks. To address this gap, we propose a hardware-in-the-loop LLM-based verification framework that closes the loop between RTL simulation and real FPGA board feedback.
```

한국어로 요약하면 다음과 같다.

```text
AutoBench는 LLM이 simulation testbench를 생성할 수 있음을 보여주었다.
하지만 실제 FPGA 개발에서는 simulation 이후 synthesis, implementation, board bring-up, hardware measurement 단계에서 많은 문제가 발생한다.
따라서 우리는 RTL simulation과 실제 FPGA board feedback을 연결하는 hardware-in-the-loop LLM verification framework를 제안한다.
```

---

## 15. 최종 판단

AutoBench는 내 아이디어의 직접적인 prior work이다.

따라서 단순히 다음 주제로 가면 novelty가 약하다.

```text
LLM-based Verilog testbench generation
```

하지만 다음 방향으로 확장하면 novelty가 생긴다.

```text
1. Hardware-in-the-loop
2. FPGA board feedback
3. Simulation-to-FPGA mismatch debugging
4. ILA / AXI / UART / DMA log analysis
5. Multi-agent verification orchestration
6. Next verification action generation
```

가장 추천하는 방향은 다음이다.

```text
AutoBench-HIL:
Hardware-in-the-Loop LLM Agent for RTL/FPGA Verification
```

이 방향은 다음 조건을 만족한다.

```text
1. AutoBench와 직접 연결되는 명확한 prior work가 있음
2. 기존 논문과 차별화되는 hardware feedback loop가 있음
3. FPGA/RTL/AXI/DMA/ILA 경험을 활용할 수 있음
4. 논문과 특허 둘 다 가능성이 있음
5. 실제 demo system을 만들기 좋음
```

---

## 16. 다음 실행 계획

### Step 1: Minimal Demo IP 선정

가장 먼저 복잡한 RFSoC 전체 시스템이 아니라, 작은 IP부터 시작하는 것이 좋다.

추천 순서:

```text
1. AXI-Lite register IP
2. AXI-Stream FIFO IP
3. Simple DMA loopback IP
4. Correlator IP
5. OFDM synchronization IP
```

---

### Step 2: Failure Case 정의

각 IP에 대해 simulation-pass but FPGA-fail case를 만든다.

예시:

```text
AXI-Lite IP:
    - register offset mismatch
    - write strobe handling error
    - reset value mismatch

AXI-Stream FIFO:
    - tvalid/tready handshake bug
    - underflow/overflow condition
    - TLAST missing case

DMA IP:
    - buffer alignment issue
    - address range error
    - transfer length mismatch
```

---

### Step 3: Agent 역할 정의

최소 agent 구조는 다음 4개로 시작할 수 있다.

```text
1. TB Agent
2. Simulation Agent
3. Board Test Agent
4. Debug Manager Agent
```

처음부터 너무 많은 agent를 만들 필요는 없다.

---

### Step 4: Evaluation Metric 정의

AutoEval처럼 내 프레임워크도 평가 기준이 필요하다.

추천 metric:

```text
Eval0-HIL:
    simulation compile/run 성공

Eval1-HIL:
    golden RTL simulation pass

Eval2-HIL:
    mutant RTL simulation fail/pass classification 성공

Eval3-HIL:
    FPGA board test execution 성공

Eval4-HIL:
    simulation-pass but FPGA-fail mismatch root-cause classification 성공

Eval5-HIL:
    generated next action이 실제 debug에 도움이 되는가
```

---

## 17. 한 줄 결론

> AutoBench가 LLM 기반 simulation testbench generation의 출발점이라면, 내가 만들 수 있는 것은 FPGA board feedback까지 포함하는 AutoBench-HIL이다. 이 방향은 논문성과 특허성이 모두 있으며, 특히 RTL simulation과 real FPGA bring-up 사이의 gap을 자동화한다는 점에서 차별화된다.
