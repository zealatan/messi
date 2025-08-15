import os, glob, numpy as np, matplotlib.pyplot as plt
plt.rcParams["figure.dpi"] = 140

def read_xy(path):
    data = np.genfromtxt(path, delimiter=',', names=True, dtype=None, encoding='utf-8')
    
    x_candidates = ["ebn0_db", "ebn0db", "ebn0", "snrdb", "snr_db"]
    x_col = None
    for candidate in x_candidates:
        for field in data.dtype.names:
            if field.lower().replace("_","").replace("/","") == candidate.replace("_",""):
                x_col = field
                break
        if x_col:
            break
    
    y_candidates = ["ber"]
    y_col = None
    for candidate in y_candidates:
        for field in data.dtype.names:
            if field.lower().replace("_","").replace("/","") == candidate.replace("_",""):
                y_col = field
                break
        if y_col:
            break
    
    if x_col is None or y_col is None:
        raise ValueError(f"Bad columns: {data.dtype.names}")
    
    return data[x_col], data[y_col]

def plot_mod(mod, root="results/eq_compare_awgn_corrected"):
    curves=[]
    for eq in ["zf","mmse"]:
        pats = sorted(glob.glob(os.path.join(root, mod, eq, f"*.csv")))
        if not pats: continue
        x,y = read_xy(pats[0])
        curves.append((eq.upper(), x, y))
    if not curves: return
    plt.figure()
    for label,x,y in curves:
        plt.semilogy(x,y,marker='o',label=label)
    plt.grid(True, which="both", ls="--", alpha=0.4)
    plt.xlabel("Eb/N0 (dB)"); plt.ylabel("BER")
    plt.title(f"{mod}: ZF vs MMSE (AWGN channel)")
    plt.legend()
    outpng=os.path.join(root, mod, f"overlay_{mod}_ZF_vs_MMSE_awgn_corrected.png")
    plt.savefig(outpng, bbox_inches="tight")
    print(f"[OK] {outpng}")

for m in ["QPSK","16QAM","64QAM","256QAM"]:
    plot_mod(m)
