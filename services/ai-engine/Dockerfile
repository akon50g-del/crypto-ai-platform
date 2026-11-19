FROM python:3.12-slim
WORKDIR /app
# TA-Lib (اختياري): يُبنى من المصدر عند الحاجة؛ المحرك يعمل بدونه بتنفيذ Python نقي
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential wget && \
#     wget https://github.com/TA-Lib/ta-lib/releases/download/v0.6.4/ta-lib-0.6.4-src.tar.gz && \
#     tar -xzf ta-lib-0.6.4-src.tar.gz && cd ta-lib-0.6.4 && ./configure --prefix=/usr && make && make install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY tests ./tests
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
