# Build stage
FROM public.ecr.aws/lambda/python:3.12 AS builder

# Install build dependencies
RUN dnf install -y wget tar xz gcc gcc-c++ && dnf clean all

# Download and extract FFmpeg
RUN cd /tmp && \
    wget -q https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz && \
    tar xf ffmpeg-master-latest-linux64-gpl.tar.xz && \
    cp ffmpeg-master-latest-linux64-gpl/bin/ffmpeg /usr/local/bin/ && \
    cp ffmpeg-master-latest-linux64-gpl/bin/ffprobe /usr/local/bin/ && \
    chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe && \
    rm -rf /tmp/ffmpeg-*

# Install Python dependencies and copy app code for cleanup
COPY requirements.txt /tmp/
COPY layers/auto-vid-shared/ /tmp/app-code/
COPY src/video_processor/ /tmp/app-code/
RUN pip install --no-cache-dir --target /tmp/python-packages -r /tmp/requirements.txt && \
    # Safe cleanup only
    find /tmp/python-packages -name "*.pyc" -delete && \
    find /tmp/python-packages -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /tmp/app-code -name "*.pyc" -delete 2>/dev/null || true && \
    find /tmp/app-code -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Runtime stage
FROM public.ecr.aws/lambda/python:3.12

# Copy FFmpeg binaries from builder
COPY --from=builder /usr/local/bin/ffmpeg /usr/local/bin/ffmpeg
COPY --from=builder /usr/local/bin/ffprobe /usr/local/bin/ffprobe

# Copy cleaned packages and app code from builder
COPY --from=builder /tmp/python-packages /var/task/
COPY --from=builder /tmp/app-code/ /var/task/

# Set FFmpeg path for MoviePy
ENV FFMPEG_BINARY=/usr/local/bin/ffmpeg
ENV IMAGEIO_FFMPEG_EXE=/usr/local/bin/ffmpeg

# Set working directory
WORKDIR /var/task

# Set the CMD to your handler
CMD ["app.lambda_handler"]