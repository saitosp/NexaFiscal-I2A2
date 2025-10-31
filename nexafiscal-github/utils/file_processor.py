"""
Processadores de arquivos para notas fiscais
"""
import base64
import xmltodict
from typing import Dict, Any, Optional
import pytesseract
from PIL import Image
import io
import os

try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import pypdfium2 as pdfium
    HAS_PYPDFIUM = True
except ImportError:
    HAS_PYPDFIUM = False


def process_xml(file_path: str) -> Dict[str, Any]:
    """
    Processa um arquivo XML de NFe
    
    Args:
        file_path: Caminho do arquivo XML
        
    Returns:
        Dicionário com os dados extraídos do XML
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Parse XML to dict
        data = xmltodict.parse(xml_content)
        
        return {
            'success': True,
            'data': data,
            'format': 'xml',
            'raw_content': xml_content
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'format': 'xml'
        }


def extract_text_from_image(image_path: str) -> str:
    """
    Extrai texto de uma imagem usando OCR
    
    Args:
        image_path: Caminho da imagem
        
    Returns:
        Texto extraído
    """
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='por')
        return text
    except Exception as e:
        return f"Erro ao extrair texto: {str(e)}"


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extrai texto de um PDF usando OCR ou extração direta
    Funciona com ou sem Poppler usando pypdfium2 como alternativa
    
    Args:
        pdf_path: Caminho do arquivo PDF
        
    Returns:
        Texto extraído de todas as páginas
    """
    # 1. Tenta primeiro extrair texto direto com pdfplumber (não requer Poppler)
    if HAS_PDFPLUMBER:
        try:
            full_text = []
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        full_text.append(f"--- Página {i+1} ---\n{text}")
            
            # Se extraiu texto, retorna
            if full_text:
                return "\n\n".join(full_text)
        except Exception as e:
            pass  # Fallback para OCR
    
    # 2. Se não tem texto (PDF escaneado), tenta OCR com pypdfium2 (não requer Poppler)
    if HAS_PYPDFIUM:
        try:
            pdf = pdfium.PdfDocument(pdf_path)
            full_text = []
            
            for i in range(len(pdf)):
                page = pdf[i]
                # Renderiza página como imagem
                bitmap = page.render(scale=2.0)  # 2x para melhor OCR
                pil_image = bitmap.to_pil()
                
                # OCR na imagem
                text = pytesseract.image_to_string(pil_image, lang='por')
                if text.strip():
                    full_text.append(f"--- Página {i+1} ---\n{text}")
            
            pdf.close()
            
            if full_text:
                return "\n\n".join(full_text)
        except Exception as e:
            pass  # Tenta próxima opção
    
    # 3. Fallback: OCR com pdf2image (requer Poppler - pode falhar)
    if HAS_PDF2IMAGE:
        try:
            images = convert_from_path(pdf_path)
            
            full_text = []
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image, lang='por')
                full_text.append(f"--- Página {i+1} ---\n{text}")
            
            return "\n\n".join(full_text)
        except Exception as e:
            pass  # Poppler não disponível
    
    # Se chegou aqui, nenhum método funcionou
    return "Erro: Não foi possível extrair texto do PDF. Instale Tesseract OCR ou verifique o arquivo."


def process_pdf(file_path: str) -> Dict[str, Any]:
    """
    Processa um arquivo PDF de nota fiscal
    Funciona com ou sem Poppler usando pypdfium2
    
    Args:
        file_path: Caminho do arquivo PDF
        
    Returns:
        Dicionário com os dados extraídos
    """
    try:
        text = extract_text_from_pdf(file_path)
        
        # Verifica se a extração falhou
        if text.startswith("Erro:"):
            return {
                'success': False,
                'error': text,
                'format': 'pdf'
            }
        
        # Tenta converter primeira página para base64 para análise visual
        image_base64 = None
        num_pages = 0
        
        # Tenta com pypdfium2 primeiro (não requer Poppler)
        if HAS_PYPDFIUM:
            try:
                pdf = pdfium.PdfDocument(file_path)
                num_pages = len(pdf)
                
                if num_pages > 0:
                    # Renderiza primeira página
                    page = pdf[0]
                    bitmap = page.render(scale=2.0)
                    pil_image = bitmap.to_pil()
                    
                    buffered = io.BytesIO()
                    pil_image.save(buffered, format="PNG")
                    image_base64 = base64.b64encode(buffered.getvalue()).decode()
                
                pdf.close()
            except Exception as e:
                pass  # Tenta alternativa
        
        # Fallback: pdf2image (requer Poppler)
        if not image_base64 and HAS_PDF2IMAGE:
            try:
                images = convert_from_path(file_path, first_page=1, last_page=1)
                if images:
                    buffered = io.BytesIO()
                    images[0].save(buffered, format="PNG")
                    image_base64 = base64.b64encode(buffered.getvalue()).decode()
                
                # Conta páginas
                all_images = convert_from_path(file_path)
                num_pages = len(all_images)
            except:
                pass  # Continua sem imagem
        
        # Última alternativa: conta páginas com pdfplumber
        if num_pages == 0 and HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(file_path) as pdf:
                    num_pages = len(pdf.pages)
            except:
                num_pages = 1  # Assume 1 página se falhar
        
        return {
            'success': True,
            'text': text,
            'image_base64': image_base64,
            'format': 'pdf',
            'num_pages': num_pages or 1
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'format': 'pdf'
        }


def process_image(file_path: str) -> Dict[str, Any]:
    """
    Processa uma imagem de nota fiscal
    
    Args:
        file_path: Caminho da imagem
        
    Returns:
        Dicionário com os dados extraídos
    """
    try:
        text = extract_text_from_image(file_path)
        
        # Converte imagem para base64
        with open(file_path, 'rb') as f:
            image_base64 = base64.b64encode(f.read()).decode()
        
        return {
            'success': True,
            'text': text,
            'image_base64': image_base64,
            'format': 'image'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'format': 'image'
        }


def get_file_type(filename: str) -> str:
    """
    Determina o tipo de arquivo baseado na extensão
    
    Args:
        filename: Nome do arquivo
        
    Returns:
        Tipo: 'xml', 'pdf', 'image' ou 'unknown'
    """
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == '.xml':
        return 'xml'
    elif ext == '.pdf':
        return 'pdf'
    elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        return 'image'
    else:
        return 'unknown'
