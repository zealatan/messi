
#### First loop ####
1.  Spec design
2.  DUT design
3.  TB design
4.  Design Verification. 

#### Second loop ####
5.  DMA Wrapper integration
6.  AXI 4 BUS Verification.


#### Third loop ####
7.  Packaging
8.  PS setting
9.  TOP Integration(Automatic setting)
10. Synthesis-implementation-bitstream generation
11. HW export with XSA format. 
12. Update HW
13. Firmware generation and build
14. Flash programming
15. FPGA TEST




# MCP 기반 AI Agent / RTL-FPGA Verification 아이디어 정리

## 0. 한 줄 요약

**MCP(Model Context Protocol)는 LLM/AI Agent가 외부 도구, 파일, 데이터베이스, API, 개발환경을 표준 방식으로 사용할 수 있게 해주는 연결 프로토콜이다.**

본 논의의 핵심은 MCP 자체가 아니라, 이를 **RTL simulation, EDA tool, FPGA board test, measurement feedback**까지 연결하여  
**AI-assisted Hardware-in-the-Loop Verification Framework**로 확장하는 것이다.

---

## 1. MCP란 무엇인가?

MCP는 AI agent가 외부 시스템과 연결되기 위한 표준 인터페이스이다.

쉽게 말하면:

```text
기존 LLM:
사용자 질문 → LLM 답변

MCP 기반 LLM:
사용자 질문 → LLM → MCP → 외부 도구/API/파일/DB/개발환경 실행 → 결과 분석 → 답변
```

즉, MCP는 AI agent에게 다음과 같은 기능을 제공한다.

```text
- 로컬 파일 읽기/쓰기
- GitHub repository 접근
- 데이터베이스 조회
- 외부 API 호출
- Shell command 실행
- 테스트 코드 실행
- 로그 분석
- 보고서 생성
- 개발환경 자동화
```

비유하면 MCP는 **AI agent용 USB-C 포트** 또는 **표준 플러그인 인터페이스**에 가깝다.

---

## 2. MCP의 기본 구조

MCP는 크게 세 가지 구성요소로 이해할 수 있다.

```text
MCP Host
  예: Claude Desktop, Claude Code, Cursor, VS Code Agent, ChatGPT류 agent

MCP Client
  Host 내부에서 MCP Server와 통신하는 모듈

MCP Server
  실제 외부 기능을 제공하는 서버
  예: 파일 접근, GitHub 조작, DB 조회, simulator 실행, Vivado report parsing 등
```

전체 구조:

```text
AI Agent / LLM Client
        |
        | MCP Protocol
        v
MCP Server
        |
        v
External Tool / File / API / Local Environment
```

MCP Server는 보통 다음 기능을 제공한다.

```text
1. Resources
   읽을 수 있는 데이터
   예: 파일, 문서, 로그, DB row, config

2. Tools
   실행 가능한 함수
   예: run_test(), query_db(), run_verilator(), parse_timing_report()

3. Prompts
   재사용 가능한 작업 템플릿
   예: 코드 리뷰 프롬프트, 실험 분석 프롬프트, verification checklist
```

---

## 3. MCP는 돈을 내야 하는가?

결론:

> **MCP 자체는 유료 서비스가 아니다. 무료/open-source 표준에 가깝다.**

다만 MCP를 사용하는 환경에 따라 비용이 발생할 수 있다.

### 무료에 가까운 것

```text
- MCP 프로토콜 자체
- 직접 MCP server 구현
- 로컬 MCP server 실행
- 로컬 파일 접근 MCP
- 직접 만든 Python/Node 기반 MCP server
- GitHub에 공개된 MCP server 사용
```

### 비용이 발생할 수 있는 것

```text
- Claude Pro / Claude Code / Anthropic API
- ChatGPT Plus / Team / OpenAI API
- Cursor, GitHub Copilot 등 AI coding tool
- 외부 API 사용료
- 클라우드 서버 비용
- SaaS 연동 비용
```

따라서 메시님이 생각하는 다음 구조에서는 MCP 자체 비용은 거의 없다.

```text
Claude Code / Cursor / ChatGPT Agent
        |
        | MCP
        v
Local MCP Server
        |
        v
Verilator / Vivado / UART script / FPGA board test / log parser
```

비용의 핵심은 MCP가 아니라 **AI 모델 사용료, 외부 API 비용, 서버 비용**이다.

---

## 4. MCP와 n8n의 관계

처음 느낌은 맞다.

> **MCP는 큰 그림에서 n8n 같은 자동화 세계관에 속한다.**

하지만 둘은 역할이 다르다.

| 구분 | n8n | MCP |
|---|---|---|
| 정체 | Workflow automation platform | AI agent tool interface standard |
| 중심 | 노드 기반 workflow | LLM이 호출하는 tools/resources |
| 목적 | 반복 업무 자동화 | AI가 외부 도구를 사용하게 함 |
| 사용 방식 | 사람이 workflow graph를 설계 | LLM/agent가 상황에 맞게 tool 호출 |
| 예시 | Gmail → 요약 → Slack 전송 | Claude가 `run_verilator()` 호출 |
| 비유 | Zapier 고급형 + AI workflow | AI용 USB-C / plugin standard |

### n8n 방식

```text
Trigger
  ↓
Node 1: Gmail read
  ↓
Node 2: LLM summarize
  ↓
Node 3: Slack send
```

### MCP 방식

```text
User asks a task
  ↓
LLM decides which tool to use
  ↓
MCP tool call
  ↓
External tool execution
  ↓
LLM analyzes result
```

### 같이 쓰는 구조도 가능하다

```text
Claude / Cursor / ChatGPT Agent
        |
        | MCP
        v
n8n Workflow
        |
        v
GitHub / Gmail / Slack / DB / Webhook / Script
```

또는 반대로:

```text
n8n AI Agent
        |
        | MCP Client
        v
External MCP Server
        |
        v
Vivado / Verilator / Local Files / Git / FPGA Board Script
```

정리하면:

> **n8n은 자동화 파이프라인을 굴리는 엔진이고, MCP는 AI가 그 파이프라인이나 외부 도구를 호출하게 해주는 표준 포트이다.**

---

## 5. 메시님 관점에서 MCP가 중요한 이유

메시님이 관심 있는 방향은 단순한 업무 자동화가 아니다.

현재 생각 중인 구조는 다음에 가깝다.

```text
LLM Agent
  ↓
RTL 코드 분석
  ↓
Testbench 생성
  ↓
Simulation 실행
  ↓
Log/Waveform 분석
  ↓
Synthesis/Implementation 실행
  ↓
Timing report 분석
  ↓
FPGA board programming
  ↓
UART / AXI / DMA / ILA log 수집
  ↓
Measurement feedback 분석
  ↓
다음 verification action 생성
```

이 구조에서 MCP는 각 도구를 agent에게 연결하는 표준 인터페이스가 된다.

예를 들어:

```text
MCP Server 1: Git Repository Access
MCP Server 2: Verilator / Icarus Verilog Runner
MCP Server 3: Simulation Log Parser
MCP Server 4: GTKWave / VCD Analyzer
MCP Server 5: Vivado Synthesis Runner
MCP Server 6: Timing Report Parser
MCP Server 7: FPGA Programmer
MCP Server 8: UART / AXI / DMA Log Collector
MCP Server 9: ILA Dump Analyzer
MCP Server 10: Report Generator
```

이렇게 구성하면 AI agent가 단순히 코드를 추천하는 것을 넘어서, 실제 verification loop를 수행할 수 있다.

---

## 6. 핵심 아이디어: MCP-based RTL/FPGA Verification Agent

본 논의에서 나온 핵심 연구 아이디어는 다음과 같다.

> **MCP 기반 AI agent가 RTL simulation 결과와 실제 FPGA board test 결과를 함께 분석하여, 다음 testbench, debug hypothesis, board test script, ILA trigger condition, verification target을 자동으로 생성하는 framework**

한 줄 요약:

```text
Simulation → Synthesis/Implementation → FPGA Board Test → Measurement Feedback → Next Verification Action
```

이를 MCP 기반으로 표현하면:

```text
AI Agent / LLM
        |
        | MCP
        v
EDA / FPGA MCP Tool Layer
        |
        +-- run_simulation()
        +-- parse_sim_log()
        +-- generate_testbench()
        +-- run_synthesis()
        +-- parse_timing_report()
        +-- program_fpga()
        +-- read_uart_log()
        +-- dump_dma_memory()
        +-- analyze_ila_capture()
        +-- generate_next_test_plan()
```

---

## 7. 기존 MCP 논문/연구 흐름

MCP를 활용한 논문이나 preprint는 이미 등장하고 있다.  
다만 아직 매우 초기 단계이며, 대부분은 다음 영역에 집중되어 있다.

```text
1. MCP architecture / survey
2. MCP security / tool poisoning / maintainability
3. MCP 기반 multi-agent system
4. MCP 기반 EDA automation
5. MCP를 이용한 RTL generation / compile-test-debug loop
```

특히 EDA 쪽에서는 다음 방향이 이미 보인다.

```text
LLM
  ↓
MCP
  ↓
Yosys / Icarus Verilog / OpenLane / GTKWave / KLayout
  ↓
RTL-to-GDSII automation
```

하지만 아직 차별화 여지가 큰 부분은 다음이다.

```text
LLM
  ↓
MCP
  ↓
RTL Simulation
  ↓
Synthesis / Implementation
  ↓
FPGA Programming
  ↓
Board-Level Test
  ↓
UART / DMA / AXI / ILA Measurement
  ↓
Closed-Loop Verification Feedback
```

즉, 기존 연구가 주로 **simulation/EDA automation** 중심이라면, 메시님 아이디어는 **Hardware-in-the-Loop verification feedback loop**까지 확장하는 점이 차별화 포인트가 될 수 있다.

---

## 8. Novelty 후보

MCP 자체는 novelty가 약하다.  
그러나 MCP를 hardware verification domain에 특화시키면 논문화 가능성이 생긴다.

### 약한 주장

```text
We use MCP to connect LLM with tools.
```

이건 너무 일반적이다.

### 강한 주장

```text
We propose an MCP-enabled closed-loop RTL-to-FPGA verification framework that integrates simulation results, synthesis/timing reports, and board-level measurement feedback to guide the next verification action.
```

즉, novelty는 다음 조합에서 나온다.

```text
MCP
+ LLM multi-agent
+ RTL simulation
+ FPGA board-level test
+ Measurement feedback
+ Next-action planning
```

---

## 9. 가능한 논문 제목

### 제목 후보 1

```text
MCP-Enabled Hardware-in-the-Loop Verification Framework for FPGA-Based Digital Systems
```

### 제목 후보 2

```text
A Model Context Protocol-Based Multi-Agent Framework for Simulation-to-FPGA Verification
```

### 제목 후보 3

```text
Closed-Loop RTL and FPGA Verification Using MCP-Integrated LLM Agents
```

### 제목 후보 4

```text
An Agentic Verification Framework for FPGA Prototyping via Model Context Protocol
```

### 제목 후보 5

```text
MCP4FPGA: A Model Context Protocol-Based Toolchain for AI-Assisted RTL Simulation and Board-Level Verification
```

---

## 10. 가능한 특허 제목

### 특허 제목 후보 1

```text
Method and System for AI-Assisted Hardware Verification Using Model Context Protocol-Based Tool Integration
```

### 특허 제목 후보 2

```text
Closed-Loop FPGA Verification System Using Large Language Model Agents and Board-Level Measurement Feedback
```

### 특허 제목 후보 3

```text
Hardware-in-the-Loop Debugging Framework Using Agentic Tool Orchestration and Measurement Feedback
```

### 특허 제목 후보 4

```text
System for Automated RTL Testbench Generation and FPGA Board Validation Using Multi-Agent AI
```

---

## 11. 시스템 아키텍처 초안

```text
+------------------------------------------------------+
|                    User / Engineer                   |
+------------------------------------------------------+
                          |
                          v
+------------------------------------------------------+
|                  LLM Verification Agent              |
|                                                      |
|  - understands design intent                         |
|  - generates test plan                               |
|  - selects tools                                     |
|  - analyzes logs                                     |
|  - proposes debug hypotheses                         |
|  - updates verification strategy                     |
+------------------------------------------------------+
                          |
                          v
+------------------------------------------------------+
|                    MCP Tool Layer                    |
+------------------------------------------------------+
     |              |              |              |
     v              v              v              v
+---------+    +----------+   +----------+   +------------+
| Git MCP |    | Sim MCP  |   | EDA MCP  |   | Board MCP  |
+---------+    +----------+   +----------+   +------------+
     |              |              |              |
     v              v              v              v
RTL source     Verilator /    Vivado /       UART / AXI /
TB files       Icarus /       Timing /       DMA / ILA /
Commits        Cocotb         Reports        Oscilloscope
```

---

## 12. Agent 역할 분리

Multi-agent 구조로 확장하면 다음과 같이 나눌 수 있다.

```text
1. Design Understanding Agent
   - RTL 구조 분석
   - module interface 파악
   - expected behavior 정리

2. Testbench Generation Agent
   - directed test 생성
   - random test 생성
   - corner case 생성
   - assertion 생성

3. Simulation Debug Agent
   - compile error 분석
   - simulation mismatch 분석
   - waveform/log 기반 bug hypothesis 생성

4. EDA Report Agent
   - synthesis 결과 분석
   - timing violation 분석
   - resource usage 분석
   - critical path 요약

5. Board Test Agent
   - FPGA programming script 실행
   - UART/AXI/DMA 기반 board test 수행
   - ILA trigger 설정
   - board-level log 수집

6. Verification Manager Agent
   - 전체 진행 상황 관리
   - 다음 action 결정
   - coverage gap 파악
   - final report 생성
```

---

## 13. MVP 구현 방향

처음부터 Vivado/FPGA board까지 모두 연결하면 복잡하다.  
따라서 MVP는 작은 loop부터 시작하는 것이 좋다.

### MVP 1단계: Read-only MCP

```text
목표:
AI agent가 repository, RTL, testbench, simulation log를 읽을 수 있게 한다.

기능:
- list_project_files()
- read_rtl_file()
- read_testbench_file()
- read_sim_log()
- summarize_design()
```

이 단계에서는 destructive action이 없기 때문에 안전하다.

---

### MVP 2단계: Simulation MCP

```text
목표:
AI agent가 simulation을 실행하고 결과를 분석하게 한다.

기능:
- run_verilator()
- run_iverilog()
- run_cocotb()
- parse_compile_error()
- parse_sim_result()
- compare_expected_actual()
```

예시 loop:

```text
1. Agent reads RTL
2. Agent generates or modifies testbench
3. Agent runs simulation
4. Agent reads error log
5. Agent proposes fix or next test
```

---

### MVP 3단계: Vivado Report MCP

```text
목표:
AI agent가 synthesis/implementation report를 분석하게 한다.

기능:
- run_vivado_synth()
- parse_utilization_report()
- parse_timing_summary()
- extract_critical_path()
- summarize_timing_violation()
```

이 단계는 논문적으로도 중요하다.  
왜냐하면 단순 functional verification을 넘어서 **timing closure / hardware feasibility**까지 들어가기 때문이다.

---

### MVP 4단계: FPGA Board Test MCP

```text
목표:
AI agent가 실제 FPGA board test 결과를 verification loop에 포함하게 한다.

기능:
- program_bitstream()
- run_uart_test()
- read_uart_log()
- read_dma_memory()
- configure_ila_trigger()
- collect_ila_capture()
- compare_board_vs_simulation()
```

이 단계가 핵심 novelty이다.

---

## 14. 보안/안전성 고려사항

MCP server는 외부 명령 실행, 파일 접근, 장비 제어를 가능하게 하므로 위험할 수 있다.

특히 FPGA/EDA 환경에서는 다음 위험이 있다.

```text
- 프로젝트 파일 삭제
- Git repository 손상
- 잘못된 bitstream programming
- 장비 설정 변경
- Vivado project overwrite
- 장시간 synthesis job 무한 실행
- 보드 전원/clock 설정 오류
- 민감한 source code 외부 유출
```

따라서 다음 안전장치가 필요하다.

```text
1. Read-only mode
2. Command whitelist
3. Working directory sandbox
4. Dry-run mode
5. User confirmation for destructive action
6. Execution timeout
7. Log recording
8. Secret/API key masking
9. Git diff review before write
10. Board programming confirmation step
```

처음에는 반드시 **read-only MCP server**부터 시작하는 것이 좋다.

---

## 15. 연구 질문 후보

논문으로 발전시키려면 다음 질문들이 필요하다.

```text
RQ1. MCP 기반 LLM agent는 기존 manual RTL verification 대비 testbench 생성 시간을 줄일 수 있는가?

RQ2. Simulation log와 waveform feedback을 사용한 iterative agent loop는 bug localization 성능을 향상시키는가?

RQ3. Synthesis/timing report를 포함하면 LLM-generated RTL/testbench의 hardware feasibility 평가가 개선되는가?

RQ4. FPGA board-level measurement feedback을 simulation loop에 통합하면 실제 hardware bug를 더 빠르게 찾을 수 있는가?

RQ5. Multi-agent 구조는 single-agent 구조보다 verification planning과 debugging에서 더 안정적인가?
```

---

## 16. 평가 지표 후보

논문에서는 성능 metric이 중요하다. 가능한 metric은 다음과 같다.

```text
1. Bug detection rate
2. Time-to-debug
3. Number of iterations until pass
4. Testbench generation time
5. Simulation pass/fail accuracy
6. Compile error recovery rate
7. Functional coverage improvement
8. Assertion coverage
9. Board-test mismatch detection rate
10. Human intervention count
11. Timing violation detection accuracy
12. Resource report interpretation accuracy
```

---

## 17. 실험 대상 후보

초기 실험은 너무 큰 SoC보다 작은 RTL block부터 시작하는 것이 좋다.

```text
- FIFO
- UART
- SPI controller
- AXI-lite slave
- DMA controller
- FIR filter
- FFT block
- OFDM synchronizer block
- Schmidl-Cox correlation block
- Zadoff-Chu correlator
- Packet detector
```

메시님에게 가장 적합한 초기 대상은 다음이다.

```text
1. Schmidl-Cox autocorrelation RTL
2. Zadoff-Chu correlator RTL
3. AXI DMA memory-copy IP
4. OFDM packet detector
5. FPGA board UART/DMA loopback test
```

이들은 메시님이 이미 경험과 코드 자산을 가지고 있기 때문에 빠르게 MVP를 만들 수 있다.

---

## 18. GitHub Repository 구조 제안

```text
mcp-fpga-verification-agent/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── motivation.md
│   ├── security.md
│   └── experiments.md
├── mcp_servers/
│   ├── repo_server/
│   ├── verilator_server/
│   ├── vivado_report_server/
│   ├── board_test_server/
│   └── log_parser_server/
├── rtl_examples/
│   ├── fifo/
│   ├── uart/
│   ├── axi_dma/
│   ├── fir_filter/
│   └── ofdm_sync/
├── testbenches/
│   ├── directed/
│   ├── random/
│   └── cocotb/
├── scripts/
│   ├── run_sim.sh
│   ├── run_synth.tcl
│   ├── parse_timing.py
│   └── board_test.py
├── experiments/
│   ├── baseline_manual/
│   ├── single_agent/
│   └── multi_agent/
└── results/
    ├── logs/
    ├── reports/
    └── figures/
```

---

## 19. README용 짧은 소개문

```markdown
# MCP-FPGA Verification Agent

This project explores a Model Context Protocol (MCP)-based framework for AI-assisted RTL and FPGA verification.

The goal is to connect LLM agents with EDA and board-level verification tools, including RTL simulators, synthesis reports, timing analysis, UART/DMA logs, and FPGA measurement feedback.

Unlike conventional LLM-based code generation workflows, this framework focuses on a closed-loop verification process:

Simulation → Synthesis → FPGA Board Test → Measurement Feedback → Next Verification Action.
```

---

## 20. 결론

이번 논의의 결론은 다음과 같다.

```text
1. MCP는 AI agent가 외부 도구를 사용하기 위한 표준 연결 프로토콜이다.

2. MCP 자체는 무료/open-source 성격이지만, 사용하는 AI model/API/client에 따라 비용이 발생할 수 있다.

3. MCP는 큰 그림에서 n8n과 같은 자동화 세계관에 속하지만, n8n은 workflow engine이고 MCP는 AI-agent tool interface이다.

4. MCP를 활용한 논문과 preprint는 이미 등장하고 있지만, 대부분은 software tool integration, security, EDA automation 초기 단계에 머물러 있다.

5. 메시님이 생각하는 RTL simulation + Vivado + FPGA board test + measurement feedback 구조는 아직 차별화 여지가 크다.

6. MCP 자체를 novelty로 삼으면 약하지만, MCP 기반 closed-loop Hardware-in-the-Loop verification framework로 확장하면 논문/특허 주제로 가능성이 있다.

7. 가장 현실적인 시작점은 read-only MCP server → simulation MCP → Vivado report MCP → FPGA board-test MCP 순서이다.
```

최종적으로 목표로 삼을 수 있는 문장:

> **We propose an MCP-enabled closed-loop RTL-to-FPGA verification framework that integrates simulation results, synthesis/timing reports, and board-level measurement feedback to guide the next verification action.**

---

## 21. 다음 액션 아이템

```text
1. GitHub repository 생성
2. README.md 초안 작성
3. read-only MCP server 구현
4. Verilator/Icarus 실행 MCP tool 구현
5. 간단한 RTL block으로 compile-test-debug loop 실험
6. Simulation log parser 작성
7. Vivado timing report parser 추가
8. FPGA board UART/DMA test script 연결
9. 실험 metric 정의
10. 논문/특허 초안 작성
```

추천 첫 MVP:

```text
Target RTL:
Schmidl-Cox autocorrelation block 또는 AXI DMA memory-copy IP

First MCP tools:
- list_files()
- read_file()
- run_simulation()
- read_sim_log()
- parse_pass_fail()
- suggest_next_test()
```

