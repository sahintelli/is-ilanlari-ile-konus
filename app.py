import streamlit as st
from openai import OpenAI
import json
from docx import Document
from PyPDF2 import PdfReader
import docx2txt

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

def istek_gonder(model, mesajlar, tools, tool_choice="auto"):
  completion = client.chat.completions.create(
    model=model,
    messages=mesajlar,
    tools=tools,
    tool_choice=tool_choice
  )
  return completion

def is_ilanlarini_filtrele(**kwargs):
  dosya_adi = kwargs.get('dosya_adi', None)
  ilan_basligi = kwargs.get('ilan_basligi', None)
  sirket_adi = kwargs.get('sirket_adi', None)
  konum = kwargs.get('konum', None)
  maas = kwargs.get('maas', None)
  calisma_sekli = kwargs.get('calisma_sekli', None)
  nitelikler = kwargs.get('nitelikler', None)
  sorumluluklar = kwargs.get('sorumluluklar', None)
  iletisim = kwargs.get('iletisim', None)
  son_basvuru_tarihi = kwargs.get('son_basvuru_tarihi', None)

  if dosya_adi:
    st.write(f"Ilanin bulundugu dosya ismi: {dosya_adi}.")
  if ilan_basligi:
    st.write(f"{ilan_basligi}")
  if sirket_adi:
    st.write(f"Ilani veren sirket: {sirket_adi}.")
  if konum:
    st.write(f"Is konumu: {konum}.")
  if maas:
    st.write(f"Maas: {maas}.")
  if calisma_sekli:
    st.write(f"Calisma sekli: {calisma_sekli}.")
  if nitelikler:
    st.write(f"Aranan nitelikler:")
    for nitelik in nitelikler:
      st.write(f"\t{nitelik}")
  if sorumluluklar:
    st.write(f"Is sorumluluklari: {sorumluluklar}.")
    for sorumluluk in sorumluluklar:
      st.write(f"\t{sorumluluk}")
  if iletisim:
    st.write(f"Iletisim: {iletisim}.")
  if son_basvuru_tarihi:
    st.write(f"Son basvuru tarihi: {son_basvuru_tarihi}.")

  return "Islem basarili"

def handle_tool_calls(completion, mesajlar, fonksiyonlarim):
  tool_calls = completion.choices[0].message.tool_calls
  # st.write(f"AI (tool_calls): {tool_calls}")
  if tool_calls:
    fonksiyon_sayisi = len(tool_calls)
    # mesajlar.append(completion.choices[0].message)
    mesajlar.append({"role": "assistant", "tool_calls": completion.choices[0].message.tool_calls})
    for i in range(fonksiyon_sayisi):
      f_id = completion.choices[0].message.tool_calls[i].id
      f_ismi = completion.choices[0].message.tool_calls[i].function.name
      f_args = json.loads(completion.choices[0].message.tool_calls[i].function.arguments)
      results = json.dumps(fonksiyonlarim[f_ismi](**f_args))
      st.write(f"Fonksiyon id: {f_id} - isim: {f_ismi} - parametreler: {f_args} - sonuc: {results}")
      mesajlar.append({
          "role": "tool",
          "tool_call_id": f_id,
          "name": f_ismi,
          "content": results
      })
    return mesajlar, tool_calls
  return mesajlar, tool_calls

def oku(dosya):
    st.write(dosya)
    dosya_yolu = dosya['upload_url']
    if dosya_yolu.endswith(".pdf"):
        icerik = ''
        pdf_reader = PdfReader(dosya_yolu)
        for sayfa in pdf_reader.pages:
            icerik += sayfa.extract_text()
        return icerik
    elif dosya_yolu.endswith(".docx"):
        # icerik = docx2txt.process(dosya)
        st.write(dosya_yolu)
        doc = Document(dosya_yolu)
        parca = [para.text for para in doc.paragraphs]
        icerik = '\n'.join(parca)
        return icerik


def main():
    st.title("Title 🎈")  # Set the app's title

    # Setup the sidebar
    model, stream, api_key, uploaded_files = sidebar_setup()
    client = OpenAI(api_key=api_key)

    if not "mesajlar" in st.session_state:
        st.session_state.mesajlar = [
        {"role": "system", "content": "Verilen is ilanlari ile ilgili yardimci bir asistansin."}
    ]

        
    icerik = ''
    for uploaded_file in uploaded_files:
      icerik += f"Dosya ismi {uploaded_file} icerisindeki icerik basladi: "
      icerik += oku(uploaded_file)
      icerik += f"Dosya ismi {uploaded_file} icerisindeki icerik bitti. "
    st.write(f"Dosya okundu. Icerik: {icerik}")
    st.session_state.mesajlar.append({"role": "user", "content": f"Dosya icerigi: {icerik}"})
    st.write(st.session_state)



    # If API key and uploaded files are provided, display the file names and types
    if api_key and uploaded_files:
        for uploaded_file in uploaded_files:
            st.write(f"Uploaded file name: {uploaded_file.name}")

if __name__ == "__main__":
    tools = [
      {
        "type": "function",
        "function": {
          "name": "is_ilanlarini_filtrele",
          "description": "Belirli kategorilere gore is ilanlarini filtreler",
          "parameters": {
            "type": "object",
            "properties": {
              "dosya_adi": {
                "type": "string",
                "description": "İş ilanı dosyasının adı",
              },
              "ilan_basligi": {
                "type": "string",
                "description": "İş ilanının başlığı",
              },
              "sirket_adi": {
                "type": "string",
                "description": "İş ilanını veren şirketin adı",
              },
              "konum": {
                "type": "string",
                "description": "İşin konumu, şehir ve ülke bilgisi",
              },
              "maas": {
                "type": "string",
                "description": "Teklif edilen maaş",
              },
              "calisma_sekli": {
                "type": "string",
                "enum": ["tam zamanlı", "yarı zamanlı", "uzaktan"],
                "description": "Çalışma şekli, örn: tam zamanlı, yarı zamanlı, uzaktan",
              },
              "nitelikler": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "Pozisyon için gereken nitelikler",
              },
              "sorumluluklar": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "Pozisyonun sorumlulukları",
              },
              "iletisim": {
                "type": "string",
                "description": "İş ilanı için iletişim bilgileri",
              },
              "son_basvuru_tarihi": {
                "type": "string",
                "description": "Son başvuru tarihi",
              }
            },
            "required": ["ilan_basligi", "sirket_adi", "konum", "maas", "calisma_sekli"],
          },
        }
      }
    ]
    
    fonksiyonlarim = {
        "is_ilanlarini_filtrele": is_ilanlarini_filtrele
    }
    
    tool_choice = "auto"
    model = "gpt-4o"

    main()
