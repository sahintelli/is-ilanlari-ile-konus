import streamlit as st
from openai import OpenAI

# Set page configuration
st.set_page_config(page_title="Is ilanlari ile konusma uygulamasi", page_icon="🤖")  # Appears on the browser tab

def sidebar_setup():
    st.sidebar.header("Setup")  # Set up the sidebar header

    # Define available models in a dictionary
    available_models = {
        "GPT-3.5 Turbo": "gpt-3.5-turbo", 
        "GPT-4": "gpt-4", 
        "GPT-4o": "gpt-4o"
    }
    
    # Provide a dropdown for the user to select an OpenAI model
    model_selection = st.sidebar.selectbox("Select an OpenAI Model", available_models.keys())
    model = available_models.get(model_selection)  # Get the value of the selected model

    # Option to enable or disable streaming
    stream = st.sidebar.checkbox("Enable Stream", value=True)

    # Input field for the OpenAI API key
    api_key = st.sidebar.text_input(label="Your OpenAI API key:", type="password")
    # If your key is stored in secrets, uncomment the line below and comment out the above line
    # api_key = st.secrets["api_key"]

    # Some options to upload files. Select or modify the code snippet that best suits your needs
    accept_multiple_files = True
    # Handle file upload
    uploaded_files = st.sidebar.file_uploader("Upload files", accept_multiple_files=accept_multiple_files, type=["pdf", "docx"])
    # uploaded_files = st.sidebar.file_uploader("Upload CSV or XLSX File", accept_multiple_files=accept_multiple_files, type=['csv', 'xlsx'])
    
    # Ensure `uploaded_files` is always a list
    uploaded_files = [uploaded_files] if uploaded_files and not accept_multiple_files else uploaded_files

    # Return the selected model, stream setting, API key, and uploaded files
    return model, stream, api_key, uploaded_files

def main():
    st.title("Title 🎈")  # Set the app's title

    # Setup the sidebar
    model, stream, api_key, uploaded_files = sidebar_setup()

    if not "sayac" in st.session_state:
        st.session_state.sayac = 0
        st.write(st.session_state)

    # If API key and uploaded files are provided, display the file names and types
    if api_key and uploaded_files:
        for uploaded_file in uploaded_files:
            st.write(f"Uploaded file name: {uploaded_file.name}")

if __name__ == "__main__":
    main()
