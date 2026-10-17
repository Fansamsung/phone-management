from datetime import datetime
import sqlite3
import pandas as pd
import streamlit as st

# Sahifa sozlamalari
st.set_page_config(
    page_title="Optom va Donabay Telefon Savdosi",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 🎨 MAXSUS CHIROYLI DIZAYN (CSS STILLAR)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    .item-card {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: bold;
        color: #1e3a8a !important;
    }
    .stButton>button {
        font-weight: bold;
        border-radius: 8px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Session state
if "kirim_savatcha" not in st.session_state:
  st.session_state.kirim_savatcha = []
if "oxirgi_qoshilgan" not in st.session_state:
  st.session_state.oxirgi_qoshilgan = None

# Bazaga ulanish
conn = sqlite3.connect("telefon_biznes.db", check_same_thread=False)
cursor = conn.cursor()

# 1. Partiyalar jadvali
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

# Migration
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

# 2. IMEI bazasi jadvali
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

# 3. Sotuvlar tarixi jadvali
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sotuvlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sana TEXT,
        partiya_id INTEGER,
        model TEXT,
        mijoz_ismi TEXT,
        sotilgan_soni INTEGER,
        sotuv_narx_dona REAL,
        umumiy_narx REAL,
        tolov_turi TEXT,
        tolangan_summa REAL,
        qarz_summasi REAL,
        umumiy_foyda REAL
    )
""")

# 4. Qarz to'lovlari jadvali
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

# 5. Partiya xarajatlari jadvali (Tannarx hisoblash uchun)
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

# --- CHAP TOMONDAGI BOSHQARUV PANEL (SIDEBAR) ---
st.sidebar.title("🎛️ Boshqaruv Paneli")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Bo'limni tanlang:",
    [
        "➕ Optom / Dona Kirim Qilish",
        "💰 Partiyalar Tannarxini Hisoblash",
        "✏️ Kirimlarni Boshqarish (O'chirish)",
        "📥 IMEI Excel / Qo'lda Kiritish yoki Yangilash",
        "🛒 Sotuv Qilish (Dona / Optom)",
        "🔍 IMEI Tekshirish va Sotilganlar Ro'yxati",
        "👥 Nasiyalar va Qarz To'lovlari",
        "📊 Savdo Tarixi va Foyda",
    ],
)

st.sidebar.markdown("---")
st.sidebar.info("💡 Dastur: Telefon Savdosi va IMEI Nazorati")

st.title("📱 Ulgurji va Donabay Telefon Savdosi Dasturi")
st.markdown("---")

# --- 1. OPTOM / DONA KIRIM QILISH ---
if menu == "➕ Optom / Dona Kirim Qilish":
  st.header("📦 Bir ta'minotchidan yuk kirim qilish")

  with st.container():
    taminotchi = st.text_input(
        "👤 Ta'minotchi / Kimdan olingan (masalan: Ali Dubai / Market 77)",
        key="taminotchi_input",
    )

  st.markdown("---")
  st.subheader("➕ Yangi Model Qo'shish Formasi")

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

  st.markdown(
      f"""
        <div style="
            background-color: #f1f5f9;
            border-left: 5px solid #3b82f6;
            padding: 10px 15px;
            border-radius: 6px;
            margin: 10px 0px 15px 0px;
            font-size: 16px;
            color: #1e293b;
        ">
            💰 <b>Ushbu modelning jami summasi:</b> <span style="color: #2563eb; font-weight: bold; font-size: 18px;">${ushbu_model_jami:,.2f}</span> ({soni} ta x ${olingan_narx:,.2f})
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.markdown("### 📲 IMEI 1 va IMEI 2 Kiritish Usulini Tanlang:")

  imei_kiritish_usuli = st.radio(
      "Kiritish qulayligini tanlang:",
      [
          "1️⃣ Har bir telefon uchun alohida kataklar (Skaner / Qo'lda)",
          "2️⃣ Excel fayl yuklash (.xlsx)",
          "3️⃣ Nusxalangan matn shaklida (Copy-Paste)",
          "4️⃣ Hozircha kiritmaslik (Keyinchalik Excelda yoki qo'lda yuklanadi)",
      ],
      horizontal=True,
  )

  imei_pairs = []

  if (
      imei_kiritish_usuli
      == "1️⃣ Har bir telefon uchun alohida kataklar (Skaner / Qo'lda)"
  ):
    st.info(
        f"Kiritilayotgan {soni} ta telefon uchun IMEI 1 va IMEI 2 raqamlarini"
        " kiriting:"
    )

    max_rows = min(int(soni), 50)
    for i in range(max_rows):
      c_no, c_im1, c_im2 = st.columns([1, 4, 4])
      with c_no:
        st.markdown(f"**#{i+1}-telefon:**")
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
            placeholder="IMEI2 (ixtiyoriy)",
            label_visibility="collapsed",
        )

      if im1.strip():
        imei_pairs.append((im1.strip(), im2.strip()))

  elif imei_kiritish_usuli == "2️⃣ Excel fayl yuklash (.xlsx)":
    uploaded_excel = st.file_uploader(
        "IMEI raqamlari mavjud Excel faylni kiriting",
        type=["xlsx", "xls"],
        key="kirim_excel",
    )
    st.caption("Eslatma: Excelda **IMEI** va **IMEI2** ustunlari bo'lishi kerak.")
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
        st.success(
            f"✅ Exceldan {len(imei_pairs)} ta telefon IMEI lari o'qib olindi!"
        )
      except Exception as e:
        st.error(f"Excelni o'qishda xatolik: {e}")

  elif imei_kiritish_usuli == "3️⃣ Nusxalangan matn shaklida (Copy-Paste)":
    st.caption(
        "Har bir qatorda bittadan: `358123456789012, 358123456789013` deb"
        " vergul bilan yopishtiring."
    )
    imei_matn = st.text_area(
        "IMEI lar ro'yxati:",
        height=120,
        placeholder="358123456789012, 358123456789013\n359876543210987,"
        " 359876543210988",
    )
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

  st.markdown("<br>", unsafe_allow_html=True)

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
      st.rerun()
    else:
      st.error("❌ Iltimos, model nomini va sonini kiriting!")

  if st.session_state.oxirgi_qoshilgan:
    oxirgi = st.session_state.oxirgi_qoshilgan
    st.success(
        f"✅ MODEL RO'YXATGA QO'SHILDI: {oxirgi['model']} ({oxirgi['xotira']}) -"
        f" {oxirgi['soni']} ta - Dona: ${oxirgi['olingan_narx']:,.2f} - Jami:"
        f" ${oxirgi['jami_summa']:,.2f}"
    )

  if st.session_state.kirim_savatcha:
    st.markdown("---")
    st.subheader("📋 Kirim qilinayotgan barcha telefonlar ro'yxati:")

    df_savatcha = pd.DataFrame(st.session_state.kirim_savatcha)

    jami_soni = df_savatcha["soni"].sum()
    jami_partiya_summasi = df_savatcha["jami_summa"].sum()

    for idx, item in enumerate(st.session_state.kirim_savatcha):
      imei_soni = len(item["imei_pairs"])
      m_nomi = item["model"]
      m_xotira = item["xotira"]
      m_rang = item["rang"]
      m_grade = item["grade"]
      m_soni = item["soni"]
      m_dona = item["olingan_narx"]
      m_jami = item["jami_summa"]

      st.markdown(
          f"""
            <div class="item-card">
                <span style="font-size: 18px; font-weight: bold; color: #1e293b;">
                    #{idx+1}. {m_nomi} ({m_xotira})
                </span> - <span style="color: #64748b;">Rangi: {m_rang} - Grade: {m_grade}</span><br>
                <span style="font-size: 16px; font-weight: 600; color: #0f766e;">
                    📦 Soni: {m_soni} ta - 💵 Dona narxi: ${m_dona:,.2f} - 💰 Jami: ${m_jami:,.2f} - 📱 Kiritilgan IMEI: {imei_soni} ta
                </span>
            </div>
            """,
          unsafe_allow_html=True,
      )

    st.markdown("### 📊 PARTIYAGA TEGISHLI JAMI HISOB-KITOB:")
    m_col1, m_col2 = st.columns(2)
    m_col1.metric("📦 Jami Telefonlar Soni", f"{jami_soni} ta")
    m_col2.metric("💵 Jami Yuk Summasi", f"${jami_partiya_summasi:,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
      if st.button(
          "🚀 BARCHASINI OMBORGA KIRIM QILISH",
          type="primary",
          use_container_width=True,
      ):
        sana = datetime.now().strftime("%Y-%m-%d %H:%M")
        for item in st.session_state.kirim_savatcha:
          # Boshlang'ich tannarx olingan narxga teng deb saqlanadi
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
        st.success(
            f"✅ Barcha telefonlar muvaffaqiyatli omborga saqlandi! Jami:"
            f" {jami_soni} ta (${jami_partiya_summasi:,.2f})"
        )
        st.rerun()

    with col_btn2:
      if st.button(
          "🗑️ Ro'yxatni tozalash", type="secondary", use_container_width=True
      ):
        st.session_state.kirim_savatcha = []
        st.session_state.oxirgi_qoshilgan = None
        st.rerun()

# --- 2. PARTIYALAR TANNARXINI HISOBLASH (YANGI BO'LIM) ---
elif menu == "💰 Partiyalar Tannarxini Hisoblash":
  st.header("🛠️ Partiyaga Qo'shimcha Xarajatlar Qo'shish va Tannarx Chiqarish")
  st.info(
      "Bu bo'limda olingan partiyaga ketgan **Remont, Karobka, Dostavka,"
      " Soliq** va boshqa xarajatlarni kiritib, 1 dona telefonning **Aniq"
      " Tannarxini** chiqarishingiz mumkin."
  )

  df_partiyalar = pd.read_sql("SELECT * FROM partiyalar", conn)

  if df_partiyalar.empty:
    st.warning("Hozircha omborda partiyalar yo'q. Avval kirim qiling!")
  else:
    partiya_id_selected = st.selectbox(
        "Tannarxini hisoblamoqchi bo'lgan Partiya ID raqamini tanlang:",
        df_partiyalar["id"].tolist(),
    )

    p_row = df_partiyalar[df_partiyalar["id"] == partiya_id_selected].iloc[0]

    # Partiya haqida umumiy ma'lumot
    soni = p_row["boshlangich_soni"]
    olingan_narx = p_row["olingan_narx"]
    xotira = p_row["xotira"] if p_row["xotira"] else ""
    rang = p_row["rang"] if p_row["rang"] else ""

    st.markdown(
        f"### 📱 Partiya: **{p_row['model']} ({xotira} - {rang})** | Soni:"
        f" **{soni} ta** | Boshlang'ich Narxi: **${olingan_narx:,.2f}**"
    )

    st.markdown("---")
    col_x1, col_x2 = st.columns([1, 1])

    with col_x1:
      st.subheader("➕ Yangi Xarajat Qo'shish")
      xarajat_nomi = st.text_input(
          "Xarajat nomi (masalan: Remont, Karobka, Dostavka)",
          placeholder="masalan: Usta haqisi / Karobka",
      )

      xarajat_turi = st.radio(
          "Xarajat turi:",
          [
              "🏢 Jami partiya uchun umumiy summa (telefonlarga teng bo'linadi)",
              "📱 Har bir dona telefon uchun alohida summa",
          ],
      )

      xarajat_summasi = st.number_input(
          "Summa ($)", min_value=0.0, step=10.0, value=0.0
      )

      if st.button("➕ Xarajatni Saqlash"):
        if xarajat_nomi and xarajat_summasi > 0:
          sana_h = datetime.now().strftime("%Y-%m-%d %H:%M")
          tur_str = (
              "Partiya uchun"
              if "Jami partiya" in xarajat_turi
              else "Dona uchun"
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
          st.success("✅ Xarajat muvaffaqiyatli qo'shildi!")
          st.rerun()
        else:
          st.error("❌ Iltimos, xarajat nomi va summasini to'g'ri kiriting!")

    with col_x2:
      st.subheader("📋 Ushbu Partiyaning Xarajatlari Tarixi:")
      df_xarajat = pd.read_sql(
          f"SELECT id, sana, xarajat_nomi, summa, tur FROM partiya_xarajatlari WHERE partiya_id = {partiya_id_selected}",
          conn,
      )

      if df_xarajat.empty:
        st.caption("Hozircha bu partiyaga qo'shimcha xarajatlar kiritilmadi.")
      else:
        st.dataframe(df_xarajat, use_container_width=True)

        silish_x_id = st.selectbox(
            "O'chirmoqchi bo'lgan xarajat ID raqami:", df_xarajat["id"].tolist()
        )
        if st.button("🗑️ Xarajatni o'chirish"):
          cursor.execute(
              "DELETE FROM partiya_xarajatlari WHERE id = ?", (silish_x_id,)
          )
          conn.commit()
          st.success("✅ Xarajat o'chirildi!")
          st.rerun()

    # TANNARXNI REAL-TIME HISOBLASH
    st.markdown("---")
    st.subheader("📊 TANNARX HISOB-KITOBI XULOSASI:")

    jami_partiya_xarajat = 0.0
    har_bir_dona_xarajat = 0.0

    if not df_xarajat.empty:
      for _, row_x in df_xarajat.iterrows():
        if row_x["tur"] == "Partiya uchun":
          jami_partiya_xarajat += row_x["summa"]
        else:
          har_bir_dona_xarajat += row_x["summa"]

    # 1 dona telefon uchun jami qo'shimcha xarajat
    dona_qoshimcha = (
        jami_partiya_xarajat / soni if soni > 0 else 0
    ) + har_bir_dona_xarajat
    yangi_tannarx = olingan_narx + dona_qoshimcha
    jami_partiya_tannarxi = yangi_tannarx * soni

    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("💵 Boshlang'ich Olingan Narxi", f"${olingan_narx:,.2f}")
    c_m2.metric(
        "🛠️ 1 Dona uchun Qo'shimcha Xarajat", f"+${dona_qoshimcha:,.2f}"
    )
    c_m3.metric(
        "⭐ YANGI ANIQ TANNARX (1 dona)",
        f"${yangi_tannarx:,.2f}",
        delta=f"+${dona_qoshimcha:,.2f}",
    )

    st.markdown(
        f"""
        <div style="
            background-color: #ecfdf5;
            border-left: 5px solid #10b981;
            padding: 12px 20px;
            border-radius: 8px;
            margin: 15px 0px;
            font-size: 18px;
            color: #065f46;
        ">
            💰 <b>Ushbu <u>{soni} ta</u> telefonning umumiy tannarx qiymati:</b> 
            <span style="font-weight: 800; font-size: 24px; color: #047857;">${jami_partiya_tannarxi:,.2f}</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if st.button("💾 USHBU TANNARXNI BAZAGA SAQLASH VA YANGILASH"):
      cursor.execute(
          "UPDATE partiyalar SET tannarx = ? WHERE id = ?",
          (yangi_tannarx, partiya_id_selected),
      )
      conn.commit()
      st.balloons()
      st.success(
          f"✅ Partiyaning tannarxi muvaffaqiyatli saqlandi! Yangi tannarx:"
          f" ${yangi_tannarx:,.2f}"
      )
      st.rerun()

# --- 3. KIRIMLARNI BOSHQARISH ---
elif menu == "✏️ Kirimlarni Boshqarish (O'chirish)":
  st.header("📋 Kirim qilingan partiyalar va ularning summalari")
  st.warning(
      "Agar sonini yoki narxini adashib noto'g'ri kiritgan bo'lsangiz, o'sha"
      " partiyani o'chirib, qaytadan to'g'ri kiritishingiz mumkin."
  )

  df_partiya = pd.read_sql("SELECT * FROM partiyalar", conn)

  if df_partiya.empty:
    st.info("Hozircha omborda partiyalar yo'q.")
  else:
    df_partiya["boshlangich_soni"] = pd.to_numeric(
        df_partiya["boshlangich_soni"], errors="coerce"
    ).fillna(0)
    df_partiya["olingan_narx"] = pd.to_numeric(
        df_partiya["olingan_narx"], errors="coerce"
    ).fillna(0)
    df_partiya["tannarx"] = pd.to_numeric(
        df_partiya["tannarx"], errors="coerce"
    ).fillna(df_partiya["olingan_narx"])

    df_partiya["Jami Olingan Summa ($)"] = (
        df_partiya["boshlangich_soni"] * df_partiya["olingan_narx"]
    )
    df_partiya["Jami Tannarx Summasi ($)"] = (
        df_partiya["boshlangich_soni"] * df_partiya["tannarx"]
    )

    jami_son = df_partiya["boshlangich_soni"].sum()
    jami_summa_barcha = df_partiya["Jami Tannarx Summasi ($)"].sum()

    m_col1, m_col2 = st.columns(2)
    m_col1.metric("📦 Ombordagi Partiyalar Soni", f"{int(jami_son)} ta")
    m_col2.metric("💵 Jami Kirim Qilingan Yuk Tannarxi", f"${jami_summa_barcha:,.2f}")

    st.markdown("---")
    st.markdown("### 📊 Partiyalar Ro'yxati va Summalari:")

    df_display = df_partiya[[
        "id",
        "sana",
        "taminotchi",
        "model",
        "xotira",
        "rang",
        "grade",
        "boshlangich_soni",
        "olingan_narx",
        "tannarx",
        "Jami Tannarx Summasi ($)",
    ]].copy()

    df_display.columns = [
        "ID",
        "Sana",
        "Ta'minotchi",
        "Model",
        "Xotira",
        "Rang",
        "Grade",
        "Soni (ta)",
        "Olingan Narxi ($)",
        "Tannarx ($)",
        "Jami Tannarx ($)",
    ]

    st.dataframe(df_display, use_container_width=True)

    st.markdown("---")
    silish_id = st.selectbox(
        "O'chirmoqchi bo'lgan partiya ID raqamini tanlang:",
        df_partiya["id"].tolist(),
    )

    if st.button("🗑️ Tanlangan partiyani va unga tegishli IMEI larni o'chirish"):
      cursor.execute("DELETE FROM partiyalar WHERE id = ?", (silish_id,))
      cursor.execute("DELETE FROM imei_baza WHERE partiya_id = ?", (silish_id,))
      cursor.execute(
          "DELETE FROM partiya_xarajatlari WHERE partiya_id = ?", (silish_id,)
      )
      conn.commit()
      st.success(
          f"✅ Bajarildi! {silish_id}-ID raqamli partiya muvaffaqiyatli"
          " o'chirildi!"
      )
      st.rerun()

# --- 4. IMEI EXCEL / QO'LDA KIRITISH YOKI YANGILASH ---
elif menu == "📥 IMEI Excel / Qo'lda Kiritish yoki Yangilash":
  st.header("📲 Partiyadagi IMEI raqamlarni yangilash / qo'lda kiritish")

  df_partiya = pd.read_sql("SELECT * FROM partiyalar", conn)
  if df_partiya.empty:
    st.info("Hozircha omborda partiyalar yo'q. Avval kirim qiling!")
  else:
    secilgan_partiya_id = st.selectbox(
        "IMEI raqamlarini to'g'rilamoqchi bo'lgan Partiya ID raqamini tanlang:",
        df_partiya["id"].tolist(),
    )

    partiya_row = df_partiya[df_partiya["id"] == secilgan_partiya_id].iloc[0]
    st.info(
        f"Tanlangan partiya: **{partiya_row['model']} ({partiya_row['xotira']} -"
        f" {partiya_row['rang']})** | Soni: **{partiya_row['boshlangich_soni']} ta**"
    )

    tab_ex, tab_manual = st.tabs(
        ["📄 Excel orqali o'zgartirish", "✍️ Qo'lda yakka-yakka to'g'rilash"]
    )

    with tab_ex:
      uploaded_file = st.file_uploader(
          "IMEI raqamlari yozilgan Excel faylni yuklang (.xlsx)",
          type=["xlsx", "xls"],
      )
      st.caption("Excelda **IMEI** va **IMEI2** nomli ustunlar bo'lishi kerak.")

      if st.button("🚀 Exceldagi IMEI larni Bazaga Yuklash"):
        if uploaded_file is not None:
          try:
            df_excel = pd.read_excel(uploaded_file)
            cursor.execute(
                "DELETE FROM imei_baza WHERE partiya_id = ?",
                (secilgan_partiya_id,),
            )

            for _, row in df_excel.iterrows():
              imei1 = (
                  str(row["IMEI"]).strip().replace(".0", "")
                  if "IMEI" in df_excel.columns
                  else ""
              )
              imei2 = (
                  str(row["IMEI2"]).strip().replace(".0", "")
                  if "IMEI2" in df_excel.columns
                  else ""
              )
              if imei1 and imei1 != "nan":
                cursor.execute(
                    """
                            INSERT INTO imei_baza (partiya_id, model, imei1, imei2, status)
                            VALUES (?, ?, ?, ?, 'Omborda')
                        """,
                    (secilgan_partiya_id, partiya_row["model"], imei1, imei2),
                )

            conn.commit()
            st.balloons()
            st.success("✅ Exceldagi barcha IMEI lar muvaffaqiyatli saqlandi!")
            st.rerun()
          except Exception as e:
            st.error(f"Xatolik: {e}")

    with tab_manual:
      st.markdown(
          "### Ushbu partiyadagi mavjud telefonlar va ularning IMEI lari:"
      )

      cursor.execute(
          "SELECT id, imei1, imei2 FROM imei_baza WHERE partiya_id = ?",
          (secilgan_partiya_id,),
      )
      imei_list = cursor.fetchall()

      if not imei_list:
        st.warning("Bu partiyada hali IMEI raqamlari mavjud emas.")
      else:
        with st.form("imei_update_form"):
          updated_data = []
          for row_id, im1, im2 in imei_list:
            c1, c2 = st.columns(2)
            with c1:
              val_im1 = st.text_input(
                  f"IMEI 1 (ID: {row_id})",
                  value=im1,
                  key=f"m_im1_{row_id}",
              )
            with c2:
              val_im2 = st.text_input(
                  f"IMEI 2 (ID: {row_id})",
                  value=im2,
                  key=f"m_im2_{row_id}",
              )
            updated_data.append((row_id, val_im1, val_im2))

          if st.form_submit_button("💾 BARCHA IMEI LARNI SAQLASH"):
            for r_id, new_i1, new_i2 in updated_data:
              cursor.execute(
                  "UPDATE imei_baza SET imei1 = ?, imei2 = ? WHERE id = ?",
                  (new_i1.strip(), new_i2.strip(), r_id),
              )
            conn.commit()
            st.success("✅ Barcha IMEI raqamlari muvaffaqiyatli yangilandi!")
            st.rerun()

# --- 5. SOTUV QILISH ---
elif menu == "🛒 Sotuv Qilish (Dona / Optom)":
  st.header("Ombordagi qoldiqlar va Sotuvni Rasmiylashtirish")

  query_ombor = """
        SELECT i.id, i.partiya_id, i.model, i.imei1, i.imei2, p.xotira, p.rang, p.grade, p.olingan_narx, p.tannarx, p.taminotchi
        FROM imei_baza i
        JOIN partiyalar p ON i.partiya_id = p.id
        WHERE i.status = 'Omborda'
    """
  df_omborda = pd.read_sql(query_ombor, conn)

  if df_omborda.empty:
    st.info("Hozircha omborda sotish uchun telefonlar yo'q!")
  else:
    st.markdown("### 📋 Ombordagi Model Qoldiqlari:")
    qoldiq_summary = (
        df_omborda.groupby(
            ["partiya_id", "model", "xotira", "rang", "tannarx"]
        )
        .size()
        .reset_index(name="Ombordagi Qoldiq (ta)")
    )
    st.dataframe(qoldiq_summary, use_container_width=True)

    st.markdown("---")
    st.markdown("### 💸 Sotuvni Rasmiylashtirish")

    partiya_list = df_omborda["partiya_id"].unique().tolist()
    secilgan_partiya_id = st.selectbox(
        "Sotiladigan Partiya ID raqamini tanlang:", partiya_list
    )

    partiya_df = df_omborda[df_omborda["partiya_id"] == secilgan_partiya_id]

    first_row = partiya_df.iloc[0]
    tannarx_val = (
        first_row["tannarx"]
        if pd.notnull(first_row["tannarx"])
        else first_row["olingan_narx"]
    )

    st.info(
        f"Ta'minotchi: **{first_row['taminotchi'] if first_row['taminotchi'] else 'Noma’lum'}** - "
        f"Model: **{first_row['model']} ({first_row['xotira']} - {first_row['rang']} - Grade: {first_row['grade']})** - "
        f"Tannarxi: **${tannarx_val:,.2f}** - Ombordagi qoldiq: **{len(partiya_df)} ta**"
    )

    mijoz_ismi = st.text_input(
        "👤 Mijozning ismi yoki Do'kon nomi (Kimga sotilyapti?)"
    )

    st.markdown("#### 🔍 IMEI va Model bo'yicha tezkor qidiruv:")
    imei_search = st.text_input(
        "🔎 IMEI raqami yoki model nomini kiriting (filtrlash uchun):",
        placeholder="masalan: 35812 yoki iPhone...",
    )

    if imei_search.strip():
      filtered_df = partiya_df[
          partiya_df["imei1"].str.contains(
              imei_search.strip(), case=False, na=False
          )
          | partiya_df["imei2"].str.contains(
              imei_search.strip(), case=False, na=False
          )
          | partiya_df["model"].str.contains(
              imei_search.strip(), case=False, na=False
          )
      ]
    else:
      filtered_df = partiya_df

    st.caption(
        f"💡 Qidiruv natijasida **{len(filtered_df)} ta** IMEI raqami"
        " topildi."
    )

    imei_options = {}
    for _, row in filtered_df.iterrows():
      label = (
          f"{row['imei1']} — {row['model']} ({row['xotira']} - {row['rang']})"
      )
      imei_options[label] = row["imei1"]

    tanlash_usuli = st.radio(
        "Sotuv turini va IMEI tanlash usulini belgilang:",
        [
            "1️⃣ Donalab sotish (1 ta IMEI tanlash)",
            "2️⃣ Ro'yxatdan bir nechta belgilash (Multiselect)",
            "3️⃣ Ko'plab IMEI larni nusxalab (Copy-Paste) kiritish",
        ],
    )

    tanlangan_imeilar = []

    if tanlash_usuli == "1️⃣ Donalab sotish (1 ta IMEI tanlash)":
      dona_label = st.selectbox(
          "Sotiladigan 1 dona telefon IMEI raqamini tanlang:",
          ["-- Tanlang --"] + list(imei_options.keys()),
      )
      if dona_label and dona_label != "-- Tanlang --":
        tanlangan_imeilar = [imei_options[dona_label]]

    elif tanlash_usuli == "2️⃣ Ro'yxatdan bir nechta belgilash (Multiselect)":
      selected_labels = st.multiselect(
          "Sotiladigan IMEI larni ro'yxatdan belgilang:",
          list(imei_options.keys()),
      )
      tanlangan_imeilar = [imei_options[lbl] for lbl in selected_labels]

    else:
      st.markdown(
          "👉 *Sotiladigan IMEI larni nusxalab, pastdagi katakka **har birini"
          " yangi qatordan** yopishtiring (Ctrl+V):*"
      )
      imei_matn = st.text_area(
          "IMEI ro'yxati (har bir qatorda bittadan):", height=120
      )
      if imei_matn:
        kiritilganlar = [
            str(x).strip().replace(".0", "")
            for x in imei_matn.split("\n")
            if str(x).strip()
        ]
        ombor_set = set(partiya_df["imei1"].tolist())
        tanlangan_imeilar = [i for i in kiritilganlar if i in ombor_set]
        topilmaganlar = [i for i in kiritilganlar if i not in ombor_set]

        st.info(f"✅ Topilgan va belgilangan IMEI lar: {len(tanlangan_imeilar)} ta")
        if topilmaganlar:
          st.error(
              f"❌ Ushbu partiyada topilmagan IMEI lar: {len(topilmaganlar)} ta"
          )

    sotilgan_soni = len(tanlangan_imeilar)

    if sotilgan_soni > 0:
      st.markdown("---")
      st.write(
          f"💰 Tanlangan va sotilayotgan jami telefonlar soni:"
          f" **{sotilgan_soni} ta**"
      )

      sotuv_narx_dona = st.number_input(
          "💵 1 dona uchun SOTILISH narxi ($)", min_value=0.0, step=1.0
      )
      umumiy_narx = sotilgan_soni * sotuv_narx_dona

      st.markdown(
          f"""
            <div style="
                background-color: #e0f2fe;
                border-left: 5px solid #0284c7;
                padding: 10px 15px;
                border-radius: 6px;
                margin: 10px 0px 15px 0px;
                font-size: 18px;
                color: #0369a1;
            ">
                💰 <b>JAMI SAVDO SUMMASI:</b> <span style="font-weight: bold; font-size: 22px; color: #0284c7;">${umumiy_narx:,.2f}</span>
            </div>
        """,
          unsafe_allow_html=True,
      )

      tolov_turi = st.selectbox(
          "To'lov turi", ["Naqd", "Nasiya (Qarz)", "Perevod"]
      )

      if tolov_turi == "Nasiya (Qarz)":
        tolangan_summa = st.number_input(
            "Hozir bergan puli (Avans) ($)",
            min_value=0.0,
            max_value=float(umumiy_narx),
            value=0.0,
            step=1.0,
        )
      else:
        tolangan_summa = umumiy_narx

      qarz_summasi = umumiy_narx - tolangan_summa

      if st.button("🚀 Sotishni Tasdiqlash va IMEI larni biriktirish"):
        if mijoz_ismi:
          sana = datetime.now().strftime("%Y-%m-%d %H:%M")
          bir_dona_foyda = sotuv_narx_dona - tannarx_val
          umumiy_foyda = bir_dona_foyda * sotilgan_soni

          cursor.execute(
              """
                    INSERT INTO sotuvlar (sana, partiya_id, model, mijoz_ismi, sotilgan_soni, sotuv_narx_dona, umumiy_narx, tolov_turi, tolangan_summa, qarz_summasi, umumiy_foyda)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
              (
                  sana,
                  secilgan_partiya_id,
                  first_row["model"],
                  mijoz_ismi,
                  sotilgan_soni,
                  sotuv_narx_dona,
                  umumiy_narx,
                  tolov_turi,
                  tolangan_summa,
                  qarz_summasi,
                  umumiy_foyda,
              ),
          )

          for imei in tanlangan_imeilar:
            cursor.execute(
                """
                        UPDATE imei_baza 
                        SET status = 'Sotilgan', mijoz_ismi = ?, sotuv_sana = ? 
                        WHERE imei1 = ?
                    """,
                (mijoz_ismi, sana, imei),
            )

          conn.commit()
          st.balloons()
          st.success(
              f"✅ SOTUV MUVAFFAQIYATLI AMALGA OSHDI!\n\n• **Mijoz:**"
              f" {mijoz_ismi}\n• **Sotilgan soni:** {sotilgan_soni} ta\n•"
              f" **Qolgan qarz:** ${qarz_summasi:,.2f}"
          )
          st.rerun()
        else:
          st.error("❌ Iltimos, mijoz ismini kiriting!")

# --- 6. IMEI TEKSHIRISH VA SOTILGANLAR RO'YXATI ---
elif menu == "🔍 IMEI Tekshirish va Sotilganlar Ro'yxati":
  st.header("Qaytarib olib kelingan telefonni tekshirish va Sotilgan IMEI lar")

  tab1, tab2 = st.tabs(
      ["🔍 Bitta IMEI ni Qidirish", "📋 Partiya bo'yicha sotilgan IMEI lar"]
  )

  with tab1:
    qidiruv_imei = st.text_input(
        "Telefonning IMEI yoki IMEI2 raqamini kiriting:"
    )

    if qidiruv_imei:
      cursor.execute(
          """
                SELECT * FROM imei_baza 
                WHERE imei1 LIKE ? OR imei2 LIKE ?
            """,
          (f"%{qidiruv_imei}%", f"%{qidiruv_imei}%"),
      )
      natija = cursor.fetchone()

      if natija:
        st.success("✅ Telefon bazadan topildi!")
        st.write(f"• **Partiya ID:** {natija[1]}")
        st.write(f"• **Model:** {natija[2]}")
        st.write(f"• **IMEI 1:** {natija[3]}")
        st.write(f"• **IMEI 2:** {natija[4]}")
        st.write(f"• **Holati (Status):** {natija[5]}")
        st.write(
            f"• **Sotib olgan mijoz:** {natija[6] if natija[6] else 'Hali sotilmagan'}"
        )
        st.write(f"• **Sotilgan sana:** {natija[7] if natija[7] else '-'}")

        if natija[5] == "Sotilgan":
          if st.button("Bu telefonni Qaytgan (Brak/Almashinuv) deb belgilash"):
            cursor.execute(
                "UPDATE imei_baza SET status = 'Qaytarilgan' WHERE id = ?",
                (natija[0],),
            )
            conn.commit()
            st.warning(
                "Telefon statusi 'Qaytarilgan' deb o'zgartirildi va omborga"
                " qaytarildi."
            )
            st.rerun()
      else:
        st.error("❌ Bunday IMEI raqami bazadan topilmadi!")

  with tab2:
    df_partiyalar = pd.read_sql("SELECT * FROM partiyalar", conn)
    if df_partiyalar.empty:
      st.info("Hozircha partiyalar mavjud emas.")
    else:
      partiya_sanoq = st.selectbox(
          "Qaysi Partiya bo'yicha sotilgan IMEI larni ko'rmoqchisiz?",
          ["Barcha partiyalar"] + df_partiyalar["id"].tolist(),
      )

      if partiya_sanoq == "Barcha partiyalar":
        df_sotilgan_imei = pd.read_sql(
            "SELECT partiya_id, model, imei1, imei2, mijoz_ismi, sotuv_sana FROM imei_baza WHERE status = 'Sotilgan'",
            conn,
        )
      else:
        df_sotilgan_imei = pd.read_sql(
            f"SELECT partiya_id, model, imei1, imei2, mijoz_ismi, sotuv_sana FROM imei_baza WHERE status = 'Sotilgan' AND partiya_id = {partiya_sanoq}",
            conn,
        )

      if df_sotilgan_imei.empty:
        st.info("Ushbu partiya bo'yicha hali sotilgan IMEI lar yo'q.")
      else:
        st.write(
            f"Jami sotilgan telefonlar soni: **{len(df_sotilgan_imei)} ta**"
        )
        st.dataframe(df_sotilgan_imei)

# --- 7. NASIYALAR VA QARZ TO'LOVLARI ---
elif menu == "👥 Nasiyalar va Qarz To'lovlari":
  st.header("Mijozlar Qarzlari va Qarz Qabul Qilish")

  df_qarz = pd.read_sql(
      "SELECT * FROM sotuvlar WHERE qarz_summasi > 0", conn
  )

  if df_qarz.empty:
    st.info("Hozirda nasiyaga olingan savdolar yo'q. Hamma qarzi yo'q!")
  else:
    jami_qarz = df_qarz["qarz_summasi"].sum()
    st.metric(
        label="Umumiy Undirilmagan Qarzlar (Nasiya)",
        value=f"${jami_qarz:,.2f}",
    )

    st.markdown("### 📋 Qarzdor Mijozlar Ro'yxati:")
    st.dataframe(
        df_qarz[[
            "id",
            "sana",
            "mijoz_ismi",
            "model",
            "sotilgan_soni",
            "umumiy_narx",
            "tolangan_summa",
            "qarz_summasi",
        ]]
    )

    st.markdown("---")
    st.markdown("### 💵 Qarz To'lovini Qabul Qilish")

    qarz_sotuv_id = st.selectbox(
        "Qarz berayotgan mijozning Savdo ID raqamini tanlang",
        df_qarz["id"].tolist(),
    )

    tanlangan_qarz = df_qarz[df_qarz["id"] == qarz_sotuv_id].iloc[0]
    qolgan_qarz = tanlangan_qarz["qarz_summasi"]

    st.info(
        f"Mijoz: {tanlangan_qarz['mijoz_ismi']} - Model: {tanlangan_qarz['model']} - Hozirgi qolgan qarzi: ${qolgan_qarz:,.2f}"
    )

    yangi_tolov = st.number_input(
        "To'lanayotgan summa ($)",
        min_value=0.1,
        max_value=float(qolgan_qarz),
        step=10.0,
    )

    if st.button("Qarz To'lovini Tasdiqlash"):
      sana_bugun = datetime.now().strftime("%Y-%m-%d %H:%M")
      yangi_qolgan_qarz = qolgan_qarz - yangi_tolov
      yangi_tolangan_summa = tanlangan_qarz["tolangan_summa"] + yangi_tolov

      cursor.execute(
          "UPDATE sotuvlar SET qarz_summasi = ?, tolangan_summa = ? WHERE id = ?",
          (yangi_qolgan_qarz, yangi_tolangan_summa, qarz_sotuv_id),
      )

      cursor.execute(
          """
            INSERT INTO qarz_tolovlari (sana, sotuv_id, mijoz_ismi, tolangan_summa, qolgan_qarz)
            VALUES (?, ?, ?, ?, ?)
        """,
          (
              sana_bugun,
              qarz_sotuv_id,
              tanlangan_qarz["mijoz_ismi"],
              yangi_tolov,
              yangi_qolgan_qarz,
          ),
      )
      conn.commit()

      st.balloons()
      st.success(
          f"✅ TO'LOV MUVAFFAQIYATLI QABUL QILINDI! Mijoz: {tanlangan_qarz['mijoz_ismi']} - Bergan puli: ${yangi_tolov:,.2f} - Qolgan qarz:${yangi_qolgan_qarz:,.2f}"
      )
      st.rerun()

  st.markdown("---")
  st.markdown("### 📜 Qarz To'lovlari Tarixi")
  df_tolovlar = pd.read_sql("SELECT * FROM qarz_tolovlari", conn)
  if not df_tolovlar.empty:
    st.dataframe(df_tolovlar)

# --- 8. SAVDO TARIXI VA FOYDA ---
elif menu == "📊 Savdo Tarixi va Foyda":
  st.header("Barcha Sotuvlar va Sof Foyda Hisoboti")

  df_sotuvlar = pd.read_sql("SELECT * FROM sotuvlar", conn)

  if df_sotuvlar.empty:
    st.info("Hozircha sotuvlar amalga oshirilmagan.")
  else:
    jami_sof_foyda = df_sotuvlar["umumiy_foyda"].sum()
    st.metric(
        label="Umumiy Sof Foyda (Barcha savdolardan)",
        value=f"${jami_sof_foyda:,.2f}",
    )

    st.markdown("### Amalga oshirilgan barcha savdolar:")
    st.dataframe(df_sotuvlar)