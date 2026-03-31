FROM node:20-bookworm-slim

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends python3 python3-pip python3-venv libgomp1 \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

COPY Backend/package.json Backend/package-lock.json ./Backend/
RUN cd Backend && npm ci --omit=dev

COPY Backend ./Backend
COPY predict_runtime.py ./predict_runtime.py
COPY bowler-DatsetFinal.csv ./bowler-DatsetFinal.csv
COPY international-mode.pkl ./international-mode.pkl
COPY local-mode.pkl ./local-mode.pkl

ENV NODE_ENV=production
ENV PYTHON_BIN=python3

WORKDIR /app/Backend

CMD ["npm", "start"]
