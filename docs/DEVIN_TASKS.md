# DEVIN_TASKS

이 저장소에서 Devin이 바로 수행할 태스크 묶음입니다.

## 0) 환경
- Python 3.11
- `pip install -r requirements.txt`

## 1) 기준선 검증
- [ ] AWGN + BPSK/QPSK에서 이론 BER( \(Q(\sqrt{2E_b/N_0})\) )과 시뮬 겹치게 하기
- [ ] 재현성: 시드 여러 개 평균(≥5), 95% CI 출력

## 2) 실험 세트
- [ ] 보간법 비교: `lin/quad/fft` × P={4,8,16,32}
- [ ] 등화기 비교: `zf` vs `mmse`
- [ ] 변조 스윕: BPSK/QPSK/16/64/256QAM
- [ ] 채널: `awgn`, `flatrayleigh`, `multipath`(CP≥taps-1)

## 3) 리포팅
- [ ] CSV/PNG 저장(폴더 구조: `results/{exp_id}/...`)
- [ ] README에 표/그림 업데이트, 실험 설정 JSON으로 아카이브

## 4) 추가 옵션
- [ ] PCSI 모드(완전 채널 지식) 추가 및 CE 대비 갭 분석
- [ ] 선형 위상 보정(a + b·k) 옵션
