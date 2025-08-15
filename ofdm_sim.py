#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OFDM link-level simulator (Python) with mmWave Beam Tracking
- Data modulation selectable (BPSK/QPSK/16/64/256QAM)
- FDM pilots (QPSK), complex interpolation (lin/quad/fft)
- ZF/MMSE equalization
- Channels: AWGN / flat Rayleigh / multipath Rayleigh / mmWave beam tracking
- EKF-based beam tracking for AoA/AoD estimation (based on ETK_Heath paper)
- Global pilot phase correction (optional)
- CLI with reproducible seed, outputs CSV & PNG
"""
import numpy as np
import matplotlib.pyplot as plt
import argparse
from pathlib import Path
from scipy.linalg import inv

# =======================
# Modulation library
# =======================
SCALE = {
    "BPSK"  : 1.0,
    "QPSK"  : 1/np.sqrt(2),
    "16QAM" : 1/np.sqrt(10),
    "64QAM" : 1/np.sqrt(42),
    "256QAM": 1/np.sqrt(170),
}

def get_mod(name: str):
    m = name.upper()
    if m == "BPSK":   return 1, bpsk_mod,  bpsk_demod
    if m == "QPSK":   return 2, qpsk_mod,  qpsk_demod
    if m == "16QAM":  return 4, qam16_mod, qam16_demod
    if m == "64QAM":  return 6, qam64_mod, qam64_demod
    if m == "256QAM": return 8, qam256_mod, qam256_demod
    raise ValueError("Unsupported modulation")

# --- BPSK ---
def bpsk_mod(bits):
    s = np.where(bits.astype(int)==0, +1.0, -1.0) * SCALE["BPSK"]
    return s.astype(complex)
def bpsk_demod(sym):
    return (sym.real < 0).astype(np.uint8)

# --- QPSK (demapper pair: b0=(I<0), b1=(Q<0)) ---
def qpsk_mod(bits):
    b = bits.reshape(-1, 2).astype(int)
    out = np.empty(len(b), dtype=complex)
    # 00:+1+1j, 10:-1+1j, 11:-1-1j, 01:+1-1j
    lut = {(0,0): 1+1j, (1,0): -1+1j, (1,1): -1-1j, (0,1): 1-1j}
    for i,(b0,b1) in enumerate(b):
        out[i] = lut[(b0,b1)]
    return out * SCALE["QPSK"]
def qpsk_demod(sym):
    bits = np.empty(2*len(sym), dtype=np.uint8)
    bits[0::2] = (sym.real < 0).astype(np.uint8)
    bits[1::2] = (sym.imag < 0).astype(np.uint8)
    return bits

# --- 16-QAM (Gray) ---
def _axis_gray_2b_to_level(b1,b0):  # (MSB,LSB)
    return { (0,0): +1, (0,1): +3, (1,1): -3, (1,0): -1 }[(b1,b0)]
def qam16_mod(bits):
    sc=SCALE["16QAM"]; b=bits.reshape(-1,4).astype(int)
    out=np.empty(len(b),dtype=complex)
    for i,(i1,i0,q1,q0) in enumerate(b):  # I:(i1,i0), Q:(q1,q0)
        I=_axis_gray_2b_to_level(i1,i0); Q=_axis_gray_2b_to_level(q1,q0)
        out[i]=(I+1j*Q)*sc
    return out
def qam16_demod(sym):
    sc=SCALE["16QAM"]; thr=np.array([-2*sc,0.0,2*sc])
    def slice2(x):
        if x>=thr[2]: return (0,1)
        if x>=thr[1]: return (0,0)
        if x>=thr[0]: return (1,0)
        return (1,1)
    bits=[]
    for z in sym:
        I,Q=z.real,z.imag
        i2=slice2(I); q2=slice2(Q)
        bits.extend([i2[0],i2[1],q2[0],q2[1]])
    return np.array(bits,dtype=np.uint8)

# --- 64-QAM (Gray) ---
_gray3 = {
    (1,1,0):-7, (1,1,1):-5, (1,0,1):-3, (1,0,0):-1,
    (0,0,0):+1, (0,0,1):+3, (0,1,1):+5, (0,1,0):+7,
}
def _gray3_to_level(b2,b1,b0): return _gray3[(b2,b1,b0)]
def qam64_mod(bits):
    sc=SCALE["64QAM"]; b=bits.reshape(-1,6).astype(int)
    out=np.empty(len(b),dtype=complex)
    for i,(i2,i1,i0,q2,q1,q0) in enumerate(b):
        I=_gray3_to_level(i2,i1,i0); Q=_gray3_to_level(q2,q1,q0)
        out[i]=(I+1j*Q)*sc
    return out
def qam64_demod(sym):
    sc=SCALE["64QAM"]; thr=sc*np.array([-6,-4,-2,0,2,4,6])
    def slice3(x):
        if x<thr[0]: return (1,1,0)
        if x<thr[1]: return (1,1,1)
        if x<thr[2]: return (1,0,1)
        if x<thr[3]: return (1,0,0)
        if x<thr[4]: return (0,0,0)
        if x<thr[5]: return (0,0,1)
        if x<thr[6]: return (0,1,1)
        return (0,1,0)
    bits=[]
    for z in sym:
        bits.extend(list(slice3(z.real))+list(slice3(z.imag)))
    return np.array(bits,dtype=np.uint8)

# --- 256-QAM (Gray) ---
_gray4 = {
    (1,1,0,0):-15,(1,1,0,1):-13,(1,1,1,1):-11,(1,1,1,0):-9,
    (1,0,1,0):-7, (1,0,1,1):-5, (1,0,0,1):-3, (1,0,0,0):-1,
    (0,0,0,0):+1, (0,0,0,1):+3, (0,0,1,1):+5, (0,0,1,0):+7,
    (0,1,1,0):+9, (0,1,1,1):+11,(0,1,0,1):+13,(0,1,0,0):+15,
}
def _gray4_to_level(b3,b2,b1,b0): return _gray4[(b3,b2,b1,b0)]
def qam256_mod(bits):
    sc=SCALE["256QAM"]; b=bits.reshape(-1,8).astype(int)
    out=np.empty(len(b),dtype=complex)
    for i,(i3,i2,i1,i0,q3,q2,q1,q0) in enumerate(b):
        I=_gray4_to_level(i3,i2,i1,i0); Q=_gray4_to_level(q3,q2,q1,q0)
        out[i]=(I+1j*Q)*sc
    return out
def qam256_demod(sym):
    sc=SCALE["256QAM"]; thr=sc*np.array([-14,-12,-10,-8,-6,-4,-2,0,2,4,6,8,10,12,14])
    def slice4(x):
        if x<thr[0]: return (1,1,0,0)
        if x<thr[1]: return (1,1,0,1)
        if x<thr[2]: return (1,1,1,1)
        if x<thr[3]: return (1,1,1,0)
        if x<thr[4]: return (1,0,1,0)
        if x<thr[5]: return (1,0,1,1)
        if x<thr[6]: return (1,0,0,1)
        if x<thr[7]: return (1,0,0,0)
        if x<thr[8]: return (0,0,0,0)
        if x<thr[9]: return (0,0,0,1)
        if x<thr[10]: return (0,0,1,1)
        if x<thr[11]: return (0,0,1,0)
        if x<thr[12]: return (0,1,1,0)
        if x<thr[13]: return (0,1,1,1)
        if x<thr[14]: return (0,1,0,1)
        return (0,1,0,0)
    bits=[]
    for z in sym:
        bits.extend(list(slice4(z.real))+list(slice4(z.imag)))
    return np.array(bits,dtype=np.uint8)

# =======================
# Pilot/Data index (unshifted axis)
# =======================
def get_data_pilot_indexes(n, num_pilots, last_pilot_as_data=False):
    step = n // num_pilots
    pilots = np.arange(0, n, step, dtype=int)  # 0, step, 2*step, ...
    if last_pilot_as_data and len(pilots) and pilots[-1]==n-1:
        pilots = pilots[:-1]
    mask = np.ones(n, dtype=bool); mask[pilots] = False
    data = np.nonzero(mask)[0]
    return data, pilots

# =======================
# Complex Interpolation
# =======================
def interp_linear(H, pilot_idx):
    x = np.arange(len(H))
    Hr = np.interp(x, pilot_idx, H[pilot_idx].real)
    Hi = np.interp(x, pilot_idx, H[pilot_idx].imag)
    return Hr + 1j*Hi

def interp_quadratic(H, pilot_idx):
    x = np.arange(len(H))
    cr = np.polyfit(pilot_idx, H[pilot_idx].real, 2)
    ci = np.polyfit(pilot_idx, H[pilot_idx].imag, 2)
    return np.polyval(cr, x) + 1j*np.polyval(ci, x)

def interp_fft(H, pilot_idx, n):
    # preconditions: equally spaced pilots starting at 0
    step = np.diff(pilot_idx)
    if not (len(pilot_idx)>=2 and np.all(step==step[0]) and pilot_idx[0]==0):
        raise ValueError("FFT interpolation requires equally spaced pilots starting at 0.")
    P = len(pilot_idx)
    Hp = H[pilot_idx]
    F  = np.fft.fft(Hp)
    zp = np.zeros(n-P, dtype=complex)
    Fz = np.concatenate([F[:P//2], zp, F[P//2:]])
    return np.fft.ifft(Fz) * (n / P)

def interpolate(H, pilot_idx, mode='lin'):
    m = mode.lower()
    if m=='lin' : return interp_linear(H, pilot_idx)
    if m=='quad': return interp_quadratic(H, pilot_idx)
    if m=='fft' : return interp_fft(H, pilot_idx, len(H))
    raise ValueError("INTERP must be 'lin'|'quad'|'fft'")

# =======================
# mmWave Beam Tracking (ETK_Heath paper)
# =======================

def ula_array_response(phi, M, d_lambda=0.5):
    """
    ULA array response vector for angle phi
    Args:
        phi: angle in radians
        M: number of antennas
        d_lambda: antenna spacing in wavelengths (default 0.5)
    Returns:
        array response vector a(phi)
    """
    k = 2 * np.pi * d_lambda  # 2π * d/λ
    indices = np.arange(M)
    phase_shifts = 1j * k * indices * np.cos(phi)
    return np.exp(phase_shifts) / np.sqrt(M)

def beamforming_gain(phi_true, phi_beam, M, d_lambda=0.5):
    """
    Calculate beamforming gain when beam points to phi_beam but true angle is phi_true
    Based on measurement function h(x[k]; φ̄) from ETK_Heath paper equation (10)
    """
    k = 2 * np.pi * d_lambda
    phi_diff = np.cos(phi_true) - np.cos(phi_beam)
    
    if np.abs(phi_diff) < 1e-12:
        return 1.0  # Perfect alignment
    
    numerator = 1 - np.exp(1j * M * k * phi_diff)
    denominator = 1 - np.exp(1j * k * phi_diff)
    return np.abs(numerator / denominator) / M

class BeamTracker:
    """
    EKF-based beam tracker for AoA/AoD estimation
    State vector: x = [αR, αI, φA, φD]^T
    """
    
    def __init__(self, rho=0.995, sigma_angle_deg=0.5, sigma_v=1.0):
        self.rho = rho  # correlation coefficient for path gain
        self.sigma_angle = np.deg2rad(sigma_angle_deg)  # angle process noise std
        self.sigma_v = sigma_v  # measurement noise std
        
        self.F = np.diag([rho, rho, 1.0, 1.0])
        
        self.Q = np.diag([
            (1 - rho**2) / 2,  # αR variance
            (1 - rho**2) / 2,  # αI variance  
            self.sigma_angle**2,  # φA variance
            self.sigma_angle**2   # φD variance
        ])
        
        self.x = np.zeros(4)  # [αR, αI, φA, φD]
        self.P = self.Q.copy()  # Initial covariance P₀|₋₁ = Σᵤ
        
    def initialize(self, alpha_init, phi_A_init, phi_D_init):
        """Initialize tracker with estimated values"""
        self.x[0] = alpha_init.real
        self.x[1] = alpha_init.imag
        self.x[2] = phi_A_init
        self.x[3] = phi_D_init
        
    def predict(self):
        """EKF prediction step"""
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        
    def measurement_function(self, phi_beam_A, phi_beam_D, Nr=16, Nt=16):
        """
        Measurement function h(x[k]; φ̄) from ETK_Heath paper equation (10)
        """
        alpha = self.x[0] + 1j * self.x[1]
        phi_A = self.x[2]
        phi_D = self.x[3]
        
        gain_A = beamforming_gain(phi_A, phi_beam_A, Nr)
        gain_D = beamforming_gain(phi_D, phi_beam_D, Nt)
        
        return alpha * gain_A * gain_D
        
    def measurement_jacobian(self, phi_beam_A, phi_beam_D, Nr=16, Nt=16):
        """
        Compute Jacobian H = ∇h/∇x for EKF update
        """
        eps = 1e-6
        H = np.zeros((2, 4))  # 2 outputs (real, imag) x 4 states
        
        h_nominal = self.measurement_function(phi_beam_A, phi_beam_D, Nr, Nt)
        
        for i in range(4):
            x_pert = self.x.copy()
            x_pert[i] += eps
            h_pert = self.measurement_function_state(x_pert, phi_beam_A, phi_beam_D, Nr, Nt)
            dh = (h_pert - h_nominal) / eps
            H[0, i] = dh.real
            H[1, i] = dh.imag
            
        return H
        
    def measurement_function_state(self, x, phi_beam_A, phi_beam_D, Nr=16, Nt=16):
        """Helper function for numerical derivatives"""
        alpha = x[0] + 1j * x[1]
        phi_A = x[2]
        phi_D = x[3]
        
        gain_A = beamforming_gain(phi_A, phi_beam_A, Nr)
        gain_D = beamforming_gain(phi_D, phi_beam_D, Nt)
        
        return alpha * gain_A * gain_D
        
    def update(self, measurement, phi_beam_A, phi_beam_D, Nr=16, Nt=16):
        """EKF measurement update step"""
        h_pred = self.measurement_function(phi_beam_A, phi_beam_D, Nr, Nt)
        
        y_pred = np.array([h_pred.real, h_pred.imag])
        y_meas = np.array([measurement.real, measurement.imag])
        residual = y_meas - y_pred
        
        H = self.measurement_jacobian(phi_beam_A, phi_beam_D, Nr, Nt)
        
        R = np.eye(2) * self.sigma_v**2
        S = H @ self.P @ H.T + R
        
        K = self.P @ H.T @ inv(S)
        
        self.x = self.x + K @ residual
        
        I = np.eye(4)
        self.P = (I - K @ H) @ self.P
        
        return residual, S  # Return for tracking performance metrics

def mmwave_beamtrack_channel(x_cp, beam_tracker, phi_beam_A, phi_beam_D, 
                           pilot_measurement, Nr=16, Nt=16, rng=None):
    """
    mmWave channel with beam tracking
    """
    beam_tracker.predict()
    
    alpha = beam_tracker.x[0] + 1j * beam_tracker.x[1]
    phi_A_true = beam_tracker.x[2]
    phi_D_true = beam_tracker.x[3]
    
    gain_A = beamforming_gain(phi_A_true, phi_beam_A, Nr)
    gain_D = beamforming_gain(phi_D_true, phi_beam_D, Nt)
    total_gain = alpha * gain_A * gain_D
    
    y_cp = total_gain * x_cp
    
    if pilot_measurement is not None:
        residual, S = beam_tracker.update(pilot_measurement, phi_beam_A, phi_beam_D, Nr, Nt)
        tracking_mse = np.trace(beam_tracker.P[2:4, 2:4])  # MSE of angle estimates
    else:
        residual = None
        S = None
        tracking_mse = np.trace(beam_tracker.P[2:4, 2:4])
    
    tracking_metrics = {
        'state': beam_tracker.x.copy(),
        'covariance': beam_tracker.P.copy(),
        'mse_angles': tracking_mse,
        'residual': residual,
        'innovation_cov': S
    }
    
    return y_cp, tracking_metrics

# =======================
# Channel & Equalizer
# =======================
def add_awgn(x, ebn0_db, n, cp, bps, plt_loss=1.0):
    """
    Map Eb/N0 (info-bit based if plt_loss < 1) -> Es/N0 and add complex AWGN.
    Es/N0 = Eb/N0 * bps * (N/(N+CP)) * plt_loss
    """
    ebn0 = 10**(ebn0_db/10)
    esn0 = ebn0 * bps * (n/(n+cp)) * plt_loss
    sig_pow = np.mean(np.abs(x)**2)
    noise_pow = sig_pow / max(esn0, 1e-12)
    w = (np.random.normal(size=x.shape) + 1j*np.random.normal(size=x.shape)) * np.sqrt(noise_pow/2)
    return x + w

def flat_rayleigh_gain(rng):
    return (rng.normal() + 1j*rng.normal())/np.sqrt(2)

def gen_multipath_taps(taps, pdp_decay, rng):
    pdp = np.exp(-pdp_decay*np.arange(taps))
    g = (rng.normal(taps)+1j*rng.normal(taps))/np.sqrt(2)
    h = g*np.sqrt(pdp)
    h = h/np.linalg.norm(h)  # unit energy
    return h

def apply_multipath(x_cp, taps):
    return np.convolve(x_cp, taps, mode='full')[:len(x_cp)]

def equalize(Y, Hest, ebn0_db, bps, n, cp, method='mmse'):
    m=method.lower()
    if m=='zf':
        denom = Hest
        denom = np.where(np.abs(denom)<1e-12, 1e-12+0j, denom)
        return Y / denom
    # mmse
    ebn0 = 10**(ebn0_db/10)
    esn0 = ebn0 * bps * (n/(n+cp))
    denom = (np.abs(Hest)**2 + 1.0/max(esn0,1e-12))
    denom = np.where(denom<1e-15, 1e-15, denom)
    return Y * np.conj(Hest) / denom

# =======================
# Simulation
# =======================
def simulate(
    EbN0_list,
    data_mod="QPSK",
    N=64, CP=16, NUM_PILOTS=8, NUM_BLOCKS=400,
    channel='awgn', interp='lin', eq='mmse',
    use_global_phase_corr=True,
    taps=5, pdp_decay=0.5, fading_per_block=True,
    seed=2025, ebn0_def="raw",   # "raw" or "info" (pilot overhead)
    save_csv=None, save_png=None,
    Nr=16, Nt=16, rho=0.995, sigma_angle_deg=0.5,
    phi_A_init=np.pi/4, phi_D_init=np.pi/4, alpha_init=1.0+0j
):
    rng = np.random.default_rng(seed)
    bps, mod_fn, demod_fn = get_mod(data_mod)
    last_pilot_as_data = (interp.lower()=='fft')
    data_idx, pilot_idx = get_data_pilot_indexes(N, NUM_PILOTS, last_pilot_as_data)

    # pilot loss factor (info-bit Eb/N0 definition)
    plt_loss = (len(data_idx)/N) if ebn0_def.lower()=="info" else 1.0

    # pilots = QPSK fixed
    pilot_bits = rng.integers(0,2, NUM_PILOTS*2, dtype=np.uint8)
    pilots = qpsk_mod(pilot_bits)

    ber=[]
    mse_angles=[]
    tracking_duration=NUM_BLOCKS
    
    if channel == 'mmwave':
        beam_tracker = BeamTracker(rho=rho, sigma_angle_deg=sigma_angle_deg)
        beam_tracker.initialize(alpha_init, phi_A_init, phi_D_init)
        tracking_metrics_list = []
    
    for eb in EbN0_list:
        errs=tots=0
        for _ in range(NUM_BLOCKS):
            # --- TX ---
            tx_bits = rng.integers(0,2, len(data_idx)*bps, dtype=np.uint8)
            data_syms = mod_fn(tx_bits)

            X = np.zeros(N, dtype=complex)
            X[pilot_idx] = pilots
            X[data_idx]  = data_syms

            x_time = np.fft.ifft(X)
            x_cp = np.concatenate([x_time[-CP:], x_time])

            # --- Channel ---
            if channel=='awgn':
                y_cp = add_awgn(x_cp, eb, N, CP, bps, plt_loss=plt_loss)
            elif channel=='flatrayleigh':
                g = flat_rayleigh_gain(rng)
                y_cp = add_awgn(g*x_cp, eb, N, CP, bps, plt_loss=plt_loss)
            elif channel=='multipath':
                h = gen_multipath_taps(taps, pdp_decay, rng) if fading_per_block or not 'h' in locals() else h
                y_cp = add_awgn(apply_multipath(x_cp, h), eb, N, CP, bps, plt_loss=plt_loss)
            elif channel=='mmwave':
                y_cp, tracking_metrics = mmwave_beamtrack_channel(
                    x_cp, beam_tracker, phi_A_init, phi_D_init, 
                    None, Nr, Nt, rng
                )
                y_cp = add_awgn(y_cp, eb, N, CP, bps, plt_loss=plt_loss)
                tracking_metrics_list.append(tracking_metrics)
            else:
                raise ValueError("channel must be 'awgn'|'flatrayleigh'|'multipath'|'mmwave'")

            # --- RX ---
            y = y_cp[CP:CP+N]
            Y = np.fft.fft(y)

            # (1) global pilot phase correction
            if use_global_phase_corr:
                phase_err = np.angle(np.sum(Y[pilot_idx] * np.conj(pilots)))
                Y *= np.exp(-1j * phase_err)

            # (2) channel estimation at pilots
            Hest = np.zeros(N, dtype=complex)
            Hest[pilot_idx] = Y[pilot_idx] / pilots
            
            if channel == 'mmwave':
                pilot_measurement = np.mean(Hest[pilot_idx])
                beam_tracker.update(pilot_measurement, phi_A_init, phi_D_init, Nr, Nt)

            # (3) interpolation
            Hest_full = interpolate(Hest, pilot_idx, mode=interp)

            # (4) equalization
            Y_eq = equalize(Y, Hest_full, eb, bps, N, CP, method=eq)

            # (5) demod (data carriers only)
            rx_bits = demod_fn(Y_eq[data_idx])
            errs += np.sum(rx_bits != tx_bits)
            tots += rx_bits.size

        ber.append(errs/tots)
        
        if channel == 'mmwave':
            block_mse = np.mean([m['mse_angles'] for m in tracking_metrics_list])
            mse_angles.append(block_mse)
            tracking_metrics_list = []  # Reset for next SNR point

    ber = np.array(ber)
    if channel == 'mmwave':
        mse_angles = np.array(mse_angles)

    # save CSV / plot
    if save_csv:
        import csv
        with open(save_csv, "w", newline="") as f:
            w = csv.writer(f)
            if channel == 'mmwave':
                w.writerow(["EbN0_dB","BER","MSE_angles","tracking_duration"])
                for e, b, m in zip(EbN0_list, ber, mse_angles):
                    w.writerow([e, b, m, tracking_duration])
            else:
                w.writerow(["EbN0_dB","BER"])
                for e, b in zip(EbN0_list, ber):
                    w.writerow([e, b])

    if save_png:
        import matplotlib.pyplot as plt
        if channel == 'mmwave':
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))
            ax1.semilogy(EbN0_list, ber, marker='o', label=f"{data_mod}, {channel}, {eq}, {interp}")
            ax1.grid(True, which='both')
            ax1.set_xlabel("Eb/N0 (dB)")
            ax1.set_ylabel("BER")
            ax1.set_title("OFDM BER vs Eb/N0")
            ax1.legend()
            
            ax2.semilogy(EbN0_list, mse_angles, marker='s', label="Beam Tracking MSE")
            ax2.grid(True, which='both')
            ax2.set_xlabel("Eb/N0 (dB)")
            ax2.set_ylabel("Angle MSE (rad²)")
            ax2.set_title("Beam Tracking Performance")
            ax2.legend()
            
            plt.tight_layout()
            plt.savefig(save_png, dpi=150, bbox_inches="tight")
            plt.close()
        else:
            plt.figure()
            plt.semilogy(EbN0_list, ber, marker='o', label=f"{data_mod}, {channel}, {eq}, {interp}")
            plt.grid(True, which='both')
            plt.xlabel("Eb/N0 (dB)")
            plt.ylabel("BER")
            plt.title("OFDM BER vs Eb/N0")
            plt.legend()
            plt.savefig(save_png, dpi=150, bbox_inches="tight")
            plt.close()

    if channel == 'mmwave':
        return ber, mse_angles
    else:
        return ber

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mod", default="QPSK", choices=["BPSK","QPSK","16QAM","64QAM","256QAM"])
    p.add_argument("--N", type=int, default=64)
    p.add_argument("--cp", type=int, default=16)
    p.add_argument("--pilots", type=int, default=8)
    p.add_argument("--blocks", type=int, default=400)
    p.add_argument("--snr", type=str, default="0,5,10,15,20")
    p.add_argument("--channel", default="awgn", choices=["awgn","flatrayleigh","multipath","mmwave"])
    p.add_argument("--interp", default="lin", choices=["lin","quad","fft"])
    p.add_argument("--eq", default="mmse", choices=["zf","mmse"])
    p.add_argument("--no-phasecorr", action="store_true", help="disable global pilot phase correction")
    p.add_argument("--taps", type=int, default=5)
    p.add_argument("--pdp_decay", type=float, default=0.5)
    p.add_argument("--fading_per_block", action="store_true", default=True)
    p.add_argument("--seed", type=int, default=2025)
    p.add_argument("--ebn0_def", default="raw", choices=["raw","info"],
                   help="'info' multiplies Es/N0 by (N_data/N) to reflect pilot overhead")
    p.add_argument("--Nr", type=int, default=16, help="number of receive antennas")
    p.add_argument("--Nt", type=int, default=16, help="number of transmit antennas")
    p.add_argument("--rho", type=float, default=0.995, help="path gain correlation coefficient")
    p.add_argument("--sigma_angle", type=float, default=0.5, help="angle process noise std (degrees)")
    p.add_argument("--phi_A_init", type=float, default=45.0, help="initial AoA (degrees)")
    p.add_argument("--phi_D_init", type=float, default=45.0, help="initial AoD (degrees)")
    p.add_argument("--outdir", default=".", help="directory to write CSV/PNG")
    args = p.parse_args()

    EbN0_dB = np.array([float(x) for x in args.snr.split(",")])
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / f"ber_{args.mod}_{args.channel}_{args.eq}_{args.interp}.csv"
    png_path = outdir / f"ber_{args.mod}_{args.channel}_{args.eq}_{args.interp}.png"

    result = simulate(
        EbN0_list=EbN0_dB,
        data_mod=args.mod,
        N=args.N, CP=args.cp, NUM_PILOTS=args.pilots, NUM_BLOCKS=args.blocks,
        channel=args.channel, interp=args.interp, eq=args.eq,
        use_global_phase_corr=not args.no_phasecorr,
        taps=args.taps, pdp_decay=args.pdp_decay, fading_per_block=args.fading_per_block,
        seed=args.seed, ebn0_def=args.ebn0_def,
        save_csv=str(csv_path), save_png=str(png_path),
        Nr=args.Nr, Nt=args.Nt, rho=args.rho, sigma_angle_deg=args.sigma_angle,
        phi_A_init=np.deg2rad(args.phi_A_init), phi_D_init=np.deg2rad(args.phi_D_init),
        alpha_init=1.0+0j
    )
    if args.channel == 'mmwave':
        ber, mse_angles = result
        print("Eb/N0(dB):", EbN0_dB)
        print("BER     :", ber)
        print("MSE     :", mse_angles)
        print("Saved:", csv_path, png_path)
    else:
        ber = result
        print("Eb/N0(dB):", EbN0_dB)
        print("BER     :", ber)
        print("Saved:", csv_path, png_path)

if __name__ == "__main__":
    main()
