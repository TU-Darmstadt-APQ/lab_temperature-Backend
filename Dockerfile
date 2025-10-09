FROM alpine:3.22.2 AS base
FROM base AS builder

COPY . /app

RUN COLOUR='\e[1;93m' && \
  echo -e "${COLOUR}Installing build dependencies...\e[0m" && \
  apk --no-cache add --virtual=build-dependencies \
    openssh-client-common \
    openssh-client-default \
    git \
    py3-pip && \
  echo -e "${COLOUR}Done.\e[0m"

# Define the python virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv --upgrade-deps $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN COLOUR='\e[1;93m' && \
  echo -e "${COLOUR}Installing Labnode PID daemon...\e[0m" && \
  pip install ./app && \
  echo -e "${COLOUR}Done.\e[0m"

FROM base AS runner
LABEL maintainer="Patrick Baus <patrick.baus@physik.tu-darmstadt.de>"
LABEL description="Labnode PID controller daemon"

ARG WORKER_USER_ID=5555
ARG SENSOR_IP=localhost

# Upgrade installed packages,
# add a user called `worker`
# Then install Python dependency
RUN apk --no-cache upgrade && \
    addgroup -g ${WORKER_USER_ID} worker && \
    adduser -D -u ${WORKER_USER_ID} -G worker worker && \
    apk --no-cache add python3

COPY --from=builder /opt/venv /opt/venv

# Enable venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=builder /app /app
RUN chown -R worker:worker /app

USER worker

CMD ["python3", "-OO", "-u", "/app/temperature_controller.py"]
