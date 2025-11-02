"""
Script para inicializar o banco de dados
"""
from database.session import init_db

if __name__ == "__main__":
    print("Inicializando banco de dados...")
    init_db()
    print("✅ Banco de dados inicializado com sucesso!")
    print("\nTabelas criadas:")
    print("  - documents")
    print("  - agent_logs")
    print("  - processing_queue")
    print("  - credentials")
