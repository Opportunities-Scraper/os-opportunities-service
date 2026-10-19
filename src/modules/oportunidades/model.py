from src.modules.categorias.model import Categoria
from src.modules.modalidade.model import Modalidade


class Oportunidade:
    oportunidad_id: int
    titulo: str 
    descricao: str 
    url_original: str 
    ṕai: str 
    cidade: str 
    modalidade: Modalidade 
    data_publicacao: str
    data_limite: str 
    categoria_id: int