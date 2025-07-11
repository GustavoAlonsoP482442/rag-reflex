import reflex as rx
import os
from dotenv import load_dotenv
load_dotenv()
print("🔍 OPENAI_API_KEY:", os.environ.get("OPENAI_API_KEY")) #para asegurarme de que realmente se estan cargando
print("🔍 PINECONE_API_KEY:", os.environ.get("PINECONE_API_KEY"))
print("🔍 PINECONE_INDEX_NAME:", os.environ.get("PINECONE_INDEX_NAME"))
import time
from pinecone import Pinecone
from openai import OpenAI
from typing import List, Dict, Optional
import fitz
import docx
import uuid
import json
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME")
PINECONE_NAMESPACE = os.environ.get("PINECONE_NAMESPACE", "Pruebas")
openai_client_instance: Optional[OpenAI] = None
pinecone_index_instance = None
initialization_error: Optional[str] = None

try:
    if OPENAI_API_KEY:
        openai_client_instance = OpenAI(api_key=OPENAI_API_KEY)
    else:
        initialization_error = "OpenAI API key not found. Please set OPENAI_API_KEY."

    if PINECONE_API_KEY and PINECONE_INDEX_NAME:
        pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
        existing_indexes = [idx_spec.name for idx_spec in pinecone_client.list_indexes()]
        if PINECONE_INDEX_NAME in existing_indexes:
            pinecone_index_instance = pinecone_client.Index(PINECONE_INDEX_NAME)
        else:
            error_msg = f"Pinecone index '{PINECONE_INDEX_NAME}' does not exist. Available indexes: {existing_indexes}."
            initialization_error = f"{initialization_error}\n{error_msg}" if initialization_error else error_msg
            print(error_msg)
    elif not PINECONE_API_KEY:
        error_msg = "Pinecone API key not found. Please set PINECONE_API_KEY."
        initialization_error = f"{initialization_error}\n{error_msg}" if initialization_error else error_msg
    elif not PINECONE_INDEX_NAME:
        error_msg = "Pinecone index name not found. Please set PINECONE_INDEX_NAME."
        initialization_error = f"{initialization_error}\n{error_msg}" if initialization_error else error_msg
except Exception as e:
    error_msg = f"Error during client initialization: {e}"
    initialization_error = f"{initialization_error}\n{error_msg}" if initialization_error else error_msg
    print(error_msg)

def get_embedding(pregunta: str) -> Optional[List[float]]:
    if not openai_client_instance:
        print("OpenAI client not initialized.")
        return None
    try:
        response = openai_client_instance.embeddings.create(
            input=pregunta, model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def buscar_contexto(embedding: List[float], top_k: int = 10) -> str:
    if not pinecone_index_instance:
        print("Pinecone index not initialized.")
        return "Error: Pinecone index not available."
    try:
        query_response = pinecone_index_instance.query(
            vector=embedding,
            top_k=top_k,
            namespace=PINECONE_NAMESPACE,
            include_metadata=True,
        )
        context_parts = []
        for match in query_response.matches:
            if match.metadata and "texto" in match.metadata:
                context_parts.append(match.metadata["texto"])
        return "\n---\n".join(context_parts)
    except Exception as e:
        print(f"Error searching context: {e}")
        return f"Error searching context: {e}"

def generar_respuesta_openai(pregunta: str, contexto: str) -> str:
    if not openai_client_instance:
        print("OpenAI client not initialized.")
        return "Error: OpenAI client not available."
    system_prompt = "Responde exclusivamente con la información proporcionada en el contexto. No agregues conocimientos previos ni información externa. Si no puedes responder con el contexto, di que no hay suficiente información."
    user_prompt = f"{contexto}\n\nPregunta: {pregunta}"
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    try:
        response = openai_client_instance.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages, temperature=0,
        )
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            return response.choices[0].message.content
        else:
            return "No response content from AI."
    except Exception as e:
        print(f"Error generating answer with OpenAI: {e}")
        return f"Error generating answer with OpenAI: {e}"

def responder_pregunta_rag(pregunta: str) -> str:
    if initialization_error or not openai_client_instance or (not pinecone_index_instance):
        error_detail = initialization_error or "OpenAI or Pinecone client not initialized."
        return f"Error: Services not properly initialized. Please check configuration and logs. Detail: {error_detail}"
    start_time = time.time()
    embedding = get_embedding(pregunta)
    if embedding is None:
        return "Error: No se pudo generar el embedding para la pregunta."
    contexto = buscar_contexto(embedding)
    if contexto.startswith("Error:"):
        return contexto
    respuesta_content = generar_respuesta_openai(pregunta, contexto)
    end_time = time.time()
    segundos = round(end_time - start_time, 2)
    minutos = round(segundos / 60, 2)
    return f"Respuesta:\n{respuesta_content}\n\nTiempo de respuesta: {segundos} segundos ({minutos} minutos)"

class RAGState(rx.State):
    pregunta: str = ""
    respuesta: str = ""
    is_loading: bool = False
    error_message: str = ""
    archivo_subido: str = ""
    mensaje_procesamiento: str = ""

    def _check_clients_initialized_internal(self) -> str:
        if initialization_error:
            return f"Error de inicialización: {initialization_error}. Por favor, verifica las variables de entorno (OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME) y la configuración del índice en Pinecone."
        if not openai_client_instance:
            return "El cliente de OpenAI no está inicializado. Verifica OPENAI_API_KEY."
        if not pinecone_index_instance:
            return "El índice de Pinecone no está inicializado. Verifica PINECONE_API_KEY, PINECONE_INDEX_NAME y que el índice exista."
        return ""

    @rx.event(background=True)        
    async def generar(self):
        async with self:
            self.is_loading = True
            self.respuesta = ""
            self.error_message = ""
            texto = self.pregunta.strip()
            #Validación: campo vacío
            if not texto:
                mensaje= "Por favor,escribe una pregunta."
                self.respuesta = mensaje
                self.error_message = mensaje
                self.is_loading = False
                yield
                return
            # Validación: emojis
            emoji_pattern = re.compile("[\U0001F600-\U0001F64F"
                           "\U0001F300-\U0001F5FF"
                           "\U0001F680-\U0001F6FF"
                           "\U0001F1E0-\U0001F1FF"
                           "\U00002700-\U000027BF"
                           "\U0001F900-\U0001F9FF"
                           "\U00002600-\U000026FF]+", flags=re.UNICODE)
            if emoji_pattern.search(texto):
                mensaje = "No se permiten emojis en la pregunta."
                self.respuesta = mensaje
                self.error_message = mensaje
                self.is_loading = False
                yield
                return
            #Validación: solo caracteres latinos
            if re.search(r"[^\u0000-\u007FáéíóúÁÉÍÓÚñÑüÜçÇ\s.,;:?!¿¡()\"'-]", texto):
                mensaje = "Solo se permite ingresar texto en alfabeto latino."
                self.respuesta = mensaje
                self.error_message = mensaje
                self.is_loading = False
                yield
                return
            #Validación: debe contener al menos una letra
            if not re.search(r"[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]", texto):
                mensaje = "La pregunta debe contener letras."
                self.respuesta = mensaje
                self.error_message = mensaje
                self.is_loading = False
                yield
                return
            # Validación: al menos 3 palabras
            if len(texto.split()) < 3:
                mensaje = "La pregunta debe contener al menos 3 palabras."
                self.respuesta = mensaje
                self.error_message = mensaje
                self.is_loading = False
                yield
                return

        error_msg = self._check_clients_initialized_internal()
        if error_msg:
            async with self:
                self.error_message = error_msg
                self.respuesta = error_msg
                self.is_loading = False
                yield
            return

        generated_response = responder_pregunta_rag(self.pregunta)
        async with self:
            self.respuesta = generated_response
            if generated_response.startswith("Error:"):
                self.error_message = generated_response
            self.is_loading = False
            yield

    @rx.event
    async def procesar_archivo(self, files: list[rx.UploadFile]):
        print("➡️ Evento 'procesar_archivo' disparado.")

        if not files:            
            self.mensaje_procesamiento = "No se seleccionó ningún archivo."
            print("⚠️ No se recibió ningún archivo.")                
            return

        file = files[0]
        print(f"📁 Archivo recibido: {file.name}")

        content = await file.read()
        path = rx.get_upload_dir() / file.name
        with open(path, "wb") as f:
            f.write(content)
        print(f"📂 Guardado como: {path}")

        nombre = file.name.lower()

        texto = ""

        # Procesamiento de texto
        try:
            if nombre.endswith(".pdf"):                
                doc = fitz.open(str(path))
                texto = "".join(p.get_text() for p in doc)
            elif nombre.endswith(".txt"):
                with open(path, "r", encoding="utf-8") as f:
                    texto = f.read()
            elif nombre.endswith(".docx"):                
                doc = docx.Document(str(path))
                texto = "\n".join(p.text for p in doc.paragraphs)
            else:            
                self.mensaje_procesamiento = "Tipo de archivo no soportado."                
                return
        except Exception as e:   
            self.mensaje_procesamiento = f"Error al procesar el archivo: {e}"
            print("❌ Error procesando archivo:", e)
            return 
        
        # Validación: texto vacío
        if not texto.strip():
            self.mensaje_procesamiento = "El archivo está vacío o no se pudo leer texto."
            print("⚠️ Archivo sin texto útil.")
            return

        
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text(texto)
        metadatos = []

        for i, chunk in enumerate(chunks):
            try:
                embedding = get_embedding(chunk)
                metadata = {
                    "id": str(uuid.uuid4()),
                    "fuente": nombre,
                    "texto": chunk,
                    "posicion": i
                }
                pinecone_index_instance.upsert([(metadata["id"], embedding, metadata)], namespace=PINECONE_NAMESPACE)
                metadatos.append(metadata)
            except Exception as e:
                print(f"[X] Error en chunk {i}: {e}")


        self.mensaje_procesamiento = (
        f"Documento '{file.name}' procesado correctamente. Chunks: {len(metadatos)}"
        )
        print("✅ Procesamiento exitoso.")
        
        
            
