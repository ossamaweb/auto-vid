FROM public.ecr.aws/lambda/python:3.11

# Copy requirements and install Python dependencies
COPY requirements.txt /var/task/
RUN pip install -r /var/task/requirements.txt

# Copy function code
COPY src/video_processor/ /var/task/

# Set the CMD to your handler
CMD ["app.lambda_handler"]