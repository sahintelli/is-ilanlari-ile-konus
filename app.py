import streamlit as st
from openai import OpenAI
import json
from docx import Document
from PyPDF2 import PdfReader
import random
import time

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

    kategoriler = ["Dosya ismi", "Maas", "Calisma Yeri", "Ilan Basligi", "Sirket Adi", "Calisma Sekli", "Nitelikler", "Sorumluluklar", "Iletisim", "Son Basvuru Tarihi"]
    secilen_kategoriler = st.sidebar.multiselect("Asagidakilerden kategorilerden seciniz: ", kategoriler, default = ["Dosya ismi", "Calisma Yeri"])

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
    return model, stream, secilen_kategoriler, api_key, uploaded_files

def istek_gonder():
  model = st.session_state.model
  mesajlar = st.session_state.mesajlar
  tools = st.session_state.tools
  tool_choice = st.session_state.tool_choice
  client = st.session_state.client

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
  yazdirilacak_cikti = ""
    
  if dosya_adi:
    yazdirilacak_cikti += f"Ilanin bulundugu dosya ismi: {dosya_adi}.\n\n"
  if ilan_basligi:
    yazdirilacak_cikti += f"*{ilan_basligi}*\n\n"
  if sirket_adi:
    yazdirilacak_cikti += f"**Ilani veren sirket: {sirket_adi}.**\n\n"
  if konum:
    yazdirilacak_cikti += f"Is konumu: {konum}.\n\n"
  if maas:
    yazdirilacak_cikti += f"Maas: {maas}.\n\n"
  if calisma_sekli:
    yazdirilacak_cikti += f"Calisma sekli: {calisma_sekli}.\n\n"
  if nitelikler:
    yazdirilacak_cikti += f"Aranan nitelikler:\n"
    for nitelik in nitelikler:
      yazdirilacak_cikti += f"\t{nitelik}\n"
  if sorumluluklar:
    yazdirilacak_cikti += f"Is sorumluluklari: {sorumluluklar}.\n"
    for sorumluluk in sorumluluklar:
      yazdirilacak_cikti += f"\t{sorumluluk}\n"
  if iletisim:
    yazdirilacak_cikti += f"Iletisim: {iletisim}.\n\n"
  if son_basvuru_tarihi:
    yazdirilacak_cikti += f"Son basvuru tarihi: {son_basvuru_tarihi}.\n\n"

  if st.session_state.stream:
      stream_text(yazdirilacak_cikti)
  else:
      st.markdown(yazdirilacak_cikti)

  return "Islem basarili"

def handle_tool_calls(fonksiyonlarim):
    try:
      completion = istek_gonder()
      tool_calls = completion.choices[0].message.tool_calls
      # st.write(f"AI (tool_calls): {tool_calls}")
      if tool_calls:
        fonksiyon_sayisi = len(tool_calls)
        # mesajlar.append(completion.choices[0].message)
        st.session_state.mesajlar.append({"role": "assistant", "tool_calls": completion.choices[0].message.tool_calls})
        for i in range(fonksiyon_sayisi):
          f_id = completion.choices[0].message.tool_calls[i].id
          f_ismi = completion.choices[0].message.tool_calls[i].function.name
          f_args = json.loads(completion.choices[0].message.tool_calls[i].function.arguments)
          # results = completion.choices[0].message.tool_calls[i].function.arguments
          results = json.dumps(fonksiyonlarim[f_ismi](**f_args))
          st.sidebar.write(f"Fonksiyon id: {f_id} - isim: {f_ismi} - parametreler: {f_args} - sonuc: {results}")
          st.session_state.mesajlar.append({
              "role": "tool",
              "tool_call_id": f_id,
              "name": f_ismi,
              "content": results
          })
        return handle_tool_calls(fonksiyonlarim)
      return completion.choices[0].message.content

    except openai.APIConnectionError as e:
        st.error(f"API Connection Error: {e}")
    except openai.AuthenticationError as e:
        st.error(f"Authentication Error: {e}")
    except openai.RateLimitError as e:
        error_message = e.body.get('message', 'No message provided')
        st.error(f"Rate Limit Error: Request exceeded the token limit for the selected model on tokens per minute (TPM). The input or output tokens must be reduced in order to run successfully. Visit the rate limits page on the OpenAI platform to learn more.")
    except openai.APIError as e:
        st.error(f"API Error: {e}")
    except openai.OpenAIError as e:
        st.error(f"OpenAI Error: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

def oku(dosya):
  dosya_yolu = dosya.name
  if dosya_yolu.endswith(".pdf"):
    icerik = ''
    pdf_reader = PdfReader(dosya)
    for sayfa in pdf_reader.pages:
        icerik += sayfa.extract_text()
    return icerik
  elif dosya_yolu.endswith(".docx"):
    doc = Document(dosya)
    parca = [para.text for para in doc.paragraphs]
    icerik = '\n'.join(parca)
    return icerik

def tools_olusturucu(secilen_kategoriler):
    properties = {}
    required = []
    for kategori in secilen_kategoriler:
        if kategori == "Dosya ismi":
            properties['dosya_adi'] = {"type": "string", "description": "İş ilanı dosyasının adı"} 
            required.append('dosya_adi')
        elif kategori == "Maas":
            properties['maas'] = {"type": "string", "description": "Teklif edilen maaş"} 
            required.append('maas')
        elif kategori == "Calisma Yeri":
            properties['konum'] = {"type": "string", "description": "İşin konumu, şehir ve ülke bilgisi"} 
            required.append('konum')
        elif kategori == "Ilan Basligi":
            properties['ilan_basligi'] = {"type": "string", "description": "İş ilanının başlığı"} 
            required.append('ilan_basligi')
        elif kategori == "Sirket Adi":
            properties['sirket_adi'] = {"type": "string", "description": "İş ilanını veren şirketin adı"} 
            required.append('sirket_adi')
        elif kategori == "Calisma Sekli":
            properties['calisma_sekli'] = {"type": "string", "enum": ["tam zamanlı", "yarı zamanlı", "uzaktan"], "description": "Çalışma şekli, örn: tam zamanlı, yarı zamanlı, uzaktan"} 
            required.append('calisma_sekli')
        elif kategori == "Nitelikler":
            properties['nitelikler'] = {"type": "array", "items": {"type": "string"}, "description": "Pozisyon için gereken nitelikler"} 
            required.append('nitelikler')
        elif kategori == "Sorumluluklar":
            properties['sorumluluklar'] = {"type": "array", "items": {"type": "string"}, "description": "Pozisyonun sorumlulukları"} 
            required.append('sorumluluklar')
        elif kategori == "Iletisim":
            properties['iletisim'] = {"type": "string", "description": "İş ilanı için iletişim bilgileri"} 
            required.append('iletisim')
        elif kategori == "Son Basvuru Tarihi":
            properties['son_basvuru_tarihi'] = {"type": "string", "description": "Son başvuru tarihi"} 
            required.append('son_basvuru_tarihi')
        
    tools = [
      {
        "type": "function",
        "function": {
          "name": "is_ilanlarini_filtrele",
          "description": "Belirli kategorilere gore is ilanlarini filtreler",
          "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
          },
        }
      }
    ]
    return tools

def stream_text(text):
    yer_tutucu = st.empty()
    n_of_tokens = random.choice([2,3,4,5])
    i = 0
    while i<=len(text):
        i += n_of_tokens
        yer_tutucu.markdown(text[:i])
        time.sleep(0.05)

def main():
    st.title("Title 🎈")  # Set the app's title

    # Setup the sidebar
    model, stream, secilen_kategoriler, api_key, uploaded_files = sidebar_setup()
    tools = tools_olusturucu(secilen_kategoriler)
    st.session_state.stream = stream
    st.session_state.tools = tools
    st.session_state.tool_choice = "auto"
    fonksiyonlarim = {
        "is_ilanlarini_filtrele": is_ilanlarini_filtrele
    }

    st.session_state.model = model

    client = OpenAI(api_key=api_key)
    st.session_state.client = client

    if not "mesajlar" in st.session_state:
        st.session_state.mesajlar = [
        {"role": "system", "content": """
        Verilen is ilanlari ile ilgili yardimci bir asistansin.
        Eger kullanici fonksiyon secilmesini gerektirmeyen bir prompt yazarsa, normal cevap ver, fonksiyon secme.
        Is ilanlari ile ilgili elde edilen sonuclari yapilandirilmis formatta, yani alt alta belirli kategorilere gore markdown formatinda yazdir.
        Islem basarili ifadesi, istenen ilanla ilgili sonnucun ekrana basarili bir sekilde yazdirildigi anlamina gelir.
        """}
    ]

    if not "dosya_icerigi" in st.session_state:
        st.session_state.dosya_icerigi = []

    icerik = ''
    for dosya in uploaded_files:
      icerik += f"Dosya ismi {dosya.name} icerisindeki icerik basladi: "
      icerik += oku(dosya)
      icerik += f"Dosya ismi {dosya.name} icerisindeki icerik bitti. "
    # st.write(f"Dosya okundu. Icerik: {icerik}")

    if icerik:
        if not st.session_state.dosya_icerigi or st.session_state.dosya_icerigi[-1]!=icerik:
            st.session_state.mesajlar.append({"role": "user", "content": f"Dosya icerigi: {icerik}"})
            st.session_state.dosya_icerigi.append(icerik)

    # If API key and uploaded files are provided, display the file names and types
    if api_key and uploaded_files:
        for uploaded_file in uploaded_files:
            st.write(f"Uploaded file name: {uploaded_file.name}")

        if prompt := st.chat_input("Prompt'u giriniz ..."):
            st.session_state.mesajlar.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                cevap = handle_tool_calls(fonksiyonlarim)
                st.session_state.mesajlar.append({"role": "assistant", "content": cevap})
                if st.session_state.mesajlar[-2]["role"] == "tool":
                    pass
                else:
                    if st.session_state.stream:
                        stream_text(cevap)
                    else:
                        st.markdown(cevap)


    st.sidebar.header("Chat gecmisi")
    for message in st.session_state.mesajlar:
        if message["role"] == "user" or message["role"] == "assistant":
            if "tool_calls" in message:
                pass
            elif message["content"].startswith("Dosya icerigi: Dosya ismi"):
                pass
            else:
                with st.sidebar.expander(message["role"]):
                    st.write(message["content"])

if __name__ == "__main__":
    main()
