import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Unpivot Opp Data", layout="wide")
st.title("Unpivot Opps (Wide → Long)")

uploaded = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])

@st.cache_data(show_spinner=False)
def reshape_dec_audit(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(file_bytes))

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
        # No Category columns found
        return pd.DataFrame()

    df_long = pd.concat(rows, ignore_index=True)

    # Drop rows where Category Value is blank
    df_long = df_long.dropna(subset=["Category Value"])
    df_long = df_long[df_long["Category Value"].astype(str).str.strip() != ""]

    # Drop original wide columns
    drop_cols = [
        f"{prefix} {i}"
        for i in range(1, 10)
        for prefix in ["Category", "Per Call Price", "Monthly Flat Fee", "APF", "Books"]
    ]
    df_final = df_long.drop(columns=[c for c in drop_cols if c in df_long.columns])

    return df_final

if uploaded:
    file_bytes = uploaded.getvalue()

    with st.spinner("Reading & reshaping..."):
        df_final = reshape_dec_audit(file_bytes)

    if df_final.empty:
        st.error("No 'Category 1'...'Category 9' columns were found in this file.")
        st.stop()

    st.success(f"Done! Output rows: {len(df_final):,}")

    st.subheader("Preview")
    st.dataframe(df_final, use_container_width=True)

    # Download as Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_final.to_excel(writer, index=False, sheet_name="Done")
    output.seek(0)

    base_name = uploaded.name.rsplit(".", 1)[0]
    out_name = f"{base_name}-done.xlsx"

    st.download_button(
        label="Download reshaped Excel",
        data=output,
        file_name=out_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.info("Upload an Excel file to begin.")
