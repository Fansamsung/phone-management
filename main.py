from datetime import datetime
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# Sahifa sozlamalari
st.set_page_config(
    page_title="ERP | Optom va Donabay Telefon Savdosi",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 🎨 ZAMONAVIY PREMIUM WEB UI STILI (CSS)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f4f6f9;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    .metric-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(226, 232, 240, 0.8);
    }
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 20px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #2563eb !important;
    }
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
    }
    .item-card {
        background-color: #ffffff;
        border-left: 4px solid #2563eb;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- 🔒 LOGIN TIZIMI ---
USERS = {"Abbos": "111", "azizbek": "7777"}

if "logged_in" not in st.session_state:
  st.session_state.logged_in = False


def login_page():
  st.markdown("<br><br>", unsafe_allow_html=True)
  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    st.markdown(
        """
        <div style="background-color: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); text-align: center;">
            <h2 style="color: #0f172a; margin-bottom: 8px;">🔐 Tizimga Kirish</h2>
            <p style="color: #64748b; font-size: 14px;">Optom va Donabay Telefon Savdosi ERP Tizimi</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    username = st.text_input("👤 Login", key="login_user")
    password = st.text_input("🔑 Parol", type="password", key="login_pass")

    if st.button("🚀 KIRISH", use_container_width=True, type="primary"):
      if username in USERS and USERS[username] == password:
        st.session_state.logged_in = True
        st.session_state.user_name = username
        st.toast("✅ DONE! Tizimga muvaffaqiyatli kirdingiz.", icon="🎉")
        st.rerun()
      else:
        st.error("❌ Login yoki parol noto'g'ri!")


if not st.session_state.logged_in:
  login_page()
  st.stop()

# Session State
if "kirim_savatcha" not in st.session_state:
  st.session_state.kirim_savatcha = []
if "oxirgi_qoshilgan" not in st.session_state:
  st.session_state.oxirgi_qoshilgan = None

# Bazaga ulanish
conn = sqlite3.connect("telefon_biznes.db", check_same_thread=False)
cursor = conn.cursor()

# Jadvallar
cursor.execute("""
    CREATE TABLE IF NOT EXISTS partiyalar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sana TEXT,
        taminotchi TEXT,
        model TEXT,
        xotira TEXT,
        rang TEXT,
        grade TEXT,
        boshlangich_soni INTEGER,
        olingan_narx REAL,
        tannarx REAL
    )
""")

for col_name in ["taminotchi", "rang", "grade"]:
  try:
    cursor.execute(f"ALTER TABLE partiyalar ADD COLUMN {col_name} TEXT")
  except sqlite3.OperationalError:
    pass

for col_name in ["olingan_narx", "tannarx"]:
  try:
    cursor.execute(f"ALTER TABLE partiyalar ADD COLUMN {col_name} REAL")
  except sqlite3.OperationalError:
    pass

cursor.execute("""
    CREATE TABLE IF NOT EXISTS imei_baza (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partiya_id INTEGER,
        model TEXT,
        imei1 TEXT,
        imei2 TEXT,
        status TEXT DEFAULT 'Omborda',
        mijoz_ismi TEXT,
        sotuv_sana TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS sotuvlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sana TEXT,
        partiya_id INTEGER,
        model TEXT,
        mijoz_ismi TEXT,
        sotilgan_soni INTEGER,
        sotuv_narx_dona REAL,
        cargo_dona REAL DEFAULT 0.0,
        sotuv_perevod_foiz REAL DEFAULT 0.0,
        umumiy_narx REAL,
        tolov_turi TEXT,
        tolangan_summa REAL,
        qarz_summasi REAL,
        umumiy_foyda REAL
    )
""")

for col, col_type in [
    ("cargo_dona", "REAL DEFAULT 0.0"),
    ("sotuv_perevod_foiz", "REAL DEFAULT 0.0"),
]:
  try:
    cursor.execute(f"ALTER TABLE sotuvlar ADD COLUMN {col} {col_type}")
  except sqlite3.OperationalError:
    pass

cursor.execute("""
    CREATE TABLE IF NOT EXISTS qarz_tolovlari (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sana TEXT,
        sotuv_id INTEGER,
        mijoz_ismi TEXT,
        tolangan_summa REAL,
        qolgan_qarz REAL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS partiya_xarajatlari (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partiya_id INTEGER,
        sana TEXT,
        xarajat_nomi TEXT,
        summa REAL,
        tur TEXT
    )
""")
conn.commit()

# --- SIDEBAR NAVIGATSIYA ---
st.sidebar.markdown(
    f"""
    <div style="text-align: center; padding: 10px 0;">
        <h3 style="margin:0; color:#1e293b;">📱 TELEFON ERP</h3>
        <span style="font-size:12px; color:#64748b;">Foydalanuvchi: <b>{st.session_state.user_name}</b></span>
    </div>
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Bo'limlar:",
    [
        "📊 Dashboard va Analytics",
        "📦 Ombor Qoldiqlari",
        "➕ Optom / Dona Kirim Qilish",
        "💰 Partiyalar Tannarxini Hisoblash",
        "✏️ Kirimlarni Boshqarish (O'chirish)",
        "📥 IMEI Excel / Qo'lda Kiritish",
        "🛒 Sotuv Qilish (Dona / Optom)",
        "🔍 IMEI va IMEIsiz Qaytarib Olish (Vozvrat)",
        "👥 Nasiyalar va Qarz To'lovlari",
        "📜 Savdo Tarixi va Hisobot",
    ],
)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Tizimdan Chiqish", use_container_width=True):
  st.session_state.logged_in = False
  st.toast("👋 Tizimdan chiqildi.", icon="ℹ️")
  st.rerun()

# --- 1. DASHBOARD VA VIZUAL ANALYTICS ---
if menu == "📊 Dashboard va Analytics":
  st.markdown(
      "<h1 class='main-header'>📊 Boshqaruv Paneli va Statistik Analytics</h1>",
      unsafe_allow_html=True,
  )

  df_sotuv = pd.read_sql("SELECT * FROM sotuvlar", conn)
  df_ombor = pd.read_sql(
      "SELECT i.*, p.tannarx, p.olingan_narx FROM imei_baza i JOIN partiyalar p"
      " ON i.partiya_id = p.id WHERE i.status = 'Omborda'",
      conn,
  )

  jami_savdo = df_sotuv["umumiy_narx"].sum() if not df_sotuv.empty else 0.0
  jami_foyda = df_sotuv["umumiy_foyda"].sum() if not df_sotuv.empty else 0.0
  jami_qarz = df_sotuv["qarz_summasi"].sum() if not df_sotuv.empty else 0.0

  df_ombor["tannarx"] = df_ombor["tannarx"].fillna(df_ombor["olingan_narx"])
  ombor_sarmoya = df_ombor["tannarx"].sum() if not df_ombor.empty else 0.0

  c1, c2, c3, c4 = st.columns(4)
  c1.metric("💰 Jami Savdo Tushumi", f"${jami_savdo:,.2f}")
  c2.metric("📈 Sof Foyda", f"${jami_foyda:,.2f}")
  c3.metric("⚠️ Undirilmagan Qarzlar", f"${jami_qarz:,.2f}")
  c4.metric("📦 Ombordagi Sarmoya", f"${ombor_sarmoya:,.2f}")

  st.markdown("---")

  if not df_sotuv.empty:
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
      st.subheader("🔥 Eng Ko'p Sotilgan Modellar Top-10")
      top_models = (
          df_sotuv.groupby("model")["sotilgan_soni"]
          .sum()
          .reset_index()
          .sort_values(by="sotilgan_soni", ascending=False)
          .head(10)
      )
      fig_top = px.bar(
          top_models,
          x="sotilgan_soni",
          y="model",
          orientation="h",
          color="sotilgan_soni",
          color_continuous_scale="Blues",
          labels={
              "sotilgan_soni": "Sotilgan Soni (ta)",
              "model": "Telefon Modeli",
          },
      )
      fig_top.update_layout(
          yaxis={"categoryorder": "total ascending"}, showlegend=False
      )
      st.plotly_chart(fig_top, use_container_width=True)

    with col_chart2:
      st.subheader("💳 To'lov Turlari Bo'yicha Ulush")
      pay_chart = (
          df_sotuv.groupby("tolov_turi")["umumiy_narx"].sum().reset_index()
      )
      fig_pay = px.pie(
          pay_chart,
          values="umumiy_narx",
          names="tolov_turi",
          hole=0.4,
          color_discrete_sequence=px.colors.qualitative.Pastel,
      )
      st.plotly_chart(fig_pay, use_container_width=True)

    st.markdown("---")
    st.subheader("📈 Vaqt Bo'yicha Savdo Va Sof Foyda Dinamikasi")

    df_sotuv["sana_dt"] = pd.to_datetime(df_sotuv["sana"]).dt.date
    daily_sales = (
        df_sotuv.groupby("sana_dt")[["umumiy_narx", "umumiy_foyda"]]
        .sum()
        .reset_index()
    )

    fig_line = px.line(
        daily_sales,
        x="sana_dt",
        y=["umumiy_narx", "umumiy_foyda"],
        labels={"value": "Summa ($)", "sana_dt": "Sana", "variable": "Ko'rsatkich"},
        markers=True,
    )
    st.plotly_chart(fig_line, use_container_width=True)

# --- 2. OMBOR QOLDIQLARI ---
elif menu == "📦 Ombor Qoldiqlari":
  st.header("📦 Ombordagi Mahsulotlar Qoldig'i va Narxlari")

  query_ombor_full = """
        SELECT i.id, i.partiya_id, i.model, i.imei1, i.imei2, p.xotira, p.rang, p.grade, p.boshlangich_soni, p.olingan_narx, p.tannarx, p.taminotchi, p.sana
        FROM imei_baza i
        JOIN partiyalar p ON i.partiya_id = p.id
        WHERE i.status = 'Omborda'
    """
  df_ombor = pd.read_sql(query_ombor_full, conn)

  if df_ombor.empty:
    st.warning("📂 Hozirda ombor bo'sh!")
  else:
    df_ombor["tannarx"] = df_ombor["tannarx"].fillna(df_ombor["olingan_narx"])

    m_c1, m_c2, m_c3 = st.columns(3)
    m_c1.metric("📱 Ombordagi Jami Telefonlar", f"{len(df_ombor)} ta")
    m_c2.metric(
        "💵 Ombordagi Jami Tovar Qiymati", f"${df_ombor['tannarx'].sum():,.2f}"
    )
    m_c3.metric("🏷️ Turli Modellar Soni", f"{df_ombor['model'].nunique()} xil")

    st.markdown("---")

    search_qoldiq = st.text_input(
        "🔎 Model bo'yicha tezkor qidiruv:",
        placeholder="masalan: iPhone 13 Pro yoki 128GB...",
    )

    if search_qoldiq.strip():
      df_ombor = df_ombor[
          df_ombor["model"].str.contains(
              search_qoldiq.strip(), case=False, na=False
          )
          | df_ombor["xotira"].str.contains(
              search_qoldiq.strip(), case=False, na=False
          )
          | df_ombor["rang"].str.contains(
              search_qoldiq.strip(), case=False, na=False
          )
      ]

    qoldiq_summary = (
        df_ombor.groupby([
            "partiya_id",
            "model",
            "xotira",
            "rang",
            "grade",
            "taminotchi",
            "tannarx",
        ])
        .size()
        .reset_index(name="Ombordagi Qoldiq (ta)")
    )

    qoldiq_summary["Jami Qoldiq Qiymati ($)"] = (
        qoldiq_summary["Ombordagi Qoldiq (ta)"] * qoldiq_summary["tannarx"]
    )

    qoldiq_summary.columns = [
        "Partiya ID",
        "Model",
        "Xotira",
        "Rang",
        "Grade",
        "Ta'minotchi",
        "1 Dona Tannarxi ($)",
        "Qoldiq (ta)",
        "Jami Qoldiq Summasi ($)",
    ]

    st.dataframe(qoldiq_summary, use_container_width=True)

    kam_qolganlar = qoldiq_summary[qoldiq_summary["Qoldiq (ta)"] <= 3]
    if not kam_qolganlar.empty:
      st.error(
          "⚠️ **DIQQAT! Quyidagi modellardan omborda juda kam (3 ta yoki undan"
          " kam) qoldi:**"
      )
      st.dataframe(
          kam_qolganlar[
              ["Model", "Xotira", "Rang", "Qoldiq (ta)", "1 Dona Tannarxi ($)"]
          ],
          use_container_width=True,
      )

# --- 3. OPTOM / DONA KIRIM QILISH ---
elif menu == "➕ Optom / Dona Kirim Qilish":
  st.header("📦 Ta'minotchidan Yuk Kirim Qilish")

  taminotchi = st.text_input(
      "👤 Ta'minotchi / Kimdan olingan (masalan: Ali Dubai / Market 77)",
      key="taminotchi_input",
  )

  st.markdown("---")
  st.subheader("➕ Model Ma'lumotlari")

  col1, col2, col3 = st.columns(3)
  with col1:
    model = st.text_input(
        "📱 Telefon modeli", placeholder="masalan: iPhone 13 Pro"
    )
    xotira = st.selectbox(
        "💾 Xotirasi", ["128GB", "256GB", "512GB", "1TB", "Boshqa"]
    )
  with col2:
    rang = st.text_input("🎨 Rangi", placeholder="masalan: Sierra Blue")
    grade = st.text_input(
        "⭐ Grade / Holati", placeholder="masalan: A+ / 90% batareya"
    )
  with col3:
    soni = st.number_input(
        "🔢 Necha dona olindi?", min_value=1, value=1, step=1
    )
    olingan_narx = st.number_input(
        "💵 1 dona Narxi ($)", min_value=0.0, step=1.0
    )

  ushbu_model_jami = soni * olingan_narx

  st.markdown("### 📲 IMEI 1 va IMEI 2 Kiritish Usuli:")
  imei_kiritish_usuli = st.radio(
      "Kiritish qulayligini tanlang:",
      [
          "1️⃣ Har bir telefon uchun alohida kataklar (Skaner / Qo'lda)",
          "2️⃣ Excel fayl yuklash (.xlsx)",
          "3️⃣ Nusxalangan matn shaklida (Copy-Paste)",
          "4️⃣ Hozircha kiritmaslik",
      ],
      horizontal=True,
  )

  imei_pairs = []

  if (
      imei_kiritish_usuli
      == "1️⃣ Har bir telefon uchun alohida kataklar (Skaner / Qo'lda)"
  ):
    max_rows = min(int(soni), 50)
    for i in range(max_rows):
      c_no, c_im1, c_im2 = st.columns([1, 4, 4])
      with c_no:
        st.markdown(f"**#{i+1}:**")
      with c_im1:
        im1 = st.text_input(
            f"IMEI 1",
            key=f"im1_{i}",
            placeholder="15 xonali IMEI1",
            label_visibility="collapsed",
        )
      with c_im2:
        im2 = st.text_input(
            f"IMEI 2",
            key=f"im2_{i}",
            placeholder="IMEI2",
            label_visibility="collapsed",
        )
      if im1.strip():
        imei_pairs.append((im1.strip(), im2.strip()))

  elif imei_kiritish_usuli == "2️⃣ Excel fayl yuklash (.xlsx)":
    uploaded_excel = st.file_uploader(
        "Excel faylni yuklang", type=["xlsx", "xls"], key="kirim_excel"
    )
    if uploaded_excel is not None:
      try:
        df_ex = pd.read_excel(uploaded_excel)
        for _, r in df_ex.iterrows():
          i1 = (
              str(r["IMEI"]).strip().replace(".0", "")
              if "IMEI" in df_ex.columns
              else ""
          )
          i2 = (
              str(r["IMEI2"]).strip().replace(".0", "")
              if "IMEI2" in df_ex.columns
              else ""
          )
          if i1 and i1 != "nan":
            imei_pairs.append((i1, i2))
        st.toast(
            f"✅ DONE! Exceldan {len(imei_pairs)} ta IMEI o'qildi.", icon="📊"
        )
      except Exception as e:
        st.error(f"Excelni o'qishda xatolik: {e}")

  elif imei_kiritish_usuli == "3️⃣ Nusxalangan matn shaklida (Copy-Paste)":
    imei_matn = st.text_area("IMEI lar ro'yxati (har bir qatorda bittadan):")
    if imei_matn:
      for line in imei_matn.split("\n"):
        line_clean = str(line).strip()
        if line_clean:
          parts = [
              p.strip().replace(".0", "")
              for p in line_clean.replace("\t", ",").split(",")
          ]
          i1 = parts[0] if len(parts) > 0 else ""
          i2 = parts[1] if len(parts) > 1 else ""
          imei_pairs.append((i1, i2))

  if st.button("➕ USHBU MODELNI RO'YXATGA QO'SHISH", use_container_width=True):
    if model and soni > 0:
      yangi_item = {
          "model": model,
          "xotira": xotira,
          "rang": rang,
          "grade": grade,
          "soni": int(soni),
          "olingan_narx": olingan_narx,
          "jami_summa": ushbu_model_jami,
          "imei_pairs": imei_pairs,
      }
      st.session_state.kirim_savatcha.append(yangi_item)
      st.session_state.oxirgi_qoshilgan = yangi_item
      st.toast(f"✅ DONE! {model} savatchaga qo'shildi.", icon="🛒")
      st.rerun()

  if st.session_state.kirim_savatcha:
    st.markdown("---")
    st.subheader("📋 Kirim qilinayotgan telefonlar savatchasi:")
    for idx, item in enumerate(st.session_state.kirim_savatcha):
      st.markdown(
          f"""
            <div class="item-card">
                <b>#{idx+1}. {item['model']} ({item['xotira']})</b> - Rangi: {item['rang']} - Grade: {item['grade']}<br>
                <span>📦 Soni: {item['soni']} ta | 💵 Dona: ${item['olingan_narx']:,.2f} | 💰 Jami: ${item['jami_summa']:,.2f} | IMEI: {len(item['imei_pairs'])} ta</span>
            </div>
            """,
          unsafe_allow_html=True,
      )

    if st.button(
        "🚀 BARCHASINI OMBORGA KIRIM QILISH",
        type="primary",
        use_container_width=True,
    ):
      sana = datetime.now().strftime("%Y-%m-%d %H:%M")
      for item in st.session_state.kirim_savatcha:
        cursor.execute(
            """
                    INSERT INTO partiyalar (sana, taminotchi, model, xotira, rang, grade, boshlangich_soni, olingan_narx, tannarx)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
            (
                sana,
                taminotchi,
                item["model"],
                item["xotira"],
                item["rang"],
                item["grade"],
                item["soni"],
                item["olingan_narx"],
                item["olingan_narx"],
            ),
        )
        partiya_id = cursor.lastrowid

        for imei1, imei2 in item["imei_pairs"]:
          cursor.execute(
              """
                        INSERT INTO imei_baza (partiya_id, model, imei1, imei2, status)
                        VALUES (?, ?, ?, ?, 'Omborda')
                    """,
              (partiya_id, item["model"], imei1, imei2),
          )

        qolgan = item["soni"] - len(item["imei_pairs"])
        if qolgan > 0:
          for i in range(qolgan):
            cursor.execute(
                """
                            INSERT INTO imei_baza (partiya_id, model, imei1, imei2, status)
                            VALUES (?, ?, ?, ?, 'Omborda')
                        """,
                (
                    partiya_id,
                    item["model"],
                    f"⚠️ IMEI kiritilmagan ({len(item['imei_pairs'])+i+1}-telefon)",
                    "",
                ),
            )

      conn.commit()
      st.session_state.kirim_savatcha = []
      st.session_state.oxirgi_qoshilgan = None
      st.balloons()
      st.toast("✅ DONE! Yuklar omborga saqlandi.", icon="🚀")
      st.rerun()

# --- 4. PARTIYALAR TANNARXINI HISOBLASH ---
elif menu == "💰 Partiyalar Tannarxini Hisoblash":
  st.header("🛠️ Partiyaga Xarajatlar va Pul Jo'natma Foizi")

  df_partiyalar = pd.read_sql("SELECT * FROM partiyalar", conn)

  if df_partiyalar.empty:
    st.warning("Hozircha omborda partiyalar yo'q.")
  else:
    partiya_options = {}
    for _, row in df_partiyalar.iterrows():
      xot = f" ({row['xotira']})" if row["xotira"] else ""
      rng = f" - {row['rang']}" if row["rang"] else ""
      label = f"ID: {row['id']} — {row['model']}{xot}{rng} (Boshlang'ich: {row['boshlangich_soni']} ta)"
      partiya_options[label] = row["id"]

    selected_label = st.selectbox(
        "Tannarxini hisoblamoqchi bo'lgan Partiyani tanlang:",
        list(partiya_options.keys()),
    )
    partiya_id_selected = partiya_options[selected_label]

    p_row = df_partiyalar[df_partiyalar["id"] == partiya_id_selected].iloc[0]

    soni = p_row["boshlangich_soni"]
    olingan_narx = p_row["olingan_narx"]

    st.info(
        f"Model: **{p_row['model']} ({p_row['xotira']})** | Soni: **{soni} ta**"
        f" | Boshlang'ich Narxi: **${olingan_narx:,.2f}**"
    )

    col_x1, col_x2 = st.columns(2)
    with col_x1:
      xarajat_nomi = st.text_input("Xarajat nomi (Dostavka, Remont, Karobka)")
      xarajat_turi = st.radio(
          "Xarajat turi:", ["Jami partiya uchun", "Har bir dona uchun"]
      )
      xarajat_summasi = st.number_input(
          "Summa ($)", min_value=0.0, step=5.0, value=0.0
      )

      if st.button("➕ Xarajatni Saqlash"):
        if xarajat_nomi and xarajat_summasi > 0:
          sana_h = datetime.now().strftime("%Y-%m-%d %H:%M")
          tur_str = (
              "Partiya uchun" if "Jami" in xarajat_turi else "Dona uchun"
          )
          cursor.execute(
              """
                        INSERT INTO partiya_xarajatlari (partiya_id, sana, xarajat_nomi, summa, tur)
                        VALUES (?, ?, ?, ?, ?)
                    """,
              (
                  partiya_id_selected,
                  sana_h,
                  xarajat_nomi,
                  xarajat_summasi,
                  tur_str,
              ),
          )
          conn.commit()
          st.toast("✅ DONE! Xarajat qo'shildi.", icon="💵")
          st.rerun()

    with col_x2:
      df_xarajat = pd.read_sql(
          f"SELECT id, sana, xarajat_nomi, summa, tur FROM partiya_xarajatlari WHERE partiya_id = {partiya_id_selected}",
          conn,
      )
      st.dataframe(df_xarajat, use_container_width=True)

    st.markdown("---")
    pul_jonatma_foiz = st.number_input(
        "Pul jo'natma (kirim perevod) foizi (%):",
        min_value=0.0,
        max_value=10.0,
        value=0.5,
        step=0.1,
    )
    pul_jonatma_dona = olingan_narx * (pul_jonatma_foiz / 100.0)

    jami_partiya_xarajat = (
        df_xarajat[df_xarajat["tur"] == "Partiya uchun"]["summa"].sum()
        if not df_xarajat.empty
        else 0
    )
    har_bir_dona_xarajat = (
        df_xarajat[df_xarajat["tur"] == "Dona uchun"]["summa"].sum()
        if not df_xarajat.empty
        else 0
    )

    dona_qoshimcha = (
        jami_partiya_xarajat / soni if soni > 0 else 0
    ) + har_bir_dona_xarajat
    yangi_tannarx = olingan_narx + dona_qoshimcha + pul_jonatma_dona

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💵 Olingan Narxi", f"${olingan_narx:,.2f}")
    m2.metric(f"💸 Perevod ({pul_jonatma_foiz}%)", f"+${pul_jonatma_dona:,.2f}")
    m3.metric("🛠️ Boshqa Xarajat", f"+${dona_qoshimcha:,.2f}")
    m4.metric("⭐ ANIQ TANNARX", f"${yangi_tannarx:,.2f}")

    if st.button("💾 USHBU TANNARXNI BAZAGA SAQLASH"):
      cursor.execute(
          "UPDATE partiyalar SET tannarx = ? WHERE id = ?",
          (yangi_tannarx, partiya_id_selected),
      )
      conn.commit()
      st.balloons()
      st.toast("✅ DONE! Yangi tannarx saqlandi.", icon="⭐")
      st.rerun()

# --- 5. KIRIMLARNI BOSHQARISH ---
elif menu == "✏️ Kirimlarni Boshqarish (O'chirish)":
  st.header("📋 Kirim Qilingan Partiyalarni Boshqarish")
  df_partiya = pd.read_sql("SELECT * FROM partiyalar", conn)

  if not df_partiya.empty:
    st.dataframe(df_partiya, use_container_width=True)

    partiya_del_options = {}
    for _, row in df_partiya.iterrows():
      label = (
          f"ID: {row['id']} — {row['model']} ({row['xotira']} - {row['rang']})"
      )
      partiya_del_options[label] = row["id"]

    del_label = st.selectbox(
        "O'chirmoqchi bo'lgan partiyani tanlang:",
        list(partiya_del_options.keys()),
    )
    silish_id = partiya_del_options[del_label]

    if st.button("🗑️ Tanlangan Partiyani O'chirish", type="primary"):
      cursor.execute("DELETE FROM partiyalar WHERE id = ?", (silish_id,))
      cursor.execute("DELETE FROM imei_baza WHERE partiya_id = ?", (silish_id,))
      cursor.execute(
          "DELETE FROM partiya_xarajatlari WHERE partiya_id = ?", (silish_id,)
      )
      conn.commit()
      st.toast(f"✅ DONE! {silish_id}-ID partiya o'chirildi.", icon="🗑️")
      st.rerun()

# --- 6. IMEI EXCEL / QO'LDA KIRITISH ---
elif menu == "📥 IMEI Excel / Qo'lda Kiritish":
  st.header("📲 IMEI Raqamlarni Yangilash")
  df_partiya = pd.read_sql("SELECT * FROM partiyalar", conn)

  if not df_partiya.empty:
    p_options = {}
    for _, row in df_partiya.iterrows():
      label = (
          f"ID: {row['id']} — {row['model']} ({row['xotira']} - {row['rang']})"
      )
      p_options[label] = row["id"]

    sec_label = st.selectbox(
        "Partiya va Modelni tanlang:", list(p_options.keys())
    )
    secilgan_partiya_id = p_options[sec_label]

    uploaded_file = st.file_uploader(
        "Excel fayl yuklang (.xlsx)", type=["xlsx", "xls"]
    )

    if st.button("🚀 Exceldagi IMEI larni Bazaga Yuklash"):
      if uploaded_file is not None:
        try:
          df_excel = pd.read_excel(uploaded_file)
          cursor.execute(
              "DELETE FROM imei_baza WHERE partiya_id = ?",
              (secilgan_partiya_id,),
          )
          p_model = df_partiya[df_partiya["id"] == secilgan_partiya_id][
              "model"
          ].values[0]

          for _, row in df_excel.iterrows():
            i1 = (
                str(row["IMEI"]).strip().replace(".0", "")
                if "IMEI" in df_excel.columns
                else ""
            )
            i2 = (
                str(row["IMEI2"]).strip().replace(".0", "")
                if "IMEI2" in df_excel.columns
                else ""
            )
            if i1 and i1 != "nan":
              cursor.execute(
                  """
                        INSERT INTO imei_baza (partiya_id, model, imei1, imei2, status)
                        VALUES (?, ?, ?, ?, 'Omborda')
                    """,
                  (secilgan_partiya_id, p_model, i1, i2),
              )
          conn.commit()
          st.toast("✅ DONE! Excel IMEI lari saqlandi.", icon="📲")
          st.rerun()
        except Exception as e:
          st.error(f"Xatolik: {e}")

# --- 7. SOTUV QILISH ---
elif menu == "🛒 Sotuv Qilish (Dona / Optom)":
  st.header("🛒 Sotuvni Rasmiylashtirish")

  df_omborda = pd.read_sql(
      """
        SELECT i.id, i.partiya_id, i.model, i.imei1, i.imei2, p.xotira, p.rang, p.grade, p.tannarx, p.olingan_narx
        FROM imei_baza i JOIN partiyalar p ON i.partiya_id = p.id
        WHERE i.status = 'Omborda'
    """,
      conn,
  )

  if df_omborda.empty:
    st.info("Omborda sotish uchun telefon yo'q!")
  else:
    ombor_partiya_summary = (
        df_omborda.groupby(
            ["partiya_id", "model", "xotira", "rang", "grade", "tannarx"]
        )
        .size()
        .reset_index(name="qoldiq")
    )

    partiya_select_dict = {}
    for _, r in ombor_partiya_summary.iterrows():
      p_id = r["partiya_id"]
      m_nomi = r["model"]
      xot = f" ({r['xotira']})" if r["xotira"] else ""
      rng = f" - {r['rang']}" if r["rang"] else ""
      grd = f" [{r['grade']}]" if r["grade"] else ""
      qold = r["qoldiq"]

      label = f"ID: {p_id} — {m_nomi}{xot}{rng}{grd} | Omborda qolgan: {qold} ta"
      partiya_select_dict[label] = p_id

    selected_partiya_label = st.selectbox(
        "Sotiladigan Model va Partiyani tanlang:",
        list(partiya_select_dict.keys()),
    )
    secilgan_partiya_id = partiya_select_dict[selected_partiya_label]

    partiya_df = df_omborda[df_omborda["partiya_id"] == secilgan_partiya_id]
    first_row = partiya_df.iloc[0]
    tannarx_val = (
        first_row["tannarx"]
        if pd.notnull(first_row["tannarx"])
        else first_row["olingan_narx"]
    )
    ombordagi_soni = len(partiya_df)

    st.markdown("---")

    df_existing_customers = pd.read_sql(
        "SELECT DISTINCT mijoz_ismi FROM sotuvlar WHERE mijoz_ismi IS NOT NULL"
        " AND mijoz_ismi != ''",
        conn,
    )
    existing_customers = (
        df_existing_customers["mijoz_ismi"].tolist()
        if not df_existing_customers.empty
        else []
    )

    st.markdown("#### 👤 Mijoz Tanlash yoki Kiritish:")
    customer_options = ["➕ Yangi mijoz kiritish..."] + existing_customers
    selected_customer_option = st.selectbox(
        "Oldingi mijozlar ro'yxatidan tanlang:",
        customer_options,
        key="customer_select",
    )

    if selected_customer_option == "➕ Yangi mijoz kiritish...":
      mijoz_ismi = st.text_input(
          "👤 Yangi Mijoz Ismi / Do'kon Nomi:", placeholder="masalan: Hasanboy"
      )
    else:
      mijoz_ismi = selected_customer_option

    st.markdown("---")
    sotuv_usuli = st.radio(
        "Sotish rejimini tanlang:",
        [
            "1️⃣ IMEI raqamlarni tanlash orqali sotish",
            "2️⃣ IMEI siz (Faqat necha dona sotilganini kiritish)",
        ],
        horizontal=True,
    )

    selected_imeis = []
    sotilgan_soni = 0

    if sotuv_usuli == "1️⃣ IMEI raqamlarni tanlash orqali sotish":
      selected_imeis = st.multiselect(
          "Tanlangan modeldagi IMEI lar ro'yxati:", partiya_df["imei1"].tolist()
      )
      sotilgan_soni = len(selected_imeis)
    else:
      sotilgan_soni = st.number_input(
          f"🔢 Necha dona sotildi? (Omborda maks: {ombordagi_soni} ta):",
          min_value=0,
          max_value=ombordagi_soni,
          value=1,
          step=1,
      )
      selected_imeis = partiya_df["imei1"].tolist()[: int(sotilgan_soni)]

    if sotilgan_soni > 0:
      col_s1, col_s2 = st.columns(2)
      with col_s1:
        sotuv_narx_dona = st.number_input(
            "💵 1 dona Sotilish narxi ($)", min_value=0.0, step=5.0
        )

        cargo_dona = st.number_input(
            "🚚 Cargo / Dostavka xarajati (1 dona uchun $) [Dubayda sotilsa"
            " 0 deb qoldiring]:",
            min_value=0.0,
            step=1.0,
            value=0.0,
        )

        sotuv_perevod_foiz = st.number_input(
            "💸 Sotuv Perevod komissiyasi (%):",
            min_value=0.0,
            max_value=10.0,
            step=0.1,
            value=0.0,
        )

      with col_s2:
        umumiy_narx = sotilgan_soni * sotuv_narx_dona
        jami_cargo = sotilgan_soni * cargo_dona
        jami_perevod_komissiya = umumiy_narx * (sotuv_perevod_foiz / 100.0)

        jami_tannarx = tannarx_val * sotilgan_soni
        umumiy_foyda = (
            umumiy_narx - jami_tannarx - jami_cargo - jami_perevod_komissiya
        )

        st.markdown(f"### 💰 Jami Savdo Summasi: **${umumiy_narx:,.2f}**")

        details_str = []
        if jami_cargo > 0:
          details_str.append(f"Cargo: **${jami_cargo:,.2f}**")
        if jami_perevod_komissiya > 0:
          details_str.append(
              f"Perevod ({sotuv_perevod_foiz}%):"
              f" **${jami_perevod_komissiya:,.2f}**"
          )

        if details_str:
          st.caption(" ➕ ".join(details_str))

        st.info(
            f"📈 Ushbu savdodan Aniq Sof Foyda: **${umumiy_foyda:,.2f}**"
        )

      tolov_turi = st.selectbox(
          "To'lov Turi:", ["Naqd", "Nasiya (Qarz)", "Perevod"]
      )

      tolangan_summa = (
          st.number_input(
              "Hozir to'langan summa ($):",
              min_value=0.0,
              max_value=float(umumiy_narx),
              value=0.0,
          )
          if tolov_turi == "Nasiya (Qarz)"
          else umumiy_narx
      )
      qarz_summasi = umumiy_narx - tolangan_summa

      if st.button("🚀 Sotuvni Tasdiqlash", type="primary"):
        if mijoz_ismi.strip():
          sana = datetime.now().strftime("%Y-%m-%d %H:%M")

          cursor.execute(
              """
                    INSERT INTO sotuvlar (sana, partiya_id, model, mijoz_ismi, sotilgan_soni, sotuv_narx_dona, cargo_dona, sotuv_perevod_foiz, umumiy_narx, tolov_turi, tolangan_summa, qarz_summasi, umumiy_foyda)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
              (
                  sana,
                  secilgan_partiya_id,
                  first_row["model"],
                  mijoz_ismi.strip(),
                  sotilgan_soni,
                  sotuv_narx_dona,
                  cargo_dona,
                  sotuv_perevod_foiz,
                  umumiy_narx,
                  tolov_turi,
                  tolangan_summa,
                  qarz_summasi,
                  umumiy_foyda,
              ),
          )

          for imei in selected_imeis:
            cursor.execute(
                """
                        UPDATE imei_baza SET status = 'Sotilgan', mijoz_ismi = ?, sotuv_sana = ? WHERE imei1 = ?
                    """,
                (mijoz_ismi.strip(), sana, imei),
            )

          conn.commit()
          st.balloons()
          st.toast(
              f"✅ DONE! {sotilgan_soni} ta {first_row['model']}"
              f" {mijoz_ismi.strip()}ga sotildi.",
              icon="🛍️",
          )
          st.rerun()
        else:
          st.error("❌ Iltimos, mijoz ismini kiriting!")

# --- 8. IMEI VA IMEISIZ VOZVRAT BOSHGARISH ---
elif menu == "🔍 IMEI va IMEIsiz Qaytarib Olish (Vozvrat)":
  st.header("🔄 Qaytarib Olish (Vozvrat qilish)")

  vozvrat_tab1, vozvrat_tab2 = st.tabs([
      "1️⃣ IMEI bor telefonni qaytarish",
      "2️⃣ IMEIsiz sotilgan telefonni qaytarish",
  ])

  with vozvrat_tab1:
    qidiruv_imei = st.text_input(
        "IMEI raqamini kiriting:", key="vozvrat_imei_input"
    )

    if qidiruv_imei.strip():
      cursor.execute(
          "SELECT * FROM imei_baza WHERE imei1 LIKE ? OR imei2 LIKE ?",
          (f"%{qidiruv_imei.strip()}%", f"%{qidiruv_imei.strip()}%"),
      )
      res = cursor.fetchone()
      if res:
        st.toast("✅ DONE! IMEI bazadan topildi.", icon="🔍")
        st.info(
            f"📱 **Model:** {res[2]} | **Status:** {res[5]} | **Mijoz:**"
            f" {res[6] if res[6] else '-'}"
        )

        if res[5] == "Sotilgan":
          st.warning(
              "⚠️ Ushbu telefon sotilgan. Omborga qaytarib olish uchun pastdagi"
              " tugmani bosing:"
          )

          if st.button("🔄 TELEFONNI VOZVRAT QILISH", key="btn_imei_vozvrat"):
            cursor.execute(
                "UPDATE imei_baza SET status = 'Omborda', mijoz_ismi = NULL,"
                " sotuv_sana = NULL WHERE id = ?",
                (res[0],),
            )

            cursor.execute(
                "SELECT id, sotilgan_soni, sotuv_narx_dona, umumiy_narx,"
                " qarz_summasi, umumiy_foyda FROM sotuvlar WHERE model = ? AND"
                " mijoz_ismi = ? ORDER BY id DESC LIMIT 1",
                (res[2], res[6]),
            )
            sotuv_record = cursor.fetchone()

            if sotuv_record:
              s_id, s_soni, s_dona, s_umumiy, s_qarz, s_foyda = sotuv_record
              if s_soni <= 1:
                cursor.execute("DELETE FROM sotuvlar WHERE id = ?", (s_id,))
              else:
                bir_dona_foyda = s_foyda / s_soni
                cursor.execute(
                    """
                                  UPDATE sotuvlar 
                                  SET sotilgan_soni = sotilgan_soni - 1,
                                      umumiy_narx = umumiy_narx - ?,
                                      qarz_summasi = CASE WHEN qarz_summasi >= ? THEN qarz_summasi - ? ELSE 0 END,
                                      umumiy_foyda = umumiy_foyda - ?
                                  WHERE id = ?
                              """,
                    (s_dona, s_dona, s_dona, bir_dona_foyda, s_id),
                )

            conn.commit()
            st.balloons()
            st.success("✅ DONE! Telefon omborga muvaffaqiyatli qaytarildi.")
            st.rerun()
      else:
        st.error("❌ Ushbu IMEI topilmadi!")

  with vozvrat_tab2:
    st.subheader("📋 IMEIsiz Sotilgan Telefonni Qaytarib Olish")

    df_sotuvlar_tab2 = pd.read_sql("SELECT * FROM sotuvlar", conn)

    if df_sotuvlar_tab2.empty:
      st.info("Hozircha savdolar tarixi bo'sh.")
    else:
      sotuv_dict2 = {}
      for _, r in df_sotuvlar_tab2.iterrows():
        lbl = (
            f"Savdo ID: {r['id']} | Sana: {r['sana']} | Mijoz:"
            f" {r['mijoz_ismi']} | Model: {r['model']} ({r['sotilgan_soni']} ta)"
            f" | Jami: ${r['umumiy_narx']:,.2f}"
        )
        sotuv_dict2[lbl] = r["id"]

      sel_sotuv_lbl2 = st.selectbox(
          "Qaysi savdodagi telefon qaytarildi?",
          list(sotuv_dict2.keys()),
          key="sel_imeisiz_vozvrat",
      )
      sotuv_id_sel2 = sotuv_dict2[sel_sotuv_lbl2]

      s_row2 = df_sotuvlar_tab2[df_sotuvlar_tab2["id"] == sotuv_id_sel2].iloc[0]

      vozvrat_soni2 = st.number_input(
          f"Necha dona telefon qaytarib olindi? (Ushbu savdoda maks:"
          f" {s_row2['sotilgan_soni']} ta bor):",
          min_value=1,
          max_value=int(s_row2["sotilgan_soni"]),
          value=1,
          step=1,
          key="num_imeisiz_vozvrat",
      )

      if st.button(
          "🔄 USHBU TELEFONNI OMBOBGA QAYTARISH (VOZVRAT)",
          type="primary",
          key="btn_imeisiz_vozvrat",
      ):
        partiya_id_v = s_row2["partiya_id"]
        model_v = s_row2["model"]
        s_dona_narx = s_row2["sotuv_narx_dona"]

        cursor.execute(
            "SELECT id FROM imei_baza WHERE partiya_id = ? AND status ="
            " 'Sotilgan' LIMIT ?",
            (partiya_id_v, vozvrat_soni2),
        )
        sold_imeis = cursor.fetchall()

        if sold_imeis:
          for im_item in sold_imeis:
            cursor.execute(
                "UPDATE imei_baza SET status = 'Omborda', mijoz_ismi = NULL,"
                " sotuv_sana = NULL WHERE id = ?",
                (im_item[0],),
            )
        else:
          for _ in range(vozvrat_soni2):
            cursor.execute(
                """
                          INSERT INTO imei_baza (partiya_id, model, imei1, imei2, status)
                          VALUES (?, ?, '⚠️ Qaytarilgan (IMEIsiz)', '', 'Omborda')
                      """,
                (partiya_id_v, model_v),
            )

        if s_row2["sotilgan_soni"] <= vozvrat_soni2:
          cursor.execute("DELETE FROM sotuvlar WHERE id = ?", (sotuv_id_sel2,))
        else:
          bir_dona_foyda = s_row2["umumiy_foyda"] / s_row2["sotilgan_soni"]
          kamayish_summasi = vozvrat_soni2 * s_dona_narx
          kamayish_foyda = vozvrat_soni2 * bir_dona_foyda

          cursor.execute(
              """
                      UPDATE sotuvlar 
                      SET sotilgan_soni = sotilgan_soni - ?,
                          umumiy_narx = umumiy_narx - ?,
                          qarz_summasi = CASE WHEN qarz_summasi >= ? THEN qarz_summasi - ? ELSE 0 END,
                          umumiy_foyda = umumiy_foyda - ?
                      WHERE id = ?
                  """,
              (
                  vozvrat_soni2,
                  kamayish_summasi,
                  kamayish_summasi,
                  kamayish_summasi,
                  kamayish_foyda,
                  sotuv_id_sel2,
              ),
          )

        conn.commit()
        st.balloons()
        st.toast(
            f"✅ DONE! {vozvrat_soni2} ta {model_v} omborga qaytarildi.",
            icon="🔄",
        )
        st.rerun()

# --- 9. NASIYALAR VA QARZ TO'LOVLARI (UMUMIY KO'CHADAGI QARZLAR NAFIS METRIKALARI BILAN) ---
elif menu == "👥 Nasiyalar va Qarz To'lovlari":
  st.header("👥 Nasiyalar va Qarz To'lovlari Nazorati")

  df_qarz = pd.read_sql("SELECT * FROM sotuvlar WHERE qarz_summasi > 0", conn)
  df_tolovlar = pd.read_sql("SELECT * FROM qarz_tolovlari", conn)

  # ✨ KO'CHADAGI JAMI NASIYA VA STATISTIKANING METRIKASINI HISOBLASH
  jami_kochada_qarz = df_qarz["qarz_summasi"].sum() if not df_qarz.empty else 0.0
  qarzdor_mijozlar_soni = (
      df_qarz["mijoz_ismi"].nunique() if not df_qarz.empty else 0
  )
  jami_undirilgan_qarz = (
      df_tolovlar["tolangan_summa"].sum() if not df_tolovlar.empty else 0.0
  )

  col_q1, col_q2, col_q3 = st.columns(3)
  col_q1.metric("⚠️ Jami Ko'chadagi Qarz (Nasiya)", f"${jami_kochada_qarz:,.2f}")
  col_q2.metric("👥 Qarzdor Mijozlar Soni", f"{qarzdor_mijozlar_soni} ta")
  col_q3.metric("✅ Undirilgan (Yopilgan) Qarzlar", f"${jami_undirilgan_qarz:,.2f}")

  st.markdown("---")

  if df_qarz.empty:
    st.success("🎉 Ajoyib! Hozirda ko'chada qarzdorlar va nasiyalar yo'q.")
  else:
    st.subheader("📋 Qarzdorlar Ro'yxati")
    st.dataframe(df_qarz, use_container_width=True)

    st.markdown("---")
    st.subheader("💵 Qarz To'lovini Qabul Qilish")

    qarz_options = {}
    for _, r in df_qarz.iterrows():
      label = (
          f"Savdo ID: {r['id']} — Mijoz: {r['mijoz_ismi']} | Model:"
          f" {r['model']} | Qarz: ${r['qarz_summasi']:,.2f}"
      )
      qarz_options[label] = r["id"]

    selected_qarz_label = st.selectbox(
        "Qarzini to'layotgan mijozni tanlang:", list(qarz_options.keys())
    )
    qarz_id = qarz_options[selected_qarz_label]

    q_row = df_qarz[df_qarz["id"] == qarz_id].iloc[0]

    yangi_tolov = st.number_input(
        "To'lanayotgan summa ($):",
        min_value=0.1,
        max_value=float(q_row["qarz_summasi"]),
    )

    if st.button("💵 Qarz To'lovini Tasdiqlash", type="primary"):
      sana_b = datetime.now().strftime("%Y-%m-%d %H:%M")
      qolgan = q_row["qarz_summasi"] - yangi_tolov
      tolangan = q_row["tolangan_summa"] + yangi_tolov

      cursor.execute(
          "UPDATE sotuvlar SET qarz_summasi = ?, tolangan_summa = ? WHERE id = ?",
          (qolgan, tolangan, qarz_id),
      )
      cursor.execute(
          """
            INSERT INTO qarz_tolovlari (sana, sotuv_id, mijoz_ismi, tolangan_summa, qolgan_qarz)
            VALUES (?, ?, ?, ?, ?)
        """,
          (sana_b, qarz_id, q_row["mijoz_ismi"], yangi_tolov, qolgan),
      )
      conn.commit()
      st.toast(f"✅ DONE! ${yangi_tolov:,.2f} qarz to'lovi qabul qilindi.", icon="💵")
      st.rerun()

    if not df_tolovlar.empty:
      st.markdown("---")
      st.subheader("📜 Qarz To'lovlari Tarixi")
      st.dataframe(df_tolovlar, use_container_width=True)

# --- 10. SAVDO TARIXI VA HISOBOT ---
elif menu == "📜 Savdo Tarixi va Hisobot":
  st.header("📜 Savdolar Tarixi")
  df_sotuvlar = pd.read_sql("SELECT * FROM sotuvlar", conn)

  if df_sotuvlar.empty:
    st.info("Hozircha savdolar amalga oshirilmagan.")
  else:
    st.dataframe(df_sotuvlar, use_container_width=True)
