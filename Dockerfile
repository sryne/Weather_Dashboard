FROM python:3.8

ADD Weather.py .

COPY requirements.txt /'Weather Monitor'/requirements.txt

RUN pip install -r requirements.txt

CMD ["python", "./Weather.py"]