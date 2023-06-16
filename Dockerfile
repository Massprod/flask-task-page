FROM python:alpine

LABEL authors="Massprod"

WORKDIR /flask-task-page

COPY requirements.txt .

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

COPY . .

EXPOSE 5000:5000/tcp

CMD ["gunicorn", "--workers=2", "-b 0.0.0.0:5000", "main:app"]