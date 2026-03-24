import streamlit as st
import pandas as pd
from datetime import datetime
import random
import string
import os

# Responsive tabs - bigger on laptop, smaller on phone
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 17px !important;
        font-weight: 700 !important;
        padding: 12px 20px !important;
        border-radius: 8px;
    }
    /* Bigger on laptop/desktop */
    @media (min-width: 768px) {
        .stTabs [data-baseweb="tab"] {
            font-size: 20px !important;
            padding: 16px 32px !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 30px;
        }
    }
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="🐰 Evans Family Easter Party", page_icon="🐰", layout="centered")

st.title("🐰 Evans Family Easter Party")
st.subheader("April 5, 2026 • Sign up for attendance + potluck!")

CSV_FILE = "signups.csv"

def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    else:
        df = pd.DataFrame(columns=["Timestamp", "Name", "Attending", "Attendees", "Food Item", "Category", "Notes", "Edit Code"])
        df.to_csv(CSV_FILE, index=False)
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
    st.caption("Checked boxes turn green")
    
    suggestions = {
        "Apps": ["Cheese & Salami roll", "Cheese & Charcuterie Board", "Vegetable Tray", "Crab Dip or Buffalo Dip", "Caesar Salad", "Deviled Eggs", "Dinner Rolls and/or Biscuits"],
        "Main": ["Roast Turkey & gravy", "Baked Ham"],
        "Side Dish": ["Mashed Potatoes", "Traditional Bread Stuffing", "Green Beans", "Glazed Carrots or Roasted Vegetables", "Sauerkraut and Sausage", "Cranberry Sauce"],
        "Dessert": ["Lemon Meringue Pie", "Pumpkin Pie", "Apple Pie", "White Cake with Chocolate Icing", "Buns", "Cookies and/or Brownies"],
        "Drinks": ["Apple Cider", "Beer - Natural Light", "Beer - Bottled (Stella/Blue Moon/Etc)", "Wine - Red", "Wine - Sparkling", "Wine - White", "Hard Seltzers", "Sodas"]
    }
    
    if "selected_foods" not in st.session_state:
        st.session_state.selected_foods = []
    
    for category, items in suggestions.items():
        st.write(f"**{category}**")
        cols = st.columns(3)
        for i, item in enumerate(items):
            with cols[i % 3]:
                checked = st.checkbox(item, value=item in st.session_state.selected_foods, key=f"cb_{category}_{i}")
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
        
        category = st.selectbox("Category", ["Apps", "Side Dish", "Main", "Dessert", "Drinks"])
        food_item_default = ", ".join(st.session_state.selected_foods) if st.session_state.selected_foods else ""
        food_item = st.text_input("What are you bringing? (leave blank if nothing)", value=food_item_default, placeholder="Deviled eggs, Mashed Potatoes")
        
        notes = st.text_area("Notes or allergies?", placeholder="Any vegetarian options?")
        
        submitted = st.form_submit_button("✅ Submit Signup")
        
        if submitted and name:
            edit_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            new_row = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Name": name,
                "Attending": attending,
                "Attendees": attendees,
                "Food Item": food_item,
                "Category": category,
                "Notes": notes,
                "Edit Code": edit_code
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)
            st.success(f"""
            🎉 **Signup added successfully!**  
            **Your Edit Code: `{edit_code}`**  
            Save this code — you’ll need it to edit or delete later!
            """)
            st.session_state.selected_foods = []
            st.rerun()

# ====================== OTHER TABS ======================
with tab_attendance:
    st.write("### 👥 Who's Coming")
    if len(df) == 0:
        st.info("No signups yet — be the first!")
    else:
        st.dataframe(df[["Name", "Attending", "Attendees", "Notes"]], use_container_width=True, hide_index=True)

with tab_food:
    st.write("### 🍽️ Potluck Food")
    food_df = df[df["Food Item"] != ""][["Name", "Food Item", "Category", "Notes"]].copy()
    if len(food_df) == 0:
        st.info("No food signed up yet!")
    else:
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
            st.session_state.edit_index = matches.index[0]
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
                    df.loc[st.session_state.edit_index, ["Name", "Attending", "Attendees", "Food Item", "Category", "Notes"]] = [name, attending, attendees, food_item, category, notes]
                    df.to_csv(CSV_FILE, index=False)
                    st.success
