import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO

st.set_page_config(page_title="ラウンジ管理アプリ", layout="wide")

st.title("ラウンジ管理アプリ")

# -------------------------
# キャストマスタ
# -------------------------

CAST_MASTER = {
    "まりか": {"時給": 2000, "ドリンク単価": 200},
    "みのり": {"時給": 1800, "ドリンク単価": 200},
    "あや": {"時給": 1500, "ドリンク単価": 200},
    "ゆり": {"時給": 1500, "ドリンク単価": 200},
    "おと": {"時給": 1400, "ドリンク単価": 200},
    "とうこ": {"時給": 1400, "ドリンク単価": 200},
    "はづき": {"時給": 1400, "ドリンク単価": 200},
    "しの": {"時給": 1400, "ドリンク単価": 200},
    "はる": {"時給": 1400, "ドリンク単価": 200},
    "JP": {"時給": 1200, "ドリンク単価": 0},
    "ゆいか": {"時給": 1200, "ドリンク単価": 0},
    "なつき": {"時給": 1000, "ドリンク単価": 0},
    "みやこ": {"時給": 1200, "ドリンク単価": 0},
}

# -------------------------
# データ保存
# -------------------------

if "records" not in st.session_state:
    st.session_state.records = []

# =========================
# ① 日付
# =========================

work_date = st.date_input("① 日付", value=date.today())

# =========================
# ② 店の売上（先に入力）
# =========================

st.subheader("② 店の売上")

# 初期値
if "group_count" not in st.session_state:
    st.session_state.group_count = 1

# 組追加ボタン
if st.button("＋組を追加"):
    st.session_state.group_count += 1

sales_total = 0
card_sales = 0

for i in range(st.session_state.group_count):

    col1, col2 = st.columns([2, 1])

    with col1:
        sales = st.number_input(
            f"{i+1}組目売上",
            min_value=0,
            value=0,
            step=1000,
            key=f"group_sales_{i}"
        )

    with col2:
        payment = st.selectbox(
            f"{i+1}組目支払",
            ["現金", "カード"],
            key=f"payment_{i}"
        )

    sales_total += sales

    if payment == "カード":
        card_sales += sales

cash_sales = sales_total - card_sales

st.metric(
    "売上合計",
    f"{sales_total:,} 円"
)

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "カード売上",
        f"{card_sales:,} 円"
    )

with col2:
    st.metric(
        "現金売上",
        f"{cash_sales:,} 円"
    )

# =========================
# ③ 出勤者選択（複数）
# =========================

st.subheader("③ 出勤キャスト")

casts = st.multiselect(
    "出勤者を選択",
    list(CAST_MASTER.keys())
)

# =========================
# ④ 共通入力（全員同じ扱い）
# =========================

st.subheader("④ 給与計算")

results = []

for c in casts:

    st.markdown(f"### {c}")

    if f"hour_{c}" not in st.session_state:
        st.session_state[f"hour_{c}"] = 0.0

    if f"drink_{c}" not in st.session_state:
        st.session_state[f"drink_{c}"] = 0

    if f"champ_{c}" not in st.session_state:
        st.session_state[f"champ_{c}"] = 0

    work_hours = st.number_input(
        f"{c} 勤務時間",
        min_value=0.0,
        step=0.5,
        key=f"hour_{c}"
    )

    drink_count = st.number_input(
        f"{c} ドリンク数",
        min_value=0,
        key=f"drink_{c}"
    )

    champ = st.number_input(
    f"{c} シャンパンバック金額",
    min_value=0,
    step=100,
    key=f"champ_{c}"
    )

    m = CAST_MASTER[c]

    base = work_hours * m["時給"]
    drink = drink_count * m["ドリンク単価"]

    total = base + drink + champ

    results.append({
        "キャスト": c,
        "勤務時間": work_hours,
        "基本給": base,
        "ドリンクバック": drink,
        "シャンパンバック": champ,
        "給与": total
    })

# =========================
# ⑤ 給与計算
# =========================

st.subheader("⑤ 給与計算結果")

df_result = pd.DataFrame(results)

st.dataframe(df_result, use_container_width=True)

# =========================
# 登録
# =========================

if st.button("登録"):

    for r in results:

        st.session_state.records.append({
            "日付": str(work_date),
            "キャスト": r["キャスト"],
            "売上": sales_total,
            "カード売上": card_sales,
            "勤務時間": r["勤務時間"],
            "給与": r["給与"]
        })

    st.success("登録完了")

    # 入力クリア
    for k in list(st.session_state.keys()):

        if (
            k.startswith("group_")
            or k.startswith("hour_")
            or k.startswith("drink_")
            or k.startswith("champ_")
        ):
            del st.session_state[k]

    st.session_state.group_count = 1

    st.rerun()

    st.header("登録データ削除")

for i, record in enumerate(st.session_state.records):

    col1, col2 = st.columns([5, 1])

    with col1:
        st.write(
            f"{record['日付']} "
            f"{record['キャスト']} "
            f"{record['給与']:,}円"
        )

    with col2:
        if st.button("削除", key=f"delete_{i}"):

            st.session_state.records.pop(i)

            st.rerun()

# =========================
# 集計
# =========================

if st.session_state.records:

    df = pd.DataFrame(st.session_state.records)

    st.divider()

    st.header("登録一覧")
    st.dataframe(df, use_container_width=True)

    st.header("人件費合計")

    st.metric("総人件費", f"{df['給与'].sum():,} 円")

    st.header("キャスト別出勤日数")

    summary = df.groupby("キャスト").agg(
        出勤日数=("日付", "nunique"),
        給与合計=("給与", "sum"),
        売上合計=("売上", "sum")
    ).reset_index()

    st.dataframe(summary, use_container_width=True)
    
    # =========================
    # Excel出力
    # =========================

    st.header("Excel出力")

    excel_buffer = BytesIO()

    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:

        df.to_excel(
        writer,
        sheet_name="登録一覧",
        index=False
        )

        summary.to_excel(
        writer,
        sheet_name="キャスト集計",
        index=False
        )

    excel_buffer.seek(0)

    st.download_button(
    label="Excelダウンロード",
    data=excel_buffer,
    file_name=f"給与集計_{work_date}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )