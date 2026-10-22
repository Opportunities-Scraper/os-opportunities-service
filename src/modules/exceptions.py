# Exceções de domínio: descrevem o que deu errado na regra de negócio, sem saber
# nada de HTTP nem de banco. Services e repositories lançam estas exceções, e a
# tradução para status HTTP acontece em um único lugar: app/main.py.


class DomainError(Exception):
    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class NaoEncontradoError(DomainError):
    pass


class ConflitoError(DomainError):
    pass


# O dado aponta para outro registro que não existe (ex.: categoria_id inexistente)
class ReferenciaInvalidaError(DomainError):
    pass


# O banco rejeitou a operação por violar uma restrição (FK, chave duplicada...).
# É genérica: quando sabe o motivo, o service a converte em uma exceção mais específica.
class IntegridadeError(DomainError):
    pass
