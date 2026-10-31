FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV LOAD_DATA=1
EXPOSE 8501
# Loads the synthetic data into Exasol (unless LOAD_DATA=0), then starts the dashboard
CMD ["sh", "-c", "[ \"$LOAD_DATA\" = \"0\" ] || python load_data.py; exec python -m streamlit run app.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true"]
