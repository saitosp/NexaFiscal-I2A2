# 📡 API REST - Documentação

API REST para extração automatizada de dados de notas fiscais brasileiras.

## 🚀 Endpoints Disponíveis

### Base URL
```
http://localhost:8000
```

## Endpoints

### 1. Health Check
```http
GET /
```

**Resposta:**
```json
{
  "status": "online",
  "service": "NFe Extraction API",
  "version": "1.0.0",
  "timestamp": "2025-10-28T22:41:33.398732"
}
```

---

### 2. Upload de Documento
```http
POST /api/documents/upload
```

**Parâmetros:**
- `file` (multipart/form-data): Arquivo XML, PDF ou imagem da nota fiscal

**Formatos aceitos:** xml, pdf, jpg, jpeg, png

**Resposta de Sucesso:**
```json
{
  "document_id": 1,
  "filename": "nota_fiscal.xml",
  "status": "completed",
  "message": "Documento processado com sucesso"
}
```

**Exemplo cURL:**
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/nota_fiscal.xml"
```

---

### 3. Listar Documentos
```http
GET /api/documents
```

**Query Parameters:**
- `limit` (int, opcional): Número máximo de resultados (máx 100, padrão 50)
- `offset` (int, opcional): Offset para paginação (padrão 0)
- `search` (string, opcional): Busca por nome de arquivo ou emitente
- `document_type` (string, opcional): Filtro por tipo de documento (NFe, NFCe, SAT, etc)

**Resposta:**
```json
[
  {
    "id": 1,
    "filename": "nota_fiscal.xml",
    "document_type": "NFe",
    "document_number": "000123",
    "issuer_name": "Empresa XYZ LTDA",
    "total_value": 1500.00,
    "is_valid": true,
    "has_errors": false,
    "processing_status": "completed",
    "created_at": "2025-10-28T20:30:15"
  }
]
```

**Exemplo cURL:**
```bash
# Listar todos
curl http://localhost:8000/api/documents

# Com filtros
curl "http://localhost:8000/api/documents?limit=10&search=empresa&document_type=NFe"
```

---

### 4. Detalhes do Documento
```http
GET /api/documents/{document_id}
```

**Parâmetros de URL:**
- `document_id` (int): ID do documento

**Resposta:**
```json
{
  "id": 1,
  "filename": "nota_fiscal.xml",
  "file_type": "xml",
  "document_type": "NFe",
  "document_number": "000123",
  "access_key": "35210812345678901234567890123456789012345678",
  "issuer_cnpj": "12345678000190",
  "issuer_name": "Empresa XYZ LTDA",
  "recipient_cnpj": "98765432000100",
  "recipient_name": "Cliente ABC",
  "total_value": 1500.00,
  "tax_total": 200.00,
  "issue_date": "2025-10-28T10:00:00",
  "extracted_data": { ... },
  "classification_data": { ... },
  "validation_data": { ... },
  "is_valid": true,
  "has_errors": false,
  "processing_status": "completed",
  "created_at": "2025-10-28T20:30:15",
  "updated_at": "2025-10-28T20:30:15"
}
```

**Exemplo cURL:**
```bash
curl http://localhost:8000/api/documents/1
```

---

### 5. Logs de Processamento
```http
GET /api/documents/{document_id}/logs
```

**Parâmetros de URL:**
- `document_id` (int): ID do documento

**Resposta:**
```json
[
  {
    "id": 1,
    "agent_name": "ClassificationAgent",
    "agent_status": "completed",
    "error_message": null,
    "started_at": "2025-10-28T20:30:15",
    "completed_at": "2025-10-28T20:30:16",
    "duration_seconds": 1.2
  },
  {
    "id": 2,
    "agent_name": "ExtractionAgent",
    "agent_status": "completed",
    "error_message": null,
    "started_at": "2025-10-28T20:30:16",
    "completed_at": "2025-10-28T20:30:18",
    "duration_seconds": 2.5
  }
]
```

**Exemplo cURL:**
```bash
curl http://localhost:8000/api/documents/1/logs
```

---

### 6. Estatísticas do Sistema
```http
GET /api/statistics
```

**Resposta:**
```json
{
  "total": 150,
  "valid": 140,
  "invalid": 10,
  "by_type": {
    "NFe": 100,
    "NFCe": 30,
    "SAT": 20
  }
}
```

**Exemplo cURL:**
```bash
curl http://localhost:8000/api/statistics
```

---

### 7. Fila de Processamento
```http
GET /api/queue
```

**Query Parameters:**
- `limit` (int, opcional): Número máximo de itens (máx 50, padrão 10)

**Resposta:**
```json
[
  {
    "id": 1,
    "batch_id": "batch_20251028_001",
    "priority": 5,
    "status": "pending",
    "scheduled_at": "2025-10-28T21:00:00",
    "created_at": "2025-10-28T20:45:00"
  }
]
```

**Exemplo cURL:**
```bash
curl http://localhost:8000/api/queue?limit=20
```

---

### 8. Status de Lote
```http
GET /api/queue/batch/{batch_id}
```

**Parâmetros de URL:**
- `batch_id` (string): ID do lote

**Resposta:**
```json
{
  "batch_id": "batch_20251028_001",
  "total": 50,
  "pending": 10,
  "processing": 5,
  "completed": 30,
  "failed": 5
}
```

**Exemplo cURL:**
```bash
curl http://localhost:8000/api/queue/batch/batch_20251028_001
```

---

## 🔐 Códigos de Status HTTP

- `200` - Sucesso
- `400` - Requisição inválida
- `404` - Recurso não encontrado
- `500` - Erro interno do servidor

## 📝 Exemplos de Integração

### Python com requests
```python
import requests

# Upload de documento
with open('nota_fiscal.xml', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/api/documents/upload', files=files)
    data = response.json()
    print(f"Documento ID: {data['document_id']}")

# Listar documentos
response = requests.get('http://localhost:8000/api/documents', params={'limit': 10})
documents = response.json()
for doc in documents:
    print(f"{doc['filename']} - {doc['document_type']}")

# Estatísticas
response = requests.get('http://localhost:8000/api/statistics')
stats = response.json()
print(f"Total de documentos: {stats['total']}")
```

### JavaScript com fetch
```javascript
// Upload de documento
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/api/documents/upload', {
  method: 'POST',
  body: formData
})
.then(res => res.json())
.then(data => console.log('Documento ID:', data.document_id));

// Listar documentos
fetch('http://localhost:8000/api/documents?limit=10')
  .then(res => res.json())
  .then(docs => console.log('Documentos:', docs));
```

### cURL Avançado
```bash
# Upload com verificação de erro
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@nota.xml" \
  -w "\nHTTP Status: %{http_code}\n"

# Pipeline de processamento
DOCUMENT_ID=$(curl -s -X POST http://localhost:8000/api/documents/upload \
  -F "file=@nota.xml" | jq -r '.document_id')

echo "Documento processado com ID: $DOCUMENT_ID"

# Buscar detalhes
curl -s http://localhost:8000/api/documents/$DOCUMENT_ID | jq .
```

## 🌐 Documentação Interativa

Acesse a documentação interativa Swagger em:
```
http://localhost:8000/docs
```

Ou a documentação ReDoc em:
```
http://localhost:8000/redoc
```

## ⚙️ Configuração

A API roda na porta `8000` por padrão e compartilha o mesmo banco de dados PostgreSQL com a interface Streamlit.

### Variáveis de Ambiente Necessárias:
- `DATABASE_URL` - URL de conexão com PostgreSQL
- `GROQ_API_KEY` - Chave de API do Groq para IA

## 🔗 Integração com ERP

A API foi projetada para fácil integração com sistemas de gestão (ERP):

1. **Upload automático**: Envie XMLs recebidos via webhook
2. **Consulta periódica**: Busque documentos processados em intervalos
3. **Sincronização**: Use os dados extraídos para popular seu sistema

### Exemplo de Integração Contínua
```python
import requests
import time

API_URL = "http://localhost:8000"

def monitor_new_documents():
    last_id = 0
    
    while True:
        # Busca documentos mais recentes
        response = requests.get(f"{API_URL}/api/documents", params={"limit": 10})
        documents = response.json()
        
        for doc in documents:
            if doc['id'] > last_id:
                # Novo documento encontrado
                print(f"Processando documento {doc['id']}: {doc['filename']}")
                
                # Busca detalhes completos
                detail = requests.get(f"{API_URL}/api/documents/{doc['id']}").json()
                
                # Integra com seu ERP
                integrate_with_erp(detail)
                
                last_id = doc['id']
        
        time.sleep(60)  # Verifica a cada 1 minuto

def integrate_with_erp(document_data):
    # Sua lógica de integração aqui
    pass
```

## 📊 Rate Limiting e Limites

Atualmente não há rate limiting configurado. Recomendações para produção:

- Máximo de 100 documentos por requisição de listagem
- Timeout de 60 segundos para processamento de upload
- Batch de até 50 itens por lote

## 🛠️ Troubleshooting

### Erro 500 no upload
- Verifique se o arquivo está no formato correto
- Confirme que GROQ_API_KEY está configurada
- Veja os logs do servidor para mais detalhes

### Documento não encontrado (404)
- Confirme que o ID do documento existe
- Verifique se o banco de dados está acessível

### Timeout
- Arquivos PDF muito grandes podem demorar
- Considere aumentar o timeout para imagens de baixa qualidade que precisam de OCR
