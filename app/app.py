import reflex as rx 
from app.states.rag_state import RAGState
from rxconfig import config

def index() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h1(
                "Asistente Virtual Inteligente",
                class_name="text-4xl font-bold text-gray-800 mb-2",
            ),
            rx.el.p(
                "Haz preguntas basadas en tus documentos indexados en Pinecone.",
                class_name="text-lg text-gray-600 mb-6",
            ),
            rx.el.div(
                rx.el.input(
                    placeholder="Escribe tu pregunta aquí...",
                    on_change=RAGState.set_pregunta,
                    class_name="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                    default_value=RAGState.pregunta,
                ),
                rx.el.button(
                    rx.cond(
                        RAGState.is_loading,
                        rx.el.div(
                            rx.icon(
                                tag="loader-circle",
                                class_name="animate-spin mr-2",
                            ),
                            "Procesando...",
                            class_name="flex items-center justify-center",
                        ),
                        "Preguntar",
                    ),
                    on_click=RAGState.generar,
                    disabled=RAGState.is_loading,
                    class_name="mt-4 w-full bg-blue-600 text-white py-3 px-6 rounded-lg shadow-md hover:bg-blue-700 transition-colors duration-200 font-medium disabled:opacity-50 flex items-center justify-center",
                ),
                class_name="mb-6",
            ),
            rx.el.div(
                rx.upload(
                    accept=[".pdf", ".txt", ".docx"],
                    max_files=1,                    
                    class_name="mb-4",
                    show_file_list=True,
                    id="archivo_usuario"
                ),              
                rx.el.button(
                    "Procesar Documento",
                    on_click=lambda: RAGState.procesar_archivo(rx.upload_files()),
                    class_name="mb-6 bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700"
                ),
                rx.el.div(
                    RAGState.mensaje_procesamiento,
                    class_name="text-sm text-gray-700 mt-2"
                )
            ),
            rx.cond(
                RAGState.error_message,
                rx.el.div(
                    RAGState.error_message,
                    class_name="p-4 mb-4 text-sm text-red-700 bg-red-100 rounded-lg border border-red-300",
                ),
                rx.fragment(),
            ),
            rx.el.textarea(
                default_value=RAGState.respuesta,
                key=RAGState.respuesta,
                read_only=True,
                class_name="w-full p-4 border border-gray-300 rounded-lg shadow-sm bg-gray-50 min-h-[200px] text-gray-700 whitespace-pre-wrap",
                placeholder="La respuesta aparecerá aquí...",
            ),
            class_name="max-w-2xl mx-auto p-6 sm:p-8 bg-white rounded-xl shadow-xl mt-10 border border-gray-200",
        ),
        class_name="min-h-screen bg-gray-100 py-10 flex flex-col items-center font-['Inter']",
    )

app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(
            rel="preconnect",
            href="https://fonts.googleapis.com",
        ),
        rx.el.link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            crossorigin="",
        ),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index, route="/")
