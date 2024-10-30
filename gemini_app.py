import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai

# Configura tu clave API de Google AI
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])  # Reemplaza "TU_CLAVE_DE_API" con tu clave de API real

# Configuraciones de generación y seguridad
generation_config = {
    "max_output_tokens": 8192,
    "temperature": 1,
    "top_p": 0.95,
}

safety_settings = {
    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
    "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
}

# Función para extraer texto de un PDF con números de página
def extract_text_with_page_numbers(pdf_path):
    try:
        pdf_document = fitz.open("pdf", pdf_path.read())
        text_paginated = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text_paginated += f"--- Página {page_num + 1} ---\n"
            text_paginated += page.get_text()
            text_paginated += "\n\n"
        return text_paginated
    except Exception as e:
        st.error(f"Ocurrió un error: {e}")
        return None

# Función para generar contenido usando la API de Gemini
def multiturn_generate_content(text, container):
    # Selecciona el modelo de Gemini
    model = genai.GenerativeModel("gemini-1.5-pro")

    # Genera contenido en streaming para múltiples turnos
    response = model.generate_content(
        text, 
        stream=True
    )
    
    full_summary = ""

    # Procesa la respuesta del modelo en streaming
    for chunk in response:
        full_summary += chunk.text
        container.markdown(full_summary, unsafe_allow_html=True)

    return full_summary

def main():
    st.title("Convertidor de PDF a Texto y Generador de Resúmenes con AI")
    
    uploaded_file = st.file_uploader("Sube un archivo PDF aquí", type="pdf")

    if uploaded_file is not None:
        text = extract_text_with_page_numbers(uploaded_file)
        
        if text:
            st.success("El PDF ha sido convertido exitosamente.")
            select_encoding = st.selectbox("Selecciona la codificación del texto", ["utf-8", "latin-1", "windows-1252"])
            output_path = uploaded_file.name.replace(".pdf", "_output.txt")
            with open(output_path, "w", encoding=select_encoding, errors="replace") as output_file:
                output_file.write(text)

            # Mostrar botón para generar resumen con AI
            ai_button = st.button("Generar Resumen con AI", key="generate_summary")

            if ai_button:
                st.session_state.summary_container = st.empty()
                summary = multiturn_generate_content(text, st.session_state.summary_container)

                user_input = st.text_area("¿Quieres ajustar algo en el resumen?", height=100)
                if user_input:
                    adjusted_input = "Instrucción adicional del usuario: " + user_input + "\n\nResumen generado previamente:\n" + summary +  "\n\nTexto original del documento:\n" + text
                    adjusted_summary = multiturn_generate_content(adjusted_input, st.session_state.summary_container)

            # Botón para descargar el texto extraído del PDF
            st.download_button(
                "Guardar Texto Extraído", 
                text, 
                f"{uploaded_file.name.replace('.pdf', '_output.txt')}", 
                mime="text/plain"
            )

if __name__ == "__main__":
    main()
