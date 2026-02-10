import streamlit as st
from main import load_coordinator, update_sheet_status

st.set_page_config(page_title="Skylark Drone Ops", layout="wide")
st.title("🚁 Drone Operations Coordinator AI")

# Load Data
if 'coord' not in st.session_state:
    st.session_state.coord = load_coordinator()

# Sidebar for Management
st.sidebar.header("Update Status (Sync to Sheets)")
u_type = st.sidebar.selectbox("Type", ["Pilot", "Drone"])
u_id = st.sidebar.text_input("ID (e.g., P001 or D001)")
u_status = st.sidebar.selectbox("New Status", ["Available", "On Leave", "Maintenance", "Assigned"])

if st.sidebar.button("Update & Sync"):
    tab = "pilot_roster" if u_type == "Pilot" else "drone_fleet"
    id_col = "pilot_id" if u_type == "Pilot" else "drone_id"
    
    # Capture the result
    success, message = update_sheet_status(tab, id_col, u_id, u_status)
    
    if success:
        st.session_state.coord = load_coordinator() # Refresh data
        st.sidebar.success(f"Successfully updated {u_id}")
    else:
        # Display the error message in the sidebar instead of a crash screen
        st.sidebar.error(message)

# Main Interface
tab1, tab2, tab3 = st.tabs(["Dashboard", "Assignment Matcher", "Conflict Check"])

with tab1:
    st.subheader("Live Roster")
    st.dataframe(st.session_state.coord.pilots)
    st.subheader("Live Fleet")
    st.dataframe(st.session_state.coord.drones)

with tab2:
    m_id = st.selectbox("Select Project ID", st.session_state.coord.missions['project_id'])
    if st.button("Find Best Matches"):
        recs = st.session_state.coord.find_best_matches(m_id)
        col1, col2 = st.columns(2)
        col1.write("Top Pilots:")
        col1.table(recs['pilots'])
        col2.write("Top Drones:")
        col2.table(recs['drones'])

with tab3:
    st.subheader("Check Manual Assignment")
    c_p = st.selectbox("Pilot", st.session_state.coord.pilots['pilot_id'])
    c_d = st.selectbox("Drone", st.session_state.coord.drones['drone_id'])
    c_m = st.selectbox("Mission", st.session_state.coord.missions['project_id'])
    
    if st.button("Validate Assignment"):
        issues = st.session_state.coord.check_conflicts(c_p, c_d, c_m)
        if not issues:
            st.success("✅ No conflicts detected. Assignment is safe.")
        else:
            for issue in issues:
                st.error(issue)

st.header("🤖 Conversational AI Assistant")
user_input = st.text_input("Ask me anything (e.g., 'Who is in Mumbai?' or 'Thermal pilots in Bangalore')")

if user_input:
    search_results = st.session_state.coord.conversational_query(user_input)
    
    if not search_results.empty:
        st.write(f"**Agent:** I found {len(search_results)} matching profiles for your request:")
        st.table(search_results)
    else:
        st.warning("Agent: I couldn't find any pilots matching those specific criteria. Try searching by location or skill.")
