FROM public.ecr.aws/lambda/python:3.9

RUN yum install -y python-pip python-pillow python-cffi python3-brotli pango gdk-pixbuf2
COPY *.py requirements.txt ./
COPY fonts ./fonts
COPY geojson ./geojson
COPY templates ./templates
RUN python3.9 -m pip install -r requirements.txt -t . --upgrade

# Command can be overwritten by providing a different command in the template directly.
CMD ["app.lambda_handler"]