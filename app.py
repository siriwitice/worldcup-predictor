import streamlit as st
import pandas as pd
import os

# ----------------- ตั้งค่าหน้าเว็บ -----------------
st.set_page_config(page_title="🏆 World Cup 2026 Predictor", page_icon="⚽", layout="wide")

# ----------------- กำหนดชื่อไฟล์ -----------------
MATCHES_FILE = "matches.csv"
PREDICTIONS_FILE = "predictions.csv"

# ----------------- ฟังก์ชันหลัก -----------------
def load_data():
    # โหลดข้อมูลจาก CSV
    matches_df = pd.read_csv(MATCHES_FILE)
    preds_df = pd.read_csv(PREDICTIONS_FILE)
    return matches_df, preds_df

def save_matches(df):
    df.to_csv(MATCHES_FILE, index=False)

def save_predictions(df):
    df.to_csv(PREDICTIONS_FILE, index=False)

def calculate_points(pred_a, pred_b, actual_a, actual_b):
    # หากยังไม่กรอกผล หรือยังไม่มีผลแข่ง ให้คะแนนเป็น 0
    if pd.isna(actual_a) or pd.isna(actual_b) or pd.isna(pred_a) or pd.isna(pred_b):
        return 0
    
    points = 0
    # หาผลลัพธ์ว่าใครชนะ หรือเสมอ
    actual_result = "A" if actual_a > actual_b else "B" if actual_b > actual_a else "Draw"
    pred_result = "A" if pred_a > pred_b else "B" if pred_b > pred_a else "Draw"
    
    # 1. ถ้าทายผล (แพ้/ชนะ/เสมอ) ถูกต้อง ได้ 3 คะแนน
    if actual_result == pred_result:
        points += 3
        # 2. โบนัสทายสกอร์ถูกเป๊ะ (+ ผลรวมประตู)
        if actual_a == pred_a and actual_b == pred_b:
            points += int(actual_a + actual_b)
            
    return points

# โหลดข้อมูล
matches_df, preds_df = load_data()

st.title("⚽ World Cup 2026 Predictor")
st.markdown("ยินดีต้อนรับสู่ระบบทายผลฟุตบอลโลก 2026!")

# สร้าง Tabs สำหรับแยกหน้าการใช้งาน
tab1, tab2, tab3, tab4 = st.tabs(["📊 ตารางคะแนน (Leaderboard)", "🔮 ทายผลการแข่งขัน", "📅 โปรแกรมการแข่งขัน", "⚙️ สำหรับแอดมิน (อัปเดตผล)"])

# ----------------- หน้า 1: Leaderboard -----------------
with tab1:
    st.header("🏆 ตารางคะแนนรวม")
    if not preds_df.empty:
        # รวมคะแนนตามชื่อ User
        leaderboard = preds_df.groupby("User_Email")["Points"].sum().reset_index()
        leaderboard = leaderboard.rename(columns={"User_Email": "ชื่อผู้เล่น", "Points": "คะแนนรวม"})
        leaderboard = leaderboard.sort_values(by="คะแนนรวม", ascending=False).reset_index(drop=True)
        leaderboard.index = leaderboard.index + 1 # ให้เริ่มที่อันดับ 1
        st.dataframe(leaderboard, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลการทายผล")

# ----------------- หน้า 2: ทายผลการแข่งขัน -----------------
with tab2:
    st.header("🔮 กรอกทายผลของคุณ")
    
    # เลือกชื่อผู้เล่น (จำลองจากรายชื่อที่มีในไฟล์)
    users = preds_df["User_Email"].dropna().unique().tolist()
    user_select = st.selectbox("เลือกชื่อของคุณ (User Email)", users)
    
    # กรองเฉพาะแมตช์ที่ยังไม่แข่ง
    upcoming_matches = matches_df[matches_df["Status"] == "ยังไม่แข่ง"]
    
    if not upcoming_matches.empty:
        match_options = upcoming_matches.apply(lambda x: f"Match {x['Match_ID']}: {x['Team_A']} vs {x['Team_B']}", axis=1).tolist()
        selected_match_str = st.selectbox("เลือกว่าจะทายผลแมตช์ไหน?", match_options)
        
        # ดึง Match ID
        match_id = int(selected_match_str.split(":")[0].replace("Match ", ""))
        match_info = matches_df[matches_df["Match_ID"] == match_id].iloc[0]
        
        st.write(f"**แข่งขันวันที่:** {match_info['Date']}")
        
        col1, col2 = st.columns(2)
        with col1:
            pred_a = st.number_input(f"สกอร์ {match_info['Team_A']}", min_value=0, max_value=20, step=1)
        with col2:
            pred_b = st.number_input(f"สกอร์ {match_info['Team_B']}", min_value=0, max_value=20, step=1)
            
        if st.button("บันทึกการทายผล", type="primary"):
            # เช็คว่าเคยทายแมตช์นี้ไปหรือยัง
            mask = (preds_df["User_Email"] == user_select) & (preds_df["Match_ID"] == match_id)
            if mask.any():
                preds_df.loc[mask, ["Predict_A", "Predict_B"]] = [pred_a, pred_b]
            else:
                # สร้าง record ใหม่
                new_pred = pd.DataFrame([{
                    "Prediction_ID": f"{user_select}_M{match_id}",
                    "User_Email": user_select,
                    "Match_ID": match_id,
                    "Team_A": match_info['Team_A'],
                    "Predict_A": pred_a,
                    "Team_B": match_info['Team_B'],
                    "Predict_B": pred_b,
                    "Points": 0
                }])
                preds_df = pd.concat([preds_df, new_pred], ignore_index=True)
            
            save_predictions(preds_df)
            st.success(f"บันทึกผลการทาย {match_info['Team_A']} {pred_a} - {pred_b} {match_info['Team_B']} เรียบร้อยแล้ว!")
    else:
        st.info("ไม่มีแมตช์ที่สามารถทายผลได้ในขณะนี้ (แข่งจบหมดแล้ว)")

# ----------------- หน้า 3: โปรแกรมการแข่งขัน -----------------
with tab3:
    st.header("📅 โปรแกรมและผลการแข่งขัน")
    display_matches = matches_df[["Match_ID", "Date", "Team_A", "Score_A", "Score_B", "Team_B", "Status"]]
    st.dataframe(display_matches, use_container_width=True)

# ----------------- หน้า 4: สำหรับแอดมิน (อัปเดตผล) -----------------
with tab4:
    st.header("⚙️ แอดมินอัปเดตผลการแข่งขันจริง")
    st.warning("หน้านี้สำหรับใส่ผลสกอร์จริงเมื่อแข่งจบแล้ว ซึ่งระบบจะคำนวณคะแนนให้ทุกคนอัตโนมัติ")
    
    admin_match_opts = matches_df.apply(lambda x: f"Match {x['Match_ID']}: {x['Team_A']} vs {x['Team_B']} ({x['Status']})", axis=1).tolist()
    admin_selected = st.selectbox("เลือกแมตช์เพื่ออัปเดตผล", admin_match_opts)
    
    admin_match_id = int(admin_selected.split(":")[0].replace("Match ", ""))
    curr_match = matches_df[matches_df["Match_ID"] == admin_match_id].iloc[0]
    
    col_a, col_b = st.columns(2)
    with col_a:
        actual_a = st.number_input(f"สกอร์จริง {curr_match['Team_A']}", min_value=0, max_value=20, step=1, key="act_a")
    with col_b:
        actual_b = st.number_input(f"สกอร์จริง {curr_match['Team_B']}", min_value=0, max_value=20, step=1, key="act_b")
        
    if st.button("ยืนยันผลการแข่งขัน (แข่งจบแล้ว)", type="primary"):
        # อัปเดตตาราง Matches
        matches_df.loc[matches_df["Match_ID"] == admin_match_id, "Score_A"] = actual_a
        matches_df.loc[matches_df["Match_ID"] == admin_match_id, "Score_B"] = actual_b
        matches_df.loc[matches_df["Match_ID"] == admin_match_id, "Status"] = "จบแล้ว"
        save_matches(matches_df)
        
        # คำนวณคะแนนใหม่ในตาราง Predictions
        for index, row in preds_df[preds_df["Match_ID"] == admin_match_id].iterrows():
            pts = calculate_points(row["Predict_A"], row["Predict_B"], actual_a, actual_b)
            preds_df.at[index, "Points"] = pts
        save_predictions(preds_df)
        
        st.success("อัปเดตผลการแข่งขันและคำนวณคะแนนเรียบร้อยแล้ว! (ตรวจสอบคะแนนที่หน้า Leaderboard)")