FROM python:3.10

WORKDIR /app

# Copy requirements from project root directory to app directory
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --retries 10 --timeout 1000 -r /app/requirements.txt

#Expose 5050 for FastAPI
EXPOSE 5050

#run command to start FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5050", "--loop", "asyncio", "--reload"]