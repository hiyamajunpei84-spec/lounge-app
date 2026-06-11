import streamlit as st
import pandas as pd
import sqlite3
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

conn = sqlite3.connect(
    "lounge.db",
    check_same_thread=False
)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_date TEXT,
    cast_name TEXT,
    sales INTEGER,
    card_sales INTEGER,
    work_hours REAL,
    salary INTEGER
)
""")

conn.commit()


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
# =========================
# 登録
# =========================

if st.button("登録"):

    for r in results:

        cursor.execute("""
        INSERT INTO records
        (work_date, cast_name, sales, card_sales, work_hours, salary)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(work_date),
            r["キャスト"],
            sales_total,
            card_sales,
            r["勤務時間"],
            r["給与"]
        ))

    conn.commit()

    st.success("登録完了")

    st.rerun()



# =========================
# 集計・データ一覧（選択された日付のみにフィルター）
# =========================
# SQLのWHERE句を使って、画面上部で選択された日付（work_date）のデータだけを読み込む
df_today = pd.read_sql_query(
    "SELECT * FROM records WHERE work_date = ?", 
    conn, 
    params=(str(work_date),)
)

# 過去の全データ（累計実績の計算や削除用）
df_all = pd.read_sql_query("SELECT * FROM records", conn)

# 選択された日のデータがある場合のみ表示
if not df_today.empty:
    st.divider()
    st.header(f"【{work_date}】の登録一覧")
    st.dataframe(df_today, use_container_width=True)

    # 経営指標の表示
    st.header(f"【{work_date}】の経営集集計")
    col_today_salary, col_today_sales = st.columns(2)
    
    with col_today_salary:
        # その日だけの人件費合計
        st.metric("本日（選択日）の人件費", f"{df_today['salary'].sum():,} 円")
    
    with col_today_sales:
        # その日だけの売上（1つの日付に対して売上は共通なので、最初の1件を取得）
        today_sales = df_today['sales'].iloc[0]
        st.metric("本日（選択日）の売上", f"{today_sales:,} 円")

    st.header(f"【{work_date}】のキャスト別実績")
    summary_today = df_today.groupby("cast_name").agg(
        給与=("salary", "sum"),
        勤務時間=("work_hours", "sum")
    ).reset_index()
    st.dataframe(summary_today, use_container_width=True)


# ※データ削除やExcel出力のエリアは、過去の履歴も見ながら操作できるように
# 全データ（df_all）をベースにするのがおすすめです。
if not df_all.empty:
    st.divider()
    # -------------------------
    # 登録データ削除（過去すべてから選択可能）
    # -------------------------
    st.header("登録データ履歴・削除")
    delete_df = pd.read_sql_query("SELECT * FROM records ORDER BY work_date DESC, id DESC", conn)

    deleted_id = None
    for _, row in delete_df.iterrows():
        col1, col2 = st.columns([5, 1])
        with col1:
            st.write(f"【{row['work_date']}】 {row['cast_name']} : {row['salary']:,}円 (売上: {row['sales']:,}円)")
        with col2:
            if st.button("削除", key=f"delete_{row['id']}"):
                deleted_id = row["id"]

    if deleted_id is not None:
        cursor.execute("DELETE FROM records WHERE id=?", (int(deleted_id),))
        conn.commit()
        st.success("データを削除しました。")
        st.rerun()

    # -------------------------
    # Excel出力
    # -------------------------
    st.header("Excel出力（全データ）")
    excel_buffer = BytesIO()
    
    # Excelには全データと、全データベースのキャスト集計を出力
    summary_all = df_all.groupby("cast_name").agg(
        出勤日数=("work_date", "nunique"),
        給与合計=("salary", "sum"),
        稼働時間=("work_hours", "sum")
    ).reset_index()

    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df_all.to_excel(writer, sheet_name="登録一覧", index=False)
        summary_all.to_excel(writer, sheet_name="キャスト累計集計", index=False)
    excel_buffer.seek(0)

    st.download_button(
        label="Excelダウンロード",
        data=excel_buffer,
        file_name=f"給与集計_全件_{work_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="excel_download"
    )

    # -------------------------
    # 全データ削除
    # -------------------------
    st.markdown("---")
    if st.button("全データ削除", type="secondary", help="注意：すべてのデータが消去されます"):
        cursor.execute("DELETE FROM records")
        conn.commit()
        st.success("全データを削除しました。")
        st.rerun()