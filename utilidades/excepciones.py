import variables_globales as vg

class BusinessException(TypeError):
    """
    Excepcion de negocio

    Se utiliza para lanzar excepciones de negocio.
    params: mensaje (str) - Mensaje de error.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        # Se asigna el mensaje de error a la variable global
        vg.business_exception = args[0]

class SystemException(TypeError):
    """
    Excepcion de sistema
    
    Se utiliza para lanzar excepciones de sistema.
    params: mensaje (str) - Mensaje de error.
    """
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        # Se asigna el mensaje de error a la variable global
        vg.system_exception = args[0]