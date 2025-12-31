import streamlit as st
from agent import run_agent

# 1. Page Config
st.set_page_config(page_title="Legacy Migration Agent", layout="wide")

st.title("🤖 Mainframe to AI Migration Agent")
st.subheader("Powered by Google Gemini 1.5 Flash")

# 2. Define the Default COBOL Code
DEFAULT_COBOL = """IDENTIFICATION DIVISION.
PROGRAM-ID. LOAN-CHECK.
DATA DIVISION.
WORKING-STORAGE SECTION.
01  CREDIT-SCORE    PIC 9(3) VALUE 720.
01  YEARLY-INCOME   PIC 9(6) VALUE 45000.
01  LOAN-STATUS     PIC X(10).

PROCEDURE DIVISION.
    DISPLAY "CHECKING LOAN ELIGIBILITY...".

    IF CREDIT-SCORE > 700 AND YEARLY-INCOME > 50000 THEN
        MOVE "APPROVED" TO LOAN-STATUS
    ELSE IF CREDIT-SCORE > 750 THEN
        MOVE "APPROVED" TO LOAN-STATUS
    ELSE
        MOVE "REJECTED" TO LOAN-STATUS
    END-IF.

    DISPLAY "STATUS: " LOAN-STATUS.
    STOP RUN."""

# 3. Input Section (Full Width)
st.markdown("### Step 1: Input Legacy Code")
cobol_input = st.text_area("Paste your COBOL here:", value=DEFAULT_COBOL, height=300)

# 4. Action Button
if st.button("🚀 Migrate to Python", type="primary"):
    if cobol_input:
        with st.spinner("🤖 AI Analyst is working..."):
            # Run the Agent
            result = run_agent(cobol_input)
            st.session_state['result'] = result

# 5. Output Section
if 'result' in st.session_state:
    st.markdown("---")
    st.markdown("### Step 2: Migration Result")
    result = st.session_state['result']
    
    # Create two columns for the results
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("🐍 **Python Code**")
        st.code(result['python_code'], language='python')
        
    with col2:
        st.success("🧠 **Business Logic Explanation**")
        st.markdown(result['explanation'])