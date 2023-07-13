docker buildx -t marcobartoli/fp .
docker run -v "$PWD/project:/final/project" -p 8000:8000 marcobartoli/fp