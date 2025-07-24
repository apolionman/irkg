FROM nvidia/cuda:11.7.1-devel-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# -------------------------------
# Set working directory
# -------------------------------
WORKDIR /app

# -------------------------------
# System dependencies
# -------------------------------
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev \
    git curl nano build-essential \
    libportaudio2 libportaudiocpp0 portaudio19-dev ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set python as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# -------------------------------
# Python environment setup
# -------------------------------
RUN python -m pip install --upgrade pip setuptools wheel packaging

# -------------------------------
# Install PyTorch (cu117)
# -------------------------------
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117

# -------------------------------
# Install DGL manually (cu121-compatible wheel)
# -------------------------------
RUN pip install  dgl -f https://data.dgl.ai/wheels/torch-2.1/cu121/repo.html

# -------------------------------
# Install application dependencies
# -------------------------------
COPY requirements.txt ./
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu117

# -------------------------------
# Copy rest of the app
# -------------------------------
COPY . .

# -------------------------------
# Expose port and run app
# -------------------------------
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]