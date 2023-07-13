FROM python:3.11

# Set the working directory in the container
WORKDIR /final

# Install Poetry
RUN pip install poetry==1.5.0

COPY pyproject.toml .

# Install project dependencies using Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY . .

# Expose any necessary ports
EXPOSE 8000

CMD ["poetry", "run", "start"]