import streamlit as st
import pandas as pd
from datetime import datetime
import random
import string
import os
import gspread
from google.oauth2 import service_account

# Responsive tabs
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 12px; }
    .stTabs [data-baseweb="tab"] {
        font-size: 17px !important;
        font-weight: 700 !important;
        padding: 12px 20px !important;
        border-radius: 8px;
    }
    @media (min-width: 768px) {
        .stTabs [data-baseweb="tab"] { font-size: 20px !important; padding: 16px 32px !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 30px; }
    }
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="🐰 Evans Family Easter Party", page_icon="🐰", layout="centered")

st.title("🐰 Evans Family Easter Party")
st.subheader("April 5, 2026 • Sign up for attendance + potluck!")

# ====================== GOOGLE SHEETS CONNECTION ======================
@st.cache_resource
def get_connection():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(credentials)

gc = get_connection()
sh = gc.open("Evans Family Easter Party Signups")
worksheet = sh.worksheet("Signups")

def load_data():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    # CRITICAL FIX: Remove any extra spaces from column names
    df.columns = [str(col).strip() for col in df.columns]
    return df

df = load_data()

tab_signup, tab_attendance, tab_food, tab_manage = st.tabs([
    "📝 Sign Up", 
    "👥 Who's Coming", 
    "🍽️ Potluck Food", 
    "🔧 Manage My Signup"
])

# ====================== SIGN UP TAB ======================
with tab_signup:
    st.write("### Add your RSVP + food")
    
    st.write("**Select the foods you are bringing (multiple OK)**")
    st.caption("Choose from the options below, or enter your own in the box provided.")
    
    suggestions = {
        "Apps": ["Cheese & Salami roll", "Cheese & Charcuterie Board", "Vegetable Tray", "Crab Dip or Buffalo Dip", "Caesar Salad", "Deviled Eggs", "Dinner Rolls and/or Biscuits"],
        "Main": ["Roast Turkey & gravy", "Baked Ham"],
        "Side Dish": ["Mashed Potatoes", "Traditional Bread Stuffing", "Green Beans", "Glazed Carrots or Roasted Vegetables", "Sauerkraut and Sausage", "Cranberry Sauce", "Broccoli Salad", "Pasta Salad", "Coleslaw"],
        "Dessert": ["Lemon Meringue Pie", "Pumpkin Pie", "Apple Pie", "White Cake with Chocolate Icing", "Buns", "Cookies and/or Brownies", "Lemon Bars", "Coconut Cake", "Carrot Cake", "Caramel Cake"],
        "Drinks": ["Apple Cider", "Beer - Natural Light", "Beer - Bottled (Stella/Blue Moon/Etc)", "Wine - Red", "Wine - Sparkling", "Wine - White", "Hard Seltzers", "Sodas"]
    }
    
    if "selected_foods" not in st.session_state:
        st.session_state.selected_foods = []
    
    claimed_foods = set()
    for food_str in df["Food Item"].dropna() if "Food Item" in df.columns else []:
        for item in str(food_str).split(", "):
            if item.strip():
                claimed_foods.add(item.strip())
    
    for category, items in suggestions.items():
        st.write(f"**{category}**")
        cols = st.columns(3)
        for i, item in enumerate(items):
            with cols[i % 3]:
                is_claimed = item in claimed_foods
                label = f"{item} (already claimed)" if is_claimed else item
                checked = st.checkbox(label, value=item in st.session_state.selected_foods, disabled=is_claimed, key=f"cb_{category}_{i}")
                if checked and item not in st.session_state.selected_foods:
                    st.session_state.selected_foods.append(item)
                elif not checked and item in st.session_state.selected_foods:
                    st.session_state.selected_foods.remove(item)
    
    if st.session_state.selected_foods:
        st.success("**Your selections:** " + ", ".join(st.session_state.selected_foods))
    else:
        st.write("*(Nothing selected yet)*")

    with st.form("signup_form", clear_on_submit=True):
        name = st.text_input("Your family name *", placeholder="Sarah Evans")
        attending = st.selectbox("Are you coming?", ["Yes", "Maybe", "No"])
        attendees = st.text_area("Who is attending? (one name per line)", placeholder="Sarah Evans\nJohn Evans\nEmma Evans", height=100)
        
        food_item_default = ", ".join(st.session_state.selected_foods) if st.session_state.selected_foods else ""
        food_item = st.text_input("What are you bringing? (leave blank if nothing)", value=food_item_default, placeholder="Deviled eggs, Mashed Potatoes")
        
        category = st.selectbox("Category", ["Apps", "Side Dish", "Main", "Dessert", "Drinks"])
        
        notes = st.text_area("Notes or allergies?", placeholder="Any vegetarian options?")
        
        submitted = st.form_submit_button("✅ Submit Signup")
        
        if submitted and name:
            edit_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            new_row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                name,
                attending,
                attendees,
                food_item,
                category,
                notes,
                edit_code
            ]
            worksheet.append_row(new_row)
            st.success(f"""
            🎉 **Signup added successfully!**  
            **Your Edit Code: `{edit_code}`**  
            Save this code — you’ll need it to edit or delete later!
            """)
            st.session_state.selected_foods = []
            st.rerun()

# (The rest of the tabs remain the same — Who's Coming, Potluck Food, Manage)

with tab_attendance:
    st.write("### 👥 Who's Coming")
    if len(df) == 0:
        st.info("No signups yet — be the first!")
    else:
        attendance_list = []
        for _, row in df.iterrows():
            family = row["Name"]
            status = row["Attending"]
            notes = row.get("Notes", "")
            attendees_str = row.get("Attendees", "")
            if pd.isna(attendees_str) or str(attendees_str).strip() == "":
                attendance_list.append({"Family": family, "Person": family, "Attending": status, "Notes": notes})
            else:
                for person in str(attendees_str).strip().split("\n"):
                    person = person.strip()
                    if person:
                        attendance_list.append({"Family": family, "Person": person, "Attending": status, "Notes": notes})
        attendance_df = pd.DataFrame(attendance_list)
        
        total_attending = len(attendance_df[attendance_df["Attending"] == "Yes"])
        total_maybe = len(attendance_df[attendance_df["Attending"] == "Maybe"])
        total_not = len(attendance_df[attendance_df["Attending"] == "No"])
        total_people = len(attendance_df)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("✅ Attending", total_attending)
        col2.metric("❔ Maybe", total_maybe)
        col3.metric("❌ Not Attending", total_not)
        col4.metric("👥 Total People", total_people)
        
        st.write("### Full Attendee List")
        st.dataframe(attendance_df, use_container_width=True, hide_index=True)

with tab_food:
    st.write("### 🍽️ Potluck Food")
    if len(df) == 0 or df["Food Item"].dropna().empty:
        st.info("No food signed up yet!")
    else:
        food_list = []
        for _, row in df.iterrows():
            name = row["Name"]
            food_str = row.get("Food Item", "")
            category = row.get("Category", "")
            notes = row.get("Notes", "")
            if pd.notna(food_str) and str(food_str).strip():
                for item in str(food_str).strip().split(", "):
                    item = item.strip()
                    if item:
                        food_list.append({"Person": name, "Food Item": item, "Category": category, "Notes": notes})
        food_df = pd.DataFrame(food_list)
        st.dataframe(food_df, use_container_width=True, hide_index=True)

with tab_manage:
    st.write("### 🔧 Manage My Signup")
    with st.expander("❓ Forgot your Edit Code?"):
        st.write("Enter your name below to retrieve it:")
        forgot_name = st.text_input("Your name", placeholder="Sarah Evans", key="forgot_name")
        if st.button("🔍 Find My Edit Code"):
            matches = df[df["Name"].str.contains(forgot_name, case=False, na=False)]
            if not matches.empty:
                for _, row in matches.iterrows():
                    st.success(f"**{row['Name']}** → Edit Code: `{row['Edit Code']}`")
            else:
                st.error("No signup found with that name.")
    
    edit_code_input = st.text_input("Enter your Edit Code", placeholder="A1B2C3")
    if st.button("🔍 Load My Signup"):
        matches = df[df["Edit Code"] == edit_code_input.upper().strip()]
        if not matches.empty:
            row = matches.iloc[0]
            st.session_state.edit_row = row.to_dict()
            st.session_state.edit_index = matches.index[0] + 2
            st.success("✅ Signup loaded!")
        else:
            st.error("❌ No signup found with that code.")

    if "edit_row" in st.session_state:
        st.write("### Edit your signup")
        with st.form("edit_form"):
            name = st.text_input("Family name", value=st.session_state.edit_row["Name"])
            attending = st.selectbox("Are you coming?", ["Yes", "Maybe", "No"], index=["Yes","Maybe","No"].index(st.session_state.edit_row["Attending"]))
            attendees = st.text_area("Who is attending?", value=st.session_state.edit_row["Attendees"], height=100)
            food_item = st.text_input("What are you bringing?", value=st.session_state.edit_row.get("Food Item", ""))
            category = st.selectbox("Category", ["Apps", "Side Dish", "Main", "Dessert", "Drinks"], index=["Apps","Side Dish","Main","Dessert","Drinks"].index(st.session_state.edit_row.get("Category", "Apps")))
            notes = st.text_area("Notes", value=st.session_state.edit_row.get("Notes", ""))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Update Signup"):
                    worksheet.update(f"B{st.session_state.edit_index}:H{st.session_state.edit_index}", 
                                   [[name, attending, attendees, food_item, category, notes, st.session_state.edit_row["Edit Code"]]])
                    st.success("✅ Updated!")
                    del st.session_state.edit_row
                    del st.session_state.edit_index
                    st.rerun()
            with col2:
                if st.form_submit_button("🗑️ Delete Signup", type="primary"):
                    worksheet.delete_rows(st.session_state.edit_index)
                    st.success("🗑️ Deleted!")
