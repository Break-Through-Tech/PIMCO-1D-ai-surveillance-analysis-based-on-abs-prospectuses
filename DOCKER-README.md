### 1. Build the Docker image
 
From the project root:
```bash
docker build -t pimco-1d .
```
 
### 2. Start the container
 
This mounts your local `data/` folder and the whole project directory into the container, so file edits and data changes are picked up live without rebuilding the image.
 
```bash
docker run -d --name pimco-container -v "$(pwd)/data:/app/data" -v "$(pwd):/app" pimco-1d tail -f /dev/null
```
 
Check it's running:
```bash
docker ps
```
You should see `pimco-container` with status "Up."
 
> **Windows users:** `$(pwd)` is bash syntax. In PowerShell use `${PWD}` instead; in Git Bash the command above should work as-is.
 
### 3. Run the extraction pipeline
 
```bash
docker exec -it pimco-container python3 src/extraction/run_extraction.py
```
 
This processes every filing in `data/`, and writes results to `data/processed/`:
- `data/processed/text/` — clean paragraph text per filing, with real tables rendered inline as Markdown
- `data/processed/tables/` — each kept table saved as its own CSV, named `<filing>__table<id>.csv`
- `data/processed/tables/toc/` — tables classified as table-of-contents, saved separately
- `data/processed/extraction_log.json` — a per-file summary (table counts, text length, any errors) 
 
### Useful commands
 
| Task | Command |
|---|---|
| Check if the container is running | `docker ps` |
| Start a stopped container | `docker start pimco-container` |
| Run any script inside the container | `docker exec -it pimco-container python3 <path/to/script.py>` |
| Open a shell inside the container | `docker exec -it pimco-container bash` |
| Stop the container | `docker stop pimco-container` |
| Remove the container (e.g. to rebuild fresh) | `docker rm pimco-container` |
 
### Troubleshooting
 
- **`ModuleNotFoundError`**: you're likely running a script with your local `python3` instead of inside the container. Use `docker exec -it pimco-container python3 ...` to run it with the container's installed dependencies.
- **Container not picking up code changes**: confirm the container was started with the `-v "$(pwd):/app"` mount (see step 2). Check with `docker inspect pimco-container --format '{{json .Mounts}}'`.