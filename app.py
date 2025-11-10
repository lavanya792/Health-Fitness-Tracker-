import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime, os, json, hashlib

USER_FILE = "users.json"
PROFILE_FILE = "profiles.json"
GLOBAL_LOG_FILE = "all_user_activity_log.csv"

# ---------------------- USER SYSTEM ----------------------
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(u):
    with open(USER_FILE, "w") as f:
        json.dump(u, f, indent=4)

def signup(u, p):
    users = load_users()
    if u in users:
        return False, "Username already exists!"
    users[u] = hash_password(p)
    save_users(users)
    return True, "Account created successfully!"

def login(u, p):
    users = load_users()
    if u not in users:
        return False, "Username not found!"
    if users[u] != hash_password(p):
        return False, "Incorrect password!"
    return True, "Login successful!"

# ---------------------- PROFILE MANAGEMENT ----------------------
def load_profiles():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_profiles(p):
    with open(PROFILE_FILE, "w") as f:
        json.dump(p, f, indent=4)

def load_user_data(u):
    safe = u.strip().replace(" ", "_")
    file = f"{safe}_fitness_logs.csv"
    if not os.path.exists(file) or os.path.getsize(file) == 0:
        df = pd.DataFrame(columns=["Date", "Steps", "Calories", "Protein", "Fat", "Carbs", "Workout", "Intensity"])
        df.to_csv(file, index=False)
        return df, file
    return pd.read_csv(file), file

def save_user_data(df, f):
    df.to_csv(f, index=False)

# ---------------------- UTILS ----------------------
def classify_intensity(steps, workout):
    workout = workout.lower().strip()
    if workout in ["rest", "none", ""]:
        return "Low"
    elif workout in ["yoga", "pilates"]:
        return "Moderate" if steps < 2000 else "High"
    elif workout in ["running", "cycling", "gym", "hiit"]:
        return "Moderate" if steps < 4000 else "High"
    return "Low" if steps < 4000 else "Moderate" if steps < 8000 else "High"

def weekly_summary(df):
    if df.empty: return None
    num = df.select_dtypes(include="number")
    return pd.DataFrame({"Average": num.mean(), "Total": num.sum()}).round(2)

# ---------------------- LOAD DATASET ----------------------
@st.cache_data
def load_food_data():
    f = "Indian_Food_Nutrition_Processed 2.csv"
    if not os.path.exists(f):
        st.error("⚠️ Dataset not found! Please add it to this folder.")
        return pd.DataFrame()
    df = pd.read_csv(f)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    rename_map = {
        "dish_name": "dish_name",
        "calories_(kcal)": "calories",
        "protein_(g)": "protein",
        "fats_(g)": "fat",
        "carbohydrates_(g)": "carbs"
    }
    df = df.rename(columns=rename_map)
    return df[["dish_name", "calories", "protein", "fat", "carbs"]]

# ---------------------- GLOBAL LOG ----------------------
def append_to_global_log(username, entry):
    entry["Username"] = username
    new_df = pd.DataFrame([entry])
    if os.path.exists(GLOBAL_LOG_FILE):
        new_df.to_csv(GLOBAL_LOG_FILE, mode="a", header=False, index=False)
    else:
        new_df.to_csv(GLOBAL_LOG_FILE, mode="w", header=True, index=False)

# ---------------------- STREAMLIT APP ----------------------
st.set_page_config(page_title="Health & Nutrition Tracker", page_icon="🍎", layout="centered")
st.title("🍎 Health, Fitness & Nutrition Tracker")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ---------------------- LOGIN/SIGNUP ----------------------
if not st.session_state.logged_in:
    st.subheader("Login or Sign Up")
    mode = st.radio("Select an option:", ["Login", "Sign Up"])
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if mode == "Login":
        if st.button("Login"):
            ok, msg = login(u, p)
            if ok:
                st.session_state.logged_in, st.session_state.username = True, u
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    else:
        if st.button("Create Account"):
            ok, msg = signup(u, p)
            st.success(msg) if ok else st.error(msg)

else:
    u = st.session_state.username
    st.sidebar.success(f"Logged in as {u}")
    df, file = load_user_data(u)
    profiles = load_profiles()

    if u not in profiles:
        profiles[u] = {
            "age": 21, "weight": 55, "height": 165, "activity": "Medium",
            "steps_goal": 8000, "calorie_goal": 1800
        }
        save_profiles(profiles)

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.sidebar.header("👤 Profile Info")
    # Set default values if keys don't exist
    if "steps_goal" not in profiles[u]:
        profiles[u]["steps_goal"] = 8000
    if "calorie_goal" not in profiles[u]:
        profiles[u]["calorie_goal"] = 1800

    age = st.sidebar.number_input("Age", 10, 100, profiles[u]["age"])
    weight = st.sidebar.number_input("Weight (kg)", 30, 150, profiles[u]["weight"])
    height = st.sidebar.number_input("Height (cm)", 100, 220, profiles[u]["height"])
    activity = st.sidebar.selectbox("Activity Level", ["Low", "Medium", "High"],
    index=["Low", "Medium", "High"].index(profiles[u]["activity"]))
    steps_goal = st.sidebar.number_input("Daily Steps Goal", 1000, 50000, profiles[u].get("steps_goal", 8000), step=500)
    calorie_goal = st.sidebar.number_input("Daily Calorie Goal", 500, 5000, profiles[u].get("calorie_goal", 1800), step=100)
    bmi = round(weight / ((height / 100) ** 2), 2)
    st.sidebar.write(f"BMI: {bmi}")

    profiles[u].update({
        "age": age, "weight": weight, "height": height, "activity": activity,
        "bmi": bmi, "steps_goal": steps_goal, "calorie_goal": calorie_goal
    })
    save_profiles(profiles)

    food_data = load_food_data()

    st.header("🍽️ Log Today's Meals")
    date = st.date_input("Date", datetime.date.today())
    steps = st.number_input("Steps Walked", 0, 50000, 0)
    workout = st.text_input("Workout Type")

    def meal_section(meal_name):
        st.subheader(meal_name)
        items = st.multiselect(f"Select items for {meal_name}", sorted(food_data["dish_name"].dropna().unique().tolist()))
        servings = st.number_input(f"Enter number of servings for {meal_name} (1 serve = 100g)", 0.0, 10.0, 1.0, step=0.5)
        total = {"Calories": 0, "Protein": 0, "Fat": 0, "Carbs": 0}
        for item in items:
            row = food_data[food_data["dish_name"] == item].iloc[0]
            total["Calories"] += (row["calories"] * servings)
            total["Protein"] += (row["protein"] * servings)
            total["Fat"] += (row["fat"] * servings)
            total["Carbs"] += (row["carbs"] * servings)
        st.info(f"{meal_name} total: {round(total['Calories'],2)} kcal | {round(total['Protein'],2)}g protein | {round(total['Fat'],2)}g fat | {round(total['Carbs'],2)}g carbs")
        return total

    breakfast = meal_section("Breakfast")
    lunch = meal_section("Lunch")
    dinner = meal_section("Dinner")

    total_cal = breakfast["Calories"] + lunch["Calories"] + dinner["Calories"]
    total_pro = breakfast["Protein"] + lunch["Protein"] + dinner["Protein"]
    total_fat = breakfast["Fat"] + lunch["Fat"] + dinner["Fat"]
    total_carb = breakfast["Carbs"] + lunch["Carbs"] + dinner["Carbs"]

    st.subheader("🌞 Daily Nutrition Summary")
    st.success(f"Total: {round(total_cal,2)} kcal | Protein: {round(total_pro,2)}g | Fat: {round(total_fat,2)}g | Carbs: {round(total_carb,2)}g")

    # --- PIE CHART ---
    if total_cal > 0:
        labels = ["Protein", "Fat", "Carbs"]
        values = [total_pro*4, total_fat*9, total_carb*4]  # calorie equivalents
        fig, ax = plt.subplots()
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
        st.pyplot(fig)

    # --- GOAL FEEDBACK ---
    if steps < steps_goal:
        st.warning(f"🚶 You walked {steps} steps, below your goal of {steps_goal}. Keep moving!")
    else:
        st.success("🎉 You hit your step goal today!")

    if total_cal > calorie_goal:
        st.warning(f"⚠️ You consumed {round(total_cal,2)} kcal, above your goal of {calorie_goal}. Try lighter meals tomorrow.")
    elif total_cal < calorie_goal * 0.8:
        st.info(f"🥗 You consumed {round(total_cal,2)} kcal, below your goal of {calorie_goal}. Make sure you eat enough!")
    else:
        st.success("🔥 Perfect! You're close to your calorie goal today.")

    # --- SAVE ENTRY ---
    if st.button("💾 Save Today's Entry"):
        inten = classify_intensity(steps, workout)
        new = {
            "Date": str(date), "Steps": steps, "Calories": total_cal,
            "Protein": total_pro, "Fat": total_fat, "Carbs": total_carb,
            "Workout": workout, "Intensity": inten
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        save_user_data(df, file)
        append_to_global_log(u, new)
        st.success("✅ Data saved successfully!")

    # --- SUMMARY ---
    st.header("📊 Weekly Summary")
    if not df.empty:
        st.dataframe(df)
        s = weekly_summary(df)
        if s is not None:
            st.table(s)

        fig, ax = plt.subplots()
        ax.plot(df["Date"], df["Calories"], marker="o", label="Calories")
        ax.plot(df["Date"], df["Steps"], marker="s", label="Steps")
        ax.set_xlabel("Date")
        ax.set_ylabel("Values")
        ax.legend()
        st.pyplot(fig)
    else:
        st.info("No data yet. Add meals above.")