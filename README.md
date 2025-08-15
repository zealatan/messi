# OFDM Simulator (Python)

논문용 링크 레벨 시뮬레이터 베이스라인입니다.

- 데이터 변조: **BPSK / QPSK / 16QAM / 64QAM / 256QAM**
- 파일럿: **QPSK FDM**
- 보간: **복소 보간** (lin/quad/fft)
- 등화: **ZF / MMSE**
- 채널: **AWGN / 평탄 Rayleigh / 다중경로 Rayleigh**
- 전역 위상 보정(파일럿 기반) 옵션

## 빠른 실행

```bash
pip install -r requirements.txt

python ofdm_sim.py \
  --mod QPSK --channel awgn --interp lin --eq mmse \
  --N 64 --cp 16 --pilots 8 --blocks 400 \
  --snr 0,5,10,15,20 --seed 2025 \
  --ebn0_def raw \
  --outdir results
```

출력: `results/ber_*.csv`, `artifacts/ber_*.png`

## 파라미터

- `--mod`: 데이터 변조 (파일럿은 QPSK 고정)
- `--channel`: `awgn`, `flatrayleigh`, `multipath`
- `--interp`: `lin`, `quad`, `fft` (FFT는 등간격·0시작 파일럿 전제)
- `--eq`: `zf`, `mmse`
- `--snr`: 콤마 구분 Eb/N0(dB) 리스트
- `--ebn0_def`: `raw`(오버헤드 무시) / `info`(파일럿 오버헤드 반영: N_data/N)
- `--blocks`: SNR 포인트당 프레임 수 (통계 안정성을 위해 크게)
- `--seed`: 재현성

## 주의/권장 사항

- **복소 보간**으로 구현되어 위상 보존됩니다.
- **전역 위상 보정 후 추정**으로 `Y`와 `Hest` 기준을 일치시킵니다.
- **MMSE** 분모에 작은 epsilon을 넣어 수치적으로 안정화.
- Multipath 채널에서 **CP ≥ taps-1** 권장.
- 논문에서는 `ebn0_def` 정의(파일럿 오버헤드 포함 여부)를 **명확히** 표기하세요.

## 개발자가 해야 할 일 (Devin 브리프)

- [ ] AWGN 이론 BER(Q-함수)과 시뮬 결과 비교 플롯 (±0.2 dB 이내)
- [ ] 보간법/파일럿 수 스윕 실험 (lin/quad/fft × P in {4,8,16,32})
- [ ] ZF vs MMSE 비교 (고/저 SNR)
- [ ] 변조 스윕(BPSK~256QAM), PCSI vs CE 갭 (PCSI 모드 추가)
- [ ] CI에서 다중 시드 평균 + 95% CI 산출, CSV/PNG 아카이브

## 라이선스

MIT
