from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

api = FastAPI(  # Esto permite exponer Swagger en /docs
    title="RAG API",
    description="API para responder preguntas usando RAG",
    version="1.0.0",
)

# Permitir CORS desde cualquier origen
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear el router
router = APIRouter()

# Modelo de entrada
class Pregunta(BaseModel):
    pregunta: str

# Ruta POST
@router.post("/rag", summary="Responder una pregunta usando RAG")
def responder_pregunta(p: Pregunta):
    from app.states.rag_state import responder_pregunta_rag
    respuesta = responder_pregunta_rag(p.pregunta)
    return {"respuesta": respuesta}

# Montar en /api
api.include_router(router, prefix="/api")
