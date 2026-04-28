# Simulation-to-FPGA Feedback-Driven Multi-Agent Verification Framework

## 1. 핵심 아이디어

본 아이디어는 단순히 LLM을 이용해 RTL 코드나 testbench를 생성하는 것이 아니라,  
**simulation → synthesis/implementation → FPGA board test → measurement/log feedback → next verification action**까지 연결하는  
**Hardware-in-the-Loop 기반 Multi-Agent RTL/FPGA Verification Framework**이다.

핵심 한 줄 요약:

> **LLM 기반 multi-agent가 RTL simulation 결과와 실제 FPGA board test 결과를 함께 분석하여, 다음 검증 목표, testbench, board test script, ILA trigger, debug hypothesis를 자동으로 생성/수정하는 시스템**

---

## 2. 왜 이 주제가 중요한가?

기존 RTL/FPGA 개발 플로우는 다음과 같이 많은 수작업을 요구한다.

```text
RTL 작성
→ testbench 작성
→ simulation 수행
→ synthesis / implementation
→ bitstream 생성
→ FPGA board programming
→ board-level test
→ 실패 시 ILA / UART / AXI log / DMA memory mismatch 분석
→ 사람이 원인 추정
→ RTL / testbench / driver / constraint 수정
→ 반복
```

이 과정에서 많은 시간이 소모되는 부분은 다음과 같다.

```text
1. testbench 작성
2. simulation failure log 분석
3. board bring-up failure 분석
4. AXI/DMA transaction mismatch debugging
5. ILA trigger 설정
6. host driver와 FPGA register map mismatch 확인
7. timing closure 이후 board-level failure 원인 분석
8. simulation에서는 통과했지만 FPGA에서는 실패하는 문제 추적
```

LLM은 코드 생성에는 강하지만, 단순 코드 생성만으로는 실제 hardware verification 문제를 해결하기 어렵다.  
따라서 중요한 것은 **LLM을 코드 생성기가 아니라 verification workflow orchestrator로 사용하는 것**이다.

---

## 3. 기존 연구/특허와의 관계

이미 다음과 같은 방향의 연구 및 특허는 존재한다.

```text
1. LLM-based RTL generation
2. LLM-based Verilog/SystemVerilog testbench generation
3. LLM-assisted UVM testbench generation
4. simulation feedback을 이용한 self-correction
5. coverage-guided test generation
6. multi-agent RTL generation/debugging
```

따라서 단순히 아래와 같이 주장하면 신규성이 약하다.

```text
LLM이 RTL을 읽고 testbench를 생성한다.
시뮬레이션 결과를 보고 코드를 수정한다.
coverage를 보고 test case를 추가한다.
```

이런 주장은 이미 prior art가 많을 가능성이 높다.

---

## 4. 차별화 포인트

본 아이디어의 차별화는 **FPGA board-level test까지 통합한다는 점**이다.

기존 LLM-for-RTL 연구는 보통 다음 단계에 머문다.

```text
natural language spec
→ RTL generation
→ testbench generation
→ simulation
→ compile/simulation error feedback
```

반면 제안 방향은 다음까지 포함한다.

```text
RTL / spec / testbench
→ simulation
→ synthesis / implementation
→ bitstream generation
→ FPGA programming
→ board-level test
→ ILA / UART / AXI-Lite / DMA / measurement log 수집
→ simulation result와 hardware result 비교
→ failure signature 추출
→ next verification action 선택
```

즉, 핵심 차별점은 다음과 같다.

```text
1. simulation result와 real FPGA result 비교
2. ILA trace 자동 해석 또는 trigger 추천
3. AXI-Lite register read/write 기반 board test 생성
4. AXI/DMA memory consistency check 자동화
5. host driver log와 RTL simulation result의 correlation
6. timing report와 board failure의 연결
7. external measurement equipment log까지 포함 가능
8. 다음 verification objective를 adaptive하게 선택
```

---

## 5. 제안 시스템 아키텍처

전체 구조는 다음과 같다.

```text
Specification / RTL / Existing Testbench / Board Config
                    ↓
            LLM Planner Agent
                    ↓
      Verification Objective Extraction
                    ↓
 ┌──────────────────────────────────────────┐
 │ Multi-Agent Verification Subsystem       │
 │                                          │
 │ 1. Test Plan Agent                       │
 │ 2. Testbench Generation Agent            │
 │ 3. Assertion Agent                       │
 │ 4. Scoreboard / Golden Model Agent       │
 │ 5. Simulation Agent                      │
 │ 6. Log Analysis Agent                    │
 │ 7. FPGA Board Test Agent                 │
 │ 8. ILA Trigger / Trace Agent             │
 │ 9. Failure Diagnosis Agent               │
 │ 10. Repair / Next-Test Selection Agent   │
 └──────────────────────────────────────────┘
                    ↓
          RTL Simulation Feedback
                    ↓
       Synthesis / Implementation Feedback
                    ↓
             FPGA Board Feedback
                    ↓
        Adaptive Verification Loop
```

---

## 6. 핵심 입력 데이터

시스템이 받을 수 있는 입력은 다음과 같다.

```text
1. RTL files
   - Verilog
   - SystemVerilog
   - VHDL

2. Design specification
   - Markdown spec
   - register map
   - interface document
   - timing requirement
   - fixed-point format

3. Simulation environment
   - existing testbench
   - xsim / Questa / Verilator / Icarus logs
   - waveform dump
   - assertion failure log

4. FPGA build reports
   - synthesis report
   - implementation report
   - timing summary
   - utilization report
   - power report

5. Board configuration
   - target board name
   - clock/reset information
   - AXI address map
   - bitstream path
   - driver path

6. Board-level logs
   - AXI-Lite register readback
   - DMA memory comparison result
   - UART log
   - JTAG log
   - ILA trace
   - RFSoC tile status
   - external measurement equipment log
```

---

## 7. 핵심 출력

시스템이 생성하는 출력은 다음과 같다.

```text
1. verification plan
2. simulation testbench
3. protocol assertion
4. scoreboard / golden model
5. board-level Python/C test script
6. AXI-Lite register access sequence
7. DMA transfer test sequence
8. ILA trigger condition
9. failure diagnosis report
10. RTL/testbench/driver 수정 제안
11. next verification objective
12. final verification report
```

---

## 8. 논문 주제 후보

### 논문 주제 1

> **LLM-Assisted Simulation-to-FPGA Verification Flow for AXI-Based Hardware Designs**

핵심 기여:

```text
1. LLM을 단순 code generator가 아니라 verification workflow orchestrator로 사용
2. simulation과 FPGA board test를 통합한 closed-loop verification 구조 제안
3. AXI/DMA IP를 대상으로 case study 수행
4. simulation-only 방식과 비교하여 board-level bug detection 능력 평가
```

---

### 논문 주제 2

> **Hardware-in-the-Loop Multi-Agent Verification Framework for FPGA-Based RTL Designs**

핵심 기여:

```text
1. multi-agent 기반 verification task decomposition
2. simulation, synthesis report, board log, ILA trace를 통합 분석
3. failure signature 기반 next-test selection
4. FPGA bring-up 시간 감소 및 manual debugging step 감소 평가
```

---

### 논문 주제 3

> **LLM-Based Board-Level Debugging Assistant for AXI/DMA and Streaming FPGA Designs**

핵심 기여:

```text
1. AXI-Lite / AXI4 / AXI-Stream protocol-aware verification graph 생성
2. DMA memory consistency check 자동화
3. valid/ready stall, register mismatch, memory mismatch failure pattern 분석
4. board test script 및 ILA trigger condition 자동 추천
```

---

### 논문 주제 4

> **AI-Assisted RFSoC Bring-Up and Measurement-Guided Verification for Communication Platforms**

핵심 기여:

```text
1. RFSoC tile status, PLL lock, RFDC configuration, LMK/LMX clock 설정 분석
2. DMA-based IQ capture와 spectrum/constellation/PDP measurement 통합
3. RFSoC bring-up failure를 LLM agent가 진단
4. communication hardware platform에 특화된 Hardware-in-the-Loop verification flow 제안
```

---

## 9. 특허 제목 후보

### 후보 1

> **Simulation-to-FPGA Feedback-Driven Multi-Agent Verification Framework for HDL-Based Hardware Designs**

### 후보 2

> **Method and Apparatus for Hardware-in-the-Loop Verification of FPGA Designs Using Language-Model Agents**

### 후보 3

> **Protocol-Aware Multi-Agent Verification System for AXI/DMA and Streaming FPGA Designs**

### 후보 4

> **LLM-Based Hardware-in-the-Loop Bring-Up and Verification System for RFSoC-Based Communication Platforms**

### 후보 5

> **Method for Adaptive FPGA Verification Using Simulation Logs, Hardware Traces, and Language-Model-Based Failure Diagnosis**

---

## 10. 특허 청구항 초안

### Claim 1: Broad Independent Claim

```text
A computer-implemented method for verifying an HDL-based FPGA design, comprising:

receiving an HDL design, a hardware interface specification, and a board configuration;

generating, by a language-model-based planning agent, a verification plan including simulation tests and FPGA on-board tests;

executing an RTL simulation using generated testbench components;

generating an FPGA implementation including a bitstream for a target FPGA board;

programming the FPGA board with the bitstream;

executing one or more on-board tests through at least one of AXI-Lite register access, DMA transfer, UART command interface, JTAG interface, integrated logic analyzer trace, or external measurement equipment;

collecting hardware execution data including register readback values, memory comparison results, timing status, logic analyzer traces, or measurement-device logs;

extracting one or more failure signatures by comparing simulation results and hardware execution data;

selecting a subsequent verification action based on the failure signatures, simulation coverage, timing reports, and hardware execution results.
```

---

### Claim 2: Protocol-Aware Verification Graph

```text
The method of claim 1, further comprising:

parsing a hardware interface description including at least one of an AXI register map, DMA descriptor format, streaming valid-ready protocol, or fixed-point signal specification;

generating a protocol-specific verification graph including transaction nodes, timing constraints, memory consistency constraints, and expected response nodes;

assigning the verification graph to a plurality of language-model-based agents including a transaction agent, assertion agent, scoreboard agent, board-test agent, and failure-analysis agent.
```

---

### Claim 3: FPGA Board Feedback

```text
The method of claim 1, wherein the hardware execution data comprises at least one of:

an AXI-Lite register readback result;

a DMA memory mismatch report;

an integrated logic analyzer trace;

a UART command response;

a JTAG programming status;

a timing violation report;

a clock or reset status signal;

or an external measurement-device output.
```

---

### Claim 4: Adaptive Next-Test Selection

```text
The method of claim 1, further comprising:

ranking candidate verification objectives based on protocol coverage, simulation failures, hardware failure signatures, timing reports, and prior test outcomes;

selecting a next verification objective from the ranked candidate verification objectives;

generating at least one of a new testbench, a new board-test script, a new assertion, or a new integrated-logic-analyzer trigger condition corresponding to the selected next verification objective.
```

---

### Claim 5: Simulation-to-Hardware Correlation

```text
The method of claim 1, further comprising:

comparing a simulated transaction trace with a hardware transaction trace obtained from an FPGA board;

identifying a mismatch between the simulated transaction trace and the hardware transaction trace;

classifying the mismatch into at least one of a protocol violation, memory consistency violation, timing-related failure, reset-sequencing failure, clock-domain-crossing failure, or host-driver mismatch.
```

---

### Claim 6: RFSoC Extension

```text
The method of claim 1, wherein the target FPGA board comprises an RFSoC device, and wherein the hardware execution data includes at least one of:

RF data converter tile status;

PLL lock status;

clock generation configuration;

ADC or DAC data clock status;

DMA-based IQ sample capture;

spectrum measurement;

constellation measurement;

or register status of an RF front-end control interface.
```

---

## 11. MVP 구현 방향

가장 현실적인 첫 번째 MVP는 **AXI/DMA FPGA Verification Agent**이다.

### 대상 IP

```text
dma_ip_top.v
AXI-Lite control register
AXI master read/write
RDMA / WDMA
host C/Python driver
Vivado xsim
Vivado implementation
FPGA board test
```

### MVP 기능

```text
1. RTL/spec 입력
2. LLM이 register map과 interface 요약
3. LLM이 simulation test plan 생성
4. LLM이 SystemVerilog testbench 생성
5. xsim 실행
6. simulation log 분석
7. board test script 생성
8. bitstream programming 후 board test 실행
9. DMA memory consistency check
10. board log 분석
11. ILA trigger 추천
12. failure diagnosis report 생성
13. next verification action 추천
```

---

## 12. MVP 폴더 구조 예시

```text
fpga_verification_agent/
│
├── specs/
│   ├── dma_ip_spec.md
│   ├── register_map.yaml
│   └── board_config.yaml
│
├── rtl/
│   └── dma_ip_top.v
│
├── tb/
│   ├── tb_dma_ip_top.sv
│   └── axi_memory_model.sv
│
├── scripts/
│   ├── run_xsim.py
│   ├── build_bitstream.py
│   ├── program_fpga.py
│   ├── run_board_test.py
│   └── collect_ila_trace.py
│
├── agents/
│   ├── planner_agent.py
│   ├── testbench_agent.py
│   ├── log_analysis_agent.py
│   ├── board_test_agent.py
│   ├── ila_agent.py
│   └── repair_agent.py
│
├── logs/
│   ├── simulation.log
│   ├── synthesis.rpt
│   ├── implementation.rpt
│   ├── timing_summary.rpt
│   └── board_test.log
│
├── reports/
│   ├── verification_plan.md
│   ├── failure_analysis.md
│   └── final_report.md
│
└── README.md
```

---

## 13. 실험 평가 지표

논문을 위해 사용할 수 있는 정량 지표는 다음과 같다.

```text
1. Testbench 작성 시간 감소율
2. Board bring-up 시간 감소율
3. Simulation iteration 수 감소
4. Bitstream iteration 수 감소
5. Manual debugging step 수 감소
6. Manual code modification line 수
7. 발견한 bug 수
8. Simulation-only에서 못 잡고 board에서 발견한 bug 수
9. ILA trigger 추천 성공률
10. AXI/DMA transaction coverage
11. Register read/write coverage
12. DMA memory consistency check 성공률
13. Failure diagnosis accuracy
14. False repair rate
15. Hallucination/error rate
```

---

## 14. 비교 baseline

논문에서는 다음 baseline과 비교할 수 있다.

```text
Baseline 1:
Human-written testbench + manual board debugging

Baseline 2:
Single-prompt LLM testbench generation

Baseline 3:
LLM simulation-only feedback loop

Baseline 4:
Traditional script-based FPGA board test

Proposed:
Simulation-to-FPGA feedback-driven multi-agent verification framework
```

---

## 15. 가능한 Case Study

### Case Study 1: AXI/DMA IP

```text
- AXI-Lite register write/readback
- RDMA transfer
- WDMA transfer
- memory copy correctness
- interrupt/status register check
- timeout/polling sequence
- memory alignment issue
```

### Case Study 2: Streaming DSP IP

```text
- AXI-Stream valid/ready
- FIFO overflow/underflow
- latency check
- backpressure scenario
- packet boundary check
```

### Case Study 3: OFDM Synchronization RTL

```text
- Schmidl-Cox autocorrelation
- Zadoff-Chu detector
- CFO estimator
- fixed-point scaling
- CORDIC phase estimator
- golden Python model comparison
- latency < N cycles
```

### Case Study 4: RFSoC Bring-Up

```text
- RFDC tile status
- PLL lock
- LMK/LMX clock configuration
- AXI GPIO SPI MUX
- ADC/DAC data clock
- DMA IQ sample capture
- spectrum/constellation analysis
```

---

## 16. 제품화 가능성

이 아이디어는 논문/특허뿐 아니라 제품화 가능성도 있다.

가능한 제품 형태:

```text
1. FPGA verification assistant
2. AXI/DMA IP verification copilot
3. RFSoC bring-up assistant
4. board-level debug report generator
5. testbench + board-test script generator
6. ILA trigger recommendation tool
7. simulation-to-hardware mismatch analyzer
```

대상 고객:

```text
1. FPGA 스타트업
2. 반도체 IP 회사
3. 통신 시스템 연구실
4. SDR/RFSoC 개발팀
5. 대학 연구실
6. HW verification engineer
7. embedded/FPGA system integrator
```

---

## 17. 전략적 판단

### 단순 LLM RTL/testbench 생성

```text
장점:
- 구현 쉬움
- 데모 빠름

단점:
- prior art 많음
- 차별화 약함
- Copilot/Claude Code와 직접 경쟁
```

### Simulation-to-FPGA Feedback Loop

```text
장점:
- 차별화 강함
- 실제 FPGA 경험이 필요하므로 진입장벽 있음
- 논문/특허/제품화 모두 가능
- 사용자의 기존 경험과 잘 맞음

단점:
- 구현 복잡도 높음
- 보드/툴체인 의존성 큼
- 자동화 안정성 확보 필요
```

### RFSoC Bring-Up Agent

```text
장점:
- 매우 차별화됨
- 고부가가치 niche 가능
- 사용자의 RFSoC 경험과 강하게 연결됨

단점:
- 범용성 낮음
- 실험 환경 의존성 큼
- 초기 MVP로는 부담이 큼
```

---

## 18. 추천 로드맵

### Phase 1: AXI/DMA Simulation Agent

```text
목표:
RTL/spec를 읽고 testbench 생성 및 simulation log 분석

산출물:
- test plan
- SystemVerilog testbench
- simulation report
- failure analysis report
```

---

### Phase 2: AXI/DMA Board Test Agent

```text
목표:
FPGA board에서 AXI-Lite/DMA test 실행 및 board log 분석

산출물:
- board test Python/C script
- register readback report
- DMA memory consistency report
- failure signature report
```

---

### Phase 3: Simulation-to-FPGA Correlation

```text
목표:
simulation result와 FPGA board result를 비교하여 mismatch 원인 분석

산출물:
- simulation-vs-hardware comparison report
- failure classification
- next verification objective
```

---

### Phase 4: ILA Integration

```text
목표:
ILA trigger condition 추천 및 trace 분석

산출물:
- ILA trigger config
- trace summary
- protocol violation report
```

---

### Phase 5: RFSoC Extension

```text
목표:
RFSoC tile/clock/RFDC/DMA/IQ capture까지 확장

산출물:
- RFSoC bring-up checklist
- RFDC status analyzer
- IQ capture validation report
- measurement-guided debug report
```

---

## 19. 최종 추천 주제

가장 좋은 최종 주제는 다음과 같다.

> **Simulation-to-FPGA Feedback-Driven Multi-Agent Verification Framework for AXI/DMA and Streaming Hardware Designs**

이 주제는 다음을 모두 만족한다.

```text
1. 논문 가능
2. 특허 가능
3. 제품화 가능
4. 사용자의 FPGA/RTL/AXI/DMA/RFSoC 경험과 직접 연결
5. 단순 LLM code generation과 차별화 가능
6. 실제 hardware-in-the-loop 검증이라는 강한 실용성 보유
```

---

## 20. 한 줄 결론

단순히 **LLM으로 RTL/testbench를 생성하는 아이디어**는 이미 prior art가 많다.  
하지만 **simulation 결과와 실제 FPGA board test 결과를 함께 분석하고, ILA/AXI/DMA/UART/measurement log 기반으로 다음 검증 액션을 선택하는 Hardware-in-the-Loop Multi-Agent Verification Framework**는 훨씬 더 강한 논문/특허/제품화 방향이다.
