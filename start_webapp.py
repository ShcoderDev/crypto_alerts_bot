import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    from webapp.backend.main import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

