FROM python:3.10-slim

WORKDIR /app

# Сначала зависимости (кэшируется)
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Потом весь код
COPY . .

CMD ["python", "app.py"]