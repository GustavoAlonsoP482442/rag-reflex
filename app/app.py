import reflex as rx
from app.states.rag_state import RAGState
from rxconfig import config

def index() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h1(
                "Sube un documento",
                class_name="text-2xl font-bold mb-4"
            ),
            rx.upload(
                id="archivo_usuario",
                accept=[".pdf", ".txt", ".docx"],
                max_files=1,
                show_file_list=True,
                class_name="mb-4",
            ),
            rx.el.button(
                "Procesar Documento",
                on_click=lambda: RAGState.procesar_archivo(rx.upload_files("archivo_usuario")),
                class_name="bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700"
            ),
            rx.el.a(
                "Ir al asistente",
                href="/chat",
                class_name="inline-block mt-4 text-blue-600 hover:text-blue-800 underline text-sm"
            ),
            rx.el.div(
                RAGState.mensaje_procesamiento,
                class_name="text-sm text-gray-700 mt-2"
            ),
            class_name="max-w-xl mx-auto p-6 bg-white rounded-xl shadow-xl border border-gray-200"
        ),
        class_name="min-h-screen flex flex-col items-center justify-center p-8 bg-gray-100"
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

from app.pages.chat import chat
app.add_page(chat, route="/chat")

