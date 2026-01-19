import streamlit as st
import pandas as pd
import numpy as np
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="SAG AI Trial Balance Pre-Processor", layout="wide")

st.title("SAG Data Laundry: Trial Balance Standardiser")
st.markdown("Protocol: Upload messy Management TB -> Anonymize -> Generate AI Prompt.")

# --- FUNCTIONS ---

def clean_dataframe(df):
    # Forward fill to handle merged cells
    df = df.ffill()
    # Drop completely empty rows and columns
    df = df.dropna(how='all')
    df = df.dropna(axis=1, how='all')
    return df

def anonymize_data(df, factor):
    # Select only numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    # Apply the multiplier
    df[numeric_cols] = df[numeric_cols] * factor
    return df

# --- MAIN APP LOGIC ---

uploaded_file = st.file_uploader("Upload Client TB (Excel or CSV)", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    try:
        # Load the file
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
            
        st.success("File uploaded. Initializing...")
        
        with st.expander("View Raw Data", expanded=False):
            st.dataframe(df_raw.head(10))

        # Controls
        col1, col2 = st.columns(2)
        with col1:
            header_row = st.number_input("Header Row Index (0 = First Row)", min_value=0, value=0)
        with col2:
            anonymize = st.checkbox("Anonymize Financials?")
            scalar = 1.0
            if anonymize:
                scalar = np.random.uniform(1.1, 9.9)
                st.info(f"Data will be multiplied by: {scalar:.4f}")

        # Processing Button
        if st.button("Run Pre-Processing"):
            # Reload with specified header
            if uploaded_file.name.endswith('.csv'):
                df_clean = pd.read_csv(uploaded_file, header=header_row)
            else:
                df_clean = pd.read_excel(uploaded_file, header=header_row)

            # Apply Cleaning
            df_clean = clean_dataframe(df_clean)
            
            # Apply Anonymization
            if anonymize:
                df_clean = anonymize_data(df_clean, scalar)

            st.markdown("### Processed Data")
            st.dataframe(df_clean.head(10))

            # Convert to CSV String
            csv_buffer = io.StringIO()
            df_clean.to_csv(csv_buffer, index=False)
            csv_string = csv_buffer.getvalue()

            # Create the Prompt String
            # Using standard string concatenation to avoid f-string complexity if using older Python
            final_prompt = (
                "*** SYSTEM INSTRUCTION ***\n"
                "Role: Senior Data Architect.\n"
                "Task: Map this trial balance to Standard Schema.\n"
                "Columns needed: [Source_Code, Source_Name, Std_Class, Std_SubClass, Norm_Value, Sign, Confidence, Logic]\n"
                "*** DATA INPUT ***\n" + csv_string
            )

            st.text_area("Copy this to AI:", value=final_prompt, height=300)
            
            st.download_button(
                label="Download Cleaned CSV",
                data=csv_string,
                file_name="clean_tb.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"Error: {e}")