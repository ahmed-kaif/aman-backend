# Aman Backend

## Project Setup 
1. Clone the repo
```bash
git clone https://github.com/ahmed-kaif/aman-backend.git
```

2. Create Python Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requiremnets.txt
```

4. Run the server
```bash 
uvicorn app.main:app --reload # without Docker 
```

5. To run with Docker 
```bash 
docker build -t my-fastapi-app .
docker run -p 8000:8000 --env-file .env --name my-api-container my-fastapi-app
```
```

