FROM continuumio/miniconda3:latest

# Set working directory
WORKDIR /app

# Create environment with Python 3.10 and install dependencies
RUN conda create -y -n streamlit-env -c conda-forge python=3.10 streamlit pyarrow httpx \
    && conda clean -afy \
    && conda run -n streamlit-env pip install streamlit-authenticator

# Copy your app code into the container
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Run Streamlit inside the conda environment
CMD ["conda", "run", "--no-capture-output", "-n", "streamlit-env", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
