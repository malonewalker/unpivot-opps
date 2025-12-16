import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Unpivot Opp Data", layout="wide")
st.title("Unpivot Opps (Wide → Long)")

uploaded = st.file_uploader("Upload Excel or CSV", type=["xlsx", "xls", "csv"])

@st.cache_data(show_spinner=False)
def load_dataframe(file_bytes: bytes, filename: str) -> pd.DataFrame:
    name = (filename or "").lower()

    if name.endswith(".csv"):
        # robust defaults for common CSV weirdness
        return pd.read_csv(io.BytesIO(file_bytes))
    elif name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
    else:
        raise ValueError("Unsupported file type. Please upload .csv, .xlsx, or .xls")

@st.cache_data(show_spinner=False)
def reshape_dec_audit(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i in range(1, 10):
        cat_col = f"Category {i}"
        pcp_col = f"Per Call Price {i}"
        mff_col = f"Monthly Flat Fee {i}"
        apf_col = f"APF {i}"
        bks_col = f"Books {i}"

        if cat_col not in df.columns:
            continue

        temp = df.copy()
        temp["Source Category Column"] = cat_col
        temp["Category Value"] = temp[cat_col]
        temp["Per Call Price"] = temp[pcp_col] if pcp_col in df.columns else None
        temp["Monthly Flat Fee"] = temp[mff_col] if mff_col in df.columns else None
        temp["APF"] = temp[apf_col] if apf_col in df.columns else None
        temp["Books"] = temp[bks_col] if bks_col in df.columns else None

        rows.append(temp)

    if not rows:
        return pd.DataFrame()

    df_long = pd.concat(rows, ignore_index=True)

    df_long = df_long.dropna(subset=["Category Value"])
    df_long = df_long[df_long["Category Value"].astype(str).str.strip() != ""]

    drop_cols = [
        f"{prefix} {i}"
        for i in range(1, 10)
        for prefix in ["Category", "Per Call Price", "Monthly Flat Fee", "APF", "Books"]
    ]
    return df_long.drop(columns=[c for c in drop_cols if c in df_long.columns])


if uploaded:
    file_bytes = uploaded.getvalue()

    with st.spinner("Loading file..."):
        df = load_dataframe(file_bytes, uploaded.name)

    with st.spinner("Reshaping..."):
        df_final = reshape_dec_audit(df)

    if df_final.empty:
        st.error("No 'Category 1'...'Category 9' columns were found in this file.")
        st.stop()

    st.success(f"Done! Output rows: {len(df_final):,}")
    st.dataframe(df_final, use_container_width=True)

    # Download as CSV (works great for both input types)
    out_csv = df_final.to_csv(index=False).encode("utf-8")
    base = uploaded.name.rsplit(".", 1)[0]
    st.download_button(
        "Download output CSV",
        data=out_csv,
        file_name=f"{base}-done.csv",
        mime="text/csv",
    )

    # Optional: also offer Excel download
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_final.to_excel(writer, index=False, sheet_name="Done")
    output.seek(0)
    st.download_button(
        "Download output Excel",
        data=output,
        file_name=f"{base}-done.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.info("Upload a file to begin.")
