# Setting Up Ollama on GCP VM with GPU Support

This guide walks you through the process of installing and configuring Ollama on a Google Cloud Platform (GCP) Virtual Machine with GPU acceleration.

## Prerequisites

- A running GCP VM instance with GPU(s) attached
- Ubuntu/Debian-based Linux distribution (based on your `.bashrc` configuration)
- CUDA drivers installed
- Sudo privileges

## Step 1: Install NVIDIA Drivers and CUDA (if not already installed)

First, check if NVIDIA drivers are already installed:

```bash
nvidia-smi
```

If not installed, follow these steps:

```bash
# Add NVIDIA package repositories
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"

# Install NVIDIA drivers and CUDA
sudo apt-get update
sudo apt-get -y install cuda-drivers cuda
```

## Step 2: Install Ollama

Install Ollama using the official installation script:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

## Step 3: Verify Installation

After installation, verify that Ollama is working correctly:

```bash
ollama --version
```

## Step 4: Configure Ollama to Use GPU

Ollama should automatically detect and use available GPUs. You can verify GPU usage by running:

```bash
# Pull a model
ollama pull llama2  
# ollama run dengcao/Qwen3-Embedding-4B

# Run a model with GPU stats visible
ollama run llama2 "Explain how GPUs accelerate AI workloads"
```

While the model is running, you can check GPU utilization in another terminal:

```bash
nvidia-smi
```

## Step 5: Create a Systemd Service (Optional)

To run Ollama as a service that starts automatically:

```bash
sudo tee /etc/systemd/system/ollama.service > /dev/null << EOF
[Unit]
Description=Ollama Service
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/usr/local/bin/ollama serve
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl enable ollama.service
sudo systemctl start ollama.service
```

## Step 6: Add Ollama to Your Path (Optional)

Add an alias to your `.bashrc` file for convenience:

```bash
echo 'alias ollama-start="sudo systemctl start ollama.service"' >> ~/.bashrc
echo 'alias ollama-stop="sudo systemctl stop ollama.service"' >> ~/.bashrc
echo 'alias ollama-status="sudo systemctl status ollama.service"' >> ~/.bashrc
source ~/.bashrc
```

## Step 7: Pull and Run Models

Pull models you want to use:

```bash
# Pull models
ollama pull llama2
ollama pull mistral
ollama pull gemma:7b

# Run a model
ollama run llama2
ollama run qwen3:0.6b --think=false
```

## Step 8: Run Qwen3 in no_thinking mode

```shell
ollama run qwen3:0.6b --think=false
```

## Common Issues and Troubleshooting

### CUDA Not Found

If Ollama can't find CUDA, ensure your environment variables are set correctly:

```bash
export PATH="/usr/local/cuda/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:$LD_LIBRARY_PATH"
```

Add these to your `.bashrc` file for persistence.

### Memory Issues

If you encounter out-of-memory errors, try using a smaller model or increase your swap space:

```bash
# Create a 16GB swap file
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

To make the swap permanent, add to `/etc/fstab`:
```
/swapfile swap swap defaults 0 0
```

### Firewall Configuration

If you need to access Ollama from other machines, configure the firewall:

```bash
# Allow Ollama's default port
sudo ufw allow 11434/tcp
sudo ufw reload
```

## Additional Resources

- [Ollama Official Documentation](https://ollama.com/docs)
- [Ollama GitHub Repository](https://github.com/ollama/ollama)
- [NVIDIA CUDA Documentation](https://docs.nvidia.com/cuda/)

## Using Ollama with Python

To use Ollama with Python applications:

```bash
pip install ollama
```

Example Python code:

```python
import ollama

# Generate a response
response = ollama.generate(model='llama2', prompt='Why is the sky blue?')
print(response['response'])

# Chat completion
messages = [
    {'role': 'user', 'content': 'Explain quantum computing in simple terms'}
]
response = ollama.chat(model='llama2', messages=messages)
print(response['message']['content'])
```

---

Happy coding with Ollama on your GCP GPU VM!