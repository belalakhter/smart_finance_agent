FROM python:3.12-slim-bullseye

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        curl \
        build-essential \
        python3-dev \
        libbrlapi-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000
EXPOSE 8501

CMD ["sh", "-c", "python -u app/main.py & streamlit run ui/streamlit_app.py --server.port=8501 --server.address=0.0.0.0"]