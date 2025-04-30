import cv2
import easyocr
import re

reader = easyocr.Reader(['pt', 'en'])

def capturar_imagem():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite('static/captures/captura.jpg', frame)
    cap.release()

def detectar_placa(path_imagem):
    resultados = reader.readtext(path_imagem)

    placas = []
    for (bbox, texto, confianca) in resultados:
        texto = texto.upper().replace(" ", "").replace("-", "")
        
        # Validação 1: tem que ter 7 caracteres
        if len(texto) == 7:
            # Validação 2 (opcional): verificar se bate com padrão brasileiro
            if re.match(r'^[A-Z]{3}[0-9]{4}$', texto) or re.match(r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$', texto):
                placas.append(texto)

    return placas
