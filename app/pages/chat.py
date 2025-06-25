import reflex as rx
from app.states.rag_state import RAGState

def chat() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h1("Asistente Virtual", class_name="text-2xl font-bold mb-4"),
            rx.el.input(
                placeholder="Escribe tu pregunta...",
                on_change=RAGState.set_pregunta,
                default_value=RAGState.pregunta,
                class_name="w-full px-4 py-2 border rounded mb-4"
            ),
            rx.el.button(
                rx.cond(
                    RAGState.is_loading,
                    "Procesando...",
                    "Preguntar"
                ),
                on_click=RAGState.generar,
                disabled=RAGState.is_loading,
                class_name="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 mb-4"
            ),
            rx.el.textarea(
                default_value=RAGState.respuesta,
                key=RAGState.respuesta,
                read_only=True,
                class_name="w-full p-4 border rounded bg-gray-100 text-gray-800 min-h-[200px]",
                placeholder="La respuesta aparecerá aquí...",
            ),
            rx.cond(
                RAGState.error_message,
                rx.el.div(
                    RAGState.error_message,
                    class_name="p-4 mt-4 text-sm text-red-700 bg-red-100 rounded border border-red-300",
                ),
                rx.fragment()
            ),
            # ✅ Botón para volver a subir documentos
            rx.el.a(
                "Subir más documentos",
                href="/",
                class_name="inline-block mt-4 text-blue-600 hover:text-blue-800 underline text-sm"
            ),
            class_name="max-w-xl mx-auto p-6 bg-white rounded-xl shadow-xl border border-gray-200"
        ),
        class_name="min-h-screen flex flex-col items-center justify-center p-8 bg-gray-100"
    )

# ✅ Registrar la página
page = rx.page(chat, route="/chat", title="Asistente RAG")
