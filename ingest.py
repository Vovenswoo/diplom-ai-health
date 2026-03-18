import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models

os.environ["GOOGLE_API_KEY"] = "AIza......"  

COLLECTION_KNOWLEDGE = "knowledge_base"
COLLECTION_SAFETY = "safety_base"

QDRANT_URL = "http://localhost:6333"

def load_and_split_docs(folder_path):
    """Загружает все PDF из папки и нарезает на кусочки"""
    all_docs = []
    
    if not os.path.exists(folder_path):
        print(f"Папка {folder_path} не найдена!")
        return []
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(folder_path, filename)
            print(f"Загружаю: {filename}")
            try:
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                all_docs.extend(docs)
                print(f"   Загружено страниц: {len(docs)}")
            except Exception as e:
                print(f"   Ошибка при загрузке {filename}: {e}")
    
    if not all_docs:
        print("   Не найдено PDF файлов для загрузки")
        return []
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, 
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = text_splitter.split_documents(all_docs)
    print(f"   Получилось {len(chunks)} смысловых кусочков")
    return chunks

def create_collection_if_not_exists(client, collection_name):
    """Создает коллекцию в Qdrant, если её ещё нет"""
    try:
        collections = client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        
        if not exists:
            print(f"Создаю коллекцию: {collection_name}")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=768,  # Для Gemini embeddings размер 768
                    distance=models.Distance.COSINE
                ),
            )
        else:
            print(f"Коллекция {collection_name} уже существует")
    except Exception as e:
        print(f"Ошибка при создании коллекции: {e}")
        raise

def main():
    print("=" * 50)
    print("ЗАПУСК ЗАГРУЗКИ ДАННЫХ В QDRANT")
    print("=" * 50)
    
    # 1. Подключаемся к Qdrant
    print("\nПодключаюсь к Qdrant...")
    try:
        client = QdrantClient(url=QDRANT_URL)
        # Проверяем соединение
        client.get_collections()
        print("Успешно подключился к Qdrant")
    except Exception as e:
        print(f"Ошибка подключения к Qdrant: {e}")
        print("   Убедись, что Docker с Qdrant запущен!")
        return
    
    # 2. Настраиваем эмбеддинги Gemini
    print("\nНастраиваю эмбеддинги Gemini...")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.environ["GOOGLE_API_KEY"]
        )
        print("Эмбеддинги настроены")
    except Exception as e:
        print(f"Ошибка при настройке эмбеддингов: {e}")
        print("   Проверь свой API ключ!")
        return
    
    # 3. Создаем коллекции
    print("\nПроверяю коллекции...")
    create_collection_if_not_exists(client, COLLECTION_KNOWLEDGE)
    create_collection_if_not_exists(client, COLLECTION_SAFETY)
    
    # 4. Загружаем полезные данные (data_protocols)
    print("\n" + "=" * 50)
    print("ЗАГРУЗКА ПОЛЕЗНЫХ ЗНАНИЙ (data_protocols)")
    print("=" * 50)
    
    kb_chunks = load_and_split_docs("./data_protocols")
    if kb_chunks:
        print(f"\nЗагружаю {len(kb_chunks)} кусочков в коллекцию {COLLECTION_KNOWLEDGE}...")
        try:
            Qdrant.from_documents(
                kb_chunks,
                embeddings,
                url=QDRANT_URL,
                collection_name=COLLECTION_KNOWLEDGE,
                force_recreate=False  # Не пересоздавать, если есть
            )
            print(f"Успешно загружено в {COLLECTION_KNOWLEDGE}!")
        except Exception as e:
            print(f"Ошибка при загрузке: {e}")
    else:
        print("Нет данных для загрузки в knowledge_base")
    
    # 5. Загружаем данные безопасности (data_safety)
    print("\n" + "=" * 50)
    print("ЗАГРУЗКА ДАННЫХ БЕЗОПАСНОСТИ (data_safety)")
    print("=" * 50)
    
    safety_chunks = load_and_split_docs("./data_safety")
    if safety_chunks:
        print(f"\nЗагружаю {len(safety_chunks)} кусочков в коллекцию {COLLECTION_SAFETY}...")
        try:
            Qdrant.from_documents(
                safety_chunks,
                embeddings,
                url=QDRANT_URL,
                collection_name=COLLECTION_SAFETY,
                force_recreate=False
            )
            print(f"Успешно загружено в {COLLECTION_SAFETY}!")
        except Exception as e:
            print(f"Ошибка при загрузке: {e}")
    else:
        print("Нет данных для загрузки в safety_base")
    
    print("\n" + "=" * 50)
    print("ЗАГРУЗКА ЗАВЕРШЕНА!")
    print("=" * 50)

if __name__ == "__main__":
    main()
