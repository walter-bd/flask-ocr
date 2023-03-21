# Flask OCR pdf

A little flask app to OCR your pdfs and make it searchable. 

Requirements:

- Docker

Installation in Linux environments:

```bash
docker build -t ocr-flask-app .
```

To run it:

```bash
docker run -it -p 80:80 --rm -v ./.paddleocr:/root/.paddleocr ocr-flask-app
```

Go to http://localhost and proceed to upload your pdf and try the service.