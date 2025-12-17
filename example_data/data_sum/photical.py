import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def plot_ratio_bars(
    xlsx_path: str = "electroopitcal.xlsx",
    sheet_name=0,
    source: int | None = None,
    out_path: str = "ratio_bars.png",
    dpi: int = 300
):
    
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)

    def _norm(s): 
        return str(s).strip().lower().replace(" ", "").replace("-", "").replace("_", "")

    cols_norm = {_norm(c): c for c in df.columns}

    name_col   = cols_norm.get("name", cols_norm.get("molecule", list(df.columns)[0]))
    exp_col    = cols_norm.get("exp",  list(df.columns)[1])
    source_col = cols_norm.get("source", list(df.columns)[2])

    if df.shape[1] >= 9:
        func_cols = list(df.columns[3:9]) 
    else:
        candidates = ["B3LYP","PBE0","M062X","wb97XD","cam-B3LYP","MP2"]
        func_cols = [c for c in df.columns if str(c).split()[0] in candidates]

        order_map = {k:i for i,k in enumerate(candidates)}
        func_cols.sort(key=lambda x: order_map.get(str(x).split()[0], 999))

    cols_needed = [name_col, exp_col, source_col] + func_cols
    df = df[cols_needed].copy()

    if source is not None:
        df = df[df[source_col].astype(str) == str(source)]
        if df.empty:
            raise ValueError(f"no source={source} data。")

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=[exp_col])

    ratio_df = df.copy()
    for c in func_cols:
        ratio_df[c] = ratio_df[c] / ratio_df[exp_col]

    long = ratio_df.melt(
        id_vars=[name_col, source_col, exp_col],
        value_vars=func_cols,
        var_name="Functional",
        value_name="Ratio"
    )

    molecules = long[name_col].astype(str).unique().tolist()
    F = func_cols
    n_groups = len(molecules)
    n_funcs  = len(F)

    bar_w = 0.12
    group_w = n_funcs * bar_w + 0.12 

    x_centers = np.arange(n_groups) * group_w
    fig = plt.figure(figsize=(max(10, n_groups * 1.4), 6))

    colors = [
       "#5a9bd4", 
       "#ec7d33",  
       "#a5a5a5", 
       "#fec000", 
       "#4472c4", 
       "#70ad47", 
    ]
    
    for i, func in enumerate(F):
        sub = long[long["Functional"] == func]
        sub = sub.set_index(name_col).reindex(molecules)
        y = sub["Ratio"].values.astype(float)
        x = x_centers + (i - (n_funcs-1)/2) * bar_w
        plt.bar(x, y, width=bar_w, label=str(func), color=colors[i % len(colors)])


    plt.axhline(y=1.0, color='gray', linestyle='--', linewidth=1)
    plt.xticks(x_centers, molecules, rotation=30, ha="right")
    plt.ylabel(r"$\beta_{\mathrm{cal}}/\beta_{\mathrm{exp}}$", fontweight='bold')
    plt.title("Ratios by Molecule (grouped by Functional)")
    plt.legend(ncol=min(n_funcs, 6), frameon=False)
    plt.tight_layout()
    plt.savefig(out_path, dpi=dpi)
    print(f"Saved figure to: {Path(out_path).resolve()}")

def main():
    parser = argparse.ArgumentParser(description="Plot (D..I)/B grouped bar chart from Excel.")
    parser.add_argument("--file", default="electroopitcal.xlsx", help="Excel file path")
    parser.add_argument("--sheet", default=0, help="Sheet name or index")
    parser.add_argument("--source", type=int, default=None, help="Filter rows by source value (e.g., 1)")
    parser.add_argument("--out", default="ratio_bars.png", help="Output image path")
    parser.add_argument("--dpi", type=int, default=300, help="Figure DPI")
    args = parser.parse_args()
    
    out_name = args.out
    if args.source is not None:
        stem, ext = Path(args.out).stem, Path(args.out).suffix
        out_name = f"{stem}{args.source}{ext}"

    plot_ratio_bars(
        xlsx_path=args.file,
        sheet_name=args.sheet,
        source=args.source,
        out_path=out_name,
        dpi=args.dpi
    )

if __name__ == "__main__":
    main()
